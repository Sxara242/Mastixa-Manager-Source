from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QWidget

from app.startup_lazy_pages import LazyPage, LazySettingsPage


class _RefreshPage(QWidget):
    created = 0

    def __init__(self) -> None:
        super().__init__()
        type(self).created += 1
        self.refresh_calls = 0

    def refresh(self) -> None:
        self.refresh_calls += 1


class _SelfRefreshingPage(QWidget):
    created = 0

    def __init__(self) -> None:
        super().__init__()
        type(self).created += 1
        self.refresh_calls = 0
        self.refresh()

    def refresh(self) -> None:
        self.refresh_calls += 1


class _SettingsPage(QWidget):
    profile_switch_requested = Signal(str)


class StartupLazyPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        _RefreshPage.created = 0
        _SelfRefreshingPage.created = 0

    def test_factory_is_deferred_until_first_refresh(self) -> None:
        lazy = LazyPage(_RefreshPage)
        self.assertFalse(lazy.is_loaded)
        self.assertEqual(0, _RefreshPage.created)

        lazy.refresh()

        self.assertTrue(lazy.is_loaded)
        self.assertEqual(1, _RefreshPage.created)
        self.assertEqual(1, lazy.resolved_page().refresh_calls)

    def test_loaded_page_is_reused(self) -> None:
        lazy = LazyPage(_RefreshPage)
        lazy.refresh()
        first = lazy.resolved_page()
        lazy.refresh()
        second = lazy.resolved_page()

        self.assertIs(first, second)
        self.assertEqual(1, _RefreshPage.created)
        self.assertEqual(2, first.refresh_calls)

    def test_self_refreshing_page_skips_only_duplicate_first_navigation_refresh(self) -> None:
        lazy = LazyPage(
            _SelfRefreshingPage,
            skip_first_navigation_refresh=True,
        )

        lazy.refresh()
        page = lazy.resolved_page()

        self.assertEqual(1, _SelfRefreshingPage.created)
        self.assertEqual(1, page.refresh_calls)

        lazy.refresh()
        self.assertEqual(2, page.refresh_calls)

    def test_resolved_page_still_refreshes_on_later_navigation(self) -> None:
        lazy = LazyPage(
            _SelfRefreshingPage,
            skip_first_navigation_refresh=True,
        )
        page = lazy.resolved_page()
        self.assertEqual(1, page.refresh_calls)

        lazy.refresh()
        self.assertEqual(2, page.refresh_calls)

    def test_settings_signal_is_forwarded_after_load(self) -> None:
        lazy = LazySettingsPage(_SettingsPage)
        received: list[str] = []
        lazy.profile_switch_requested.connect(received.append)

        real = lazy.resolved_page()
        real.profile_switch_requested.emit("profile-2")

        self.assertEqual(["profile-2"], received)

    def test_main_installs_lazy_pages_after_extension_installers(self) -> None:
        with open("main.py", "r", encoding="utf-8") as handle:
            source = handle.read()

        lazy_call = source.index("install_startup_lazy_pages()")
        for call in (
            "install_crop_program_ui()",
            "install_phase13_calendar_ui()",
            "install_plant_tracking_ui()",
            "install_sensor_view_ui()",
        ):
            self.assertLess(source.index(call), lazy_call)


if __name__ == "__main__":
    unittest.main()
