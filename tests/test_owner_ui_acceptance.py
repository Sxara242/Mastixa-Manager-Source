"""Owner regressions for cached theme lifecycle and constrained desktop UI."""
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QScrollArea, QTableWidgetItem
from tests import test_ui_revamp_phase1 as fixture


class OwnerUiAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.UiRevampTests.setUpClass()

    def setUp(self):
        self.case = fixture.UiRevampTests('test_small_window_scroll_and_dark_palette')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.case.window.resize(1050, 720)
        self.case.window.show()
        self.case.theme.set_theme('light', persist=False)
        QTest.qWait(30)

    def page(self, key):
        self.case.nav.open(key)
        QTest.qWait(20)
        holder = self.case.window.pages[self.case.nav.targets[key].page][1]
        return holder.resolved_page() if hasattr(holder, 'resolved_page') else holder

    def test_cached_hidden_page_catches_up_in_both_directions_without_font_change(self):
        page = self.page('expense')
        child = QLabel('Raw Ω', page)
        child.setStyleSheet('QLabel { background:#f5f6f3; color:#21483A; }')
        page.layout().addWidget(child)
        self.case.theme.apply_to(page)
        QTest.qWait(20)
        original, font = child.styleSheet(), child.font()
        self.page('settings')
        with patch.object(self.case.app, 'setStyleSheet', wraps=self.case.app.setStyleSheet) as setter:
            self.case.theme.set_theme('dark', persist=False)
            self.assertEqual(original, child.styleSheet())
            self.page('expense')
            self.assertIn('#e7ecef', child.styleSheet())
            self.assertEqual(font, child.font())
            self.page('settings')
            self.case.theme.set_theme('light', persist=False)
            self.assertIn('#e7ecef', child.styleSheet())
            self.page('expense')
            self.assertEqual(original, child.styleSheet())
            self.assertEqual(font, child.font())
            setter.assert_not_called()
        self.assertEqual(1, self.case.theme.receivers('2theme_changed(QString)'))

    def test_report_icons_and_localized_return_controls(self):
        hub = self.page('reports')
        self.assertEqual(7, len(hub.buttons))
        self.assertTrue(all(not button.icon().isNull() for button in hub.buttons))
        self.assertEqual(1, len({button.iconSize().width() for button in hub.buttons}))
        self.assertEqual(1, len({button.height() for button in hub.buttons}))
        self.page('annual_report')
        back = self.case.nav.actions['reports']
        self.assertTrue(back.isVisible())
        self.assertEqual('Επιστροφή στις Αναφορές', back.text())
        self.case.controller.set_language('en', persist=False)
        self.assertEqual('Back to Reports', back.text())
        back.click()
        self.assertEqual(self.case.nav.targets['reports'].page, self.case.window._current_page_index())

    def test_tools_return_and_click_already_selected_settings(self):
        settings = self.page('settings')
        self.assertFalse(settings.tabs.documentMode())
        self.assertTrue(self.case.nav.tools_description.isVisible())
        for route in ('year_lock', 'data_export', 'declaration', 'package', 'sensors'):
            with self.subTest(route=route):
                self.page(route)
                self.assertEqual(self.case.nav.items['settings'].index(), self.case.nav.tree.currentIndex())
                self.assertTrue(self.case.nav.actions['settings'].isVisible())
                self.case.nav.actions['settings'].click()
                self.assertEqual(31, self.case.window._current_page_index())
                self.page(route)
                tree = self.case.nav.tree
                tree.scrollTo(self.case.nav.items['settings'].index())
                QTest.mouseClick(tree.viewport(), Qt.MouseButton.LeftButton,
                                pos=tree.visualRect(self.case.nav.items['settings'].index()).center())
                self.assertEqual(31, self.case.window._current_page_index())
        self.case.controller.set_language('en', persist=False)
        self.assertEqual('Back to Settings', self.case.nav.actions['settings'].text())

    def test_work_popup_width_hover_and_unavailable_option(self):
        self.page('activity')
        combo = self.case.nav.selector
        self.case.theme.apply_to(self.case.nav.header)
        combo.showPopup()
        QTest.qWait(30)
        view = combo.view()
        self.assertTrue(view.hasMouseTracking())
        longest = max(view.fontMetrics().horizontalAdvance(combo.itemText(i)) for i in range(combo.count()))
        self.assertGreaterEqual(view.width(), longest)
        self.assertFalse(combo.model().item(combo.findData('other')).isEnabled())
        combo.hidePopup()
        self.case.theme.set_theme('dark', persist=False)
        combo.showPopup()
        QTest.qWait(20)
        self.assertTrue(view.hasMouseTracking())
        combo.hidePopup()

    def test_constrained_tables_keep_long_values_accessible(self):
        for key, attribute in (('expense', 'table'), ('equipment', 'equipment_table'),
                               ('history', 'table'), ('annual_report', 'finance_table')):
            with self.subTest(key=key):
                page = self.page(key)
                # This test inspects below-fold report tables. Deliberately
                # expose them through the same completion hook as scrolling.
                construction = getattr(page, '_secondary_construction', None)
                if construction is not None:
                    construction.finish_all()
                table = getattr(page, attribute)
                table.setRowCount(1)
                text = 'Long representative owner value Ω ' * 5
                for column in range(table.columnCount()):
                    table.setItem(0, column, QTableWidgetItem(text))
                table.resizeColumnsToContents()
                QTest.qWait(20)
                self.assertGreater(table.horizontalScrollBar().maximum(), 0)
                table.horizontalScrollBar().setValue(table.horizontalScrollBar().maximum())
                self.assertEqual(text, table.item(0, table.columnCount() - 1).text())
        for key in ('products', 'annual_report'):
            scroll = self.page(key).findChild(QScrollArea)
            self.assertEqual(Qt.ScrollBarPolicy.ScrollBarAsNeeded, scroll.horizontalScrollBarPolicy())
        for key in ('expense', 'history', 'products'):
            scroll = self.page(key).findChild(QScrollArea)
            self.assertLessEqual(scroll.widget().width(), scroll.viewport().width())

    def test_production_date_and_field_tools_share_usable_geometry(self):
        page = self.page('production')
        self.assertGreaterEqual(page.date.width(), 148)
        self.assertGreaterEqual(page.date.lineEdit().width(), page.date.fontMetrics().horizontalAdvance(page.date.text()))
        self.page('fields')
        actions = [self.case.nav.actions[key] for key in ('map', 'field_profile', 'plants')]
        self.assertTrue(all(button.parent() is self.case.nav.field_tools for button in actions))
        self.assertEqual(1, len({button.geometry().top() for button in actions}))
        self.assertTrue(all(button.isVisible() for button in actions))


if __name__ == '__main__':
    unittest.main()
