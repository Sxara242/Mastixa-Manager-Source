from __future__ import annotations

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

from app.main_window import MainWindow


class RecordingNavigationCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _window_stub(self):
        pages = [(f"Page {index}", QWidget()) for index in range(4)]
        stub = SimpleNamespace(
            tabs=QTabWidget(),
            pages=pages,
            recording_groups=[
                ("Group A", [("A1", 0), ("A2", 1)]),
                ("Group B", [("B1", 2), ("B2", 3)]),
            ],
            _recording_group_tabs=[],
            _recording_group_page_indices=[],
            _last_recording_group=0,
            _last_recording_tab_by_group={},
            _recording_inner_tab_changed=lambda _index: None,
            _tab_icon_for_page=lambda _index: QIcon(),
            _standard_icon=lambda _name: QIcon(),
        )
        return stub

    def test_recording_tabs_are_reused_after_leaving_and_reentering_category(self) -> None:
        stub = self._window_stub()
        try:
            MainWindow._build_recording_tabs(stub)
            first_tabs = tuple(stub._recording_group_tabs)
            self.assertEqual(2, len(first_tabs))
            self.assertEqual(2, stub.tabs.count())

            while stub.tabs.count():
                stub.tabs.removeTab(0)
            stub._recording_group_tabs = []
            stub._recording_group_page_indices = []

            MainWindow._build_recording_tabs(stub)
            second_tabs = tuple(stub._recording_group_tabs)

            self.assertEqual(first_tabs, second_tabs)
            self.assertEqual(2, stub.tabs.count())
            self.assertEqual([[0, 1], [2, 3]], stub._recording_group_page_indices)
        finally:
            stub.tabs.close()
            for _name, page in stub.pages:
                page.close()

    def test_recording_cache_invalidates_when_navigation_structure_changes(self) -> None:
        stub = self._window_stub()
        try:
            MainWindow._build_recording_tabs(stub)
            first_tabs = tuple(stub._recording_group_tabs)

            while stub.tabs.count():
                stub.tabs.removeTab(0)
            stub.recording_groups[0][1].append(("A3", 2))
            stub._recording_group_tabs = []
            stub._recording_group_page_indices = []

            MainWindow._build_recording_tabs(stub)
            second_tabs = tuple(stub._recording_group_tabs)

            self.assertIsNot(first_tabs[0], second_tabs[0])
            self.assertEqual([0, 1, 2], stub._recording_group_page_indices[0])
        finally:
            stub.tabs.close()
            for _name, page in stub.pages:
                page.close()


if __name__ == "__main__":
    unittest.main()
