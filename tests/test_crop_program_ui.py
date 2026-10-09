from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialogButtonBox, QLabel, QMessageBox

from app.crop_program import CropProgramRule
from app.crop_programs import CropProgramsPage, RuleDialog
from app.database import Database
from app.language import LanguageController, install_language_controller, tr
from app.profile_manager import ProfileManager


class CropProgramUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_page_saves_program_and_renders_generated_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "ui.db")
            field_id = db.execute(
                "INSERT INTO fields(name) VALUES(?)", ("UI field",)
            )
            page = CropProgramsPage(db)
            try:
                page.name_edit.setText("Mastic first year")
                page.crop_edit.setText("Mastic")
                page.description_edit.setPlainText("UI contract")
                page.rules = [
                    CropProgramRule(
                        id="water",
                        title="Water",
                        category="irrigation",
                        schedule_kind="interval_window",
                        start_month=5,
                        start_day=1,
                        end_month=5,
                        end_day=15,
                        every_days=7,
                    )
                ]
                page._render_rules()
                page.save_program()

                self.assertIsNotNone(page.selected_program_id)
                detail = page.store.program(page.selected_program_id)
                self.assertEqual("Mastic first year", detail["name"])
                self.assertEqual(1, len(detail["rules"]))
                self.assertEqual(1, page.program_list.count())

                generated = page.store.generate_for_field(
                    page.selected_program_id, field_id, 2026
                )
                self.assertEqual(3, len(generated))
                page.refresh_tasks()
                self.assertEqual(3, page.tasks_table.rowCount())
                self.assertEqual("01/05/2026", page.tasks_table.item(0, 0).text())
                self.assertEqual("UI field", page.tasks_table.item(0, 1).text())
            finally:
                page.deleteLater()

    def test_rule_dates_are_numeric_not_locale_month_names(self) -> None:
        fixed = CropProgramRule(
            id="fixed",
            title="Prune",
            category="pruning",
            schedule_kind="fixed_date",
            month=2,
            day=15,
        )
        dialog = RuleDialog(rule=fixed)
        try:
            self.assertEqual("dd/MM", dialog.fixed_date.displayFormat())
            self.assertNotIn("February", dialog.fixed_date.text())
        finally:
            dialog.deleteLater()

        interval = CropProgramRule(
            id="repeat",
            title="Water",
            category="irrigation",
            schedule_kind="interval_window",
            start_month=5,
            start_day=1,
            end_month=9,
            end_day=30,
            every_days=7,
        )
        dialog = RuleDialog(rule=interval)
        try:
            self.assertEqual("dd/MM", dialog.start_date.displayFormat())
            self.assertEqual("dd/MM", dialog.end_date.displayFormat())
            self.assertNotIn("May", dialog.start_date.text())
            self.assertNotIn("September", dialog.end_date.text())
        finally:
            dialog.deleteLater()

    def test_rule_dialog_save_cancel_follow_live_language(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            manager = ProfileManager(Path(folder))
            controller = LanguageController(self.app, manager)
            install_language_controller(controller)
            dialog = RuleDialog()
            try:
                controller.apply_to(dialog)
                buttons = dialog.findChild(QDialogButtonBox)
                self.assertIsNotNone(buttons)
                self.assertEqual(
                    "Αποθήκευση",
                    buttons.button(QDialogButtonBox.StandardButton.Save).text(),
                )
                self.assertEqual(
                    "Ακύρωση",
                    buttons.button(QDialogButtonBox.StandardButton.Cancel).text(),
                )

                controller.set_language("en", persist=False)
                self.app.processEvents()
                controller.apply_to(dialog)
                self.assertEqual(
                    "Save",
                    buttons.button(QDialogButtonBox.StandardButton.Save).text(),
                )
                self.assertEqual(
                    "Cancel",
                    buttons.button(QDialogButtonBox.StandardButton.Cancel).text(),
                )
            finally:
                dialog.deleteLater()

    def test_program_category_and_rule_association_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "association-ui.db")
            page = CropProgramsPage(db)
            try:
                page.name_edit.setText("Φυτοπροστασία")
                page.crop_edit.setText("Μαστίχα")
                category_index = page.program_category_combo.findData(
                    "plant_protection"
                )
                self.assertGreaterEqual(category_index, 0)
                page.program_category_combo.setCurrentIndex(category_index)
                page.save_program()

                detail = page.store.program(page.selected_program_id)
                self.assertEqual("plant_protection", detail["category"])
                self.assertEqual(
                    f"{tr('Κανόνες του προγράμματος')}: Φυτοπροστασία",
                    page.rules_box.title(),
                )

                dialog = RuleDialog(
                    page,
                    program_name="Φυτοπροστασία",
                    default_category="plant_protection",
                )
                try:
                    self.assertIn("Φυτοπροστασία", dialog.windowTitle())
                    self.assertEqual(
                        "plant_protection",
                        dialog.category_combo.currentData(),
                    )
                finally:
                    dialog.deleteLater()
            finally:
                page.deleteLater()

    def test_apply_program_lists_only_active_programs_with_rules(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "apply-eligibility.db")
            db.execute("INSERT INTO fields(name) VALUES(?)", ("Field",))
            page = CropProgramsPage(db)
            try:
                page.store.save_program(
                    "empty",
                    "Empty",
                    [],
                    category="inspection",
                )
                rule = CropProgramRule(
                    id="rule",
                    title="Inspect",
                    category="inspection",
                    schedule_kind="fixed_date",
                    month=5,
                    day=1,
                )
                page.store.save_program(
                    "usable",
                    "Usable",
                    [rule],
                    category="inspection",
                )
                page.refresh()

                ids = {
                    str(page.assignment_program.itemData(index))
                    for index in range(page.assignment_program.count())
                }
                self.assertEqual({"usable"}, ids)
                self.assertTrue(page.generate_button.isEnabled())
            finally:
                page.deleteLater()

    def test_program_deactivation_wording_is_explicit_and_preserves_history_message(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "deactivate-wording.db")
            page = CropProgramsPage(db)
            try:
                page.store.save_program(
                    "program",
                    "Program",
                    [],
                    crop="Mastic",
                )
                page.refresh()
                page._select_program("program")
                # Verify the Greek source wording without depending on process-global\n                # language state that another UI test may have left in English.\n                self.assertEqual("Απενεργοποίηση", page.archive_button.text())

                with patch.object(
                    QMessageBox,
                    "question",
                    return_value=QMessageBox.StandardButton.No,
                ) as question:
                    page.archive_program()

                question.assert_called_once()
                args = question.call_args.args
                self.assertEqual("Απενεργοποίηση προγράμματος", args[1])
                self.assertIn("εκκρεμείς προγραμματισμένες εργασίες", args[2])
                self.assertIn("παραμένουν στο ιστορικό", args[2])
                self.assertIn("ανενεργό", args[2])
                self.assertTrue(page.store.program("program")["active"])
            finally:
                page.deleteLater()

    def test_english_pack_translates_phase12_static_and_dynamic_labels(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            manager = ProfileManager(Path(folder))
            manager.set_language(manager.active_profile.id, "en")
            db = Database(manager.active_profile.database_path)
            controller = LanguageController(self.app, manager)
            page = CropProgramsPage(db)
            try:
                controller.apply_to(page)
                title = page.findChild(QLabel, "pageTitle")
                self.assertIsNotNone(title)
                self.assertEqual("Crop Program", title.text())
                self.assertEqual("All statuses", page.task_status_filter.itemText(0))
                self.assertEqual("Irrigation", controller.translate("Άρδευση"))
                self.assertEqual("every", controller.translate("κάθε"))
            finally:
                page.deleteLater()

    def test_live_language_switch_rebuilds_only_crop_program_system_items(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            manager = ProfileManager(Path(folder))
            db = Database(manager.active_profile.database_path)
            field_id = db.execute(
                "INSERT INTO fields(name) VALUES(?)",
                ("Αγρός Χίος",),
            )
            controller = LanguageController(self.app, manager)
            install_language_controller(controller)
            page = CropProgramsPage(db)
            try:
                page.store.save_program(
                    "user-program",
                    "Πρόγραμμα δοκιμής",
                    [],
                    crop="Μαστίχα",
                )
                page.refresh()

                program_index = page.task_program_filter.findData("user-program")
                field_index = page.task_field_filter.findData(str(field_id))
                self.assertGreaterEqual(program_index, 0)
                self.assertGreaterEqual(field_index, 0)

                controller.set_language("en", persist=False)
                self.app.processEvents()
                self.assertEqual("All programs", page.task_program_filter.itemText(0))
                self.assertEqual("All fields", page.task_field_filter.itemText(0))
                self.assertEqual(
                    "Πρόγραμμα δοκιμής",
                    page.task_program_filter.itemText(
                        page.task_program_filter.findData("user-program")
                    ),
                )
                self.assertEqual(
                    "Αγρός Χίος",
                    page.task_field_filter.itemText(
                        page.task_field_filter.findData(str(field_id))
                    ),
                )

                controller.set_language("el", persist=False)
                self.app.processEvents()
                self.assertEqual("Όλα τα προγράμματα", page.task_program_filter.itemText(0))
                self.assertEqual("Όλα τα αγροτεμάχια", page.task_field_filter.itemText(0))

                controller.set_language("en", persist=False)
                self.app.processEvents()
                self.assertEqual("All programs", page.task_program_filter.itemText(0))
                self.assertEqual("All fields", page.task_field_filter.itemText(0))
                self.assertEqual(
                    "Πρόγραμμα δοκιμής",
                    page.task_program_filter.itemText(
                        page.task_program_filter.findData("user-program")
                    ),
                )
                self.assertEqual(
                    "Αγρός Χίος",
                    page.task_field_filter.itemText(
                        page.task_field_filter.findData(str(field_id))
                    ),
                )
            finally:
                page.deleteLater()

    def test_startup_integration_appends_page_without_shifting_existing_indices(self) -> None:
        # The extension contract can be tested without constructing the full
        # production MainWindow. Full-window construction here overlapped with
        # other startup tests and left native Qt objects pending for teardown on
        # Windows runners. A lightweight base keeps this test deterministic and
        # materially cheaper while dedicated tests still exercise the real page.
        from app import crop_program_integration, crop_programs, main_window

        original_window = main_window.MainWindow
        original_crop_page = crop_program_integration.CropProgramsPage
        original_module_crop_page = crop_programs.CropProgramsPage
        original_rule_dialog = crop_programs.RuleDialog

        class BaseWindow:
            def __init__(self, *args, **kwargs) -> None:
                self.db = object()
                self.pages = [
                    ("Ρυθμίσεις" if index == 31 else f"page-{index}", object())
                    for index in range(32)
                ]
                self.recording_groups = [("Καταγραφή", [])]

        class StubPage:
            def __init__(self, db: object) -> None:
                self.db = db

        try:
            main_window.MainWindow = BaseWindow
            crop_program_integration.CropProgramsPage = StubPage
            crop_program_integration.install_crop_program_ui()
            window = main_window.MainWindow()

            self.assertEqual(33, len(window.pages))
            self.assertEqual("Ρυθμίσεις", window.pages[31][0])
            self.assertEqual("Πρόγραμμα Καλλιέργειας", window.pages[32][0])
            self.assertIsInstance(window.pages[32][1], StubPage)
            self.assertIn(
                ("Πρόγραμμα Καλλιέργειας", 32),
                window.recording_groups[0][1],
            )
        finally:
            main_window.MainWindow = original_window
            crop_program_integration.CropProgramsPage = original_crop_page
            crop_programs.CropProgramsPage = original_module_crop_page
            crop_programs.RuleDialog = original_rule_dialog


if __name__ == "__main__":
    unittest.main()
