import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.crop_program import CropProgramRule
from app.crop_program_store import CropProgramStore, migrate_crop_programs
from app.database import Database


FIXTURE = Path(__file__).resolve().parents[1] / "shared" / "fixtures" / "phase12_crop_program.json"


class CropProgramStoreTest(unittest.TestCase):
    def fixture_rules(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        return data, [CropProgramRule.from_mapping(row) for row in data["rules"]]

    def make_db(self, root: Path, name: str = "farm.db"):
        db = Database(root / name)
        field_id = db.execute("INSERT INTO fields(name) VALUES(?)", ("Phase 12 field",))
        return db, field_id

    def test_additive_migration_rolls_back_with_caller_transaction(self):
        con = sqlite3.connect(":memory:")
        try:
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("BEGIN")
            migrate_crop_programs(con)
            self.assertIsNotNone(
                con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crop_tasks'"
                ).fetchone()
            )
            con.rollback()
            self.assertIsNone(
                con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='crop_tasks'"
                ).fetchone()
            )
        finally:
            con.close()

    def test_program_read_api_preserves_rule_order_and_active_filter(self):
        with tempfile.TemporaryDirectory() as folder:
            db, _field_id = self.make_db(Path(folder))
            data, rules = self.fixture_rules()
            store = CropProgramStore(db)
            store.save_program(
                data["program_id"],
                "Fixture program",
                rules,
                crop="mastic",
                description="Phase 12 UI fixture",
            )

            programs = store.programs()
            self.assertEqual(1, len(programs))
            self.assertEqual(data["program_id"], programs[0]["id"])
            self.assertEqual(len(rules), programs[0]["rule_count"])
            self.assertTrue(programs[0]["active"])

            detail = store.program(data["program_id"])
            self.assertEqual("Fixture program", detail["name"])
            self.assertEqual("mastic", detail["crop"])
            self.assertEqual("Phase 12 UI fixture", detail["description"])
            self.assertEqual(
                [rule.id for rule in rules], [rule.id for rule in detail["rules"]]
            )

            store.archive_program(data["program_id"])
            self.assertEqual([], store.programs(active_only=True))
            archived = store.programs()
            self.assertEqual(1, len(archived))
            self.assertFalse(archived[0]["active"])
            with self.assertRaisesRegex(ValueError, "does not exist"):
                store.program("missing-program")

    def test_regeneration_preserves_decisions_and_archive_preserves_history(self):
        with tempfile.TemporaryDirectory() as folder:
            db, field_id = self.make_db(Path(folder))
            data, rules = self.fixture_rules()
            store = CropProgramStore(db)
            store.save_program(data["program_id"], "Fixture program", rules, crop="mastic")

            first = store.generate_for_field(data["program_id"], field_id, 2026)
            self.assertEqual(8, len(first))
            prune_key = next(
                row["generation_key"]
                for row in first
                if row["rule_id"] == "prune-winter"
            )
            irrigation_key = next(
                row["generation_key"]
                for row in first
                if row["rule_id"] == "irrigate-window"
            )
            store.set_task_status(prune_key, "completed")
            store.set_task_status(irrigation_key, "skipped")

            edited = []
            for rule in rules:
                if rule.id == "winter-inspection":
                    continue
                if rule.id == "irrigate-window":
                    rule = replace(rule, title="Irrigation revised")
                edited.append(rule)
            store.save_program(
                data["program_id"], "Fixture program", edited, crop="mastic"
            )
            regenerated = store.generate_for_field(data["program_id"], field_id, 2026)

            self.assertEqual(5, len(regenerated))
            by_key = {row["generation_key"]: row for row in regenerated}
            self.assertEqual("completed", by_key[prune_key]["status"])
            self.assertEqual("skipped", by_key[irrigation_key]["status"])
            self.assertFalse(
                any(row["rule_id"] == "winter-inspection" for row in regenerated)
            )
            self.assertTrue(
                all(
                    row["title"] == "Irrigation revised"
                    for row in regenerated
                    if row["rule_id"] == "irrigate-window"
                    and row["status"] == "pending"
                )
            )

            store.archive_program(data["program_id"])
            history = store.tasks(
                program_id=data["program_id"],
                field_id=field_id,
                season_year=2026,
            )
            self.assertEqual({"completed", "skipped"}, {row["status"] for row in history})
            self.assertEqual(2, len(history))
            with self.assertRaisesRegex(ValueError, "archived"):
                store.generate_for_field(data["program_id"], field_id, 2026)

    def test_failed_generation_is_atomic_and_profiles_are_isolated(self):
        leap_rule = CropProgramRule(
            id="leap-check",
            title="Leap check",
            category="inspection",
            schedule_kind="fixed_date",
            month=2,
            day=29,
        )
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db_a, field_a = self.make_db(root, "a.db")
            db_b, field_b = self.make_db(root, "b.db")
            store_a = CropProgramStore(db_a)
            store_b = CropProgramStore(db_b)

            store_a.save_program("leap-program", "Leap", [leap_rule])
            before = store_a.generate_for_field("leap-program", field_a, 2028)
            self.assertEqual(1, len(before))
            with self.assertRaises(ValueError):
                store_a.generate_for_field("leap-program", field_a, 2027)
            self.assertEqual(
                before,
                store_a.tasks(
                    program_id="leap-program", field_id=field_a, season_year=2028
                ),
            )
            self.assertEqual(
                [],
                store_a.tasks(
                    program_id="leap-program", field_id=field_a, season_year=2027
                ),
            )

            self.assertEqual([], store_b.tasks())
            with self.assertRaisesRegex(ValueError, "does not exist"):
                store_b.generate_for_field("leap-program", field_b, 2028)


if __name__ == "__main__":
    unittest.main()
