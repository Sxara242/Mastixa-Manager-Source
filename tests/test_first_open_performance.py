"""Bound repeated work while preserving real lazy navigation and fresh data."""
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDate
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem
from types import SimpleNamespace

from app.date_preferences import SETTING_KEY, format_iso_date
from app.money import MoneyPage
from app.ui_helpers import batched_table_refresh
from tests import test_ui_revamp_phase1 as ui_fixture


class FirstOpenPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ui_fixture.UiRevampTests.setUpClass()

    def setUp(self):
        self.case = ui_fixture.UiRevampTests('test_small_window_scroll_and_dark_palette')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def seed(self, key, count):
        db = self.case.db
        if key == 'production':
            product = db.query_one("SELECT id FROM products WHERE name='QA crop Ω'")
            product_id = product['id'] if product else db.execute("INSERT INTO products(name,unit) VALUES('QA crop Ω','kg')")
        with db.transaction() as tx:
            for index in range(count):
                if key == 'production':
                    tx.execute("INSERT INTO production(entry_date,product,product_id,quantity_kg) VALUES('2027-09-17','QA crop Ω',?,?)",
                               (product_id, index + 1))
                else:
                    tx.execute(f"INSERT INTO {key}(entry_date,description,amount" +
                               (",category" if key == 'expenses' else "") +
                               ") VALUES('2027-09-17',?,?" + (",'Other'" if key == 'expenses' else "") + ")",
                               (f'Raw Ω {index}', index + 1))

    def page(self, key):
        self.case.nav.open('expense' if key == 'expenses' else key)
        return self.case.window.pages[self.case.nav.targets['expense' if key == 'expenses' else key].page][1].resolved_page()

    def assert_bounded_date_reads(self, key):
        self.seed(key, 30)
        self.case.db.set_app_setting(SETTING_KEY, 'DD/MM/YYYY')
        page = self.page(key)
        page.description.setText('unsaved Ω') if key != 'production' else page.notes.setText('unsaved Ω')
        snapshot = self.case.snapshot()
        counts = []
        for count, fmt, rendered in ((30, 'DD/MM/YYYY', '17/09/2027'), (60, 'YYYY-MM-DD', '2027-09-17')):
            if count == 60:
                self.seed(key, 30)
                self.case.db.set_app_setting(SETTING_KEY, fmt)
                snapshot = self.case.snapshot()
            with patch.object(page.db, 'get_app_setting', wraps=page.db.get_app_setting) as reads:
                page.refresh()
            counts.append(sum(call.args[0] == SETTING_KEY for call in reads.call_args_list))
            self.assertEqual(count, page.table.rowCount())
            self.assertTrue(all(page.table.item(row, 0).text() == rendered for row in range(count)))
            self.assertEqual(snapshot, self.case.snapshot())
            self.assertEqual('unsaved Ω', page.description.text() if key != 'production' else page.notes.text())
        self.assertGreater(min(counts), 0, counts)
        self.assertLessEqual(max(counts), 12, counts)
        self.assertEqual(counts[0], counts[1], counts)

    def test_income_date_reads_do_not_grow_with_table_rows(self):
        self.assert_bounded_date_reads('income')

    def test_expense_date_reads_do_not_grow_with_table_rows(self):
        self.assert_bounded_date_reads('expenses')

    def test_production_date_reads_do_not_grow_with_table_rows(self):
        self.assert_bounded_date_reads('production')

    def test_first_money_navigation_populates_once_and_later_write_invalidates(self):
        self.seed('income', 3)
        real_refresh = MoneyPage.refresh
        calls = []
        def counted(page, *args):
            calls.append(page)
            return real_refresh(page, *args)
        with patch.object(MoneyPage, 'refresh', counted):
            page = self.page('income')
            self.assertEqual([page], calls)
            self.assertEqual(3, page.table.rowCount())
            page.description.setText('unsaved Ω')
            self.case.nav.open('home')
            self.seed('income', 1)
            self.assertIs(page, self.page('income'))
            self.assertEqual([page, page], calls)
            self.assertEqual(4, page.table.rowCount())
            self.assertEqual('unsaved Ω', page.description.text())
            self.assertEqual(QDate(2027, QDate.currentDate().month(), QDate.currentDate().day()), page.date.date())
        loaded = [i for i, (_, holder) in enumerate(self.case.window.pages) if getattr(holder, 'is_loaded', False)]
        self.assertEqual([4], loaded)

    def test_visible_refresh_batches_updates_and_preserves_notifications(self):
        self.seed('income', 30)
        page = self.page('income')
        self.case.window.show()
        self.case.app.processEvents()
        page.table.resizeColumnsToContents()
        modes = [page.table.horizontalHeader().sectionResizeMode(i) for i in range(page.table.columnCount())]
        spy = QSignalSpy(page.table.itemChanged)
        setter = page.table.setItem
        states = []
        def set_item(*args):
            states.append(page.table.updatesEnabled())
            self.assertTrue(all(page.table.horizontalHeader().sectionResizeMode(column) == QHeaderView.ResizeMode.Fixed
                                for column in range(page.table.columnCount())))
            return setter(*args)
        with patch.object(page.table, 'setItem', set_item):
            page.refresh()
        self.assertEqual(30 * page.table.columnCount(), len(states))
        self.assertFalse(any(states))
        self.assertTrue(page.table.updatesEnabled())
        self.assertGreater(spy.count(), 0)
        self.assertEqual(modes, [page.table.horizontalHeader().sectionResizeMode(i) for i in range(page.table.columnCount())])

    def test_batch_restores_disabled_state_and_updates_after_error(self):
        table = QTableWidget(1, 2)
        self.addCleanup(table.deleteLater)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        @batched_table_refresh
        def failing(page):
            self.assertFalse(page.table.updatesEnabled())
            page.table.setItem(0, 0, QTableWidgetItem('Raw Ω'))
            raise ValueError('injected refresh failure')
        for enabled in (True, False):
            table.setUpdatesEnabled(enabled)
            with self.assertRaisesRegex(ValueError, 'injected refresh failure'):
                failing(SimpleNamespace(table=table))
            self.assertEqual(enabled, table.updatesEnabled())
            self.assertEqual('Raw Ω', table.item(0, 0).text())
            self.assertEqual(QHeaderView.ResizeMode.ResizeToContents, table.horizontalHeader().sectionResizeMode(0))
            self.assertEqual(QHeaderView.ResizeMode.Stretch, table.horizontalHeader().sectionResizeMode(1))

    def test_explicit_date_format_preserves_invalid_and_legacy_values(self):
        with patch.object(self.case.db, 'get_app_setting', side_effect=AssertionError('per-row preference read')):
            for fmt, shown in (('DD/MM/YY', '17/09/27'), ('DD/MM/YYYY', '17/09/2027'),
                               ('MM/DD/YYYY', '09/17/2027'), ('YYYY-MM-DD', '2027-09-17')):
                self.assertEqual(shown, format_iso_date('2027-09-17', self.case.db, display_format=fmt))
                self.assertEqual('invalid Ω', format_iso_date('invalid Ω', self.case.db, display_format=fmt))
                self.assertEqual('', format_iso_date(None, self.case.db, display_format=fmt))


if __name__ == '__main__':
    unittest.main()
