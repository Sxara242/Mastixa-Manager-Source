"""Focused coverage of shipped explanatory help, including contextual entries."""
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QWidget
from app.language import LanguageController, _has_greek
from app.ui_help import HELP_TEXTS, CONTEXT_HELP_TEXTS, _tooltip_html


class HelpLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = LanguageController(
            self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el"))
        )
        self.root = QWidget()
        self.entries = [("general", k, v) for k, v in HELP_TEXTS.items()]
        self.entries += [(group, k, v) for group, entries in CONTEXT_HELP_TEXTS.items()
                         for k, v in entries.items()]

    def tearDown(self):
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.root.deleteLater()

    def test_every_explanation_has_a_complete_english_translation(self):
        translations = self.language._packs["en"].translations
        for group, caption, source in self.entries:
            with self.subTest(group=group, caption=caption):
                self.assertTrue(source in translations, f"Missing full explanation: {group}/{caption}")
                self.assertTrue(translations[source].strip())
                self.assertFalse(_has_greek(translations[source]))

    def test_all_open_help_tooltips_switch_both_directions(self):
        labels = []
        for group, caption, source in self.entries:
            label = QLabel(caption, self.root)
            label.setToolTip(_tooltip_html(source))
            labels.append((group, caption, source, label))
        for code in ("el", "en", "el", "en", "el", "en"):
            self.language.set_language(code, persist=False)
            self.language.apply_to(self.root)
            for group, caption, source, label in labels:
                with self.subTest(language=code, group=group, caption=caption):
                    if code == "el":
                        self.assertEqual(_tooltip_html(source), label.toolTip())
                    else:
                        self.assertFalse(_has_greek(label.toolTip()))
                        expected = self.language._packs["en"].translations.get(source)
                        if expected is not None:
                            self.assertEqual(_tooltip_html(expected), label.toolTip())
