from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.backup_manager import BackupError, BackupManager
from app.database import Database


class Phase16DBackupRestoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp_dir.name)
        self.live_path = self.root / "live.db"
        self.backup_dir = self.root / "backups"
        self.db = Database(self.live_path)
        self.manager = BackupManager(
            self.live_path,
            self.backup_dir,
            auto_keep=3,
            pre_restore_keep=3,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_live_data(self) -> int:
        self.db.execute(
            "UPDATE producer SET name=?,notes=? WHERE id=1",
            ("Παραγωγός Χίου", "phase 16D"),
        )
        field_id = self.db.execute(
            """INSERT INTO fields(
                   name,kaek,location,area_stremma,productive_trees,notes
               ) VALUES(?,?,?,?,?,?)""",
            ("Πυργί Α", "050123456789/0/0", "Χίος", 7.5, 42, "backup proof"),
        )
        self.db.execute(
            """INSERT INTO production(
                   entry_date,field_id,product,quantity_kg,notes
               ) VALUES(?,?,?,?,?)""",
            ("2026-09-01", field_id, "Μαστίχα", 12.75, "παραγωγή"),
        )
        self.db.execute(
            """INSERT INTO income(
                   entry_date,field_id,description,partner,payment_method,amount,notes
               ) VALUES(?,?,?,?,?,?,?)""",
            ("2026-09-02", field_id, "Πώληση", "Αγοραστής", "Μετρητά", 510.0, ""),
        )
        self.db.execute(
            """INSERT INTO expenses(
                   entry_date,field_id,category,description,supplier,payment_method,amount,notes
               ) VALUES(?,?,?,?,?,?,?,?)""",
            ("2026-09-03", field_id, "Εφόδια", "Υλικά", "Προμηθευτής", "Κάρτα", 73.4, ""),
        )
        self.db.set_app_setting("farm_name", "Κτήμα Δοκιμής")
        return field_id

    def test_round_trip_restores_exact_live_snapshot_and_creates_safety_backup(self) -> None:
        field_id = self._seed_live_data()
        backup = self.manager.create_backup(prefix="phase16d")

        self.db.execute("UPDATE producer SET name=? WHERE id=1", ("Νεότερη τιμή",))
        self.db.execute("DELETE FROM production")
        self.db.execute(
            "INSERT INTO fields(name,kaek) VALUES(?,?)",
            ("Νεότερο αγροτεμάχιο", "newer"),
        )
        self.db.set_app_setting("farm_name", "Νεότερο κτήμα")

        restored_from, safety_backup = self.manager.restore_backup(backup)
        self.db.initialize()

        self.assertEqual(backup, restored_from)
        self.assertTrue(safety_backup.is_file())
        self.assertTrue(safety_backup.name.startswith("pre_restore_"))
        self.assertEqual(
            "Παραγωγός Χίου",
            self.db.query_one("SELECT name FROM producer WHERE id=1")["name"],
        )
        fields = self.db.query("SELECT id,name,kaek FROM fields ORDER BY id")
        self.assertEqual(1, len(fields))
        self.assertEqual(field_id, fields[0]["id"])
        self.assertEqual("050123456789/0/0", fields[0]["kaek"])
        production = self.db.query_one("SELECT product,quantity_kg FROM production")
        self.assertEqual("Μαστίχα", production["product"])
        self.assertAlmostEqual(12.75, float(production["quantity_kg"]))
        self.assertAlmostEqual(
            510.0,
            float(self.db.query_one("SELECT amount FROM income")["amount"]),
        )
        self.assertAlmostEqual(
            73.4,
            float(self.db.query_one("SELECT amount FROM expenses")["amount"]),
        )
        self.assertEqual("Κτήμα Δοκιμής", self.db.get_app_setting("farm_name"))

    def test_invalid_or_unrelated_database_is_rejected_before_live_data_changes(self) -> None:
        self._seed_live_data()
        original_name = self.db.query_one("SELECT name FROM producer WHERE id=1")["name"]

        corrupt = self.root / "corrupt.db"
        corrupt.write_bytes(b"not a sqlite database")
        with self.assertRaises(BackupError):
            self.manager.restore_backup(corrupt)

        unrelated = self.root / "unrelated.db"
        with sqlite3.connect(unrelated) as con:
            con.execute("CREATE TABLE other(id INTEGER PRIMARY KEY, value TEXT)")
            con.execute("INSERT INTO other(value) VALUES('foreign data')")
        with self.assertRaises(BackupError):
            self.manager.restore_backup(unrelated)

        self.assertEqual(
            original_name,
            self.db.query_one("SELECT name FROM producer WHERE id=1")["name"],
        )
        self.assertEqual([], self.manager._matching_backups(self.manager.PRE_RESTORE_PREFIX))

    def test_failed_restore_rolls_back_to_pre_restore_snapshot(self) -> None:
        self._seed_live_data()
        backup = self.manager.create_backup(prefix="phase16d")
        self.db.execute("UPDATE producer SET name=? WHERE id=1", ("Τρέχουσα ασφαλής τιμή",))

        original_copy = BackupManager._sqlite_copy
        calls = 0

        def fail_after_partial_write(*, source_path: Path, destination_path: Path) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                with sqlite3.connect(destination_path) as con:
                    con.execute("UPDATE producer SET name='BROKEN' WHERE id=1")
                    con.commit()
                raise RuntimeError("forced phase16d restore failure")
            original_copy(source_path=source_path, destination_path=destination_path)

        with patch.object(BackupManager, "_sqlite_copy", side_effect=fail_after_partial_write):
            with self.assertRaises(BackupError):
                self.manager.restore_backup(backup)

        self.assertEqual(2, calls)
        self.assertEqual(
            "Τρέχουσα ασφαλής τιμή",
            self.db.query_one("SELECT name FROM producer WHERE id=1")["name"],
        )
        safety = self.manager._matching_backups(self.manager.PRE_RESTORE_PREFIX)
        self.assertEqual(1, len(safety))
        with sqlite3.connect(safety[0]) as con:
            restored_name = con.execute("SELECT name FROM producer WHERE id=1").fetchone()[0]
        self.assertEqual("Τρέχουσα ασφαλής τιμή", restored_name)

    def test_same_second_backups_preserve_both_snapshots(self) -> None:
        self._seed_live_data()
        with patch("app.backup_manager.datetime") as clock:
            clock.now.return_value.strftime.return_value = "2026-09-12_12-00-00"
            first = self.manager.create_backup(prefix="manual")
            self.db.execute("UPDATE producer SET name='newer' WHERE id=1")
            second = self.manager.create_backup(prefix="manual")
        self.assertNotEqual(first, second)
        with sqlite3.connect(first) as con:
            self.assertEqual("Παραγωγός Χίου", con.execute("SELECT name FROM producer WHERE id=1").fetchone()[0])
        with sqlite3.connect(second) as con:
            self.assertEqual("newer", con.execute("SELECT name FROM producer WHERE id=1").fetchone()[0])

    def test_restore_retention_cannot_delete_selected_source_or_rollback_snapshot(self) -> None:
        self._seed_live_data()
        backup = self.manager.create_backup(prefix="pre_restore")
        self.db.execute("UPDATE producer SET name='current' WHERE id=1")
        self.manager.pre_restore_keep = 0
        original_copy = BackupManager._sqlite_copy

        def interrupted(*, source_path, destination_path):
            if source_path == backup:
                self.assertTrue(backup.is_file())
                with sqlite3.connect(destination_path) as con:
                    con.execute("UPDATE producer SET name='broken' WHERE id=1")
                raise RuntimeError("interrupted restore")
            original_copy(source_path=source_path, destination_path=destination_path)

        with patch.object(BackupManager, "_sqlite_copy", side_effect=interrupted):
            with self.assertRaises(BackupError):
                self.manager.restore_backup(backup)
        self.assertEqual("current", self.db.query_one("SELECT name FROM producer WHERE id=1")["name"])
        self.assertTrue(backup.is_file())

    def test_successful_restore_retains_source_and_returned_safety_at_zero_retention(self) -> None:
        self._seed_live_data()
        backup = self.manager.create_backup(prefix="pre_restore")
        self.db.execute("UPDATE producer SET name='current' WHERE id=1")
        self.manager.pre_restore_keep = 0
        source, safety = self.manager.restore_backup(backup)
        self.assertNotEqual(source, safety)
        self.assertTrue(source.is_file())
        self.assertTrue(safety.is_file())
        self.assertEqual("Παραγωγός Χίου", self.db.query_one("SELECT name FROM producer WHERE id=1")["name"])
        with sqlite3.connect(safety) as con:
            self.assertEqual("current", con.execute("SELECT name FROM producer WHERE id=1").fetchone()[0])

    def test_backup_restore_paths_with_uri_characters_are_literal(self) -> None:
        special = self.root / "Κτήμα #1 %25"
        db = Database(special / "live.db")
        db.execute("UPDATE producer SET name='original' WHERE id=1")
        manager = BackupManager(db.path, special / "backups")
        backup = manager.create_backup()
        db.execute("UPDATE producer SET name='changed' WHERE id=1")
        manager.restore_backup(backup)
        self.assertEqual("original", db.query_one("SELECT name FROM producer WHERE id=1")["name"])
        self.assertFalse((self.root / "Κτήμα ").exists())


if __name__ == "__main__":
    unittest.main()
