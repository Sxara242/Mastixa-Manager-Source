from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLabel, QMessageBox

from app import language as language_module
from app.database import Database
from app.language import LanguageController, install_language_controller
from app.plant_tracking import PlantEvent, PlantRecord
from app.plant_tracking_store import PlantTrackingStore
from app.plant_tracking_ui import PlantDialog, PlantEventDialog, PlantTrackingPage
from app.profile_manager import ProfileManager


class PlantTrackingUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_page_lists_projected_state_history_and_soft_deleted_records(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "plants-ui.db")
            field_id = db.execute(
                "INSERT INTO fields(name) VALUES(?)", ("North field",)
            )
            store = PlantTrackingStore(db)
            store.save_plant(
                PlantRecord(
                    id="tree-001",
                    field_id=str(field_id),
                    label="A-001",
                    planted_date="2026-03-01",
                    variety="Mastic",
                    latitude=38.25,
                    longitude=26.02,
                    status="active",
                    health="good",
                    notes="North row",
                )
            )
            store.append_event(
                PlantEvent(
                    id="event-001",
                    plant_id="tree-001",
                    event_date="2026-04-10",
                    kind="health",
                    value="watch",
                    notes="Recheck next visit",
                )
            )

            page = PlantTrackingPage(db)
            try:
                self.assertEqual(1, page.table.rowCount())
                self.assertEqual("A-001", page.table.item(0, 0).text())
                self.assertEqual("North field", page.table.item(0, 1).text())
                self.assertEqual("Παρακολούθηση", page.table.item(0, 5).text())
                self.assertEqual("1", page.table.item(0, 6).text())
                self.assertEqual("10/04/2026", page.table.item(0, 7).text())

                page.table.selectRow(0)
                QApplication.processEvents()
                self.assertEqual("tree-001", page.selected_id)
                self.assertEqual(1, page.history.rowCount())
                self.assertEqual("Υγεία", page.history.item(0, 1).text())

                store.delete_plant("tree-001")
                page.refresh()
                self.assertEqual(0, page.table.rowCount())
                page.include_deleted.setChecked(True)
                QApplication.processEvents()
                self.assertEqual(1, page.table.rowCount())
                self.assertEqual("A-001", page.table.item(0, 0).text())
            finally:
                page.deleteLater()

    def test_page_explains_individual_tracking_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = PlantTrackingPage(Database(Path(folder) / "optional.db"))
            try:
                texts = [label.text() for label in page.findChildren(QLabel)]
                self.assertIn("Μεμονωμένα Φυτά / Δέντρα", texts)
                self.assertTrue(any("Δεν αλλάζει αυτόματα" in value for value in texts))
            finally:
                page.deleteLater()

    def test_plant_dialog_axis_and_native_buttons_follow_app_language(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = Database(root / "plants-localization.db")
            db.execute("INSERT INTO fields(name) VALUES(?)", ("North field",))
            profiles = ProfileManager(root / "profiles")
            language = LanguageController(self.app, profiles)
            plant_dialog = PlantDialog(db)
            event_dialog = PlantEventDialog("tree-001")
            try:
                plant_form = plant_dialog.layout().itemAt(0).layout()
                latitude_label = plant_form.labelForField(plant_dialog.latitude)
                longitude_label = plant_form.labelForField(plant_dialog.longitude)
                plant_buttons = plant_dialog.findChild(QDialogButtonBox)
                event_buttons = event_dialog.findChild(QDialogButtonBox)
                self.assertIsNotNone(latitude_label)
                self.assertIsNotNone(longitude_label)
                self.assertIsNotNone(plant_buttons)
                self.assertIsNotNone(event_buttons)

                for code in ("el", "en", "el"):
                    language.set_language(code, persist=False)
                    language.apply_to(plant_dialog)
                    language.apply_to(event_dialog)
                    if code == "en":
                        expected_axis = ("Latitude (WGS84)", "Longitude (WGS84)")
                        expected_buttons = ("Save", "Cancel")
                    else:
                        expected_axis = (
                            "Γεωγραφικό πλάτος (WGS84)",
                            "Γεωγραφικό μήκος (WGS84)",
                        )
                        expected_buttons = ("Αποθήκευση", "Ακύρωση")

                    self.assertEqual(expected_axis[0], latitude_label.text())
                    self.assertEqual(expected_axis[1], longitude_label.text())
                    for button_box in (plant_buttons, event_buttons):
                        self.assertEqual(
                            expected_buttons[0],
                            button_box.button(QDialogButtonBox.StandardButton.Save).text(),
                        )
                        self.assertEqual(
                            expected_buttons[1],
                            button_box.button(QDialogButtonBox.StandardButton.Cancel).text(),
                        )
            finally:
                self.app.removeEventFilter(language)
                language._enabled = False
                plant_dialog.close()
                event_dialog.close()
                plant_dialog.deleteLater()
                event_dialog.deleteLater()

    def test_plant_validation_warnings_are_localized_without_echoing_raw_input(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = Database(root / "plants-warning-localization.db")
            db.execute("INSERT INTO fields(name) VALUES(?)", ("North field",))
            profiles = ProfileManager(root / "profiles")
            language = LanguageController(self.app, profiles)
            previous_controller = language_module._active_controller
            install_language_controller(language)
            plant_dialog = PlantDialog(db)
            event_dialog = PlantEventDialog("tree-001")
            plant_dialog.field.setCurrentIndex(1)
            plant_dialog.latitude.setText("PRIVATE_COORDINATE_VALUE")
            plant_dialog.longitude.setText("26.0")
            try:
                expectations = {
                    "el": (
                        "Μη έγκυρα στοιχεία",
                        "Έλεγξε τα στοιχεία του φυτού.",
                        "Έλεγξε τα στοιχεία του συμβάντος.",
                    ),
                    "en": (
                        "Invalid information",
                        "Check the plant information.",
                        "Check the event information.",
                    ),
                }
                for code in ("el", "en", "el"):
                    language.set_language(code, persist=False)
                    title, plant_message, event_message = expectations[code]

                    with patch.object(QMessageBox, "warning") as warning:
                        plant_dialog._accept_if_valid()
                    warning.assert_called_once()
                    self.assertEqual(title, warning.call_args.args[1])
                    self.assertEqual(plant_message, warning.call_args.args[2])
                    self.assertNotIn(
                        "PRIVATE_COORDINATE_VALUE",
                        " ".join(str(value) for value in warning.call_args.args[1:]),
                    )

                    with patch.object(QMessageBox, "warning") as warning:
                        event_dialog._accept_if_valid()
                    warning.assert_called_once()
                    self.assertEqual(title, warning.call_args.args[1])
                    self.assertEqual(event_message, warning.call_args.args[2])
            finally:
                language.set_language("el", persist=False)
                language_module._active_controller = previous_controller
                self.app.removeEventFilter(language)
                language._enabled = False
                plant_dialog.close()
                event_dialog.close()
                plant_dialog.deleteLater()
                event_dialog.deleteLater()

    def test_startup_integration_appends_after_crop_program_without_shifting_indices(self) -> None:
        # This test verifies the startup-extension contract, not QWidget lifetime.
        # Constructing the full MainWindow here duplicated the much broader startup
        # tests and intermittently crashed inside native Qt teardown on Windows CI.
        # Lightweight page stubs keep the same integration assertions deterministic
        # while the real CropProgramsPage/PlantTrackingPage behavior is covered by
        # their dedicated UI tests above and in test_crop_program_ui.py.
        from app import crop_program_integration, main_window, plant_tracking_integration

        original_window = main_window.MainWindow
        original_crop_page = crop_program_integration.CropProgramsPage
        original_plant_page = plant_tracking_integration.PlantTrackingPage

        class BaseWindow:
            def __init__(self, *args, **kwargs) -> None:
                self.db = object()
                self.pages = [
                    ("Ρυθμίσεις" if index == 31 else f"page-{index}", object())
                    for index in range(32)
                ]
                self.recording_groups = [("Καταγραφή", [])]

        class StubPage:
            def __init__(self, db: object, kind: str) -> None:
                self.db = db
                self.kind = kind

        try:
            main_window.MainWindow = BaseWindow
            crop_program_integration.CropProgramsPage = lambda db: StubPage(db, "crop")
            plant_tracking_integration.PlantTrackingPage = lambda db: StubPage(db, "plant")

            crop_program_integration.install_crop_program_ui()
            plant_tracking_integration.install_plant_tracking_ui()
            window = main_window.MainWindow()

            self.assertEqual(34, len(window.pages))
            self.assertEqual("Ρυθμίσεις", window.pages[31][0])
            self.assertEqual("Πρόγραμμα Καλλιέργειας", window.pages[32][0])
            self.assertEqual("crop", window.pages[32][1].kind)
            self.assertEqual("Μεμονωμένα Φυτά / Δέντρα", window.pages[33][0])
            self.assertEqual("plant", window.pages[33][1].kind)
            self.assertIn(
                ("Πρόγραμμα Καλλιέργειας", 32),
                window.recording_groups[0][1],
            )
            self.assertIn(
                ("Μεμονωμένα Φυτά / Δέντρα", 33),
                window.recording_groups[0][1],
            )
        finally:
            main_window.MainWindow = original_window
            crop_program_integration.CropProgramsPage = original_crop_page
            plant_tracking_integration.PlantTrackingPage = original_plant_page


if __name__ == "__main__":
    unittest.main()
