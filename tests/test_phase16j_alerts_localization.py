from __future__ import annotations

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication

from app.alerts import AlertsPage
from app.database import Database
from app import language


RAW = "Παραγωγή Ναι Αποθήκευση <b>tag</b> {year}"


class AlertsLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "alerts.db")
        # Minimal real SQLite fixture covering every column consumed by AlertsPage.
        for sql in (
            "CREATE TABLE farm_activities(id INTEGER PRIMARY KEY, activity_date TEXT, category TEXT, description TEXT, status TEXT, field_id INTEGER)",
            "CREATE TABLE inventory_items(id INTEGER PRIMARY KEY, name TEXT, unit TEXT, minimum_stock REAL)",
            "CREATE TABLE inventory_movements(item_id INTEGER, movement_type TEXT, quantity REAL)",
            "CREATE TABLE equipment(id INTEGER PRIMARY KEY, name TEXT, current_meter REAL, meter_type TEXT, status TEXT)",
            "CREATE TABLE equipment_maintenance(id INTEGER PRIMARY KEY, equipment_id INTEGER, service_date TEXT, next_service_date TEXT, next_service_meter REAL)",
            "CREATE TABLE plant_protection_records(id INTEGER PRIMARY KEY, application_date TEXT, product_name TEXT, purpose TEXT, harvest_interval_days INTEGER, field_id INTEGER)",
        ):
            self.db.execute(sql)
        self.today = QDate.currentDate()
        self.iso = lambda days: self.today.addDays(days).toString("yyyy-MM-dd")
        self.display_date = lambda days: self.today.addDays(days).toString("dd/MM/yyyy")
        self.db.execute("INSERT INTO fields(id,name) VALUES(1,?)", (RAW,))
        for ident, days, category in ((1, -1, "Πότισμα"), (2, 0, "Λίπανση"), (3, 2, "Πότισμα"), (4, 3, RAW)):
            self.db.execute("INSERT INTO farm_activities VALUES(?,?,?,?,?,1)", (ident, self.iso(days), category, RAW, "Προγραμματισμένη"))
        for ident, stock in ((1, 0), (2, 2.5)):
            self.db.execute("INSERT INTO inventory_items VALUES(?,?,?,5)", (ident, RAW, RAW))
            self.db.execute("INSERT INTO inventory_movements VALUES(?,'Παραλαβή',?)", (ident, stock))
        for ident, days, meter, unit in ((1, -1, 100, "hours"), (2, 2, 120, "km")):
            self.db.execute("INSERT INTO equipment VALUES(?,?,100,?,'Ενεργό')", (ident, RAW, unit))
            self.db.execute("INSERT INTO equipment_maintenance VALUES(?,?,?,?,?)", (ident, ident, self.iso(-10), self.iso(days), meter))
        for ident, days in ((1, 1), (2, 3)):
            self.db.execute("INSERT INTO plant_protection_records VALUES(?,?,?,?,?,1)", (ident, self.iso(0), RAW, RAW, days))
        self.before = self.snapshot()
        self.previous = language._active_controller
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.page = AlertsPage(self.db)
        self.canonical = self.identities()

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

    def identities(self):
        return [(a["kind"], a["record_id"], a["severity"], a["date"], a["subject"]) for a in self.page._alerts]

    def switch(self, code, refresh=True):
        self.controller.set_language(code, persist=False)
        if refresh:
            self.page.refresh()

    def expected(self, kind, ident, en):
        if kind == "activity":
            prefixes = ("Overdue planned activity", "Scheduled for today", "Upcoming activity", "Upcoming activity") if en else ("Εκπρόθεσμη προγραμματισμένη εργασία", "Προγραμματισμένη για σήμερα", "Επερχόμενη εργασία", "Επερχόμενη εργασία")
            categories = ("Irrigation", "Fertilization", "Irrigation", RAW) if en else ("Πότισμα", "Λίπανση", "Πότισμα", RAW)
            return f"{prefixes[ident-1]}: {categories[ident-1]} — {RAW}"
        if kind == "inventory":
            if ident == 1:
                return f"{'Out of stock' if en else 'Εξαντλημένο απόθεμα'}: 0 {RAW}"
            return f"{'Low stock' if en else 'Χαμηλό απόθεμα'}: 2.5 {RAW} ({'minimum' if en else 'ελάχιστο'} 5)"
        if kind == "equipment":
            title = ("Overdue service" if ident == 1 else "Service due soon") if en else ("Εκπρόθεσμο service" if ident == 1 else "Πλησιάζει service")
            date = self.display_date(-1 if ident == 1 else 2)
            unit = ("hours" if en else "ώρες") if ident == 1 else "km"
            return f"{title}: {'date' if en else 'ημερομηνία'} {date} / {'meter' if en else 'μετρητής'} {100 if ident == 1 else 120} {unit}"
        days = 1 if ident == 1 else 3
        date = self.display_date(days)
        if en:
            return f"Do not harvest for another {days} {'day' if days == 1 else 'days'}. Safe date: {date} — {RAW}"
        return f"Μην γίνει συγκομιδή για ακόμη {days} {'ημέρα' if days == 1 else 'ημέρες'}. Ασφαλής ημερομηνία: {date} — {RAW}"

    def assert_rows(self, en, kind=None):
        categories = {
            "activity": ("Άρδευση & Λίπανση", "Irrigation & Fertilization"),
            "inventory": ("Αποθήκη & Εφόδια", "Inventory & Supplies"),
            "equipment": ("Μηχανήματα & Service", "Equipment & Service"),
            "harvest_wait": ("Φυτοπροστασία", "Plant protection"),
        }
        severities = {"critical": ("Άμεση", "Immediate"), "warning": ("Προσοχή", "Warning"), "info": ("Ενημέρωση", "Information")}
        for row in range(self.page.table.rowCount()):
            alert = self.page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if kind and alert["kind"] != kind:
                continue
            actual = [self.page.table.item(row, col).text() for col in range(5)]
            self.assertEqual(actual, [severities[alert["severity"]][en], categories[alert["kind"]][en], alert["date"], RAW, self.expected(alert["kind"], alert["record_id"], en)])
            self.assertEqual(self.page.table.item(row, 4).toolTip(), actual[4])

    def test_greek_all_kinds(self):
        self.assert_rows(False)

    def test_count_both_languages(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            expected = "10 alerts" if code == "en" else "10 ειδοποιήσεις"
            self.assertEqual(self.page.result_label.text(), expected)
            self.controller.apply_to(self.page)
            self.assertEqual(self.page.result_label.text(), expected)

    def test_activity_english(self):
        self.switch("en")
        self.assert_rows(True, "activity")

    def test_inventory_english(self):
        self.switch("en")
        self.assert_rows(True, "inventory")

    def test_equipment_english(self):
        self.switch("en")
        self.assert_rows(True, "equipment")

    def test_harvest_singular_plural_english(self):
        self.switch("en")
        self.assert_rows(True, "harvest_wait")

    def test_live_cycle_without_manual_refresh(self):
        for code in ("el", "en", "el"):
            self.switch(code, refresh=False)
            self.assert_rows(code == "en")
            self.assertEqual(self.identities(), self.canonical)

    def test_filters_order_navigation_and_identity(self):
        targets = {"activity": 12, "inventory": 13, "equipment": 16, "harvest_wait": 19}
        called = []
        self.page.change_page = called.append
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assertEqual(self.identities(), self.canonical)
            self.assertEqual([self.page.category_filter.itemData(i) for i in range(5)], [None, *targets])
            self.assertEqual([self.page.severity_filter.itemData(i) for i in range(4)], [None, "critical", "warning", "info"])
            for category in range(5):
                self.page.category_filter.setCurrentIndex(category)
                for severity in range(4):
                    self.page.severity_filter.setCurrentIndex(severity)
                    kind = self.page.category_filter.currentData()
                    level = self.page.severity_filter.currentData()
                    expected = [a for a in self.canonical if (not kind or a[0] == kind) and (not level or a[2] == level)]
                    actual = []
                    for row in range(self.page.table.rowCount()):
                        self.page.table.selectRow(row)
                        a = self.page._selected_alert()
                        actual.append((a["kind"], a["record_id"], a["severity"], a["date"], a["subject"]))
                        self.page.open_related_page()
                        self.assertEqual(called[-1], targets[a["kind"]])
                        self.assertEqual(self.page.defer_button.isEnabled(), a["kind"] == "activity")
                    self.assertEqual(actual, expected)
                    count_text = f"{len(expected)} alerts" if code == "en" else f"{len(expected)} ειδοποιήσεις"
                    self.assertEqual(self.page.result_label.text(), count_text)
            self.assertEqual(self.snapshot(), self.before)

    def test_database_snapshot_after_render_filters_switch(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            for index in range(5):
                self.page.category_filter.setCurrentIndex(index)
                self.page.refresh()
            self.assertEqual(self.snapshot(), self.before)

    def test_unknown_category_and_raw_user_values(self):
        for code in ("el", "en", "el"):
            self.switch(code)
            for a in self.page._alerts:
                self.assertEqual(a["subject"], RAW)
                if a["kind"] in ("activity", "inventory", "harvest_wait"):
                    self.assertIn(RAW, a["message"])
                if a["kind"] == "activity" and a["record_id"] == 4:
                    self.assertTrue(a["message"].endswith(f"{RAW} — {RAW}"))

    def test_fallback_labels_display_only_and_order_preserved(self):
        self.db.execute("UPDATE farm_activities SET field_id=NULL, category='' WHERE id=1")
        self.db.execute("UPDATE plant_protection_records SET field_id=NULL, product_name='' WHERE id=1")
        before = self.snapshot()
        self.page.refresh()
        identities = self.identities()
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assertEqual(self.identities(), identities)
            for row in range(self.page.table.rowCount()):
                a = self.page.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if a["record_id"] != 1:
                    continue
                if a["kind"] == "activity":
                    self.assertEqual(self.page.table.item(row, 3).text(), "General / all fields" if code == "en" else "Γενική / όλα τα αγροτεμάχια")
                    self.assertEqual(a["message"], f"Overdue planned activity: Task — {RAW}" if code == "en" else f"Εκπρόθεσμη προγραμματισμένη εργασία: Εργασία — {RAW}")
                elif a["kind"] == "harvest_wait":
                    self.assertEqual(self.page.table.item(row, 3).text(), "Field" if code == "en" else "Αγροτεμάχιο")
                    self.assertTrue(a["message"].endswith("— Plant protection" if code == "en" else "— Φυτοπροστασία"))
            self.assertEqual(self.snapshot(), before)

    def test_legacy_category_matching_catalog_is_not_an_enum(self):
        self.db.execute("UPDATE farm_activities SET category='Εργασία' WHERE id=4")
        before = self.snapshot()
        self.switch("en")
        a = next(a for a in self.page._alerts if a["kind"] == "activity" and a["record_id"] == 4)
        self.assertEqual(a["message"], f"Upcoming activity: Εργασία — {RAW}")
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
