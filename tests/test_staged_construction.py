"""Visible-first construction must preserve current data and user state."""
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout

from app.database import Database
from app.staged_construction import AfterFirstPaint
from app.year_context import set_active_working_year


class StagedConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_ui_revamp_phase1 import UiRevampTests
        UiRevampTests.setUpClass()

    def setUp(self):
        from tests.test_ui_revamp_phase1 import UiRevampTests
        self.fixture = UiRevampTests('test_small_window_scroll_and_dark_palette')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.window = self.fixture.window
        self.nav = self.fixture.nav
        self.db = self.fixture.db
        self.app = QApplication.instance()
        self.window.resize(1050, 720)
        self.window.show()
        self.app.processEvents()

    def open(self, key):
        self.nav.open(key)
        page = self.window.pages[self.nav.targets[key].page][1].resolved_page()
        page.show()
        return page

    def finish(self, page):
        for _ in range(10):
            page.repaint()
            QTest.qWait(70)
            if page._secondary_construction.complete:
                return
        self.fail('secondary construction did not complete')

    def test_inventory_away_external_write_year_and_primary_draft(self):
        page = self.open('inventory')
        self.assertFalse(page._secondary_construction.complete)
        self.assertFalse(page._movement_ready)
        self.assertEqual('0', page.items_metric[1].text())
        page.item_name.setText('unsaved primary Ω')
        self.nav.open('home')
        QTest.qWait(80)
        self.assertFalse(page._secondary_construction.complete)
        other = Database(self.db.path)
        item = other.execute("INSERT INTO inventory_items(name,unit) VALUES('QA item','kg')")
        other.execute("INSERT INTO inventory_movements(movement_date,item_id,movement_type,quantity) VALUES('2028-01-02',?,'Παραλαβή',9)", (item,))
        set_active_working_year(self.db, 2028, audit=False)
        self.open('inventory')
        self.finish(page)
        self.assertEqual('unsaved primary Ω', page.item_name.text())
        self.assertEqual('1', page.items_metric[1].text())
        self.assertEqual('9', page.stock_table.item(0, 3).text())
        self.assertEqual(1, page.movement_table.rowCount())
        self.assertEqual(2028, page.movement_date.date().year())
        page.movement_quantity.setText('2.5')
        page.movement_notes.setText('unsaved movement Ω')
        page.item_filter.setCurrentIndex(page.item_filter.findData(item))
        page.type_filter.setCurrentIndex(page.type_filter.findData('Παραλαβή'))
        self.nav.open('home')
        other.execute("INSERT INTO inventory_movements(movement_date,item_id,movement_type,quantity) VALUES('2028-01-03',?,'Παραλαβή',3)", (item,))
        self.assertIs(page, self.open('inventory'))
        self.assertEqual(2, page.movement_table.rowCount())
        self.assertEqual('12', page.stock_table.item(0, 3).text())
        self.assertEqual('2.5', page.movement_quantity.text())
        self.assertEqual('unsaved movement Ω', page.movement_notes.text())
        self.assertEqual(item, page.item_filter.currentData())

    def test_inventory_hide_between_phases_preserves_movement_draft(self):
        page = self.open('inventory')
        stage = page._secondary_construction
        stage.finish()
        self.assertEqual(1, stage.phase)
        self.assertFalse(stage.complete)
        page.movement_notes.setText('between phases Ω')
        self.nav.open('home')
        QTest.qWait(70)
        self.assertEqual(1, stage.phase)
        self.open('inventory')
        self.finish(page)
        self.assertEqual('between phases Ω', page.movement_notes.text())

    def test_inventory_year_context_before_movement_form_exists(self):
        from app.year_context import begin_year_correction, finish_year_correction
        page = self.open('inventory')
        self.assertFalse(page._movement_form_ready)
        self.nav.open('home')
        self.db.execute("INSERT INTO year_locks(year,is_locked) VALUES(2026,1)")
        set_active_working_year(self.db, 2026, audit=False)
        self.window._refresh_year_context_ui()
        self.open('inventory')
        self.finish(page)
        self.assertEqual(2026, page.movement_date.date().year())
        self.assertFalse(page.movement_save_button.isEnabled())
        begin_year_correction(self.db, 2026, 'Deferred form correction')
        self.window._refresh_year_context_ui()
        self.assertTrue(page.movement_save_button.isEnabled())
        finish_year_correction(self.db)
        self.window._refresh_year_context_ui()
        self.assertFalse(page.movement_save_button.isEnabled())

    def test_annual_latest_filter_and_write_win_over_pending_work(self):
        self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES('2027-01-01','QA',3)")
        self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES('2028-01-01','QA',5)")
        page = self.open('annual_report')
        self.assertFalse(page._secondary_construction.complete)
        self.assertFalse(hasattr(page, 'finance_table'))
        page.year_filter.setCurrentIndex(page.year_filter.findData(2028))
        self.nav.open('home')
        QTest.qWait(70)
        self.assertFalse(page._secondary_construction.complete)
        other = Database(self.db.path)
        other.execute("INSERT INTO income(entry_date,description,amount) VALUES('2028-02-01','QA',7)")
        self.open('annual_report')
        self.assertEqual(2027, page.year_filter.currentData())
        page.year_filter.setCurrentIndex(page.year_filter.findData(2028))
        self.finish(page)
        self.assertEqual(2028, page.year_filter.currentData())
        self.assertEqual(12, page._annual_report_snapshot().total_income)
        self.assertEqual('12,00 €', page.other_income_metric[1].text())
        self.assertEqual('12,00 €', page.finance_table.item(1, 1).text())
        self.assertEqual(3, page.finance_table.rowCount())
        self.assertEqual(len(page._rows_cache), page.product_table.rowCount())

    def test_settings_secondary_tabs_are_lazy_and_preserve_saved_values(self):
        self.db.save_app_settings({'farm_name': 'QA farm', 'auto_backup_keep': 41, 'auto_backup_enabled': '0'})
        page = self.open('settings')
        self.assertFalse(hasattr(page, 'auto_backup_enabled'))
        self.assertFalse(hasattr(page, '_mastixa_check_updates_button'))
        self.nav.open('home')
        QTest.qWait(70)
        self.assertFalse(page._secondary_construction.complete)
        self.open('settings')
        self.finish(page)
        self.assertEqual('QA farm', page.farm_name.text())
        self.assertFalse(hasattr(page, 'auto_backup_enabled'))
        page.tabs.setCurrentIndex(1)
        self.assertEqual(41, page.auto_backup_keep.value())
        self.assertFalse(page.auto_backup_enabled.isChecked())
        page.auto_backup_keep.setValue(42)
        page.tabs.setCurrentIndex(0)
        page.tabs.setCurrentIndex(1)
        self.assertEqual(42, page.auto_backup_keep.value())
        page.tabs.setCurrentIndex(2)
        self.assertEqual(4, page.tabs.count())
        self.assertNotIn(2, page._lazy_settings_tabs)
        self.nav.open('updates')
        self.assertEqual(3, page.tabs.currentIndex())
        self.assertTrue(page._mastixa_check_updates_button.isVisible())
        self.assertEqual(4, page.tabs.count())

    def test_annual_write_while_visible_invalidates_deferred_snapshot(self):
        self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES('2027-01-01','QA',3)")
        page = self.open('annual_report')
        other = Database(self.db.path)
        other.execute("INSERT INTO income(entry_date,description,amount) VALUES('2027-01-02','QA',7)")
        self.finish(page)
        self.assertEqual(10, page._annual_report_snapshot().total_income)
        self.assertEqual('10,00 €', page.finance_table.item(1, 1).text())

    def test_settings_save_before_secondary_paint_does_not_replace_preferences(self):
        self.db.save_app_settings({'farm_name':'preserved Ω', 'auto_backup_keep': 53, 'pre_restore_keep':17, 'auto_backup_enabled':'0'})
        page = self.open('settings')
        with patch('app.settings.QMessageBox.information'):
            page.save()
        self.assertEqual('preserved Ω', self.db.get_app_setting('farm_name'))
        self.assertEqual('53', self.db.get_app_setting('auto_backup_keep'))
        self.assertEqual('17', self.db.get_app_setting('pre_restore_keep'))
        self.assertEqual('0', self.db.get_app_setting('auto_backup_enabled'))

    def test_language_and_theme_before_and_after_secondary_creation(self):
        page = self.open('settings')
        self.fixture.controller.set_language('en', persist=False)
        self.fixture.theme.set_theme('dark', persist=False)
        self.finish(page)
        page.tabs.setCurrentIndex(1)
        self.assertIn('Backups', page.tabs.tabText(1))
        self.fixture.controller.set_language('el', persist=False)
        self.fixture.theme.set_theme('light', persist=False)
        self.app.processEvents()
        self.assertIn('Αντίγραφα', page.tabs.tabText(1))
        self.fixture.controller.set_language('en', persist=False)
        self.fixture.theme.set_theme('dark', persist=False)
        self.app.processEvents()
        self.assertEqual(1, page.tabs.currentIndex())
        self.assertIn('Backups', page.tabs.tabText(1))
        self.assertTrue(page.auto_backup_keep.isVisible())

    def test_page_deletion_cancels_pending_timer(self):
        page = QWidget()
        QVBoxLayout(page)
        calls = []
        stage = AfterFirstPaint(page, lambda: calls.append(True))
        page.show()
        page.repaint()
        self.assertFalse(stage.complete)
        page.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.assertEqual([], calls)

    def test_hidden_legacy_chrome_keeps_visible_settings_tab_icons(self):
        page = self.open('settings')
        self.finish(page)
        from app.icon_theme import apply_icon_theme
        page.tabs.setTabText(0, 'Ρυθμίσεις')
        apply_icon_theme(self.window)
        self.assertTrue(self.window.tabs.property('mastixaHiddenNavigation'))
        self.assertFalse(self.window.tabs.tabBar().isVisible())
        self.assertFalse(page.tabs.property('mastixaHiddenNavigation'))
        self.assertTrue(page.tabs.tabBar().isVisible())
        self.assertFalse(page.tabs.tabIcon(0).isNull())

    def test_large_viewport_constructs_visible_report_sections_synchronously(self):
        self.window.resize(1200, 1000)
        self.app.processEvents()
        page = self.open('annual_report')
        self.assertTrue(page._finance_ready)
        self.assertEqual(3, page.finance_table.rowCount())
        self.assertFalse(hasattr(page, '_secondary_construction'))

    def test_resize_before_paint_fills_newly_visible_sections(self):
        page = self.open('annual_report')
        stage = page._secondary_construction
        self.assertFalse(stage.complete)
        page.resize(page.width(), 750)
        self.assertTrue(stage.complete)
        self.assertEqual(3, page.finance_table.rowCount())

    def test_primary_keyboard_entry_survives_secondary_phases(self):
        page = self.open('inventory')
        page.item_name.setFocus()
        QTest.keyClicks(page.item_name, 'QA keyboard')
        self.finish(page)
        self.assertEqual('QA keyboard', page.item_name.text())
        self.assertIs(page.item_name, self.app.focusWidget())


if __name__ == '__main__':
    unittest.main()
