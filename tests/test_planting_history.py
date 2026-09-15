from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.planting_history import PlantingHistoryStore


FIXTURE = Path(__file__).resolve().parents[1] / "shared" / "fixtures" / "phase14_planting_history.json"


class PlantingHistoryStoreTest(unittest.TestCase):
    @staticmethod
    def _batch(db: Database, *, planted: int, alive: int, planting_date: str = "2026-03-01") -> int:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS planting_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planting_date TEXT NOT NULL,
                field_id INTEGER NOT NULL,
                trees_planted INTEGER NOT NULL DEFAULT 0,
                trees_alive INTEGER NOT NULL DEFAULT 0,
                material_type TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                variety TEXT NOT NULL DEFAULT '',
                spacing TEXT NOT NULL DEFAULT '',
                cost REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE RESTRICT
            )
            """
        )
        field_id = db.execute("INSERT INTO fields(name) VALUES(?)", ("History field",))
        return db.execute(
            """
            INSERT INTO planting_batches(
                planting_date,field_id,trees_planted,trees_alive
            ) VALUES(?,?,?,?)
            """,
            (planting_date, field_id, planted, alive),
        )

    def test_shared_fixture_preserves_positions_and_counts_historical_plantings(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        batch = fixture["planting_batch"]
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "history.db")
            batch_id = self._batch(
                db,
                planted=batch["initial_positions"],
                alive=batch["current_alive"],
                planting_date=batch["planting_date"],
            )
            history = PlantingHistoryStore(db)
            for row in fixture["replantings"]:
                history.add_replanting(
                    str(batch_id),
                    row["replanting_date"],
                    row["tree_count"],
                    row["notes"],
                    event_id=row["id"],
                )

            totals = history.totals(str(batch_id))
            expected = fixture["expected"]
            self.assertEqual(expected["positions"], totals.positions)
            self.assertEqual(expected["replantings"], totals.replantings)
            self.assertEqual(expected["historical_plantings"], totals.historical_plantings)
            self.assertEqual(expected["living"], totals.living)
            self.assertEqual(expected["historical_losses"], totals.historical_losses)
            self.assertEqual(expected["vacant_positions"], totals.vacant_positions)
            self.assertEqual(
                ["replacement-01", "replacement-02"],
                [row.id for row in history.replantings(str(batch_id))],
            )

    def test_losses_without_replanting_are_distinct_from_vacant_positions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "losses.db")
            batch_id = self._batch(db, planted=500, alive=472)
            totals = PlantingHistoryStore(db).totals(str(batch_id))
            self.assertEqual(500, totals.historical_plantings)
            self.assertEqual(28, totals.historical_losses)
            self.assertEqual(28, totals.vacant_positions)

    def test_events_are_append_only_and_cannot_predate_batch(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "validation.db")
            batch_id = self._batch(db, planted=20, alive=20)
            history = PlantingHistoryStore(db)
            history.add_replanting(
                str(batch_id), "2026-03-10", 2, event_id="same-id"
            )
            with self.assertRaisesRegex(ValueError, "already exists"):
                history.add_replanting(
                    str(batch_id), "2026-03-11", 1, event_id="same-id"
                )
            with self.assertRaisesRegex(ValueError, "predate"):
                history.add_replanting(str(batch_id), "2026-02-28", 1)
            with self.assertRaisesRegex(ValueError, "positive integer"):
                history.add_replanting(str(batch_id), "2026-03-12", 0)
            self.assertEqual(1, len(history.replantings(str(batch_id))))

    def test_replanting_table_is_part_of_full_sqlite_backup(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = Database(root / "source.db")
            batch_id = self._batch(db, planted=50, alive=50)
            history = PlantingHistoryStore(db)
            history.add_replanting(
                str(batch_id), "2026-04-01", 3, event_id="backup-event"
            )
            backup_path = root / "backup.db"
            with db.connect() as source, closing(sqlite3.connect(backup_path)) as target:
                source.backup(target)
            restored = Database(backup_path)
            restored_history = PlantingHistoryStore(restored)
            self.assertEqual(3, restored_history.totals(str(batch_id)).replantings)
            self.assertEqual("backup-event", restored_history.replantings(str(batch_id))[0].id)


if __name__ == "__main__":
    unittest.main()
