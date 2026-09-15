from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from app.appearance_theme import ThemeController
from app.database import Database
from app.icon_theme import _path_for_text
from app.main_window import ApplicationController, STYLESHEET, build_app_palette
from app.profile_manager import ProfileManager
from app.settings import ProfileSelectionDialog
from app.widgets import area_input


class ProfileSwitchUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_hot_switch_survives_all_delayed_icon_refreshes(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            child = manager.create("Δεύτερο προφίλ")
            for profile in manager.profiles():
                Database(profile.database_path).set_app_setting(
                    "auto_backup_enabled", "0"
                )
            palette = build_app_palette()
            self.app.setPalette(palette)
            self.app.setStyleSheet(STYLESHEET)
            theme = ThemeController(self.app, STYLESHEET, palette)
            controller = ApplicationController(self.app, theme, manager)
            uncaught: list[tuple] = []
            previous_hook = sys.excepthook
            sys.excepthook = lambda *details: uncaught.append(details)
            try:
                controller.start()
                controller.switch_profile(child.id)
                QTest.qWait(8_300)
                self.assertEqual(child.id, manager.active_profile.id)
                self.assertEqual(child.database_path, controller.window.db.path)
                self.assertEqual([], uncaught)
            finally:
                sys.excepthook = previous_hook
                if controller.window is not None:
                    controller.window._skip_close_backup = True
                    controller.window.close()
                    controller.window.deleteLater()
                QTest.qWait(50)

    def test_startup_chooser_unlocks_pin_and_area_is_compact(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            child = manager.create("Παιδί")
            manager.set_pin(child.id, "2468")
            chooser = ProfileSelectionDialog(manager)
            chooser.combo.setCurrentIndex(chooser.combo.findData(child.id))
            self.assertTrue(chooser.pin_edit.isVisibleTo(chooser))
            chooser.pin_edit.setText("2468")
            chooser.accept()
            self.assertEqual(QDialog.DialogCode.Accepted, chooser.result())
            self.assertEqual(child.id, chooser.selected_profile_id)

            area = area_input()
            area.setValue(5)
            self.assertEqual("5 στρ.", area.text())
            area.setValue(5.125)
            self.assertEqual("5.125 στρ.", area.text())

    def test_report_navigation_uses_matching_optimized_icons(self) -> None:
        expected = {
            "Data Check": "data_quality.png",
            "Data Checks": "data_quality.png",
            "Checks Data": "data_quality.png",
            "Annual Report": "annual_report.png",
            "Annual Farm Report": "annual_report.png",
            "Costs by Field": "field_costs.png",
        }
        for label, filename in expected.items():
            with self.subTest(label=label):
                path = _path_for_text(label)
                self.assertIsNotNone(path)
                self.assertEqual(filename, path.name)
                self.assertTrue(path.is_file())
                image = QImage(str(path))
                self.assertFalse(image.isNull())
                self.assertEqual((512, 512), (image.width(), image.height()))
                self.assertTrue(image.hasAlphaChannel())


if __name__ == "__main__":
    unittest.main()
