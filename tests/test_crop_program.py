import json
import unittest
from pathlib import Path

from app.crop_program import CropProgramRule, generate_crop_tasks


FIXTURE = Path(__file__).resolve().parents[1] / "shared" / "fixtures" / "phase12_crop_program.json"


class CropProgramTest(unittest.TestCase):
    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_shared_fixture_generation(self):
        fixture = self.load_fixture()
        rules = [CropProgramRule.from_mapping(row) for row in fixture["rules"]]
        tasks = generate_crop_tasks(
            fixture["program_id"],
            fixture["field_id"],
            fixture["season_year"],
            rules,
        )
        actual = [
            {
                "rule_id": task["rule_id"],
                "due_date": task["due_date"],
                "generation_key": task["generation_key"],
            }
            for task in tasks
        ]
        self.assertEqual(fixture["expected"], actual)
        self.assertTrue(all(task["status"] == "pending" for task in tasks))
        self.assertEqual(
            sorted(actual, key=lambda row: (row["due_date"], row["rule_id"])),
            actual,
        )

    def test_duplicate_rule_ids_are_rejected(self):
        rule = CropProgramRule(
            id="same",
            title="Check",
            category="inspection",
            schedule_kind="fixed_date",
            month=3,
            day=1,
        )
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            generate_crop_tasks("program", "field", 2026, [rule, rule])

    def test_invalid_date_and_interval_are_rejected(self):
        invalid_date = CropProgramRule(
            id="bad-date",
            title="Bad date",
            category="inspection",
            schedule_kind="fixed_date",
            month=2,
            day=30,
        )
        with self.assertRaises(ValueError):
            generate_crop_tasks("program", "field", 2026, [invalid_date])

        invalid_interval = CropProgramRule(
            id="bad-step",
            title="Bad interval",
            category="irrigation",
            schedule_kind="interval_window",
            start_month=5,
            start_day=1,
            end_month=5,
            end_day=31,
            every_days=0,
        )
        with self.assertRaisesRegex(ValueError, "positive"):
            generate_crop_tasks("program", "field", 2026, [invalid_interval])

    def test_generator_has_no_database_side_effect_contract(self):
        fixture = self.load_fixture()
        rules = tuple(CropProgramRule.from_mapping(row) for row in fixture["rules"])
        first = generate_crop_tasks("program", "42", 2026, rules)
        second = generate_crop_tasks("program", 42, 2026, rules)
        self.assertEqual(first, second)
        self.assertEqual(len({row["generation_key"] for row in first}), len(first))


if __name__ == "__main__":
    unittest.main()
