from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.backup_manager import BackupManager
from app.database import Database
from app.inventory import InventoryPage
from app.inventory_sync import current_stock, sync_consumption


class InventoryQualityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def _database(self, name: str) -> tuple[tempfile.TemporaryDirectory, Database]:
        tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tempdir.cleanup)
        db = Database(Path(tempdir.name) / name)
        return tempdir, db

    def _page(self, db: Database) -> InventoryPage:
        page = InventoryPage(db)
        self.addCleanup(page.close)
        return page

    def test_inventory_page_low_stock_metrics_statuses_and_filter(self):
        _tempdir, db = self._database("inventory-ui.db")
        page = self._page(db)

        ok_id = int(
            db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('A OK','Λίπασμα','kg',5,'')
                """
            )
        )
        low_id = int(
            db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('B Low','Λίπασμα','kg',5,'')
                """
            )
        )
        db.execute(
            """
            INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
            VALUES('C Empty','Λίπασμα','kg',5,'')
            """
        )
        db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,field_id,notes
            ) VALUES('2026-09-11',?,'Παραλαβή',10,NULL,'opening')
            """,
            (ok_id,),
        )
        db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,field_id,notes
            ) VALUES('2026-09-11',?,'Παραλαβή',4,NULL,'opening')
            """,
            (low_id,),
        )

        page.refresh()
        self.assertEqual("3", page.items_metric[1].text())
        self.assertEqual("2", page.low_metric[1].text())
        self.assertEqual("1", page.zero_metric[1].text())

        statuses = {
            page.stock_table.item(row, 0).text(): page.stock_table.item(row, 5).text()
            for row in range(page.stock_table.rowCount())
        }
        stocks = {
            page.stock_table.item(row, 0).text(): page.stock_table.item(row, 3).text()
            for row in range(page.stock_table.rowCount())
        }
        self.assertEqual(
            {"A OK": "OK", "B Low": "Χαμηλό", "C Empty": "Εξαντλήθηκε"},
            statuses,
        )
        self.assertEqual("10", stocks["A OK"])
        self.assertEqual("4", stocks["B Low"])
        self.assertEqual("0", stocks["C Empty"])

        page.low_only.setCurrentIndex(page.low_only.findData("low"))
        self.qt.processEvents()
        self.assertEqual(2, page.stock_table.rowCount())
        self.assertEqual(
            {"B Low", "C Empty"},
            {
                page.stock_table.item(row, 0).text()
                for row in range(page.stock_table.rowCount())
            },
        )

    def test_backup_restore_preserves_inventory_provenance_expense_and_triggers(self):
        tempdir, db = self._database("inventory-backup.db")
        page = self._page(db)

        item_id = int(
            db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('Θείο','Φυτοπροστασία','kg',2,'')
                """
            )
        )
        receipt_id = int(
            db.execute(
                """
                INSERT INTO inventory_movements(
                    movement_date,item_id,movement_type,quantity,field_id,notes,
                    partner_id,supplier_name,unit_price,total_cost
                ) VALUES('2026-09-11',?,'Παραλαβή',10,NULL,'receipt',
                         NULL,'Supplier',2.5,25)
                """,
                (item_id,),
            )
        )
        sync_consumption(
            db,
            source_type="farm_activity",
            source_id=501,
            movement_date="2026-09-11",
            item_id=item_id,
            quantity=2,
            field_id=None,
            notes="owner consumption",
        )
        self.assertAlmostEqual(8.0, current_stock(db, item_id))
        expense = db.query_one(
            """
            SELECT id,amount FROM expenses
            WHERE source_type='inventory_receipt' AND source_id=?
            """,
            (receipt_id,),
        )
        self.assertIsNotNone(expense)
        self.assertAlmostEqual(25.0, float(expense["amount"]))

        manager = BackupManager(
            db.path,
            Path(tempdir.name) / "backups",
        )
        backup = manager.create_backup(prefix="phase10e")

        sync_consumption(
            db,
            source_type="farm_activity",
            source_id=501,
            movement_date="2026-09-12",
            item_id=item_id,
            quantity=4,
            field_id=None,
            notes="mutated after backup",
        )
        db.execute(
            """
            UPDATE inventory_movements
            SET unit_price=6,total_cost=60,notes='mutated receipt'
            WHERE id=?
            """,
            (receipt_id,),
        )
        self.assertAlmostEqual(6.0, current_stock(db, item_id))
        self.assertAlmostEqual(
            60.0,
            float(
                db.query_one(
                    """
                    SELECT amount FROM expenses
                    WHERE source_type='inventory_receipt' AND source_id=?
                    """,
                    (receipt_id,),
                )["amount"]
            ),
        )

        manager.restore_backup(backup)

        self.assertAlmostEqual(8.0, current_stock(db, item_id))
        source = db.query_one(
            """
            SELECT quantity,source_type,source_id,notes
            FROM inventory_movements
            WHERE source_type='farm_activity' AND source_id=501
            """
        )
        self.assertIsNotNone(source)
        self.assertAlmostEqual(2.0, float(source["quantity"]))
        self.assertEqual("farm_activity", source["source_type"])
        self.assertEqual(501, int(source["source_id"]))
        self.assertEqual("owner consumption", source["notes"])

        restored_expense = db.query_one(
            """
            SELECT amount FROM expenses
            WHERE source_type='inventory_receipt' AND source_id=?
            """,
            (receipt_id,),
        )
        self.assertIsNotNone(restored_expense)
        self.assertAlmostEqual(25.0, float(restored_expense["amount"]))

        # The restored database must retain the Phase 10C projection trigger,
        # not only the rows that happened to exist at backup time.
        db.execute(
            """
            UPDATE inventory_movements
            SET unit_price=3,total_cost=30,notes='after restore'
            WHERE id=?
            """,
            (receipt_id,),
        )
        self.assertAlmostEqual(
            30.0,
            float(
                db.query_one(
                    """
                    SELECT amount FROM expenses
                    WHERE source_type='inventory_receipt' AND source_id=?
                    """,
                    (receipt_id,),
                )["amount"]
            ),
        )

        page.refresh()
        self.assertEqual("1", page.items_metric[1].text())

    def test_legacy_inventory_schema_migrates_without_losing_stock_or_guards(self):
        _tempdir, db = self._database("legacy-inventory.db")
        db.execute(
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
        db.execute(
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
        first_item = int(
            db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('Legacy A','Λίπασμα','kg',1,'legacy')
                """
            )
        )
        second_item = int(
            db.execute(
                """
                INSERT INTO inventory_items(name,category,unit,minimum_stock,notes)
                VALUES('Legacy B','Λίπασμα','kg',1,'legacy')
                """
            )
        )
        receipt_id = int(
            db.execute(
                """
                INSERT INTO inventory_movements(
                    movement_date,item_id,movement_type,quantity,field_id,notes
                ) VALUES('2025-01-01',?,'Παραλαβή',5,NULL,'legacy receipt')
                """,
                (first_item,),
            )
        )
        db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,field_id,notes
            ) VALUES('2025-01-02',?,'Κατανάλωση',4,NULL,'legacy use')
            """,
            (first_item,),
        )

        page = self._page(db)
        page.refresh()

        columns = {
            row["name"]
            for row in db.query("PRAGMA table_info(inventory_movements)")
        }
        self.assertTrue(
            {
                "source_type",
                "source_id",
                "partner_id",
                "supplier_name",
                "unit_price",
                "total_cost",
                "expense_id",
            }.issubset(columns)
        )
        self.assertAlmostEqual(1.0, current_stock(db, first_item))

        trigger_names = {
            row["name"]
            for row in db.query(
                """
                SELECT name FROM sqlite_master
                WHERE type='trigger' AND name LIKE 'inventory_%'
                """
            )
        }
        self.assertIn("inventory_item_unit_immutable_after_history", trigger_names)
        self.assertIn("inventory_manual_movement_item_immutable", trigger_names)
        self.assertIn("inventory_delete_preserves_nonnegative_stock", trigger_names)
        self.assertIn("inventory_receipt_expense_after_insert", trigger_names)
        self.assertIn("inventory_receipt_expense_after_update", trigger_names)
        self.assertIn("inventory_receipt_expense_after_delete", trigger_names)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_unit_has_history",
        ):
            db.execute(
                "UPDATE inventory_items SET unit='L' WHERE id=?",
                (first_item,),
            )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_manual_item_immutable",
        ):
            db.execute(
                "UPDATE inventory_movements SET item_id=? WHERE id=?",
                (second_item, receipt_id),
            )

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "inventory_negative_stock",
        ):
            db.execute(
                "DELETE FROM inventory_movements WHERE id=?",
                (receipt_id,),
            )

        self.assertAlmostEqual(1.0, current_stock(db, first_item))


if __name__ == "__main__":
    unittest.main()
