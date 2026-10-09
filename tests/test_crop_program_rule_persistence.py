from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from app import crop_programs as crop_programs_module
from app.crop_program import CropProgramRule
from app.crop_program_store import CropProgramStore
from app.crop_programs import CropProgramsPage
from app.database import Database


class CropProgramImmediateRulePersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_store_save_rules_preserves_program_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "store.db")
            store = CropProgramStore(db)
            original = CropProgramRule(
                id="rule-1",
                title="Original",
                category="inspection",
                schedule_kind="fixed_date",
                month=3,
                day=10,
            )
            store.save_program(
                "program-1",
                "Saved name",
                [original],
                crop="Mastic",
                description="Saved description",
            )

            edited = replace(original, title="Edited")
            store.save_rules("program-1", [edited])

            program = store.program("program-1")
            self.assertEqual("Saved name", program["name"])
            self.assertEqual("Mastic", program["crop"])
            self.assertEqual("Saved description", program["description"])
            self.assertEqual(["Edited"], [rule.title for rule in program["rules"]])

    def test_rule_add_edit_remove_are_immediately_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "ui.db")
            page = CropProgramsPage(db)
            original_dialog = crop_programs_module.RuleDialog
            try:
                page.new_program()
                self.assertFalse(page.add_rule_button.isEnabled())

                page.name_edit.setText("Immediate rules")
                page.crop_edit.setText("Mastic")
                page.save_program()
                program_id = page.selected_program_id
                self.assertIsNotNone(program_id)
                self.assertTrue(page.add_rule_button.isEnabled())

                first = CropProgramRule(
                    id="rule-1",
                    title="First",
                    category="inspection",
                    schedule_kind="fixed_date",
                    month=3,
                    day=10,
                )
                edited = replace(first, title="Edited")

                values = iter((first, edited))

                class AcceptedDialog:
                    def __init__(self, parent=None, rule=None, **_kwargs):
                        self._value = next(values)

                    def exec(self):
                        return QDialog.DialogCode.Accepted

                    def rule(self):
                        return self._value

                crop_programs_module.RuleDialog = AcceptedDialog

                page.add_rule()
                stored = page.store.program(program_id)
                self.assertEqual(["First"], [rule.title for rule in stored["rules"]])
                self.assertIn("(1)", page.program_list.currentItem().text())

                page.rules_table.selectRow(0)
                page.edit_rule()
                stored = page.store.program(program_id)
                self.assertEqual(["Edited"], [rule.title for rule in stored["rules"]])
                self.assertIn("(1)", page.program_list.currentItem().text())

                page.rules_table.selectRow(0)
                page.remove_rule()
                stored = page.store.program(program_id)
                self.assertEqual([], stored["rules"])
                self.assertIn("(0)", page.program_list.currentItem().text())
            finally:
                crop_programs_module.RuleDialog = original_dialog
                page.deleteLater()


if __name__ == "__main__":
    unittest.main()
