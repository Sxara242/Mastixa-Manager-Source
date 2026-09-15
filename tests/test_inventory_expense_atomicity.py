import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.expense_sync import delete_expense, ensure_expense_source_schema, sync_expense
from app.inventory_sync import ensure_inventory_source_schema


class InventoryExpenseAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Database(Path(self.tempdir.name) / "phase10c.db")
        self.db.execute(
            """
            CREATE TABLE inventory_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT '',
                minimum_stock REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE inventory_movements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_date TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                field_id INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_inventory_source_schema(self.db)
        ensure_expense_source_schema(self.db)
        self.item_id = int(
            self.db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('Λίπασμα 20-10-10','Λίπασμα','kg',0,'')
                """
            )
        )

    def _receipt(
        self,
        *,
        quantity: float = 10.0,
        unit_price: float = 2.5,
        supplier: str = "Supplier A",
        notes: str = "first",
    ) -> int:
        return int(
            self.db.execute(
                """
                INSERT INTO inventory_movements(
                    movement_date,item_id,movement_type,quantity,field_id,notes,
                    partner_id,supplier_name,unit_price,total_cost
                )
                VALUES('2026-09-11',?,'Παραλαβή',?,NULL,?,NULL,?,?,?)
                """,
                (
                    self.item_id,
                    quantity,
                    notes,
                    supplier,
                    unit_price,
                    quantity * unit_price,
                ),
            )
        )

    def _expense(self, movement_id: int):
        return self.db.query_one(
            """
            SELECT * FROM expenses
            WHERE source_type='inventory_receipt' AND source_id=?
            ORDER BY id LIMIT 1
            """,
            (movement_id,),
        )

    def test_expense_failure_rolls_back_receipt_movement(self):
        self.db.execute(
            """
            CREATE TRIGGER fail_inventory_receipt_expense
            BEFORE INSERT ON expenses
            WHEN NEW.source_type='inventory_receipt'
            BEGIN
                SELECT RAISE(ABORT, 'forced_expense_failure');
            END
            """
        )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "forced_expense_failure",
        ):
            self._receipt()

        movements = self.db.query_one(
            "SELECT COUNT(*) AS total FROM inventory_movements"
        )
        expenses = self.db.query_one(
            """
            SELECT COUNT(*) AS total FROM expenses
            WHERE source_type='inventory_receipt'
            """
        )
        self.assertEqual(0, int(movements["total"]))
        self.assertEqual(0, int(expenses["total"]))

    def test_receipt_insert_and_update_project_expense_in_same_statement(self):
        movement_id = self._receipt()
        expense = self._expense(movement_id)
        self.assertIsNotNone(expense)
        original_expense_id = int(expense["id"])
        self.assertAlmostEqual(25.0, float(expense["amount"]))
        self.assertEqual("Supplier A", expense["supplier"])
        self.assertEqual(
            "Παραλαβή αποθήκης — Λίπασμα 20-10-10",
            expense["description"],
        )
        self.assertIn("#" + str(movement_id), expense["notes"])
        self.assertIn("first", expense["notes"])

        self.db.execute(
            """
            UPDATE inventory_movements
            SET quantity=4, unit_price=3, total_cost=12,
                supplier_name='Supplier B', notes='edited'
            WHERE id=?
            """,
            (movement_id,),
        )
        expense = self._expense(movement_id)
        self.assertIsNotNone(expense)
        self.assertEqual(original_expense_id, int(expense["id"]))
        self.assertAlmostEqual(12.0, float(expense["amount"]))
        self.assertEqual("Supplier B", expense["supplier"])
        self.assertIn("edited", expense["notes"])

        # The legacy UI compatibility call must be idempotent and reuse the
        # trigger-projected expense rather than creating/updating a second row.
        synced_id = sync_expense(
            self.db,
            source_type="inventory_receipt",
            source_id=movement_id,
            entry_date="2026-09-11",
            category="Αποθήκη & Εφόδια",
            description="Παραλαβή αποθήκης — Λίπασμα 20-10-10",
            supplier="Supplier B",
            payment_method="",
            amount=12.0,
            notes="compatibility call",
            partner_id=None,
        )
        self.assertEqual(original_expense_id, synced_id)
        count = self.db.query_one(
            """
            SELECT COUNT(*) AS total FROM expenses
            WHERE source_type='inventory_receipt' AND source_id=?
            """,
            (movement_id,),
        )
        self.assertEqual(1, int(count["total"]))
        self.assertIn("edited", self._expense(movement_id)["notes"])

    def test_changing_receipt_semantics_removes_and_recreates_projection(self):
        movement_id = self._receipt()
        self.assertIsNotNone(self._expense(movement_id))

        self.db.execute(
            """
            UPDATE inventory_movements
            SET movement_type='Διόρθωση +', total_cost=0, unit_price=0
            WHERE id=?
            """,
            (movement_id,),
        )
        self.assertIsNone(self._expense(movement_id))

        self.db.execute(
            """
            UPDATE inventory_movements
            SET movement_type='Παραλαβή', quantity=5,
                unit_price=2, total_cost=10
            WHERE id=?
            """,
            (movement_id,),
        )
        expense = self._expense(movement_id)
        self.assertIsNotNone(expense)
        self.assertAlmostEqual(10.0, float(expense["amount"]))

    def test_rejected_movement_delete_cannot_delete_linked_expense(self):
        receipt_id = self._receipt(quantity=10.0, unit_price=2.0)
        self.db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,field_id,notes
            ) VALUES('2026-09-11',?,'Κατανάλωση',8,NULL,'used')
            """,
            (self.item_id,),
        )
        self.assertIsNotNone(self._expense(receipt_id))

        # This is the exact legacy UI order: delete_expense() is called before
        # DELETE inventory_movements.  Phase 10C keeps the expense until the
        # movement DELETE really succeeds.
        delete_expense(
            self.db,
            source_type="inventory_receipt",
            source_id=receipt_id,
        )
        self.assertIsNotNone(self._expense(receipt_id))

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_negative_stock",
        ):
            self.db.execute(
                "DELETE FROM inventory_movements WHERE id=?",
                (receipt_id,),
            )

        self.assertIsNotNone(
            self.db.query_one(
                "SELECT id FROM inventory_movements WHERE id=?",
                (receipt_id,),
            )
        )
        self.assertIsNotNone(self._expense(receipt_id))

    def test_successful_movement_delete_removes_linked_expense_atomically(self):
        receipt_id = self._receipt(quantity=10.0, unit_price=2.0)
        self.assertIsNotNone(self._expense(receipt_id))

        delete_expense(
            self.db,
            source_type="inventory_receipt",
            source_id=receipt_id,
        )
        self.assertIsNotNone(self._expense(receipt_id))

        self.db.execute(
            "DELETE FROM inventory_movements WHERE id=?",
            (receipt_id,),
        )
        self.assertIsNone(
            self.db.query_one(
                "SELECT id FROM inventory_movements WHERE id=?",
                (receipt_id,),
            )
        )
        self.assertIsNone(self._expense(receipt_id))


if __name__ == "__main__":
    unittest.main()
