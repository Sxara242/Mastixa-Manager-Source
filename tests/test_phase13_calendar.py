from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.crop_program_store import CropProgramStore
from app.database import Database
from app.phase13_calendar_integration import GREEK_MONTHS, Phase13FarmCalendarPage


class Phase13CalendarUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_greek_month_filter_and_generated_tasks_join_calendar(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "calendar.db")
            field_id = db.execute(
                "INSERT INTO fields(name) VALUES(?)", ("Χωράφι δοκιμής",)
            )
            CropProgramStore(db)
            due = (date.today() - timedelta(days=1)).isoformat()
            now = 1
            with db.connect() as con:
                con.execute(
                    """
                    INSERT INTO crop_tasks(
                        generation_key,program_id,rule_id,field_id,season_year,
                        due_date,category,title,notes,status,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "program:field:rule:" + due,
                        "program",
                        "rule",
                        str(field_id),
                        date.today().year,
                        due,
                        "inspection",
                        "Έλεγχος χωραφιού",
                        "δοκιμή",
                        "pending",
                        now,
                        now,
                    ),
                )

            page = Phase13FarmCalendarPage(db)
            try:
                self.assertEqual("Όλοι οι μήνες", page.month.itemText(0))
                self.assertEqual(list(GREEK_MONTHS), [
                    page.month.itemText(index) for index in range(1, 13)
                ])
                self.assertNotIn("September", [
                    page.month.itemText(index) for index in range(page.month.count())
                ])
                self.assertGreaterEqual(
                    page.section.findData("Πρόγραμμα Καλλιέργειας"), 0
                )
                planned = [
                    row for row in page._rows
                    if row["section"] == "Πρόγραμμα Καλλιέργειας"
                ]
                self.assertEqual(1, len(planned))
                self.assertIn("Εκπρόθεσμη", planned[0]["description"])
                self.assertEqual("Χωράφι δοκιμής", planned[0]["field_name"])
            finally:
                page.deleteLater()


if __name__ == "__main__":
    unittest.main()
