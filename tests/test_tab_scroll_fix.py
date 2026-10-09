import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

from app.tab_scroll_fix import (
    _known_tab_widgets,
    _left_scroll_proxy,
    _native_scroll_buttons,
    _refresh_tab_scroll_controls,
    _sync_native_scroll_buttons,
)


class TabScrollFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_left_scroll_proxy_owns_hit_area_and_drives_native_scroll(self):
        tabs = QTabWidget()
        tabs.resize(280, 160)
        for index in range(9):
            tabs.addTab(QWidget(), f"Long navigation tab {index}")

        tabs.show()
        tabs.setCurrentIndex(tabs.count() - 1)
        self.app.processEvents()

        bar = tabs.tabBar()
        bar.setUsesScrollButtons(False)
        self.assertFalse(bar.usesScrollButtons())

        _refresh_tab_scroll_controls(tabs)
        self.app.processEvents()

        self.assertTrue(bar.usesScrollButtons())
        left_button, right_button = _native_scroll_buttons(bar)
        self.assertIsNotNone(left_button)
        self.assertIsNotNone(right_button)
        self.assertTrue(left_button.isVisible())
        self.assertTrue(left_button.isEnabled())

        proxy = _left_scroll_proxy(bar)
        self.assertIsNotNone(proxy)
        self.assertTrue(proxy.isVisible())
        self.assertTrue(proxy.isEnabled())
        self.assertEqual(left_button.geometry(), proxy.geometry())

        # The production symptom is specifically that the painted native arrow
        # does not receive pointer input. The explicit proxy must own the hit
        # rectangle and its real mouse click must move Qt's native tab offset.
        _sync_native_scroll_buttons(tabs)
        self.app.processEvents()
        hit = bar.childAt(proxy.geometry().center())
        self.assertIs(hit, proxy)

        before = bar.tabRect(0).left()
        QTest.mouseClick(proxy, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        after = bar.tabRect(0).left()
        self.assertGreater(after, before)

        tabs.deleteLater()

    def test_known_navigation_tabs_are_collected_without_tree_scan(self):
        main_tabs = QTabWidget()
        recording_tabs = QTabWidget()
        report_tabs = QTabWidget()

        class DummyWindow:
            tabs = main_tabs
            _recording_group_tabs = [recording_tabs, main_tabs]
            _report_group_tabs = [report_tabs]

        collected = _known_tab_widgets(DummyWindow())
        self.assertEqual([main_tabs, recording_tabs, report_tabs], collected)

        main_tabs.deleteLater()
        recording_tabs.deleteLater()
        report_tabs.deleteLater()


if __name__ == "__main__":
    unittest.main()
