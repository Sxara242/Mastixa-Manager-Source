"""Year-correction wording, modal semantics and read-only language switching."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton
from app.database import Database
from app.language import LanguageController
from app.year_context import (begin_year_correction, correction_state,
                              finish_year_correction, set_active_working_year)
from app.year_context_ui import EnhancedYearLockPage, YearContextBar, CorrectionMutationGuard


class YearCorrectionLocalizationTests(unittest.TestCase):
    REASON = "Παραγωγή <b>Ναι</b> & Αποθήκευση {year}\n  user reason Ω"

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.folder.name) / "fixture.db")
        set_active_working_year(self.db, 2027, audit=False)
        self.language = LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        self.page = EnhancedYearLockPage(self.db)
        for year in (2024, 2025):
            self.db.execute("INSERT INTO year_locks(year,is_locked,reason) VALUES(?,1,?)", (year, self.REASON))
        self.page.refresh()
        self.page.year.setCurrentIndex(self.page.year.findData(2024))
        self.bar = YearContextBar(self.db)
        self.page.show()
        self.bar.show()
        self.app.processEvents()
        self.page.year.setCurrentIndex(self.page.year.findData(2024))

    def tearDown(self):
        finish_year_correction(self.db)
        for widget in (self.page, self.bar):
            widget.close()
            widget.deleteLater()
        self.app.removeEventFilter(self.language)
        self.language._enabled = False
        self.app.processEvents()
        self.folder.cleanup()

    def snapshot(self):
        with self.db.connect() as connection:
            return tuple(connection.iterdump()), correction_state(self.db)

    def switch(self, code):
        self.language.set_language(code, persist=False)
        self.language.apply_to(self.page)
        self.language.apply_to(self.bar)
        self.app.processEvents()

    def active(self):
        begin_year_correction(self.db, 2024, self.REASON)
        self.page.refresh()
        self.bar.refresh()
        self.app.processEvents()

    def modal(self, action, check, answer=QMessageBox.StandardButton.No):
        errors = []
        def inspect():
            box = QApplication.activeModalWidget()
            try:
                self.assertIsInstance(box, QMessageBox)
                check(box)
            except BaseException as error:
                errors.append(error)
            finally:
                if isinstance(box, QMessageBox):
                    box.button(answer).click()
        QTimer.singleShot(0, inspect)
        result = action()
        if errors:
            raise errors[0]
        return result

    def assert_confirmation(self, box, title, text, default):
        self.language.apply_to(box)
        self.assertEqual(title, box.windowTitle())
        self.assertEqual(text, box.text())
        self.assertEqual(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, box.standardButtons())
        self.assertIs(box.button(default), box.defaultButton())

    def test_inactive_banner_live_cycle_is_read_only(self):
        self.page.year.setCurrentIndex(self.page.year.findData(2027))
        before = self.snapshot()
        for code in ("el", "en", "el"):
            self.switch(code)
            self.assertEqual(
                "For a forgotten entry or correction, temporarily open only the locked year you need. The normal active year does not change."
                if code == "en" else "Για ξεχασμένη εγγραφή ή διόρθωση, άνοιξε προσωρινά μόνο το κλειδωμένο έτος που χρειάζεσαι. Το κανονικό ενεργό έτος δεν αλλάζει.",
                self.page.correction_banner.text())
            self.assertEqual(before, self.snapshot())

    def test_active_banners_preserve_reason_and_years_during_live_cycle(self):
        self.page.correction_reason.setText(self.REASON)
        self.active()
        before = self.snapshot()
        for code in ("el", "en", "el", "en"):
            self.switch(code)
            expected = ("WARNING: You are temporarily editing locked year 2024. The active year remains 2027. Reason: "
                        if code == "en" else "ΠΡΟΣΟΧΗ: Επεξεργάζεσαι προσωρινά το κλειδωμένο έτος 2024. Το ενεργό έτος παραμένει 2027. Αιτιολογία: ") + self.REASON
            self.assertEqual(expected, self.page.correction_banner.text())
            self.assertEqual(self.REASON, self.page.correction_reason.text())
            self.assertEqual("Editing year: 2024 — temporary mode" if code == "en" else "Επεξεργασία έτους: 2024 — προσωρινό mode", self.bar.context_label.text())
            self.assertEqual("WARNING: You are editing locked year 2024 — Current year: 2027" if code == "en" else "ΠΡΟΣΟΧΗ: Επεξεργάζεσαι το κλειδωμένο έτος 2024 — Τρέχον έτος: 2027", self.bar.warning_label.text())
            self.assertEqual(before, self.snapshot())
        self.assertEqual(Qt.TextFormat.PlainText, self.page.correction_banner.textFormat())

    def test_begin_confirmation_complete_and_no_preserves_state(self):
        self.page.correction_reason.setText(self.REASON)
        before = self.snapshot()
        for code in ("el", "en"):
            self.switch(code)
            text = ("Locked year 2024 will temporarily open for corrections.\n\nThe active year 2027 will remain saved and will be restored when you finish corrections.\n\nEvery change will display a warning. Continue?" if code == "en" else
                    "Θα ανοίξει προσωρινά για διορθώσεις το κλειδωμένο έτος 2024.\n\nΤο ενεργό έτος 2027 θα παραμείνει αποθηκευμένο και θα επανέλθει μόλις ολοκληρώσεις τις διορθώσεις.\n\nΚάθε ενέργεια αλλαγής θα εμφανίζει προειδοποίηση. Συνέχεια;")
            self.modal(self.page.begin_correction, lambda box: self.assert_confirmation(box, "Edit locked year" if code == "en" else "Επεξεργασία κλειδωμένου έτους", text, QMessageBox.StandardButton.No))
            self.assertEqual(before, self.snapshot())
            self.assertEqual(self.REASON, self.page.correction_reason.text())

    def test_finish_confirmations_preserve_defaults_and_years(self):
        self.active()
        before = self.snapshot()
        for code in ("el", "en"):
            self.switch(code)
            messages = (
                (self.page.finish_correction, "Finish corrections in 2024?\n\nYou will return to active year 2027. 2024 remains locked." if code == "en" else "Να ολοκληρωθούν οι διορθώσεις στο 2024;\n\nΘα επιστρέψεις στο ενεργό έτος 2027. Το 2024 παραμένει κλειδωμένο."),
                (lambda: self.bar._finish_correction(return_active=True), "Finish corrections in 2024 and return to active year 2027?\n\nThe old year remains locked." if code == "en" else "Να ολοκληρωθούν οι διορθώσεις στο 2024 και να επιστρέψεις στο ενεργό έτος 2027;\n\nΤο παλιό έτος παραμένει κλειδωμένο."),
            )
            for action, text in messages:
                self.modal(action, lambda box: self.assert_confirmation(box, "Finish corrections" if code == "en" else "Ολοκλήρωση διορθώσεων", text, QMessageBox.StandardButton.Yes))
                self.assertEqual(before, self.snapshot())

    def test_validation_messages_and_existing_correction_error(self):
        for code in ("el", "en"):
            self.switch(code)
            for selected, reason, expected in (
                (2027, "", "Select a locked year." if code == "en" else "Επίλεξε κλειδωμένο έτος."),
                (2024, "", "Enter a correction reason." if code == "en" else "Συμπλήρωσε αιτιολογία διόρθωσης."),
            ):
                self.page.year.setCurrentIndex(self.page.year.findData(selected))
                self.page.correction_reason.setText(reason)
                before = self.snapshot()
                self.modal(self.page.begin_correction, lambda box: (self.language.apply_to(box), self.assertEqual(expected, box.text())), QMessageBox.StandardButton.Ok)
                self.assertEqual(before, self.snapshot())
        self.active()
        self.page.year.setCurrentIndex(self.page.year.findData(2025))
        self.page.correction_reason.setText(self.REASON)
        for code in ("el", "en"):
            self.switch(code)
            before = self.snapshot()
            # Accept only the first confirmation; inspect the real error modal.
            expected = "A correction session is already active for year 2024." if code == "en" else "Υπάρχει ήδη προσωρινή επεξεργασία για το έτος 2024."
            def first(box):
                QTimer.singleShot(0, second)
            errors = []
            def second():
                box = QApplication.activeModalWidget()
                try:
                    self.language.apply_to(box)
                    self.assertEqual(expected, box.text())
                except BaseException as error:
                    errors.append(error)
                finally:
                    if isinstance(box, QMessageBox):
                        box.button(QMessageBox.StandardButton.Ok).click()
            self.modal(self.page.begin_correction, first, QMessageBox.StandardButton.Yes)
            if errors:
                raise errors[0]
            self.assertEqual(before, self.snapshot())

    def test_mutation_warning_live_cycle_protects_user_reason(self):
        self.active()
        button = QPushButton("Αποθήκευση", self.page)
        guard = CorrectionMutationGuard(self.db, self.page)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        before = self.snapshot()
        def inspect(box):
            for code in ("el", "en", "el"):
                self.switch(code)
                self.language.apply_to(box)
                text = (f"You are editing locked year 2024.\n\nAction: {'Save' if code == 'en' else 'Αποθήκευση'}\nReason: {self.REASON}\n\nContinue with this action?" if code == "en" else
                        f"Επεξεργάζεσαι το κλειδωμένο έτος 2024.\n\nΕνέργεια: Αποθήκευση\nΑιτιολογία: {self.REASON}\n\nΝα συνεχιστεί η ενέργεια;")
                self.assert_confirmation(box, "Temporary editing of old year" if code == "en" else "Προσωρινή επεξεργασία παλιού έτους", text, QMessageBox.StandardButton.No)
                self.assertTrue(any(label.text() == text for label in box.findChildren(QLabel)))
        self.assertTrue(self.modal(lambda: guard.eventFilter(button, event), inspect))
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
