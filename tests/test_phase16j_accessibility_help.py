from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QWidget,
)

from app.language import LanguageController, _has_greek
from app.ui_help import HELP_TEXTS, apply_help_tooltips


class HelpAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.language = LanguageController(
            self.app,
            SimpleNamespace(active_profile=SimpleNamespace(language="el")),
        )
        self.root = QMainWindow()
        self.page = QWidget()
        self.root.setCentralWidget(self.page)
        layout = QFormLayout(self.page)
        self.label = QLabel("Ποσό")
        self.field = QLineEdit()
        layout.addRow(self.label, self.field)
        apply_help_tooltips(self.root)
        # The real MainWindow also reapplies help to page instances. This must
        # not install an overlapping F1 shortcut on the page itself.
        apply_help_tooltips(self.page)

    def tearDown(self) -> None:
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.root.close()
        self.root.deleteLater()

    def test_help_is_exposed_to_assistive_apis_and_single_f1(self) -> None:
        expected = HELP_TEXTS["Ποσό"]
        for widget in (self.label, self.field):
            with self.subTest(widget=type(widget).__name__):
                self.assertEqual(expected, widget.accessibleDescription())
                self.assertEqual(expected, widget.whatsThis())
                self.assertTrue(widget.toolTip())

        self.assertTrue(self.root.property("mastixaKeyboardHelpInstalled"))
        self.assertFalse(self.page.property("mastixaKeyboardHelpInstalled"))
        self.assertFalse(hasattr(self.page, "_mastixa_help_shortcut"))

        shortcut = self.root._mastixa_help_shortcut
        self.assertEqual(QKeySequence(Qt.Key.Key_F1), shortcut.key())
        self.assertEqual(
            Qt.ShortcutContext.WidgetWithChildrenShortcut,
            shortcut.context(),
        )

        self.root.show()
        self.field.setFocus()
        self.app.processEvents()
        self.assertIs(self.app.focusWidget(), self.field)
        with patch("app.help_accessibility.QToolTip.showText") as show_text:
            shortcut.activated.emit()
            show_text.assert_called_once()
            self.assertIs(show_text.call_args.args[2], self.field)

    def test_assistive_help_switches_both_language_directions(self) -> None:
        source = HELP_TEXTS["Ποσό"]
        english = self.language._packs["en"].translations[source]

        for code, expected in (("en", english), ("el", source), ("en", english)):
            self.language.set_language(code, persist=False)
            self.language.apply_to(self.root)
            with self.subTest(language=code):
                self.assertEqual(expected, self.label.accessibleDescription())
                self.assertEqual(expected, self.field.accessibleDescription())
                self.assertEqual(expected, self.label.whatsThis())
                self.assertEqual(expected, self.field.whatsThis())
                if code == "en":
                    self.assertFalse(_has_greek(self.field.accessibleDescription()))


if __name__ == "__main__":
    unittest.main()
