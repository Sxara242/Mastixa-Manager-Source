import tempfile
import unittest
from pathlib import Path

from app.backup_manager import BackupManager
from app.crop_program import CropProgramRule
from app.crop_program_store import CropProgramStore
from app.database import Database


class CropProgramBackupTest(unittest.TestCase):
    def test_sqlite_backup_round_trip_preserves_phase12_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = Database(root / "farm.db")
            field_id = db.execute(
                "INSERT INTO fields(name) VALUES(?)",
                ("Backup field",),
            )
            crop = CropProgramStore(db)
            rule = CropProgramRule(
                id="spring-check",
                title="Spring inspection",
                category="inspection",
                schedule_kind="fixed_date",
                month=3,
                day=15,
                notes="backup proof",
            )
            crop.save_program(
                "backup-program",
                "Backup program",
                [rule],
                crop="mastic",
                description="Phase 12C",
            )
            tasks = crop.generate_for_field("backup-program", field_id, 2026)
            self.assertEqual(1, len(tasks))
            key = str(tasks[0]["generation_key"])
            crop.set_task_status(key, "completed")

            manager = BackupManager(db.path, root / "backups")
            backup = manager.create_backup(prefix="phase12c")

            crop.archive_program("backup-program")
            db.execute("DELETE FROM crop_tasks")
            self.assertEqual([], crop.tasks())
            self.assertEqual(
                0,
                db.query_one(
                    "SELECT COUNT(*) AS n FROM crop_program_assignments"
                )["n"],
            )

            manager.restore_backup(backup)

            program = db.query_one(
                "SELECT name,crop,description,active FROM crop_programs WHERE id=?",
                ("backup-program",),
            )
            self.assertIsNotNone(program)
            self.assertEqual("Backup program", program["name"])
            self.assertEqual("mastic", program["crop"])
            self.assertEqual("Phase 12C", program["description"])
            self.assertEqual(1, program["active"])
            self.assertEqual(
                1,
                db.query_one(
                    "SELECT COUNT(*) AS n FROM crop_program_rules WHERE program_id=?",
                    ("backup-program",),
                )["n"],
            )
            self.assertEqual(
                1,
                db.query_one(
                    "SELECT COUNT(*) AS n FROM crop_program_assignments "
                    "WHERE program_id=? AND CAST(field_id AS TEXT)=? AND season_year=?",
                    ("backup-program", str(field_id), 2026),
                )["n"],
            )
            restored = crop.tasks(
                program_id="backup-program",
                field_id=field_id,
                season_year=2026,
            )
            self.assertEqual(1, len(restored))
            self.assertEqual(key, restored[0]["generation_key"])
            self.assertEqual("completed", restored[0]["status"])


if __name__ == "__main__":
    unittest.main()
