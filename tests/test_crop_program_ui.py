from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from app.crop_program import CropProgramRule
from app.crop_programs import CropProgramsPage, RuleDialog
from app.database import Database
from app.language import LanguageController
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

    def test_startup_integration_appends_page_without_shifting_existing_indices(self) -> None:
        # The extension contract can be tested without constructing the full
        # production MainWindow. Full-window construction here overlapped with
        # other startup tests and left native Qt objects pending for teardown on
        # Windows runners. A lightweight base keeps this test deterministic and
        # materially cheaper while dedicated tests still exercise the real page.
        from app import crop_program_integration, main_window

        original_window = main_window.MainWindow
        original_crop_page = crop_program_integration.CropProgramsPage

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


if __name__ == "__main__":
    unittest.main()
