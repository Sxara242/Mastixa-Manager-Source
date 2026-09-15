import json
import sqlite3
import unittest
from pathlib import Path

from app.activity_identity import register_field, register_source
from app.activity_projection import project_field_activities


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "phase9f_activity_identity.json"
ANDROID_FIXTURE = (
    ROOT
    / "android"
    / "app"
    / "src"
    / "androidTest"
    / "assets"
    / "phase9f_activity_identity.json"
)


class ActivityIdentityCrossClientTests(unittest.TestCase):
    def test_shared_fixture_is_identical_and_projects_same_portable_identity(self):
        expected_text = FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(expected_text, ANDROID_FIXTURE.read_text(encoding="utf-8"))
        fixture = json.loads(expected_text)

        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(
            """
            CREATE TABLE fields(id INTEGER PRIMARY KEY);
            CREATE TABLE production(id INTEGER PRIMARY KEY, field_id INTEGER, entry_date TEXT);
            INSERT INTO fields VALUES(1);
            INSERT INTO production VALUES(10,1,'2026-09-11');
            """
        )

        register_field(
            db,
            fixture["scope_id"],
            fixture["dataset_id"],
            fixture["windows"]["local_field_id"],
            fixture["field_uuid"],
            updated_at=1,
        )
        register_source(
            db,
            fixture["scope_id"],
            fixture["dataset_id"],
            fixture["source_type"],
            fixture["windows"]["local_source_id"],
            fixture["windows"]["local_field_id"],
            fixture["source_uuid"],
            updated_at=2,
        )

        events = project_field_activities(
            db,
            fixture["scope_id"],
            int(fixture["windows"]["local_field_id"]),
            fixture["dataset_id"],
        )
        self.assertEqual(1, len(events))
        self.assertEqual(fixture["expected_sync_ref"], events[0]["sync_ref"])
        self.assertEqual(fixture["event_date"], events[0]["event_date"])
        self.assertEqual(
            {"type": fixture["source_type"], "id": fixture["windows"]["local_source_id"]},
            events[0]["source_ref"],
        )

        unrelated = project_field_activities(
            db,
            "profile-b",
            int(fixture["windows"]["local_field_id"]),
            fixture["dataset_id"],
        )
        self.assertNotIn("sync_ref", unrelated[0])


if __name__ == "__main__":
    unittest.main()
