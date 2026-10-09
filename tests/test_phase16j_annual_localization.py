from __future__ import annotations

import csv
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app import language
from app.annual_report import AnnualFarmReportPage
from app.database import Database
from app.product_registry import ensure_product_links
from app.year_context import set_active_working_year


NAME = "Παραγωγή Ναι Αποθήκευση Έξοδα <b>tag</b> {year}"
ALL_EL = "Προβολή όλων των προϊόντων: το Καθαρό αποτέλεσμα είναι Σύνολο εσόδων − Σύνολο εξόδων για ολόκληρη την εκμετάλλευση."
ALL_EN = "All-products view: Net result is Total income minus Total expenses for the entire operation."
PRODUCT_EL = "Προβολή προϊόντος «{product_name}»: Παραγωγή, Πωλήσεις, Stock και Έσοδα πωλήσεων αφορούν μόνο το προϊόν. Τα Λοιπά έσοδα και Έξοδα εμφανίζονται ως γενικά / μη κατανεμημένα και ΔΕΝ επιμερίζονται αυθαίρετα στο προϊόν. Για αυτό δεν υπολογίζεται ψευδές «καθαρό αποτέλεσμα προϊόντος»."
PRODUCT_EN = "Product view «{product_name}»: Production, Sales, Stock and Sales revenue refer only to this product. Other income and Expenses are shown as general / unallocated and are NOT arbitrarily allocated to the product. Therefore, no misleading «product net result» is calculated."


class AnnualLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "annual.db")
        set_active_working_year(self.db, 2026, audit=False)
        self.db.execute("CREATE TABLE production_sales(id INTEGER PRIMARY KEY, sale_date TEXT, product TEXT, product_id INTEGER, quantity_kg REAL, total_amount REAL, income_id INTEGER)")
        self.product = self.db.execute("INSERT INTO products(name) VALUES(?)", (NAME,))
        other = self.db.execute("INSERT INTO products(name) VALUES('Other product')")
        for product, name, qty in ((self.product, NAME, 100), (other, "Other product", 50)):
            self.db.execute("INSERT INTO production(entry_date,product,product_id,quantity_kg) VALUES('2026-02-01',?,?,?)", (name, product, qty))
        self.db.execute("INSERT INTO production(entry_date,product,product_id,quantity_kg) VALUES('2025-02-01',?,?,10)", (NAME, self.product))
        income = self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES('2026-03-01',?,80)", (NAME,))
        self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES('2026-03-01',?,30)", (NAME,))
        self.db.execute("INSERT INTO expenses(entry_date,category,description,amount) VALUES('2026-03-01',?,?,25)", (NAME, NAME))
        self.db.execute("INSERT INTO production_sales VALUES(1,'2026-03-01',?,?,20,80,?)", (NAME, self.product, income))
        ensure_product_links(self.db)
        self.before = self.snapshot()
        self.previous = language._active_controller
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.page = AnnualFarmReportPage(self.db)

    def tearDown(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def snapshot(self):
        with self.db.connect() as conn:
            return tuple(conn.iterdump())

    def select(self, product):
        self.page.product_filter.setCurrentIndex(self.page.product_filter.findData(product))

    def switch(self, code):
        self.controller.set_language(code, persist=False)
        self.controller.apply_to(self.page)

    def assert_finance(self, en, product):
        categories = ["Sales revenue", "Other income", "Expenses"] if en else ["Έσοδα πωλήσεων", "Λοιπά έσοδα", "Έξοδα"]
        if product:
            handling = ["Included in product", "Unallocated — not attributed to the product", "Unallocated — not deducted from the product"] if en else ["Περιλαμβάνονται στο προϊόν", "Μη κατανεμημένα — δεν αποδίδονται στο προϊόν", "Μη κατανεμημένα — δεν αφαιρούνται από προϊόν"]
        else:
            handling = ["Included in result" if en else "Περιλαμβάνονται στο αποτέλεσμα"] * 3
        self.assertEqual([self.page.finance_table.item(r, 0).text() for r in range(3)], categories)
        self.assertEqual([self.page.finance_table.item(r, 2).text() for r in range(3)], handling)
        self.assertEqual([self.page.finance_table.item(r, 2).toolTip() for r in range(3)], handling)

    def test_product_note_live_cycle_preserves_literal_name(self):
        self.select(self.product)
        for code in ("el", "en", "el", "en", "el"):
            self.switch(code)
            self.assertEqual(self.page.scope_note.text(), (PRODUCT_EN if code == "en" else PRODUCT_EL).format(product_name=NAME))
        self.assertEqual(self.page.scope_note.textFormat(), Qt.TextFormat.PlainText)

    def test_all_products_note_after_refresh(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            self.page.refresh()
            self.assertEqual(self.page.scope_note.text(), ALL_EN if code == "en" else ALL_EL)

    def test_product_finance_live_cycle(self):
        self.select(self.product)
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assert_finance(code == "en", True)

    def test_all_products_finance_live_cycle(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assert_finance(code == "en", False)

    def test_numeric_report_identity_and_database_preserved(self):
        for product in (None, self.product, None):
            self.select(product)
            baseline = list(self.page._rows_cache)
            for code in ("el", "en", "el"):
                self.switch(code)
                self.page.refresh()
                self.assertEqual(self.page.product_filter.currentData(), product)
                self.assertEqual(self.page.year_filter.currentData(), 2026)
                self.assertEqual(self.page._rows_cache, baseline)
                row = next(r for r in self.page._rows_cache if r["product_id"] == self.product)
                self.assertEqual(row, dict(product=NAME, product_id=self.product, unit="kg", key=("id", self.product), produced=100.0, sold=20.0, revenue=80.0, avg=4.0, stock=90.0))
                self.assertEqual([self.page.finance_table.item(r, 1).text() for r in range(3)], ["80,00 €", "30,00 €", "25,00 €"])
                self.assertEqual(self.page.result_metric[1].text(), "—" if product else "85,00 €")
                names = [self.page.product_table.item(r, 0).text() for r in range(self.page.product_table.rowCount())]
                self.assertIn(NAME, names)
                index = self.page.product_filter.findData(self.product)
                self.assertEqual(self.page.product_filter.itemText(index), NAME)
                if product:
                    self.assertEqual(language.combo_source_text(self.page.product_filter), NAME)
                self.assertEqual(self.snapshot(), self.before)

    def test_csv_product_and_numeric_values_preserved(self):
        self.select(self.product)
        path = Path(self.temp.name) / "Παραγωγή {year}.csv"
        for code in ("el", "en", "el"):
            self.switch(code)
            with patch("app.annual_report.QFileDialog.getSaveFileName", return_value=(str(path), "CSV")), patch("app.annual_report._message"):
                self.page.export_csv()
            with path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, delimiter=";"))
            self.assertEqual(rows[1][1], "2026")
            self.assertEqual(rows[2][1], NAME)
            self.assertEqual(rows[5], [NAME, "100", "20", "80", "4", "90", "kg"])
            self.assertEqual(len(rows), 6)
            self.assertEqual(self.snapshot(), self.before)


if __name__ == "__main__":
    unittest.main()
