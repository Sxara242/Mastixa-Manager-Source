import sqlite3
import unittest
import uuid

from app.activity_identity import (
    lookup_sync_ref,
    migrate,
    register_field,
    register_source,
)
from app.activity_projection import project_field_activities


class ActivityIdentityRegistryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(
            """
            CREATE TABLE fields(id INTEGER PRIMARY KEY);
            CREATE TABLE production(
                id INTEGER PRIMARY KEY,
                field_id INTEGER,
                entry_date TEXT
            );
            INSERT INTO fields VALUES(1),(2);
            INSERT INTO production VALUES(10,1,'2026-09-11');
            INSERT INTO production VALUES(20,2,'2026-09-10');
            """
        )
        self.scope = "profile-a"
        self.dataset = str(uuid.uuid4())
        self.field1 = str(uuid.uuid4())
        self.field2 = str(uuid.uuid4())
        self.source1 = str(uuid.uuid4())

    def test_verified_mapping_enriches_projection_without_changing_local_identity(self):
        register_field(self.db, self.scope, self.dataset, 1, self.field1, updated_at=1)
        register_source(
            self.db,
            self.scope,
            self.dataset,
            "production",
            10,
            1,
            self.source1,
            updated_at=2,
        )
        items = project_field_activities(self.db, self.scope, 1, self.dataset)
        self.assertEqual(1, len(items))
        self.assertEqual({"type": "production", "id": "10"}, items[0]["source_ref"])
        self.assertEqual("1", items[0]["field_id"])
        self.assertEqual(
            {
                "dataset_id": self.dataset,
                "source_uuid": self.source1,
                "field_uuid": self.field1,
            },
            items[0]["sync_ref"],
        )

    def test_missing_or_wrong_scope_and_dataset_never_claim_identity(self):
        register_field(self.db, self.scope, self.dataset, 1, self.field1)
        register_source(self.db, self.scope, self.dataset, "production", 10, 1, self.source1)
        other_dataset = str(uuid.uuid4())
        self.assertIsNone(
            lookup_sync_ref(self.db, "profile-b", self.dataset, "production", 10, 1)
        )
        self.assertIsNone(
            lookup_sync_ref(self.db, self.scope, other_dataset, "production", 10, 1)
        )
        self.assertNotIn(
            "sync_ref", project_field_activities(self.db, self.scope, 1, other_dataset)[0]
        )

    def test_conflicting_field_and_source_aliases_are_rejected_without_overwrite(self):
        register_field(self.db, self.scope, self.dataset, 1, self.field1, updated_at=1)
        with self.assertRaises(ValueError):
            register_field(self.db, self.scope, self.dataset, 1, self.field2, updated_at=2)
        register_field(self.db, self.scope, self.dataset, 2, self.field2, updated_at=2)
        with self.assertRaises(ValueError):
            register_field(self.db, self.scope, self.dataset, 2, self.field1, updated_at=3)

        register_source(self.db, self.scope, self.dataset, "production", 10, 1, self.source1)
        with self.assertRaises(ValueError):
            register_source(
                self.db,
                self.scope,
                self.dataset,
                "production",
                20,
                2,
                self.source1,
            )
        ref = lookup_sync_ref(self.db, self.scope, self.dataset, "production", 10, 1)
        self.assertEqual(self.source1, ref["source_uuid"])
        self.assertEqual(self.field1, ref["field_uuid"])

    def test_reassignment_requires_verified_target_field_and_preserves_source_uuid(self):
        register_field(self.db, self.scope, self.dataset, 1, self.field1)
        register_source(self.db, self.scope, self.dataset, "production", 10, 1, self.source1)
        with self.assertRaises(ValueError):
            register_source(self.db, self.scope, self.dataset, "production", 10, 2, self.source1)
        register_field(self.db, self.scope, self.dataset, 2, self.field2)
        register_source(self.db, self.scope, self.dataset, "production", 10, 2, self.source1)
        self.assertIsNone(
            lookup_sync_ref(self.db, self.scope, self.dataset, "production", 10, 1)
        )
        self.assertEqual(
            self.field2,
            lookup_sync_ref(self.db, self.scope, self.dataset, "production", 10, 2)[
                "field_uuid"
            ],
        )

    def test_validation_rejects_fabricated_or_noncanonical_identity(self):
        migrate(self.db)
        with self.assertRaises(ValueError):
            register_field(self.db, self.scope, "not-a-uuid", 1, self.field1)
        with self.assertRaises(ValueError):
            register_field(self.db, self.scope, self.dataset.upper(), 1, self.field1)
        register_field(self.db, self.scope, self.dataset, 1, self.field1)
        with self.assertRaises(ValueError):
            register_source(self.db, self.scope, self.dataset, "unknown", 10, 1, self.source1)
        with self.assertRaises(ValueError):
            register_source(self.db, self.scope, self.dataset, "production", 10, 1, "10")


if __name__ == "__main__":
    unittest.main()
