"""Audit literal UI sources, excluding protocol/dynamic data and the retired page copy."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit
from app.language import LanguageController, _has_greek


class StaticUiCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = LanguageController(
            self.app, SimpleNamespace(active_profile=SimpleNamespace(language='el')))

    def tearDown(self):
        self.app.removeEventFilter(self.language)
        self.language._enabled = False

    def test_literal_greek_ui_sources_have_complete_english_output(self):
        self.language.set_language('en', persist=False)
        apis = {'setWindowTitle', 'setTitle', 'QLabel', 'QPushButton', 'QCheckBox',
                'QGroupBox', 'setPlaceholderText', 'addRow', 'setToolTip',
                'setWhatsThis', 'setAccessibleName', 'setAccessibleDescription',
                'setText', 'warning', 'information', 'question', 'critical',
                'getText', 'getItem', 'getSaveFileName', 'getOpenFileName'}
        count = 0
        for path in (Path(__file__).resolve().parents[1] / 'app').rglob('*.py'):
            if path.name == 'pagesbackup.py':
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
                if not isinstance(node, ast.Call):
                    continue
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
                if name not in apis:
                    continue
                for value in node.args:
                    if isinstance(value, ast.Constant) and isinstance(value.value, str) and _has_greek(value.value):
                        count += 1
                        with self.subTest(file=path.name, line=node.lineno, text=value.value):
                            self.assertFalse(_has_greek(self.language.translate(value.value)))
        self.assertGreater(count, 500, 'The scanner must exercise the actual application UI sources')

    def test_titles_placeholders_help_and_status_cycle_without_stale_text(self):
        dialog = QDialog()
        dialog.setWindowTitle('Επεξεργασία αγροτεμαχίου')
        status = QLabel('Δεν υπάρχει ακόμα αποθηκευμένο backup.', dialog)
        edit = QLineEdit('Παραγωγή', dialog)
        edit.setPlaceholderText('YYYY-MM-DD (προαιρετικό)')
        status.setToolTip('Η μονάδα μετρητή δεν αλλάζει όταν υπάρχει ιστορικό service.')
        try:
            for code in ('en', 'el', 'en', 'el'):
                self.language.set_language(code, persist=False)
                self.language.apply_to(dialog)
                self.assertEqual('Edit field' if code == 'en' else 'Επεξεργασία αγροτεμαχίου', dialog.windowTitle())
                self.assertEqual('YYYY-MM-DD (optional)' if code == 'en' else 'YYYY-MM-DD (προαιρετικό)', edit.placeholderText())
                self.assertEqual('Παραγωγή', edit.text())
                self.assertEqual(code == 'el', _has_greek(status.text()))
                self.assertEqual(code == 'el', _has_greek(status.toolTip()))
        finally:
            dialog.deleteLater()
