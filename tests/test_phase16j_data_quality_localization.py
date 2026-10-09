from __future__ import annotations

import ast
import csv
import inspect
import os
from pathlib import Path
import tempfile
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from app import language
from app import data_quality
from app.database import Database
from app.data_quality import DataQualityPage, CATEGORY_LABELS

RAW = "Παραγωγή Ναι Αποθήκευση Έξοδα Προειδοποίηση <b>tag</b> {year} line1\nline2"
REGISTRY = "Registry " + RAW


class DataQualityLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "quality.db")
        self.db.execute("UPDATE producer SET name=?,tax_id='123456789' WHERE id=1", (RAW,))
        self.db.execute("INSERT INTO fields(id,name,kaek,location,area_stremma,productive_trees) VALUES(1,?,'KAEK','Location',1,0)", (RAW,))
        self.db.execute("INSERT INTO production(entry_date,field_id,product,quantity_kg) VALUES(?,1,?,1)", (RAW, RAW))
        with self.db.connect() as con:
            con.execute("PRAGMA foreign_keys=OFF")
            con.execute("INSERT INTO production(entry_date,field_id,product,quantity_kg) VALUES('2020-01-01',98765,?,1)", (RAW,))
        self.db.execute("CREATE TABLE business_partners(id INTEGER PRIMARY KEY, name TEXT)")
        self.db.execute("INSERT INTO business_partners VALUES(1,?)", (REGISTRY,))
        self.db.execute("ALTER TABLE income ADD COLUMN partner_id INTEGER")
        self.db.execute("ALTER TABLE expenses ADD COLUMN partner_id INTEGER")
        self.db.execute("INSERT INTO income(entry_date,description,amount,partner,partner_id) VALUES('2020-01-01',?,1,?,1)", (RAW, RAW))
        self.db.execute("CREATE TABLE inventory_items(id INTEGER PRIMARY KEY,name TEXT,unit TEXT,minimum_stock REAL)")
        self.db.execute("CREATE TABLE inventory_movements(id INTEGER PRIMARY KEY,item_id INTEGER,field_id INTEGER,movement_date TEXT,movement_type TEXT,quantity REAL,unit_price REAL,total_cost REAL,expense_id INTEGER,partner_id INTEGER)")
        self.db.execute("INSERT INTO inventory_items VALUES(1,?,?,5)", (RAW, RAW))
        self.db.execute("INSERT INTO inventory_movements VALUES(1,1,1,'2020-01-01','Παραλαβή',2.5,2,5,NULL,1)")
        self.before = self.snapshot()
        self.previous = language._active_controller
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.page = DataQualityPage(self.db)
        self.source = self.logical()

    def tearDown(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump())

    def logical(self):
        return [{k: str(v) for k, v in issue.items()} for issue in self.page.all_issues]

    def switch(self, code):
        self.controller.set_language(code, persist=False)
        self.controller.apply_to(self.page)

    def assert_issue(self, prefix, problem, fix):
        issues = self.page._filtered_issues()
        index = next(i for i, a in enumerate(issues) if a["problem"].startswith(prefix))
        a = issues[index]
        values = [self.page.table.item(index, c).text() for c in range(5)]
        self.assertEqual(values[2:], [a["record"], problem, fix])
        self.assertEqual(self.page.table.item(index, 3).toolTip(), problem)

    def test_labels_count_and_canonical_keys(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assertEqual(self.logical(), self.source)
            self.assertEqual([self.page.category_filter.itemData(i) for i in range(self.page.category_filter.count())], [None, *CATEGORY_LABELS])
            self.assertEqual([self.page.severity_filter.itemData(i) for i in range(3)], [None, "ERROR", "WARNING"])
            for i, a in enumerate(self.page.all_issues):
                expected = {"ERROR": "Error", "WARNING": "Warning"} if code == "en" else {"ERROR": "Σφάλμα", "WARNING": "Προειδοποίηση"}
                self.assertEqual(self.page.table.item(i, 0).text(), expected[a["severity"]])
                expected_category = self.controller.translate_exact(CATEGORY_LABELS[a["category"]])
                self.assertEqual(self.page.table.item(i, 1).text(), expected_category)
            self.assertEqual(self.page.result_label.text(), f"{len(self.source)} " + ("issues" if code == "en" else "θέματα"))

    def test_static_problem_and_fix(self):
        self.assert_issue("Τα παραγωγικά", "Τα παραγωγικά δέντρα είναι 0.", "Αν υπάρχουν παραγωγικά δέντρα, ενημέρωσε τον αριθμό.")
        self.switch("en")
        self.assert_issue("Τα παραγωγικά", "The number of productive trees is 0.", "If there are productive trees, update the count.")

    def test_dynamic_date_and_id(self):
        self.switch("en")
        self.assert_issue("Μη έγκυρη ημερομηνία:", f"Invalid date: {RAW}.", "Correct the date of the production entry.")
        self.assert_issue("Αναφέρεται σε ανύπαρκτο αγροτεμάχιο", "References a nonexistent field ID 98765.", "Correct or delete the production entry.")

    def test_dynamic_field_name(self):
        self.switch("en")
        self.assert_issue("Υπάρχει παραγωγή", f"There is production in «{RAW}», but it has 0 productive trees.", "Check the field's productive trees.")

    def test_two_protected_partner_values(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            if code == "en":
                self.assert_issue("Το αποθηκευμένο όνομα", f"The stored partner name «{RAW}» does not match the registry «{REGISTRY}».", "Open and save the record again.")
            else:
                self.assert_issue("Το αποθηκευμένο όνομα", f"Το αποθηκευμένο όνομα συνεργάτη «{RAW}» δεν συμφωνεί με το μητρώο «{REGISTRY}».", "Άνοιξε και αποθήκευσε ξανά την εγγραφή.")

    def test_item_and_quantities(self):
        self.switch("en")
        self.assert_issue("Η παραλαβή", f"The receipt of {RAW} has a cost but its linked automatic expense was not found.", "Open and save the receipt again.")
        self.assert_issue("Χαμηλό απόθεμα", "Low stock (2.500, threshold 5.000).", "Check whether replenishment is needed.")

    def test_filter_search_order_and_database(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            self.page.refresh()
            for level in range(3):
                self.page.severity_filter.setCurrentIndex(level)
                for category in range(self.page.category_filter.count()):
                    self.page.category_filter.setCurrentIndex(category)
                    for query in ("", "παραγωγικά", "productive trees", "line1\nline2", "98765"):
                        self.page.search.setText(query)
                        expected = []
                        for a in self.source:
                            if level and a["severity"] != self.page.severity_filter.currentData():
                                continue
                            if category and a["category"] != self.page.category_filter.currentData():
                                continue
                            haystack = " ".join([{"ERROR":"Σφάλμα","WARNING":"Προειδοποίηση"}[a["severity"]], CATEGORY_LABELS[a["category"]], a["record"], a["problem"], a["fix"]]).casefold()
                            if query.casefold() in haystack:
                                expected.append(a)
                        self.assertEqual(self.page._filtered_issues(), expected)
                        self.assertEqual(self.page.table.rowCount(), len(expected))
            self.assertEqual(self.logical(), self.source)
            self.assertEqual(self.snapshot(), self.before)

    def test_status_clean_warning_error_live(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()
        db = Database(Path(self.temp.name) / "states.db")
        db.execute("UPDATE producer SET name='QA',tax_id='123456789' WHERE id=1")
        db.execute("INSERT INTO fields(name,kaek,location,area_stremma,productive_trees) VALUES('QA','K','L',1,1)")
        self.page = DataQualityPage(db)
        for name, tax, el, en, count in (("QA","123456789","Καθαρά","Clear",0),("QA","bad","Με προειδοποιήσεις","With warnings",1),("","123456789","Χρειάζεται διόρθωση","Needs correction",1)):
            db.execute("UPDATE producer SET name=?,tax_id=? WHERE id=1", (name,tax))
            self.page.refresh()
            with db.connect() as con:
                before = tuple(con.iterdump())
            for code in ("el", "en", "el"):
                self.switch(code)
                self.assertEqual(self.page.status_card[1].text(), en if code == "en" else el)
                self.page.refresh()
                self.assertEqual(self.page.status_card[1].text(), en if code == "en" else el)
                self.assertEqual(self.page.result_label.text(), f"{count} " + ("issues" if code == "en" else "θέματα"))
                with db.connect() as con:
                    self.assertEqual(tuple(con.iterdump()), before)

    def test_live_switch_renders_once_without_database_reads(self):
        for code in ("en", "el", "en", "el"):
            with patch.object(self.page, "_apply_filters", wraps=self.page._apply_filters) as render, patch.object(self.db, "query", side_effect=AssertionError("Unexpected query")), patch.object(self.db, "query_one", side_effect=AssertionError("Unexpected query")):
                self.switch(code)
                self.assertEqual(render.call_count, 1)
            self.assertEqual(self.logical(), self.source)
        self.assertEqual(self.snapshot(), self.before)

    def test_every_owned_template_has_complete_english_catalog_entry(self):
        tree = ast.parse(inspect.getsource(data_quality))
        templates = set()
        calls = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_add_issue":
                calls += 1
                for value in node.args[3:5]:
                    if isinstance(value, ast.Constant):
                        templates.add(value.value)
                    else:
                        self.assertIsInstance(value, ast.Call)
                        self.assertEqual(value.func.id, "_IssueText")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_IssueText":
                templates.add(node.args[0].value)
        self.assertEqual(calls, 86)
        self.switch("en")
        for template in templates:
            translated = self.controller.translate_exact(template)
            self.assertNotEqual(translated, template, template)
            self.assertFalse(any('\u0370' <= c <= '\u03ff' for c in translated), translated)
            fields = lambda text: sorted((name, spec, conversion) for _,name,spec,conversion in Formatter().parse(text) if name is not None)
            self.assertEqual(fields(template), fields(translated))

    def test_empty_date_marker_is_owned_but_literal_user_marker_is_raw(self):
        for value, expected in (("", "(empty)"), ("(κενή)", "(κενή)")):
            self.db.execute("UPDATE production SET entry_date=? WHERE id=1", (value,))
            self.page.refresh()
            before = self.snapshot()
            self.switch("en")
            self.assert_issue("Μη έγκυρη ημερομηνία:", f"Invalid date: {expected}.", "Correct the date of the production entry.")
            self.assertEqual(self.snapshot(), before)

    def test_csv_localized_body_and_raw_values(self):
        path = Path(self.temp.name) / "Παραγωγή {year}.csv"
        self.page.category_filter.setCurrentIndex(self.page.category_filter.findData("income"))
        for code in ("el", "en", "el"):
            self.switch(code)
            with patch("app.data_quality.QFileDialog.getSaveFileName", return_value=(str(path), "CSV")), patch("app.data_quality._message"):
                self.page.export_csv()
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
            with path.open(encoding="utf-8-sig",newline="") as handle:
                rows = list(csv.reader(handle,delimiter=";"))
            self.assertEqual(len(rows), 2)
            self.assertEqual(len(rows[1]), 5)
            self.assertEqual(rows[1][0], "Warning" if code == "en" else "Προειδοποίηση")
            self.assertEqual(rows[1][2], "#1")
            expected = f"The stored partner name «{RAW}» does not match the registry «{REGISTRY}»." if code == "en" else f"Το αποθηκευμένο όνομα συνεργάτη «{RAW}» δεν συμφωνεί με το μητρώο «{REGISTRY}»."
            self.assertEqual(rows[1][3], expected)
            self.assertEqual(rows[1], [self.page.table.item(0,c).text() for c in range(5)])
            self.assertEqual(self.snapshot(), self.before)


if __name__ == "__main__":
    unittest.main()
