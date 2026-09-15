import json
import sqlite3
import unittest
from pathlib import Path

from app.inventory_sync import (
    InventoryStockError,
    current_stock,
    ensure_can_consume,
    ensure_inventory_source_schema,
    sync_consumption,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "phase10_inventory_ledger.json"
ANDROID_FIXTURE = (
    ROOT
    / "android"
    / "app"
    / "src"
    / "androidTest"
    / "assets"
    / "phase10_inventory_ledger.json"
)


class _Db:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def execute(self, sql, params=()):
        return self.connection.execute(sql, tuple(params))

    def query(self, sql, params=()):
        return list(self.connection.execute(sql, tuple(params)).fetchall())

    def query_one(self, sql, params=()):
        return self.connection.execute(sql, tuple(params)).fetchone()


class InventoryLedgerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _Db()
        self.addCleanup(self.db.close)
        self.db.execute(
            """
            CREATE TABLE inventory_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT ''
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

    def _item(self, name="Fixture", unit="kg") -> int:
        cursor = self.db.execute(
            "INSERT INTO inventory_items(name,unit) VALUES(?,?)",
            (name, unit),
        )
        return int(cursor.lastrowid)

    def _movement(
        self,
        item_id: int,
        movement_type: str,
        quantity: float,
        *,
        source_type: str = "",
        source_id: int | None = None,
    ) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,
                field_id,notes,source_type,source_id
            ) VALUES('2026-09-11',?,?,?,?,?,?,?)
            """,
            (
                item_id,
                movement_type,
                quantity,
                None,
                "fixture",
                source_type,
                source_id,
            ),
        )
        return int(cursor.lastrowid)

    def test_shared_fixture_is_byte_identical_and_has_same_running_stock(self):
        fixture_text = FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(
            fixture_text,
            ANDROID_FIXTURE.read_text(encoding="utf-8"),
        )
        fixture = json.loads(fixture_text)
        item_id = self._item()

        signed = {
            "Παραλαβή": 1.0,
            "Κατανάλωση": -1.0,
            "Διόρθωση +": 1.0,
            "Διόρθωση -": -1.0,
        }
        running = 0.0
        ids = {}
        for movement in fixture["movements"]:
            running += signed[movement["type"]] * float(movement["quantity"])
            self.assertAlmostEqual(
                float(movement["running_stock"]),
                running,
            )
            ids[movement["id"]] = self._movement(
                item_id,
                movement["type"],
                movement["quantity"],
            )

        self.assertAlmostEqual(
            float(fixture["expected_final_stock"]),
            current_stock(self.db, item_id),
        )
        self.assertAlmostEqual(
            18.0,
            current_stock(self.db, item_id, ids["m2"]),
        )

    def test_consumption_guard_uses_ledger_balance(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        item_id = self._item()
        for movement in fixture["movements"]:
            self._movement(
                item_id,
                movement["type"],
                movement["quantity"],
            )

        ensure_can_consume(
            self.db,
            item_id=item_id,
            quantity=float(fixture["exact_consume_allowed"]),
            source_type="farm_activity",
            source_id=100,
        )
        with self.assertRaises(InventoryStockError) as raised:
            ensure_can_consume(
                self.db,
                item_id=item_id,
                quantity=float(fixture["over_consume_rejected"]),
                source_type="farm_activity",
                source_id=101,
            )
        self.assertAlmostEqual(
            float(fixture["expected_final_stock"]),
            raised.exception.available,
        )

    def test_item_unit_cannot_change_after_movement_history(self):
        item_id = self._item(unit="kg")
        self._movement(item_id, "Παραλαβή", 5.0)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_unit_has_history",
        ):
            self.db.execute(
                "UPDATE inventory_items SET unit='L' WHERE id=?",
                (item_id,),
            )

        row = self.db.query_one(
            "SELECT unit FROM inventory_items WHERE id=?",
            (item_id,),
        )
        self.assertEqual("kg", row["unit"])

    def test_manual_movement_item_identity_is_immutable(self):
        first = self._item("First")
        second = self._item("Second")
        movement_id = self._movement(first, "Παραλαβή", 5.0)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_manual_item_immutable",
        ):
            self.db.execute(
                "UPDATE inventory_movements SET item_id=? WHERE id=?",
                (second, movement_id),
            )

        row = self.db.query_one(
            "SELECT item_id FROM inventory_movements WHERE id=?",
            (movement_id,),
        )
        self.assertEqual(first, int(row["item_id"]))

    def test_automatic_source_can_reassign_item_through_owner(self):
        first = self._item("First")
        second = self._item("Second")
        self._movement(first, "Παραλαβή", 10.0)
        self._movement(second, "Παραλαβή", 10.0)

        sync_consumption(
            self.db,
            source_type="farm_activity",
            source_id=77,
            movement_date="2026-09-11",
            item_id=first,
            quantity=2.0,
            field_id=None,
            notes="first",
        )
        sync_consumption(
            self.db,
            source_type="farm_activity",
            source_id=77,
            movement_date="2026-09-11",
            item_id=second,
            quantity=2.0,
            field_id=None,
            notes="moved by owner",
        )

        row = self.db.query_one(
            """
            SELECT item_id FROM inventory_movements
            WHERE source_type='farm_activity' AND source_id=77
            """
        )
        self.assertEqual(second, int(row["item_id"]))

    def test_delete_positive_movement_cannot_make_stock_negative(self):
        item_id = self._item()
        receipt_id = self._movement(item_id, "Παραλαβή", 10.0)
        self._movement(item_id, "Κατανάλωση", 8.0)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_negative_stock",
        ):
            self.db.execute(
                "DELETE FROM inventory_movements WHERE id=?",
                (receipt_id,),
            )

        self.assertAlmostEqual(2.0, current_stock(self.db, item_id))

    def test_delete_is_allowed_when_projected_stock_stays_nonnegative(self):
        item_id = self._item()
        removable_receipt = self._movement(item_id, "Παραλαβή", 5.0)
        self._movement(item_id, "Παραλαβή", 10.0)
        self._movement(item_id, "Κατανάλωση", 8.0)

        self.db.execute(
            "DELETE FROM inventory_movements WHERE id=?",
            (removable_receipt,),
        )

        self.assertAlmostEqual(2.0, current_stock(self.db, item_id))


if __name__ == "__main__":
    unittest.main()
