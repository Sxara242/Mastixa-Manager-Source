from __future__ import annotations

import importlib
import csv
import io
import pkgutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QLabel

import app
import app.main_window as main_window
from app.database import Database
from app.expense_sync import delete_expense, sync_expense
from app.inventory_sync import (
    InventoryStockError,
    current_stock,
    delete_consumption,
    sync_consumption,
)
from app.year_lock import ensure_year_lock_schema, is_year_locked


class StabilizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp_dir.name)
        self.db = Database(self.root / "legacy.db")

        self.original_database = main_window.Database
        self.original_base_dir = main_window.BASE_DIR
        main_window.Database = lambda: self.db
        main_window.BASE_DIR = self.root
        self.window = main_window.MainWindow()

    def tearDown(self) -> None:
        self.window.close()
        main_window.Database = self.original_database
        main_window.BASE_DIR = self.original_base_dir
        self.temp_dir.cleanup()

    def test_all_modules_import_and_all_pages_refresh(self) -> None:
        for module in pkgutil.walk_packages(app.__path__, app.__name__ + "."):
            importlib.import_module(module.name)
        self.assertGreaterEqual(len(self.window.pages), 31)
        self.assertGreaterEqual(self.window.category_list.count(), 6)
        self.assertIn("Προϊόντα", {name for name, _page in self.window.pages})
        self.assertNotIn(
            "Ρυθμίσεις Προϊόντων", {name for name, _page in self.window.pages}
        )
        for _name, page in self.window.pages:
            refresh = getattr(page, "refresh", None)
            if refresh is not None:
                refresh()

    def test_product_registry_starts_empty_crud_status_legacy_and_navigation(self) -> None:
        self.assertEqual(
            0,
            self.db.query_one("SELECT COUNT(*) AS n FROM products")["n"],
        )

        page = self.window.pages[30][1]
        page.name.setText("Ντομάτες")
        page.unit.setCurrentText("κιβώτια")
        page.save_product()
        tomato = self.db.query_one(
            "SELECT * FROM products WHERE name=?", ("Ντομάτες",)
        )
        self.assertIsNotNone(tomato)
        self.assertEqual("κιβώτια", tomato["unit"])

        page.refresh()
        tomato_row = next(
            row for row in range(page.table.rowCount())
            if page.table.item(row, 0).text() == "Ντομάτες"
        )
        page.load_product(tomato_row, 0)
        page.unit.setCurrentText("τεμάχια")
        page.save_product()
        self.assertEqual(
            "τεμάχια",
            self.db.query_one(
                "SELECT unit FROM products WHERE id=?", (tomato["id"],)
            )["unit"],
        )

        page.refresh()
        tomato_row = next(
            row for row in range(page.table.rowCount())
            if page.table.item(row, 0).text() == "Ντομάτες"
        )
        page.load_product(tomato_row, 0)
        page.toggle_status()
        self.assertEqual(
            0,
            self.db.query_one(
                "SELECT is_active FROM products WHERE id=?", (tomato["id"],)
            )["is_active"],
        )
        page.refresh()
        tomato_row = next(
            row for row in range(page.table.rowCount())
            if page.table.item(row, 0).text() == "Ντομάτες"
        )
        page.load_product(tomato_row, 0)
        page.toggle_status()
        self.assertEqual(
            1,
            self.db.query_one(
                "SELECT is_active FROM products WHERE id=?", (tomato["id"],)
            )["is_active"],
        )

        self.window.change_page(30)
        self.qt.processEvents()
        self.assertEqual(5, self.window.category_list.currentRow())
        self.assertEqual(30, self.window._current_page_index())

        legacy_path = self.root / "legacy_products.db"
        with sqlite3.connect(legacy_path) as con:
            con.execute(
                """CREATE TABLE production(
                    id INTEGER PRIMARY KEY,entry_date TEXT,field_id INTEGER,
                    product TEXT,quantity_kg REAL,notes TEXT DEFAULT ''
                )"""
            )
            con.execute(
                "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
                ("2025-01-01", "μαστίχα", 1),
            )
        legacy_db = Database(legacy_path)
        legacy_mastic = [
            row for row in legacy_db.query("SELECT * FROM products")
            if str(row["name"]).casefold() == "μαστίχα".casefold()
        ]
        self.assertEqual(1, len(legacy_mastic))
        self.assertEqual(1, legacy_mastic[0]["is_active"])
        retired_tables = {
            row["name"] for row in legacy_db.query(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertNotIn("product_connection_settings", retired_tables)
        self.assertNotIn("product_delivery_queue", retired_tables)

        for size in ((950, 650), (1200, 780), (1440, 900)):
            self.window.resize(*size)
            self.qt.processEvents()

    def test_report_navigation_uses_groups_and_reaches_every_page(self) -> None:
        report_indices = {8, 9, 10, 11, 20, 25, 27, 28, 29}
        grouped_indices = {
            page_index
            for _group, entries in self.window.report_groups
            for _label, page_index in entries
        }
        self.assertEqual(report_indices, grouped_indices)

        self.window.category_list.setCurrentRow(3)
        self.assertEqual(3, self.window.tabs.count())
        self.assertEqual(3, len(self.window._report_group_tabs))

        for page_index in sorted(report_indices):
            self.window.change_page(page_index)
            self.qt.processEvents()
            self.assertEqual(3, self.window.category_list.currentRow())
            self.assertEqual(page_index, self.window._current_page_index())
            page = self.window.pages[page_index][1]
            refresh = getattr(page, "refresh", None)
            if refresh is not None:
                refresh()

    def test_data_export_product_filter_and_unfiltered_export(self) -> None:
        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2026-08-01", "Μαστίχα Α", 10),
        )
        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2026-08-02", "Μαστίχα Β", 20),
        )
        self.db.execute(
            "INSERT INTO inventory_items(name,category,unit) VALUES(?,?,?)",
            ("Λίπασμα 20-20-20", "Λιπάσματα", "kg"),
        )
        page = self.window.pages[11][1]
        page.refresh()

        available_products = {
            page.product_filter.itemText(index)
            for index in range(page.product_filter.count())
        }
        self.assertIn("Μαστίχα Α", available_products)
        self.assertIn("Μαστίχα Β", available_products)
        self.assertNotIn("Λίπασμα 20-20-20", available_products)

        full_bytes, full_count = page._table_export_bytes("production")
        self.assertEqual(2, full_count)
        full_rows = list(csv.reader(io.StringIO(full_bytes.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(3, len(full_rows))

        page.product_filter_check.setChecked(True)
        page.product_filter.setCurrentIndex(
            page.product_filter.findText("Μαστίχα Α")
        )
        filtered_bytes, filtered_count = page._table_export_bytes(
            "production", page._selected_product()
        )
        self.assertEqual(1, filtered_count)
        filtered_rows = list(csv.reader(io.StringIO(filtered_bytes.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual("Μαστίχα Α", filtered_rows[1][3])

        # Common reference data remains complete while the filter is active.
        _fields_bytes, fields_count = page._table_export_bytes(
            "fields", page._selected_product()
        )
        self.assertEqual(
            self.db.query_one("SELECT COUNT(*) n FROM fields")["n"],
            fields_count,
        )

    def test_sale_creates_updates_and_deletes_exactly_one_income(self) -> None:
        partner_id = self.db.execute(
            "INSERT INTO business_partners(name,partner_type) VALUES(?,?)",
            ("Αγοραστής Test", "buyer"),
        )
        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2026-08-01", "Μαστίχα", 100),
        )
        page = self.window.pages[26][1]
        page.refresh()
        page.buyer.setCurrentIndex(page.buyer.findData(partner_id))
        mastic_id = self.db.query_one(
            "SELECT id FROM products WHERE name=?", ("Μαστίχα",)
        )["id"]
        page.product.setCurrentIndex(page.product.findData(mastic_id))
        page.quantity.setValue(10)
        page.price_per_kg.setValue(20)
        with patch(
            "app.sales.QMessageBox.warning",
            side_effect=AssertionError("unexpected sale validation warning"),
        ):
            page.save_sale()

        sale = self.db.query_one("SELECT * FROM production_sales")
        self.assertIsNotNone(sale)
        income_id = int(sale["income_id"])
        self.assertEqual(1, self.db.query_one("SELECT COUNT(*) n FROM income")["n"])
        self.assertEqual(200, self.db.query_one("SELECT amount FROM income WHERE id=?", (income_id,))["amount"])

        page.load_sale(0, 0)
        page.quantity.setValue(12)
        with patch(
            "app.sales.QMessageBox.warning",
            side_effect=AssertionError("unexpected sale validation warning"),
        ):
            page.save_sale()
        self.assertEqual(1, self.db.query_one("SELECT COUNT(*) n FROM income")["n"])
        self.assertEqual(240, self.db.query_one("SELECT amount FROM income WHERE id=?", (income_id,))["amount"])

        page.load_sale(0, 0)
        page.confirm_delete = lambda *_args: True
        page.delete_sale()
        self.assertEqual(0, self.db.query_one("SELECT COUNT(*) n FROM production_sales")["n"])
        self.assertEqual(0, self.db.query_one("SELECT COUNT(*) n FROM income")["n"])

    def test_product_registry_integration_active_inactive_legacy_and_reports(self) -> None:
        field_id = self.db.execute("INSERT INTO fields(name) VALUES(?)", ("Κτήμα",))
        walnut_id = self.db.execute(
            "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
            ("Καρύδια", "kg"),
        )

        production_page = self.window.pages[3][1]
        production_page.refresh()
        production_page.field.setCurrentIndex(
            production_page.field.findData(field_id)
        )
        production_page.product.setCurrentIndex(
            production_page.product.findData(walnut_id)
        )
        production_page.quantity.setValue(30)
        production_page.save_production()
        produced = self.db.query_one(
            "SELECT * FROM production WHERE product_id=?", (walnut_id,)
        )
        self.assertIsNotNone(produced)
        self.assertEqual("Καρύδια", produced["product"])

        self.db.execute(
            "UPDATE products SET name=? WHERE id=?", ("Καρύδια Premium", walnut_id)
        )
        production_page.refresh()
        renamed_link = self.db.query_one(
            "SELECT product,product_id FROM production WHERE id=?", (produced["id"],)
        )
        self.assertEqual(walnut_id, renamed_link["product_id"])
        self.assertEqual("Καρύδια", renamed_link["product"])

        self.db.execute(
            "UPDATE products SET is_active=0 WHERE id=?", (walnut_id,)
        )
        production_page.clear_form()
        self.assertEqual(-1, production_page.product.findData(walnut_id))
        production_page.refresh()
        production_page.load_selected(0, 0)
        self.assertGreaterEqual(production_page.product.findData(walnut_id), 0)
        self.assertEqual(walnut_id, production_page.product.currentData())

        buyer_id = self.db.execute(
            "INSERT INTO business_partners(name,partner_type) VALUES(?,?)",
            ("Αγοραστής Καρυδιών", "buyer"),
        )
        sale_id = self.db.execute(
            """INSERT INTO production_sales(
                sale_date,buyer_id,buyer_name,product,product_id,quantity_kg,
                price_per_kg,total_amount,payment_method,notes
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                "2026-08-10", buyer_id, "Αγοραστής Καρυδιών", "Καρύδια",
                walnut_id, 5, 4, 20, "", "legacy inactive edit",
            ),
        )
        sales_page = self.window.pages[26][1]
        sales_page.refresh()
        self.assertEqual(-1, sales_page.product.findData(walnut_id))
        sale_row = next(
            row for row in range(sales_page.table.rowCount())
            if sales_page.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == sale_id
        )
        sales_page.load_sale(sale_row, 0)
        self.assertEqual(walnut_id, sales_page.product.currentData())

        annual_page = self.window.pages[29][1]
        annual_page.refresh()
        self.assertGreaterEqual(annual_page.product_filter.findData(walnut_id), 0)
        annual_page.product_filter.setCurrentIndex(
            annual_page.product_filter.findData(walnut_id)
        )
        annual_page.refresh()
        self.assertEqual(1, annual_page.product_table.rowCount())
        self.assertEqual("Καρύδια Premium", annual_page.product_table.item(0, 0).text())

        self.db.execute(
            """INSERT INTO production(entry_date,field_id,product,quantity_kg,notes)
               VALUES(?,?,?,?,?)""",
            ("2024-01-01", field_id, "Legacy Σύκα", 2, ""),
        )
        production_page.refresh()
        legacy = self.db.query_one(
            """SELECT p.product_id,pr.name FROM production p
               JOIN products pr ON pr.id=p.product_id
               WHERE p.product='Legacy Σύκα'"""
        )
        self.assertIsNotNone(legacy)
        self.assertEqual("Legacy Σύκα", legacy["name"])

    def test_product_field_many_to_many_crud_uniqueness_and_legacy_backfill(self) -> None:
        page = self.window.pages[30][1]
        active_id = self.db.execute(
            "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
            ("Ελιές", "kg"),
        )
        inactive_id = self.db.execute(
            "INSERT INTO products(name,unit,is_active) VALUES(?,?,0)",
            ("Παλαιό προϊόν", "kg"),
        )
        field_a = self.db.execute("INSERT INTO fields(name) VALUES(?)", ("Α",))
        field_b = self.db.execute("INSERT INTO fields(name) VALUES(?)", ("Β",))
        page.refresh()
        self.assertGreaterEqual(page.link_product.findData(active_id), 0)
        self.assertEqual(-1, page.link_product.findData(inactive_id))

        for field_id in (field_a, field_b):
            page.link_product.setCurrentIndex(page.link_product.findData(active_id))
            page.link_field.setCurrentIndex(page.link_field.findData(field_id))
            page.add_link()
        second_product_id = self.db.execute(
            "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
            ("Αμύγδαλα", "kg"),
        )
        page.refresh()
        page.link_product.setCurrentIndex(
            page.link_product.findData(second_product_id)
        )
        page.link_field.setCurrentIndex(page.link_field.findData(field_a))
        page.add_link()
        self.assertEqual(
            3, self.db.query_one("SELECT COUNT(*) n FROM product_fields")["n"]
        )
        defaults = self.db.query_one(
            """SELECT variety,planting_date,cultivation_status
               FROM product_fields WHERE product_id=? AND field_id=?""",
            (active_id, field_b),
        )
        self.assertEqual("", defaults["variety"])
        self.assertEqual("", defaults["planting_date"])
        self.assertEqual("active", defaults["cultivation_status"])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO product_fields(product_id,field_id) VALUES(?,?)",
                (active_id, field_a),
            )

        self.db.execute(
            "UPDATE products SET is_active=0 WHERE id=?", (active_id,)
        )
        page.refresh()
        self.assertEqual(-1, page.link_product.findData(active_id))
        link_names = {
            page.links_table.item(row, 0).text()
            for row in range(page.links_table.rowCount())
        }
        self.assertIn("Ελιές", link_names)

        profile_row = next(
            row for row in range(page.links_table.rowCount())
            if page.links_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            == (active_id, field_b)
        )
        page.select_link(profile_row, 0)
        page.link_variety.setText("Καλαμών")
        page.link_date_enabled.setChecked(True)
        page.link_planting_date.setDate(QDate(2022, 11, 5))
        page.link_cultivation_status.setCurrentIndex(
            page.link_cultivation_status.findData("inactive")
        )
        page.save_link_profile()
        profile = self.db.query_one(
            """SELECT variety,planting_date,cultivation_status
               FROM product_fields WHERE product_id=? AND field_id=?""",
            (active_id, field_b),
        )
        self.assertEqual("Καλαμών", profile["variety"])
        self.assertEqual("2022-11-05", profile["planting_date"])
        self.assertEqual("inactive", profile["cultivation_status"])
        with self.assertRaises(ValueError):
            page.validate_profile("05/11/2022", "active")
        with self.assertRaises(ValueError):
            page.validate_profile("2022-11-05", "unknown")

        target_row = next(
            row for row in range(page.links_table.rowCount())
            if page.links_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            == (active_id, field_a)
        )
        page.select_link(target_row, 0)
        page.confirm_delete = lambda *_args: True
        page.remove_link()
        self.assertIsNone(
            self.db.query_one(
                "SELECT 1 FROM product_fields WHERE product_id=? AND field_id=?",
                (active_id, field_a),
            )
        )
        reopened = Database(self.db.path)
        self.assertIsNone(
            reopened.query_one(
                "SELECT 1 FROM product_fields WHERE product_id=? AND field_id=?",
                (active_id, field_a),
            )
        )
        self.assertIsNotNone(
            self.db.query_one(
                "SELECT 1 FROM product_fields WHERE product_id=? AND field_id=?",
                (active_id, field_b),
            )
        )

        legacy_path = self.root / "legacy_product_fields.db"
        with sqlite3.connect(legacy_path) as con:
            con.executescript(
                """CREATE TABLE fields(id INTEGER PRIMARY KEY,name TEXT NOT NULL);
                   CREATE TABLE production(
                       id INTEGER PRIMARY KEY,entry_date TEXT,field_id INTEGER,
                       product TEXT,quantity_kg REAL,notes TEXT DEFAULT ''
                   );
                   INSERT INTO fields(id,name) VALUES(1,'Legacy Field');
                   INSERT INTO production(entry_date,field_id,product,quantity_kg)
                   VALUES('2024-01-01',1,'Legacy Product',5);"""
            )
        legacy_db = Database(legacy_path)
        link = legacy_db.query_one(
            """SELECT p.name,f.name field_name,pf.variety,pf.planting_date,
                      pf.cultivation_status
               FROM product_fields pf
               JOIN products p ON p.id=pf.product_id
               JOIN fields f ON f.id=pf.field_id"""
        )
        self.assertIsNotNone(link)
        self.assertEqual("Legacy Product", link["name"])
        self.assertEqual("Legacy Field", link["field_name"])
        self.assertEqual("", link["variety"])
        self.assertEqual("", link["planting_date"])
        self.assertEqual("active", link["cultivation_status"])

    def test_expense_and_inventory_sync_are_idempotent_and_clean_up(self) -> None:
        expense_id = sync_expense(
            self.db, source_type="inventory_receipt", source_id=7,
            entry_date="2026-08-01", category="Αποθήκη & Εφόδια",
            description="Test", supplier="Supplier", payment_method="",
            amount=10, notes="",
        )
        self.assertEqual(expense_id, sync_expense(
            self.db, source_type="inventory_receipt", source_id=7,
            entry_date="2026-08-02", category="Αποθήκη & Εφόδια",
            description="Updated", supplier="Supplier", payment_method="",
            amount=12, notes="",
        ))
        self.assertEqual(1, self.db.query_one("SELECT COUNT(*) n FROM expenses WHERE source_type='inventory_receipt' AND source_id=7")["n"])
        delete_expense(self.db, source_type="inventory_receipt", source_id=7)
        self.assertEqual(0, self.db.query_one("SELECT COUNT(*) n FROM expenses WHERE source_type='inventory_receipt' AND source_id=7")["n"])

        item_id = self.db.execute("INSERT INTO inventory_items(name,category,unit) VALUES(?,?,?)", ("Θείο", "Φυτοπροστασία", "kg"))
        self.db.execute("INSERT INTO inventory_movements(movement_date,item_id,movement_type,quantity) VALUES(?,?,?,?)", ("2026-08-01", item_id, "Παραλαβή", 20))
        sync_consumption(self.db, source_type="plant_protection", source_id=3, movement_date="2026-08-02", item_id=item_id, quantity=5, field_id=None, notes="test")
        sync_consumption(self.db, source_type="plant_protection", source_id=3, movement_date="2026-08-03", item_id=item_id, quantity=7, field_id=None, notes="updated")
        self.assertEqual(1, self.db.query_one("SELECT COUNT(*) n FROM inventory_movements WHERE source_type='plant_protection' AND source_id=3")["n"])
        self.assertEqual(13, current_stock(self.db, item_id))
        with self.assertRaises(InventoryStockError):
            sync_consumption(self.db, source_type="farm_activity", source_id=4, movement_date="2026-08-04", item_id=item_id, quantity=14, field_id=None, notes="too much")
        delete_consumption(self.db, source_type="plant_protection", source_id=3)
        self.assertEqual(20, current_stock(self.db, item_id))

    def test_year_lock_schema_and_state(self) -> None:
        ensure_year_lock_schema(self.db)
        self.assertFalse(is_year_locked(self.db, 2026))
        self.db.execute("INSERT INTO year_locks(year,is_locked,locked_at,reason) VALUES(?,?,CURRENT_TIMESTAMP,?)", (2026, 1, "test"))
        self.assertTrue(is_year_locked(self.db, 2026))

    def test_plant_protection_hides_approval_number_but_preserves_legacy_value(self) -> None:
        field_id = self.db.execute("INSERT INTO fields(name) VALUES(?)", ("Χωράφι Test",))
        record_id = self.db.execute(
            """INSERT INTO plant_protection_records(
                application_date,field_id,purpose,product_name,authorization_number
            ) VALUES(?,?,?,?,?)""",
            ("2026-08-01", field_id, "Test", "Σκεύασμα", "LEGACY-123"),
        )
        page = self.window.pages[19][1]
        labels = {label.text() for label in page.findChildren(QLabel)}
        self.assertNotIn("Αρ. έγκρισης", labels)
        page.refresh()
        page.load_record(0, 0)
        page.purpose.setText("Updated")
        with patch(
            "app.plant_protection.QMessageBox.warning",
            side_effect=AssertionError("unexpected validation warning"),
        ):
            page.save_record()
        row = self.db.query_one("SELECT purpose,authorization_number FROM plant_protection_records WHERE id=?", (record_id,))
        self.assertEqual("Updated", row["purpose"])
        self.assertEqual("LEGACY-123", row["authorization_number"])


if __name__ == "__main__":
    unittest.main()
