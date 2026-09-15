from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.backup_manager import BackupManager
from app.database import Database
from app.plant_tracking import PlantEvent, PlantRecord
from app.plant_tracking_store import PlantTrackingStore


class PlantTrackingStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.db = Database(root / "farm.db")
        self.backups = root / "backups"
        self.field_a = self.db.execute(
            "INSERT INTO fields(name,area_stremma) VALUES(?,?)",
            ("Α", 2.0),
        )
        self.field_b = self.db.execute(
            "INSERT INTO fields(name,area_stremma) VALUES(?,?)",
            ("Β", 3.0),
        )
        self.db.execute(
            """
            CREATE TABLE planting_batches(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planting_date TEXT NOT NULL,
                field_id INTEGER NOT NULL,
                trees_planted INTEGER NOT NULL,
                trees_alive INTEGER NOT NULL,
                material_type TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                variety TEXT NOT NULL DEFAULT '',
                spacing TEXT NOT NULL DEFAULT '',
                cost REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.batch_a = self.db.execute(
            """
            INSERT INTO planting_batches(planting_date,field_id,trees_planted,trees_alive)
            VALUES(?,?,?,?)
            """,
            ("2026-03-01", self.field_a, 70, 68),
        )
        self.batch_b = self.db.execute(
            """
            INSERT INTO planting_batches(planting_date,field_id,trees_planted,trees_alive)
            VALUES(?,?,?,?)
            """,
            ("2026-03-02", self.field_b, 20, 20),
        )
        self.store = PlantTrackingStore(self.db)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def plant(self, plant_id: str = "plant-1") -> PlantRecord:
        return PlantRecord(
            id=plant_id,
            field_id=str(self.field_a),
            planting_batch_id=str(self.batch_a),
            label="A-001",
            planted_date="2026-03-01",
            variety="Mastic",
            latitude=38.25,
            longitude=26.02,
            status="active",
            health="good",
            notes="baseline",
        )

    def test_persistence_history_soft_delete_and_batch_count_are_independent(self) -> None:
        self.store.save_plant(self.plant())
        self.store.append_event(
            PlantEvent("event-2", "plant-1", "2026-04-10", "status", "dead", "")
        )
        self.store.append_event(
            PlantEvent("event-1", "plant-1", "2026-04-01", "health", "watch", "")
        )

        snapshot = self.store.snapshot("plant-1")
        self.assertEqual("dead", snapshot["status"])
        self.assertEqual("watch", snapshot["health"])
        self.assertEqual("2026-04-10", snapshot["last_event_date"])
        self.assertEqual(2, snapshot["event_count"])
        self.assertEqual(
            ["event-1", "event-2"],
            [event.id for event in self.store.events("plant-1")],
        )

        aggregate = self.db.query_one(
            "SELECT trees_planted,trees_alive FROM planting_batches WHERE id=?",
            (self.batch_a,),
        )
        self.assertEqual((70, 68), (aggregate["trees_planted"], aggregate["trees_alive"]))

        self.store.delete_plant("plant-1")
        self.assertEqual([], self.store.plants())
        self.assertEqual(2, len(self.store.events("plant-1")))
        self.store.restore_plant("plant-1")
        self.assertEqual("dead", self.store.snapshot("plant-1")["status"])

    def test_field_and_batch_relationships_are_enforced(self) -> None:
        bad = PlantRecord(
            id="bad",
            field_id=str(self.field_a),
            planting_batch_id=str(self.batch_b),
        )
        with self.assertRaises(ValueError):
            self.store.save_plant(bad)
        with self.assertRaises(ValueError):
            self.store.save_plant(PlantRecord(id="missing", field_id="999999"))

    def test_events_are_immutable_and_metadata_edits_cannot_invalidate_history(self) -> None:
        self.store.save_plant(self.plant())
        event = PlantEvent("event-1", "plant-1", "2026-03-10", "note", "checked", "")
        self.store.append_event(event)
        with self.assertRaises(ValueError):
            self.store.append_event(event)

        moved_date = PlantRecord(
            **{**self.plant().__dict__, "planted_date": "2026-03-20"}
        )
        with self.assertRaises(ValueError):
            self.store.save_plant(moved_date)

    def test_windows_sqlite_backup_restore_includes_plant_registry_and_events(self) -> None:
        self.store.save_plant(self.plant())
        self.store.append_event(
            PlantEvent("event-1", "plant-1", "2026-03-12", "health", "poor", "")
        )
        manager = BackupManager(self.db.path, self.backups)
        backup = manager.create_backup("phase14")

        self.store.save_plant(self.plant("plant-newer"))
        self.assertEqual(2, len(self.store.plants()))
        manager.restore_backup(backup)

        restored = PlantTrackingStore(self.db)
        self.assertEqual(["plant-1"], [plant.id for plant in restored.plants()])
        self.assertEqual("poor", restored.snapshot("plant-1")["health"])
        self.assertEqual(1, len(restored.events("plant-1")))


if __name__ == "__main__":
    unittest.main()
