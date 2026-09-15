from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.task_calendar import reminder_severity, task_state


class TaskCalendarTest(unittest.TestCase):
    def test_shared_fixture_matches_phase13_contract(self) -> None:
        fixture = json.loads(
            Path("shared/fixtures/phase13_task_calendar.json").read_text(
                encoding="utf-8"
            )
        )
        for row in fixture["tasks"]:
            self.assertEqual(
                row["state"],
                task_state(
                    row["status"],
                    row["due_date"],
                    fixture["today"],
                    horizon_days=fixture["horizon_days"],
                ),
            )
            self.assertEqual(
                row["severity"],
                reminder_severity(
                    row["status"],
                    row["due_date"],
                    fixture["today"],
                    horizon_days=fixture["horizon_days"],
                ),
            )

    def test_invalid_values_fail_instead_of_silently_moving_dates(self) -> None:
        with self.assertRaises(ValueError):
            task_state("pending", "11/09/2026", "2026-09-11")
        with self.assertRaises(ValueError):
            task_state("done", "2026-09-11", "2026-09-11")
        with self.assertRaises(ValueError):
            task_state("pending", "2026-09-11", "2026-09-11", horizon_days=-1)


if __name__ == "__main__":
    unittest.main()
