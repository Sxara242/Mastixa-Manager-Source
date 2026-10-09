import os
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from string import Formatter
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QTabWidget, QWidget
from app import language
from app import product_registry
from app.database import Database
from app.equipment import EquipmentPage
from app.inventory_report import InventoryReportPage
from app.invoice_documents import InvoiceDocumentsPage
from app.products import ProductsPage
from app.phase13_calendar_integration import GREEK_MONTHS, Phase13FarmCalendarPage
from app.product_registry import add_product_choices
from app.tab_scroll_fix import _ensure_left_scroll_proxy, _native_scroll_buttons

RAW = "Παραγωγή Ναι Αποθήκευση Έξοδα <b>tag</b> {year}"
UNIT = "Ναι {unit} & Ω"
MONTHS = "January February March April May June July August September October November December".split()


class StaticSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "selectors.db")
        self.previous = language._active_controller
        self.previous_app = getattr(self.app, "_mastixa_language_controller", None)
        self.previous_enabled = getattr(self.previous_app, "_enabled", False)
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.pages = []

    def tearDown(self):
        for page in self.pages:
            page.close()
            page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        self.app._mastixa_language_controller = self.previous_app
        if self.previous_app is not None:
            self.previous_app._enabled = self.previous_enabled
            if self.previous_enabled:
                self.app.installEventFilter(self.previous_app)
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def page(self, cls):
        page = cls(self.db)
        self.pages.append(page)
        return page

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump())

    def cycle(self, page, combo, el, en, data, selection, check=None):
        combo.setCurrentIndex(combo.findData(selection))
        before = self.snapshot()
        changed = Mock()
        combo.currentIndexChanged.connect(changed)
        for code in ("el", "en", "el"):
            with self.subTest(language=code):
                with patch.object(self.db, "execute", wraps=self.db.execute) as write:
                    self.controller.set_language(code, persist=False)
                    self.controller.apply_to(page)
                    write.assert_not_called()
                self.assertEqual([combo.itemData(i) for i in range(combo.count())], data)
                self.assertEqual(combo.currentData(), selection)
                changed.assert_not_called()
                if check:
                    check()
                self.assertEqual(self.snapshot(), before)
                self.assertEqual([combo.itemText(i) for i in range(combo.count())], en if code == "en" else el)

    def test_equipment_reminder_filter(self):
        page = self.page(EquipmentPage)
        ident = self.db.execute("INSERT INTO equipment(name) VALUES(?)", (RAW,))
        expected = {}
        for key, days in (("upcoming", 5), ("overdue", -5)):
            expected[key] = self.db.execute("INSERT INTO equipment_maintenance(equipment_id,service_date,service_type,next_service_date) VALUES(?,?,?,?)", (ident, "2027-01-01", RAW, QDate.currentDate().addDays(days).toString("yyyy-MM-dd")))
        page.refresh()
        for key in expected:
            def check(key=key):
                page.refresh()
                self.assertEqual(page.service_table.rowCount(), 1)
                self.assertEqual(page.service_table.item(0, 0).data(Qt.ItemDataRole.UserRole), expected[key])
            self.cycle(page, page.reminder_filter, ["Όλες", "Επερχόμενες", "Εκπρόθεσμες"], ["All", "Upcoming", "Overdue"], [None, "upcoming", "overdue"], key, check)

    def test_inventory_stock_filter_and_raw_categories(self):
        self.db.execute("CREATE TABLE inventory_items(id INTEGER PRIMARY KEY,name TEXT,category TEXT,unit TEXT,minimum_stock REAL)")
        self.db.execute("CREATE TABLE inventory_movements(item_id INTEGER,movement_type TEXT,quantity REAL,unit_price REAL,total_cost REAL)")
        for ident, qty in ((1, 0), (2, 2), (3, 10)):
            self.db.execute("INSERT INTO inventory_items VALUES(?,?,?,?,5)", (ident, RAW, RAW, UNIT))
            self.db.execute("INSERT INTO inventory_movements VALUES(?,'Παραλαβή',?,3,?)", (ident, qty, qty * 3))
        page = self.page(InventoryReportPage)
        for key, expected in (("positive", [2, 10]), ("low", [0, 2])):
            def check(expected=expected):
                page.refresh()
                self.assertEqual([r["stock"] for r in page._rows_cache], expected)
                self.assertEqual(page.category_filter.itemText(page.category_filter.findData(RAW)), RAW)
            self.cycle(page, page.stock_filter, ["Όλα", "Με απόθεμα", "Χαμηλό / εξαντλημένο"], ["All", "In stock", "Low / out of stock"], ["all", "positive", "low"], key, check)

    def test_invoice_type_selector(self):
        with patch("app.invoice_documents.INVOICE_FILES_DIR", Path(self.temp.name) / "invoices"):
            page = self.page(InvoiceDocumentsPage)
        self.cycle(page, page.document_type,
                   ["Αδιευκρίνιστο — επίλεξε πριν την καταχώριση", "Αγορά — καταχώριση στα Έξοδα", "Πώληση — καταχώριση στα Έσοδα"],
                   ["Unspecified — select before posting", "Purchase — post to Expenses", "Sale — post to Income"],
                   ["unknown", "purchase", "sale"], "purchase")

    def test_products_integer_filter(self):
        page = self.page(ProductsPage)
        for ident, active in ((81, 1), (82, 0)):
            self.db.execute("INSERT INTO products(id,name,unit,is_active) VALUES(?,?,?,?)", (ident, RAW + str(ident), UNIT, active))
        for key, ident in ((1, 81), (0, 82)):
            def check(ident=ident):
                page.refresh()
                self.assertEqual(page.table.rowCount(), 1)
                self.assertEqual(page.table.item(0, 0).data(Qt.ItemDataRole.UserRole), ident)
                self.assertIs(type(page.status_filter.currentData()), int)
            self.cycle(page, page.status_filter, ["Όλα", "Ενεργά", "Ανενεργά"], ["All", "Active", "Inactive"], ["all", 1, 0], key, check)

    def test_all_months_and_calendar_filter(self):
        page = self.page(Phase13FarmCalendarPage)
        rows = [dict(date=f"2027-{month:02d}-02", section="raw", field_id=None, field_name=RAW, description=RAW, value=UNIT, page_index=0, record_id=month, search_text=RAW) for month in range(1, 13)]
        def load():
            page._rows = [row.copy() for row in rows]
        with patch.object(page, "_load_activities", side_effect=load):
            def check():
                page.refresh()
                self.assertEqual([r["record_id"] for r in page._rows], [7])
            self.cycle(page, page.month, ["Όλοι οι μήνες", *GREEK_MONTHS], ["All months", *MONTHS], [None, *range(1, 13)], 7, check)

    def registry(self):
        for ident, active in ((91, 1), (92, 0)):
            self.db.execute("INSERT INTO products(id,name,unit,is_active) VALUES(?,?,?,?)", (ident, RAW + str(ident), UNIT, active))
        combo = QComboBox()
        self.pages.append(combo)
        add_product_choices(combo, self.db, selected_id=92)
        return combo

    def test_registry_suffix_preserves_raw_name_unit(self):
        combo = self.registry()
        active = f"{RAW}91 ({UNIT})"
        inactive = f"{RAW}92 ({UNIT}) — "
        self.cycle(combo, combo, ["Επίλεξε προϊόν", active, inactive + "Ανενεργό"], ["Select a product", active, inactive + "Inactive"], [None, 91, 92], 92)

    def test_registry_repopulation_does_not_retain_stale_suffix(self):
        combo = self.registry()
        before = self.snapshot()
        for code in ("en", "el", "en"):
            self.controller.set_language(code, persist=False)
            for selected in (92, 91, 92):
                add_product_choices(combo, self.db, selected_id=selected)
                self.controller.apply_to(combo)
                self.assertEqual(combo.currentData(), selected)
                expected = f"{RAW}{selected} ({UNIT})"
                if selected == 92:
                    expected += " — " + ("Inactive" if code == "en" else "Ανενεργό")
                self.assertEqual(combo.currentText(), expected)
                self.assertEqual(combo.count(), 3 if selected == 92 else 2)
        self.assertEqual(self.snapshot(), before)

    def test_registry_refresh_is_single_silent_and_read_only(self):
        combo = self.registry()
        for _ in range(4):
            add_product_choices(combo, self.db, selected_id=92)
        changed = Mock()
        combo.currentTextChanged.connect(changed)
        with patch.object(product_registry, "_text", wraps=product_registry._text) as render, patch.object(self.db, "query", wraps=self.db.query) as query, patch.object(self.db, "query_one", wraps=self.db.query_one) as query_one:
            self.controller.set_language("en", persist=False)
            render.assert_called_once_with("Ανενεργό")
            query.assert_not_called()
            query_one.assert_not_called()
        changed.assert_not_called()
        self.assertEqual(combo.currentData(), 92)

    def test_new_catalog_keys_are_unique_and_valid(self):
        root = Path(language.__file__).parent / "locales"
        target = root / "en_phase16j_static_selectors.json"
        entries = json.loads(target.read_text(encoding="utf-8"))["translations"]
        self.assertEqual(len(entries), 22)
        for key, value in entries.items():
            self.assertTrue(value.strip())
            self.assertNotRegex(value, r"[\u0370-\u03ff\u1f00-\u1fff]")
            fields = lambda text: [f for _, f, _, _ in Formatter().parse(text) if f is not None]
            self.assertEqual(fields(key), fields(value))
        for path in root.glob("*.json"):
            if path != target:
                self.assertFalse(entries.keys() & json.loads(path.read_text(encoding="utf-8"))["translations"].keys(), path.name)

    def test_tab_scroll_accessible_name_and_proxy_identity(self):
        tabs = QTabWidget()
        self.pages.append(tabs)
        for i in range(9):
            tabs.addTab(QWidget(), f"Long tab {i}")
        tabs.resize(280, 160)
        tabs.show()
        tabs.setCurrentIndex(tabs.count() - 1)
        self.app.processEvents()
        bar = tabs.tabBar()
        left, right = _native_scroll_buttons(bar)
        proxy = _ensure_left_scroll_proxy(bar, left)
        for code in ("el", "en", "el"):
            with self.subTest(language=code):
                self.controller.set_language(code, persist=False)
                self.controller.apply_to(tabs)
                self.assertIs(_ensure_left_scroll_proxy(bar, left), proxy)
                self.assertEqual(proxy.text(), "")
                self.assertEqual(proxy.arrowType(), Qt.ArrowType.LeftArrow)
                self.assertEqual(proxy.geometry(), left.geometry())
                with patch("app.tab_scroll_fix._click_native_left_scroll") as click:
                    proxy.click()
                    click.assert_called_once_with(bar)
                self.assertIs(_native_scroll_buttons(bar)[1], right)
                self.assertEqual(proxy.accessibleName(), "Scroll tabs left" if code == "en" else "Κύλιση καρτελών προς τα αριστερά")


if __name__ == "__main__":
    unittest.main()
