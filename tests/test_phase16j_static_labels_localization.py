import csv
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QLabel
from app import language
from app.database import Database
from app.inventory_report import InventoryReportPage
from app.sensor_view_integration import SensorViewPage

RAW = "Παραγωγή Αποθήκευση Stock Ναι <b>tag</b> {year}"
LABELS = {
    "Αναφορά Αποθήκης & Αξίας Αποθέματος": "Inventory & Stock Value Report",
    "Τρέχον απόθεμα, αγορές, καταναλώσεις, μέση τιμή αγοράς και εκτιμώμενη αξία αποθέματος ανά είδος": "Current stock, purchases, consumption, average purchase price and estimated stock value by item",
    "Απόθεμα": "Stock",
    "Είδη με απόθεμα": "Items in stock",
    "Εκτιμώμενη αξία αποθέματος": "Estimated stock value",
    "Η «Μέση τιμή αγοράς» υπολογίζεται σταθμισμένα από τις Παραλαβές που έχουν καταχωρημένη τιμή μονάδας. Η «Αξία αποθέματος» είναι Τρέχον απόθεμα × Μέση τιμή αγοράς και αποτελεί εκτίμηση.": "Average purchase price is weighted from Receipts with a recorded unit price. Stock value is Current stock × Average purchase price and is an estimate.",
}


class StaticLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "inventory.db")
        self.db.execute("CREATE TABLE inventory_items(id INTEGER PRIMARY KEY,name TEXT,category TEXT,unit TEXT,minimum_stock REAL)")
        self.db.execute("CREATE TABLE inventory_movements(item_id INTEGER,movement_type TEXT,quantity REAL,unit_price REAL,total_cost REAL)")
        for ident, qty, category in ((1,0,"Παραγωγή"),(2,2,"Αποθήκευση"),(3,10,"Stock")):
            self.db.execute("INSERT INTO inventory_items VALUES(?,?,?,?,5)", (ident,RAW,category,RAW))
            self.db.execute("INSERT INTO inventory_movements VALUES(?,'Παραλαβή',?,3,?)", (ident,qty,qty*3))
        self.before = self.snapshot()
        self.previous = language._active_controller
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.page = InventoryReportPage(self.db)
        self.sensor = SensorViewPage(self.db)
        self.rows = self.page._rows_cache.copy()

    def tearDown(self):
        for page in (self.page,self.sensor):
            page.close()
            page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump())

    def switch(self, code):
        self.controller.set_language(code,persist=False)
        self.controller.apply_to(self.page)
        self.controller.apply_to(self.sensor)

    def test_sensor_same_page_cycle(self):
        labels = self.sensor.findChildren(QLabel)
        for code in ("el","en","el"):
            self.switch(code)
            self.assertEqual(self.sensor.findChild(QLabel,"sensorUnderConstructionStatus").text(), "UNDER CONSTRUCTION" if code=="en" else "ΥΠΟ ΚΑΤΑΣΚΕΥΗ")
            self.assertEqual(self.sensor.findChildren(QLabel),labels)
            self.assertEqual(self.sensor.findChild(QLabel,"pageTitle").text(), "Sensors / API" if code=="en" else "Αισθητήρες / API")
            detail = "Η λειτουργία αισθητήρων και API δεν είναι ακόμη διαθέσιμη. Θα ενεργοποιηθεί όταν ολοκληρωθεί η πραγματική σύνδεση συσκευών και υπηρεσιών."
            self.assertEqual(self.sensor.findChild(QLabel,"pageSubtitle").text(), "The sensors and API feature is not available yet. It will be enabled when the real device and service integrations are complete." if code=="en" else detail)

    def assert_labels(self, en):
        texts = [label.text() for label in self.page.findChildren(QLabel)]
        for el, english in LABELS.items():
            self.assertIn(english if en else el,texts)
        self.assertEqual(self.page.table.horizontalHeaderItem(3).text(),"Current stock" if en else "Τρέχον απόθεμα")
        self.assertEqual(self.page.table.horizontalHeaderItem(8).text(),"Stock value" if en else "Αξία αποθέματος")

    def test_greek_static_wording(self):
        self.assert_labels(False)

    def test_inventory_static_live_cycle(self):
        for code in ("el","en","el"):
            self.switch(code)
            self.assert_labels(code=="en")

    def test_generated_status_live_cycle(self):
        for code in ("el","en","el"):
            self.switch(code)
            self.assertEqual([self.page.table.item(i,9).text() for i in range(3)], ["Out of stock","Low","OK"] if code=="en" else ["Εξαντλημένο","Χαμηλό","OK"])
            self.assertEqual(self.page._rows_cache,self.rows)

    def test_category_names_and_other_user_values(self):
        for code in ("el","en","el"):
            self.switch(code)
            for i in range(1,self.page.category_filter.count()):
                self.assertEqual(self.page.category_filter.itemText(i),self.page.category_filter.itemData(i))
            for i,row in enumerate(self.rows):
                self.assertEqual([self.page.table.item(i,c).text() for c in range(3)], [RAW,row['category'],RAW])
                self.assertIn(RAW,self.page.table.item(i,7).text()) if row['avg_price'] else None

    def test_filters_calculations_search_and_database(self):
        self.assertEqual([r['stock'] for r in self.rows],[0,2,10])
        self.assertEqual([r['stock_value'] for r in self.rows],[0,6,30])
        for code in ("el","en","el"):
            self.switch(code)
            self.assertEqual([self.page.stock_filter.itemData(i) for i in range(3)],["all","positive","low"])
            for category in (None,"Παραγωγή","Αποθήκευση","Stock"):
                self.page.category_filter.setCurrentIndex(self.page.category_filter.findData(category))
                for index, mode in enumerate(("all","positive","low")):
                    self.page.stock_filter.setCurrentIndex(index)
                    for search in ("","stock","{year}","absent"):
                        self.page.search.setText(search)
                        self.page.refresh()
                        expected=[r for r in self.rows if (not category or r['category']==category) and (mode!='positive' or r['stock']>0) and (mode!='low' or r['status']!='OK') and search.casefold() in f"{r['name']} {r['category']} {r['unit']}".casefold()]
                        self.assertEqual(self.page._rows_cache,expected)
                        self.assertEqual(self.page.table.rowCount(),len(expected))
                        self.assertEqual(self.page.category_filter.currentData(),category)
            self.assertEqual(self.snapshot(),self.before)

    def test_csv_headers_and_unchanged_canonical_body(self):
        path=Path(self.temp.name)/"Stock {year}.csv"
        for code in ("el","en","el"):
            self.switch(code)
            with patch("app.inventory_report.QFileDialog.getSaveFileName",return_value=(str(path),"CSV")), patch("app.inventory_report._message"):
                self.page.export_csv()
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
            with path.open(encoding='utf-8-sig',newline='') as handle:
                rows=list(csv.reader(handle,delimiter=';'))
            self.assertEqual(rows[0][3],"Current stock" if code=='en' else "Τρέχον απόθεμα")
            self.assertEqual(rows[0][8],"Stock value" if code=='en' else "Αξία αποθέματος")
            self.assertEqual(rows[2],[RAW,"Αποθήκευση",RAW,"2","5","2","0","3","6","Χαμηλό"])
            self.assertEqual(len(rows),4)
            self.assertEqual(self.snapshot(),self.before)
