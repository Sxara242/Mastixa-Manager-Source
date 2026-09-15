from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox

from app.profile_login_keyboard import install_profile_login_keyboard
from app.profile_manager import UserProfile
from app.settings import ProfileSelectionDialog


class _Profiles:
    def __init__(self) -> None:
        self.profile = UserProfile(
            id="profile-1",
            name="Test",
            database_path=Path("test.db"),
            backup_dir=Path("backup"),
            created_at="2026-09-15T00:00:00",
            has_pin=True,
            is_active=True,
        )
        self.saved_language = None

    def profiles(self):
        return [self.profile]

    @property
    def active_profile(self):
        return self.profile

    def has_pin(self, profile_id: str) -> bool:
        return profile_id == self.profile.id

    def verify_pin(self, profile_id: str, pin: str) -> bool:
        return profile_id == self.profile.id and pin == "1234"

    def set_language(self, profile_id: str, language: str):
        self.saved_language = (profile_id, language)
        return self.profile

    def get(self, profile_id: str):
        if profile_id != self.profile.id:
            raise RuntimeError(profile_id)
        return self.profile


class _Language:
    language = "el"

    def available_languages(self):
        return (SimpleNamespace(native_name="Ελληνικά", code="el"),)

    def set_language(self, language: str, persist: bool = True) -> None:
        self.language = language


class ProfileLoginKeyboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        install_profile_login_keyboard()

    def _dialog(self) -> ProfileSelectionDialog:
        dialog = ProfileSelectionDialog(_Profiles(), _Language())
        dialog.pin_edit.setText("1234")
        dialog.show()
        self.app.processEvents()
        return dialog

    def test_open_button_is_default(self) -> None:
        dialog = self._dialog()
        try:
            box = dialog.findChild(QDialogButtonBox)
            self.assertIsNotNone(box)
            open_button = box.button(QDialogButtonBox.StandardButton.Open)
            self.assertTrue(open_button.isDefault())
            self.assertTrue(open_button.autoDefault())
        finally:
            dialog.close()

    def test_return_accepts_valid_pin(self) -> None:
        dialog = self._dialog()
        QTest.keyClick(dialog.pin_edit, Qt.Key.Key_Return)
        self.app.processEvents()
        self.assertEqual(QDialog.DialogCode.Accepted, dialog.result())

    def test_keypad_enter_accepts_valid_pin(self) -> None:
        dialog = self._dialog()
        QTest.keyClick(dialog.pin_edit, Qt.Key.Key_Enter)
        self.app.processEvents()
        self.assertEqual(QDialog.DialogCode.Accepted, dialog.result())


if __name__ == "__main__":
    unittest.main()
