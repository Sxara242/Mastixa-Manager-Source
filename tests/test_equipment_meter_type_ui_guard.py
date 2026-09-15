from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.database import Database
from app.equipment import EquipmentPage


class EquipmentMeterTypeUiGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tempdir.cleanup)
        self.db = Database(Path(self.tempdir.name) / "phase11c.db")
        self.page = EquipmentPage(self.db)
        self.addCleanup(self.page.close)

        self.page.name.setText("Τρακτέρ UI")
        self.page.category.setCurrentText("Τρακτέρ")
        self.page.code.setText("EQ-11C")
        self.page.current_meter.setValue(100)
        self.page.save_equipment()
        row = self.db.query_one(
            "SELECT id FROM equipment WHERE equipment_code='EQ-11C'"
        )
        self.assertIsNotNone(row)
        self.equipment_id = int(row["id"])

    def _load_equipment(self) -> None:
        self.page.refresh()
        self.assertEqual(1, self.page.equipment_table.rowCount())
        self.page.load_equipment(0, 0)
        self.assertEqual(self.equipment_id, self.page.selected_equipment_id)

    def test_meter_type_change_without_history_is_allowed(self) -> None:
        self._load_equipment()
        index = self.page.meter_type.findData("km")
        self.assertGreaterEqual(index, 0)
        self.page.meter_type.setCurrentIndex(index)
        self.page.save_equipment()

        row = self.db.query_one(
            "SELECT meter_type FROM equipment WHERE id=?", (self.equipment_id,)
        )
        self.assertEqual("km", row["meter_type"])

    def test_meter_type_change_with_history_warns_and_keeps_original(self) -> None:
        self.db.execute(
            """
            INSERT INTO equipment_maintenance(
                equipment_id,service_date,service_type,cost,meter_value,
                technician,notes
            ) VALUES(?, '2026-09-11', 'Τακτικό service', 0, 120, '', '')
            """,
            (self.equipment_id,),
        )
        self._load_equipment()

        index = self.page.meter_type.findData("km")
        self.assertGreaterEqual(index, 0)
        self.page.meter_type.setCurrentIndex(index)
        self.page.name.setText("Δεν πρέπει να αποθηκευτεί")

        with patch("app.equipment.QMessageBox.warning") as warning:
            self.page.save_equipment()

        warning.assert_called_once_with(
            self.page,
            "Αλλαγή μετρητή",
            "Η μονάδα μετρητή δεν αλλάζει όταν υπάρχει ιστορικό service.",
        )
        row = self.db.query_one(
            "SELECT name,meter_type FROM equipment WHERE id=?", (self.equipment_id,)
        )
        self.assertEqual("Τρακτέρ UI", row["name"])
        self.assertEqual("hours", row["meter_type"])
        self.assertEqual(self.equipment_id, self.page.selected_equipment_id)


if __name__ == "__main__":
    unittest.main()
