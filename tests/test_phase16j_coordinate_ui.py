"""Coordinate dialog UI localization; file-format and user values stay unchanged."""
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from app.database import Database
from app.gis.geometry import manual_coordinates
from app.gis.store import GeometryStore
from app.gis.export_dialog import CoordinateExportDialog
from app.gis import exports
from app.language import LanguageController, _has_greek


class CoordinateLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.folder.name) / 'fixture.db')
        self.identity = self.db.execute('INSERT INTO fields(name,kaek) VALUES(?,?)',
                                       ('Παραγωγή / John Deere X350', '001234'))
        GeometryStore(self.db).save(self.identity, manual_coordinates(
            '26 38\n26.001 38\n26.001 38.001\n26 38.001', 'EPSG:4326'))
        with self.db.connect() as conn:
            self.before = list(conn.iterdump())
        self.language = LanguageController(
            self.app, SimpleNamespace(active_profile=SimpleNamespace(language='el')))
        self.dialog = CoordinateExportDialog(self.db, self.identity)
        self.dialog.show()
        self.app.processEvents()

    def tearDown(self):
        self.dialog.close()
        self.dialog.deleteLater()
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.app.processEvents()
        with self.db.connect() as conn:
            self.assertEqual(self.before, list(conn.iterdump()))
        self.folder.cleanup()

    def language_ui(self, code):
        self.language.set_language(code, persist=False)
        self.language.apply_to(self.dialog)
        self.app.processEvents()

    def test_open_dialog_cycles_keep_names_and_file_headers_unchanged(self):
        original_rows = exports.table(self.dialog.parcels, 'wgs84')
        for code in ('el', 'en', 'el', 'en', 'el', 'en'):
            with self.subTest(language=code):
                self.language_ui(code)
                self.assertEqual('Coordinate export' if code == 'en' else 'Εξαγωγή κορυφών',
                                 self.dialog.windowTitle())
                self.assertEqual('Παραγωγή / John Deere X350 · KAEK: 001234',
                                 self.dialog.fields.item(0).text())
                self.assertEqual('Παραγωγή / John Deere X350', self.dialog.preview.item(0, 0).text())
                self.assertEqual(original_rows, exports.table(self.dialog.parcels, 'wgs84'))
                captions = [w.text() for w in self.dialog.findChildren(QPushButton)]
                captions += [w.text() for w in self.dialog.findChildren(QLabel)]
                captions += [self.dialog.mode.itemText(i) for i in range(self.dialog.mode.count())]
                captions += [self.dialog.preview.horizontalHeaderItem(i).text()
                             for i in range(self.dialog.preview.columnCount())]
                if code == 'en':
                    self.assertFalse(any(_has_greek(text) for text in captions), captions)
                else:
                    self.assertIn('Όλα', captions)
                    self.assertIn('Γεωγραφικό πλάτος', captions)
                    self.assertIn('αγροτεμάχια', self.dialog.note.text())

    def test_dynamic_selection_mode_and_failure_messages_follow_language(self):
        for code in ('en', 'el', 'en'):
            self.language_ui(code)
            self.dialog.select_all(False)
            self.app.processEvents()
            self.assertEqual('Select fields' if code == 'en' else 'Επίλεξε αγροτεμάχια',
                             self.dialog.note.text())
            self.dialog.select_all(True)
            self.dialog.mode.setCurrentIndex(1)
            self.app.processEvents()
            self.assertEqual('source', self.dialog.effective_mode())
            self.assertEqual('X / Longitude' if code == 'en' else 'X / Γεωγραφικό μήκος',
                             self.dialog.preview.horizontalHeaderItem(10).text())
            with patch('app.gis.export_dialog.exports.snapshot', side_effect=ValueError('private raw diagnostic')):
                self.dialog.refresh()
            self.app.processEvents()
            self.assertFalse(self.dialog.parcels)
            self.assertNotIn('private raw diagnostic', self.dialog.note.text())
            self.assertEqual(code == 'el', _has_greek(self.dialog.note.text()))

