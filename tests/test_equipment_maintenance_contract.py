from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from app.database import Database
from app.equipment import EquipmentPage


class EquipmentMaintenanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tempdir.cleanup)
        self.db = Database(Path(self.tempdir.name) / "phase11a.db")
        self.page = EquipmentPage(self.db)
        self.addCleanup(self.page.close)

    def _create_equipment(self) -> int:
        self.page.name.setText("Τρακτέρ δοκιμής")
        self.page.category.setCurrentText("Τρακτέρ")
        self.page.brand_model.setText("Model A")
        self.page.code.setText("EQ-11")
        self.page.meter_type.setCurrentIndex(
            self.page.meter_type.findData("hours")
        )
        self.page.current_meter.setValue(100)
        self.page.status.setCurrentText("Ενεργό")
        self.page.save_equipment()
        row = self.db.query_one(
            "SELECT id FROM equipment WHERE equipment_code='EQ-11'"
        )
        self.assertIsNotNone(row)
        return int(row["id"])

    def _create_service(self, equipment_id: int) -> int:
        self.page.refresh()
        index = self.page.service_equipment.findData(equipment_id)
        self.assertGreaterEqual(index, 0)
        self.page.service_equipment.setCurrentIndex(index)
        self.page.service_type.setEditText("Τακτικό service")
        self.page.service_cost.setValue(75)
        self.page.service_meter.setValue(120)
        self.page.technician.setText("Service Test")
        self.page.service_notes.setText("phase11 baseline")
        self.page.next_date_enabled.setChecked(True)
        self.page.next_date.setDate(QDate.currentDate().addDays(10))
        self.page.save_service()
        row = self.db.query_one(
            "SELECT id FROM equipment_maintenance WHERE equipment_id=?",
            (equipment_id,),
        )
        self.assertIsNotNone(row)
        return int(row["id"])

    def test_equipment_service_expense_reminder_and_history_lifecycle(self) -> None:
        equipment_id = self._create_equipment()
        service_id = self._create_service(equipment_id)

        equipment = self.db.query_one(
            "SELECT * FROM equipment WHERE id=?", (equipment_id,)
        )
        self.assertEqual("hours", equipment["meter_type"])
        self.assertAlmostEqual(120.0, float(equipment["current_meter"]))

        expense = self.db.query_one(
            """
            SELECT * FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=?
            """,
            (service_id,),
        )
        self.assertIsNotNone(expense)
        expense_id = int(expense["id"])
        self.assertAlmostEqual(75.0, float(expense["amount"]))
        self.assertEqual("Service Test", expense["supplier"])

        self.page.refresh()
        self.assertEqual("1", self.page.upcoming_metric[1].text())
        self.assertEqual("0", self.page.overdue_metric[1].text())
        self.assertEqual("Επερχόμενη", self.page.service_table.item(0, 7).text())

        # Editing the service updates the same financial projection and does not
        # allow an older/lower service value to reduce the equipment high-water mark.
        self.page.load_service(0, 0)
        self.page.service_cost.setValue(90)
        self.page.service_meter.setValue(110)
        self.page.technician.setText("Service Edited")
        self.page.save_service()

        expense = self.db.query_one(
            """
            SELECT * FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=?
            """,
            (service_id,),
        )
        self.assertEqual(expense_id, int(expense["id"]))
        self.assertAlmostEqual(90.0, float(expense["amount"]))
        self.assertEqual("Service Edited", expense["supplier"])
        count = self.db.query_one(
            """
            SELECT COUNT(*) AS total FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=?
            """,
            (service_id,),
        )
        self.assertEqual(1, int(count["total"]))
        self.assertAlmostEqual(
            120.0,
            float(
                self.db.query_one(
                    "SELECT current_meter FROM equipment WHERE id=?",
                    (equipment_id,),
                )["current_meter"]
            ),
        )

        # Equipment history is protected while maintenance exists.
        self.page.refresh()
        self.page.load_equipment(0, 0)
        with patch("app.equipment.QMessageBox.warning") as warning:
            self.page.delete_equipment()
        warning.assert_called_once()
        self.assertIsNotNone(
            self.db.query_one("SELECT id FROM equipment WHERE id=?", (equipment_id,))
        )

        # Removing the source service removes its one linked expense.
        self.page.refresh()
        self.page.load_service(0, 0)
        with patch.object(self.page, "confirm_delete", return_value=True):
            self.page.delete_service()
        self.assertIsNone(
            self.db.query_one(
                "SELECT id FROM equipment_maintenance WHERE id=?", (service_id,)
            )
        )
        self.assertIsNone(
            self.db.query_one(
                """
                SELECT id FROM expenses
                WHERE source_type='equipment_maintenance' AND source_id=?
                """,
                (service_id,),
            )
        )

        # With history removed the equipment can be deleted normally.
        self.page.refresh()
        self.page.load_equipment(0, 0)
        with patch.object(self.page, "confirm_delete", return_value=True):
            self.page.delete_equipment()
        self.assertIsNone(
            self.db.query_one("SELECT id FROM equipment WHERE id=?", (equipment_id,))
        )


if __name__ == "__main__":
    unittest.main()
