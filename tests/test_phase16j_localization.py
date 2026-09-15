from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton, QWidget

from app.language import LanguageController
from app.profile_manager import ProfileManager


class LocalizationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.profiles = ProfileManager(Path(self.temp.name))
        self.language = LanguageController(self.app, self.profiles)
        self.root = QWidget()

    def tearDown(self):
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.root.close()
        self.root.deleteLater()
        self.temp.cleanup()

    def cycles(self):
        # Both starting directions, without replacing the open widgets.
        for code in ("el", "en", "el", "en", "el", "en"):
            self.language.set_language(code, persist=False)
            self.language.apply_to(self.root)
            yield code

    def test_readonly_business_values_and_paths_are_never_translated(self):
        values = ("Παραγωγή", "C:/Παραγωγή/Αποθήκη/αρχείο.db", "John Deere X350")
        fields = [QLineEdit(value, self.root) for value in values]
        for field in fields:
            field.setReadOnly(True)
        for code in self.cycles():
            with self.subTest(language=code):
                self.assertEqual(list(values), [field.text() for field in fields])

    def test_record_combo_preserves_names_matching_translation_keys(self):
        combo = QComboBox(self.root)
        combo.addItem("Όλα", None)
        combo.addItem("Παραγωγή", 17)
        combo.addItem("Αποθήκη", 18)
        combo.setCurrentIndex(1)
        for code in self.cycles():
            with self.subTest(language=code):
                self.assertEqual("Παραγωγή", combo.itemText(1))
                self.assertEqual("Αποθήκη", combo.itemText(2))
                self.assertEqual(17, combo.currentData())
                self.assertEqual("All" if code == "en" else "Όλα", combo.itemText(0))

    def test_explicit_static_readonly_and_enum_still_translate(self):
        status = QLineEdit("Παραγωγή", self.root)
        status.setReadOnly(True)
        status.setProperty("mastixaI18nStaticText", True)
        combo = QComboBox(self.root)
        combo.setProperty("mastixaI18nStaticItems", True)
        combo.addItem("Παραγωγή", 1)
        for code in self.cycles():
            expected = "Production" if code == "en" else "Παραγωγή"
            self.assertEqual(expected, status.text())
            self.assertEqual(expected, combo.currentText())
            self.assertEqual(1, combo.currentData())

    def test_accessible_description_and_help_follow_language_changes(self):
        button = QPushButton("Αποθήκευση", self.root)
        button.setAccessibleName("Αποθήκευση")
        button.setAccessibleDescription("Παραγωγή")
        button.setToolTip("Παραγωγή")
        button.setWhatsThis("Παραγωγή")
        for code in self.cycles():
            expected = "Production" if code == "en" else "Παραγωγή"
            self.assertEqual(expected, button.accessibleDescription())
            self.assertEqual(expected, button.toolTip())
            self.assertEqual(expected, button.whatsThis())
            self.assertEqual("Save" if code == "en" else "Αποθήκευση", button.accessibleName())
