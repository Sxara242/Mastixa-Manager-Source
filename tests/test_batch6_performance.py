"""Targeted performance regressions without weakening year-context guards."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDate, QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QWidget

from app.database import Database
from app import year_context as context
from app.year_context_ui import CorrectionMutationGuard
from tests.language_fixture import scoped_language


class CorrectionGuardPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.enterContext(scoped_language(self.qt, "el"))
        keys = ("mastixaActiveWorkingYear", "mastixaEffectiveWorkingYear",
                "mastixaCorrectionYear", "mastixaCorrectionReason")
        previous = {key: self.qt.property(key) for key in keys}
        self.addCleanup(lambda: [self.qt.setProperty(key, value) for key, value in previous.items()])
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.db = self.database("first")
        self.window = QWidget()
        self.addCleanup(self.window.deleteLater)
        self.addCleanup(self.window.close)
        self.button = QPushButton("Αποθήκευση", self.window)
        self.guard = CorrectionMutationGuard(self.db, self.window)
        self.message = self.enterContext(patch("app.year_context_ui._message", return_value=QMessageBox.StandardButton.No))
        self.enterContext(patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No))

    def database(self, name):
        db = Database(self.root / (name + ".db"))
        self.addCleanup(context.initialize_year_context, db)
        context.set_active_working_year(db, 2026, audit=False)
        context.is_year_physically_locked(db, 2024)
        db.execute("INSERT OR REPLACE INTO year_locks(year,is_locked) VALUES(2024,1)")
        return db

    def key(self, key=Qt.Key.Key_Space):
        return QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)

    def mouse(self, button=Qt.MouseButton.LeftButton):
        return QMouseEvent(QEvent.Type.MouseButtonPress, QPointF(1, 1), QPointF(1, 1),
                           button, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)

    def test_irrelevant_events_never_resolve_context(self):
        with patch("app.year_context_ui.correction_state") as resolve:
            for kind in (QEvent.Type.Paint, QEvent.Type.Resize, QEvent.Type.LayoutRequest,
                         QEvent.Type.HoverMove, QEvent.Type.MouseMove, QEvent.Type.Enter,
                         QEvent.Type.Leave, QEvent.Type.Show, QEvent.Type.Hide,
                         QEvent.Type.KeyRelease, QEvent.Type.MouseButtonRelease):
                self.assertFalse(self.guard.eventFilter(self.button, QEvent(kind)))
            self.assertFalse(self.guard.eventFilter(self.button, self.key(Qt.Key.Key_A)))
            self.assertFalse(self.guard.eventFilter(self.button, self.mouse(Qt.MouseButton.RightButton)))
            resolve.assert_not_called()

    def test_ineligible_widgets_never_resolve_context(self):
        edit = QLineEdit(self.window)
        other = QWidget()
        self.addCleanup(other.deleteLater)
        outside = QPushButton("Save", other)
        with patch("app.year_context_ui.correction_state") as resolve:
            for widget in (edit, outside):
                self.assertFalse(self.guard.eventFilter(widget, self.key()))
            self.button.setProperty("mastixaYearContextControl", True)
            self.assertFalse(self.guard.eventFilter(self.button, self.key()))
            self.button.setProperty("mastixaYearContextControl", False)
            self.button.setEnabled(False)
            self.assertFalse(self.guard.eventFilter(self.button, self.key()))
            self.button.setEnabled(True)
            self.button.setText("Cancel")
            self.assertFalse(self.guard.eventFilter(self.button, self.key()))
            resolve.assert_not_called()

    def test_all_existing_keyboard_activations_require_confirmation(self):
        context.begin_year_correction(self.db, 2024, "Raw reason")
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            with self.subTest(key=key), patch("app.year_context_ui.audit_correction_action") as audit:
                self.message.return_value = QMessageBox.StandardButton.No
                self.assertTrue(self.guard.eventFilter(self.button, self.key(key)))
                audit.assert_not_called()
                self.message.return_value = QMessageBox.StandardButton.Yes
                self.assertFalse(self.guard.eventFilter(self.button, self.key(key)))
                audit.assert_called_once_with(self.db, self.button.text())
                self.assertEqual("Raw reason", self.message.call_args.kwargs["reason"])

    def test_mouse_activation_requires_confirmation(self):
        context.begin_year_correction(self.db, 2024, "Reason")
        self.assertTrue(self.guard.eventFilter(self.button, self.mouse()))
        self.message.return_value = QMessageBox.StandardButton.Yes
        self.assertFalse(self.guard.eventFilter(self.button, self.mouse()))
        self.assertTrue(context.is_year_physically_locked(self.db, 2024))

    def test_profile_and_context_changes_are_resolved_fresh(self):
        context.begin_year_correction(self.db, 2024, "First profile")
        other = self.database("second")
        self.assertTrue(self.guard.eventFilter(self.button, self.key()))
        self.guard.db = other
        self.message.reset_mock()
        self.assertFalse(self.guard.eventFilter(self.button, self.key()))
        self.message.assert_not_called()
        context.begin_year_correction(other, 2024, "Second profile")
        self.assertTrue(self.guard.eventFilter(self.button, self.key()))
        self.assertEqual("Second profile", self.message.call_args.kwargs["reason"])
        context.finish_year_correction(other)
        self.assertFalse(self.guard.eventFilter(self.button, self.key()))
        # Even reusing a DB handle with a changed path must not retain old state.
        self.guard.db = self.db
        with patch.object(self.db, "path", other.path):
            self.assertFalse(self.guard.eventFilter(self.button, self.key()))
        self.assertTrue(self.guard.eventFilter(self.button, self.key()))

    def check_money_activation(self, keyboard):
        from app.money import MoneyPage
        page = MoneyPage(self.db, "income")
        self.addCleanup(page.deleteLater)
        self.addCleanup(page.close)
        guard = CorrectionMutationGuard(self.db, page)
        page.save_button.installEventFilter(guard)
        page.show()
        def save(year):
            page.date.setDate(QDate(year, 3, 4))
            page.description.setText("Typed raw value")
            page.amount.setValue(12)
            if keyboard:
                QTest.keyClick(page.save_button, Qt.Key.Key_Space)
            else:
                QTest.mouseClick(page.save_button, Qt.MouseButton.LeftButton)
        def rows():
            return [tuple(row) for row in self.db.query("SELECT entry_date,description,amount FROM income ORDER BY id")]
        save(2024)
        self.assertEqual([], rows())
        context.begin_year_correction(self.db, 2024, "Reason")
        save(2024)
        self.assertEqual([], rows())  # NO at the correction prompt blocks the write.
        self.message.return_value = QMessageBox.StandardButton.Yes
        save(2024)
        self.assertEqual([("2024-03-04", "Typed raw value", 12)], rows())
        context.finish_year_correction(self.db)
        save(2026)
        self.assertEqual([("2024-03-04", "Typed raw value", 12),
                          ("2026-03-04", "Typed raw value", 12)], rows())
        self.assertTrue(context.is_year_physically_locked(self.db, 2024))

    def test_locked_mouse_edit_correction_and_current_year(self):
        self.check_money_activation(keyboard=False)

    def test_locked_keyboard_edit_correction_and_current_year(self):
        self.check_money_activation(keyboard=True)


class InventoryLazyPerformanceTests(unittest.TestCase):
    def test_real_inventory_first_load_and_later_refresh(self):
        code = textwrap.dedent('''
            import tempfile, os
            from pathlib import Path
            from unittest.mock import patch
            from PySide6.QtWidgets import QApplication
            with tempfile.TemporaryDirectory() as root:
                os.environ['MASTIXA_DATA_HOME'] = root
                import main
                from app import main_window
                from app.database import Database
                from app.profile_manager import ProfileManager
                from app.inventory import InventoryPage
                app = QApplication([])
                manager = ProfileManager(Path(root) / 'profiles')
                db = Database(manager.active_profile.database_path)
                seed = InventoryPage(db)
                db.execute("INSERT INTO inventory_items(name,unit) VALUES('Initial','kg')")
                seed.close()
                with patch.object(main_window.MainWindow, '_run_startup_backup', lambda self: None):
                    window = main_window.MainWindow(profiles=manager)
                lazy = next(page for title, page in window.pages if title == 'Αποθήκη & Εφόδια')
                calls = []
                original = InventoryPage.refresh
                def refresh(self, *args):
                    calls.append(self)
                    return original(self, *args)
                with patch.object(InventoryPage, 'refresh', refresh):
                    lazy.refresh()
                    page = lazy.resolved_page()
                    assert len(calls) == 1, len(calls)
                    assert page.stock_table.rowCount() == 1
                    assert page.stock_table.item(0, 0).text() == 'Initial'
                    db.execute("INSERT INTO inventory_items(name,unit) VALUES('Later','pieces')")
                    lazy.refresh()
                    assert len(calls) == 2, len(calls)
                    assert page.stock_table.rowCount() == 2
                    assert lazy.resolved_page() is page
                # Avoid the real MainWindow close/backup workflow in this check.
                window.hide()
        ''')
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', code],
                                env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'},
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class ThemeTraversalPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_nested_and_independent_windows_styled_once_and_restored(self):
        from app.appearance_theme import ThemeController
        class CountingLabel(QLabel):
            reads = 0
            def styleSheet(self):
                self.reads += 1
                return super().styleSheet()
        style, palette = self.qt.styleSheet(), self.qt.palette()
        self.addCleanup(self.qt.setStyleSheet, style)
        self.addCleanup(self.qt.setPalette, palette)
        root, independent = QWidget(), QWidget()
        for widget in (root, independent):
            self.addCleanup(widget.deleteLater)
            self.addCleanup(widget.close)
        dialog = QDialog(root)
        nested = QDialog(dialog)
        labels = [CountingLabel("Content", parent) for parent in (root, dialog, nested, independent)]
        original = "color: #21483A; background: #f5f6f3;"
        for label in labels:
            label.setStyleSheet(original)
        controller = ThemeController(self.qt, style, palette)
        self.addCleanup(self.qt.removeEventFilter, controller)
        controller._theme = "light"
        controller.set_theme("dark", persist=False)
        for label in labels:
            self.assertEqual(1, label.reads)
            self.assertIn("#e7ecef", QLabel.styleSheet(label))
            self.assertIn("#171d21", QLabel.styleSheet(label))
        controller.set_theme("light", persist=False)
        for label in labels:
            self.assertEqual(2, label.reads)
            self.assertEqual(original, QLabel.styleSheet(label))
        controller.set_theme("light", persist=False)
        self.assertEqual([2] * 4, [label.reads for label in labels])
