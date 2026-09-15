import sqlite3
import unittest

from app.activity_projection import project_field_activities


DATASET = "11111111-1111-4111-8111-111111111111"
PARCEL = "22222222-2222-4222-8222-222222222222"
POINT = "33333333-3333-4333-8333-333333333333"


class Phase9FIdentityMappingTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript("""
            CREATE TABLE fields(id INTEGER PRIMARY KEY);
            CREATE TABLE production(id INTEGER PRIMARY KEY, field_id INTEGER, entry_date TEXT);
            CREATE TABLE parcel_geometry(
                id TEXT PRIMARY KEY, field_id INTEGER, deleted_at INTEGER
            );
            CREATE TABLE geo_points(
                id TEXT PRIMARY KEY, parcel_id TEXT, created_at INTEGER,
                deleted_at INTEGER, point_type TEXT
            );
            CREATE TABLE gis_sync_state(
                dataset TEXT NOT NULL, id TEXT NOT NULL, local_hash TEXT NOT NULL,
                remote_version INTEGER NOT NULL, PRIMARY KEY(dataset,id)
            );
            INSERT INTO fields VALUES(1);
            INSERT INTO production VALUES(9,1,'2026-09-10');
        """)
        self.db.execute(
            "INSERT INTO parcel_geometry VALUES(?,?,NULL)", (PARCEL, 1)
        )
        self.db.execute(
            "INSERT INTO geo_points VALUES(?,?,?,NULL,'note')",
            (POINT, PARCEL, 1789094400000),
        )
        self.db.commit()

    def observation(self, dataset=None):
        items = project_field_activities(self.db, "profile-a", 1, dataset)
        return next(i for i in items if i["kind"] == "observation")

    def test_sync_ref_requires_acknowledged_source_and_field_in_same_dataset(self):
        self.db.executemany(
            "INSERT INTO gis_sync_state VALUES(?,?,?,1)",
            [(DATASET, PARCEL, "a"), (DATASET, POINT, "b")],
        )
        event = self.observation(DATASET)
        self.assertEqual({
            "dataset_id": DATASET,
            "source_uuid": POINT,
            "field_uuid": PARCEL,
        }, event["sync_ref"])

    def test_missing_dataset_or_partial_mapping_omits_sync_ref(self):
        self.assertNotIn("sync_ref", self.observation())
        self.db.execute(
            "INSERT INTO gis_sync_state VALUES(?,?,?,1)", (DATASET, POINT, "b")
        )
        self.assertNotIn("sync_ref", self.observation(DATASET))

    def test_business_integer_identity_is_never_promoted(self):
        self.db.executemany(
            "INSERT INTO gis_sync_state VALUES(?,?,?,1)",
            [(DATASET, PARCEL, "a"), (DATASET, POINT, "b")],
        )
        production = next(
            i for i in project_field_activities(self.db, "profile-a", 1, DATASET)
            if i["kind"] == "harvest"
        )
        self.assertNotIn("sync_ref", production)

    def test_invalid_dataset_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            project_field_activities(self.db, "profile-a", 1, "not-a-uuid")


if __name__ == "__main__":
    unittest.main()
