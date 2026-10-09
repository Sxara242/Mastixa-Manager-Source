import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget
from app.database import Database
from app.language import LanguageController
from app import year_context_integration as integration
from app.year_context import begin_year_correction, correction_state, finish_year_correction, set_active_working_year
from app.year_context_ui import CorrectionMutationGuard
from app.year_lock import ensure_year_lock_schema

EL = "Επεξεργάζεσαι ακόμη το κλειδωμένο έτος 2024.\n\nΑν κλείσεις τώρα, η λειτουργία προσωρινής διόρθωσης θα τερματιστεί και στην επόμενη εκκίνηση θα επιστρέψεις στο ενεργό έτος 2027.\n\nΟι αλλαγές που έχουν ήδη αποθηκευτεί παραμένουν. Να κλείσει η εφαρμογή;"
EN = "You are still editing locked year 2024.\n\nIf you close now, temporary correction mode will end and the next launch will return to active year 2027.\n\nChanges already saved will remain. Close the application?"
OUTCOME = "Τερματισμός προσωρινής διόρθωσης κατά το κλείσιμο εφαρμογής"


class ExitCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name)/"exit.db")
        set_active_working_year(self.db, 2027, audit=False)
        ensure_year_lock_schema(self.db)
        self.db.execute("CREATE TABLE audit_events(id INTEGER PRIMARY KEY,event_time TEXT,table_name TEXT,action TEXT,record_id TEXT,details TEXT)")
        self.db.execute("INSERT INTO year_locks(year,is_locked,reason) VALUES(2024,1,'QA')")
        begin_year_correction(self.db,2024,"User reason {year} Ναι")
        self.language = LanguageController(self.app,SimpleNamespace(active_profile=SimpleNamespace(language="el")))

        class Parent(QWidget):
            def closeEvent(window,event):
                window.trace.append("parent")
                window.parent_state = correction_state(window.db)
                event.setAccepted(window.accept_parent)

        # Exercise the actual installed override with a controlled parent close,
        # without constructing every unrelated application page or real backups.
        with patch.object(integration._main_window,"MainWindow",Parent), patch.object(integration._main_window,"YearLockPage"), patch.dict(integration._audit.TABLE_LABELS):
            integration.install_year_context_ui()
            window_type = integration._main_window.MainWindow
        self.window = window_type.__new__(window_type)
        QWidget.__init__(self.window)
        self.window.db = self.db
        self.window.trace = []
        self.window.accept_parent = True

        class Guard(CorrectionMutationGuard):
            hits = 0
            def eventFilter(guard,watched,event):
                if event.type() == QEvent.Type.User:
                    guard.hits += 1
                    return False
                return super().eventFilter(watched,event)

        self.guard = Guard(self.db,self.window)
        self.window._year_correction_guard = self.guard
        self.app.installEventFilter(self.guard)
        self.before = self.snapshot()

    def tearDown(self):
        self.app.removeEventFilter(self.guard)
        finish_year_correction(self.db)
        self.window.deleteLater()
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.app.processEvents()
        self.temp.cleanup()

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump()),correction_state(self.db)

    def assert_guard(self,installed):
        before = self.guard.hits
        self.app.sendEvent(self.window,QEvent(QEvent.Type.User))
        self.assertEqual(self.guard.hits,before+int(installed))

    def modal(self,answer,inspect=lambda box: None):
        errors=[]
        def visit():
            box=self.app.activeModalWidget()
            try:
                self.assertIsInstance(box,QMessageBox)
                inspect(box)
            except BaseException as error:
                errors.append(error)
            finally:
                if isinstance(box,QMessageBox):
                    box.button(answer).click()
        QTimer.singleShot(0,visit)
        event=QCloseEvent()
        self.window.closeEvent(event)
        if errors:
            raise errors[0]
        return event

    def check_dialog(self,box,code):
        self.language.apply_to(box)
        self.assertEqual(box.windowTitle(),"Temporary editing of old year" if code=="en" else "Προσωρινή επεξεργασία παλιού έτους")
        self.assertEqual(box.text(),EN if code=="en" else EL)
        self.assertEqual(box.standardButtons(),QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.assertIs(box.defaultButton(),box.button(QMessageBox.StandardButton.No))
        self.assertEqual(box.button(QMessageBox.StandardButton.Yes).text().replace('&',''),"Yes" if code=="en" else "Ναι")
        self.assertEqual(box.button(QMessageBox.StandardButton.No).text().replace('&',''),"No" if code=="en" else "Όχι")
        self.assertNotIn("User reason",box.text())

    def test_greek_warning(self):
        self.modal(QMessageBox.StandardButton.No,lambda box:self.check_dialog(box,"el"))

    def test_english_warning(self):
        self.language.set_language("en",persist=False)
        self.modal(QMessageBox.StandardButton.No,lambda box:self.check_dialog(box,"en"))

    def test_same_modal_live_cycle(self):
        def inspect(box):
            for code in ("el","en","el","en","el"):
                self.language.set_language(code,persist=False)
                self.assertIs(self.app.activeModalWidget(),box)
                self.check_dialog(box,code)
                self.assertEqual(self.snapshot(),self.before)
        self.modal(QMessageBox.StandardButton.No,inspect)

    def test_no_preserves_state_database_and_guard(self):
        with patch.object(integration,"finish_year_correction") as finish:
            event=self.modal(QMessageBox.StandardButton.No)
            finish.assert_not_called()
        self.assertFalse(event.isAccepted())
        self.assertEqual(self.window.trace,[])
        self.assertEqual(self.snapshot(),self.before)
        self.assert_guard(True)

    def test_yes_parent_accept_finishes_once_then_removes_guard(self):
        original_remove=self.app.removeEventFilter
        def finish(db,**kwargs):
            self.assertEqual(self.window.trace,["parent"])
            self.assert_guard(True)
            self.window.trace.append("finish")
            return finish_year_correction(db,**kwargs)
        def remove(guard):
            if guard is self.guard:
                self.assertIsNone(correction_state(self.db))
                self.window.trace.append("remove")
            original_remove(guard)
        with patch.object(integration,"finish_year_correction",side_effect=finish) as finished, patch.object(self.app,"removeEventFilter",side_effect=remove):
            event=self.modal(QMessageBox.StandardButton.Yes)
            finished.assert_called_once_with(self.db,outcome=OUTCOME)
        self.assertTrue(event.isAccepted())
        self.assertEqual(self.window.trace,["parent","finish","remove"])
        self.assertEqual(self.window.parent_state,self.before[1])
        self.assert_guard(False)
        self.assertIsNone(correction_state(self.db))
        audit=self.db.query("SELECT details FROM audit_events ORDER BY id")
        self.assertEqual(len(audit),2)
        self.assertEqual(audit[-1]['details'],OUTCOME+": έτος 2024 | Αιτιολογία: User reason {year} Ναι")

    def test_yes_parent_reject_preserves_correction_and_guard(self):
        self.window.accept_parent=False
        with patch.object(integration,"finish_year_correction") as finish:
            event=self.modal(QMessageBox.StandardButton.Yes)
            finish.assert_not_called()
        self.assertFalse(event.isAccepted())
        self.assertEqual(self.window.trace,["parent"])
        self.assertEqual(self.snapshot(),self.before)
        self.assert_guard(True)

    def test_inactive_delegates_without_warning_or_finish(self):
        finish_year_correction(self.db)
        for accept in (False,True):
            self.window.accept_parent=accept
            self.window.trace=[]
            with patch.object(QMessageBox,"exec",side_effect=AssertionError("Unexpected dialog")), patch.object(QMessageBox,"warning",side_effect=AssertionError("Unexpected warning")), patch.object(integration,"finish_year_correction") as finish:
                event=QCloseEvent()
                self.window.closeEvent(event)
                finish.assert_not_called()
            self.assertEqual(event.isAccepted(),accept)
            self.assertEqual(self.window.trace,["parent"])
