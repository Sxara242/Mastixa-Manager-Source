"""Focused 9C1 checks against synthetic, source-derived Windows tables."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.activity_projection import project_field_activities
from tests.test_phase9b_schema_compatibility import declaration, insert


class ActivityProjectionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys=ON")
        for path, table in (
            ("app/database.py", "fields"),
            ("app/database.py", "production"),
            ("app/activities.py", "farm_activities"),
        ):
            self.db.execute(declaration(path, table))
        for field in (1, 2):
            insert(self.db, "fields", id=field)
            insert(self.db, "production", id=field, field_id=field,
                   entry_date="2026-09-10")
            insert(self.db, "farm_activities", id=field, field_id=field,
                   activity_date="2026-09-09", category="Πότισμα")
        insert(self.db, "farm_activities", id=3, field_id=1,
               activity_date="2026-09-08", category="Λίπανση")
        self.db.commit()
        self.before = list(self.db.iterdump())
        self.db.execute("PRAGMA query_only=ON")

    def tearDown(self):
        self.assertEqual(self.before, list(self.db.iterdump()))

    def test_production_projection(self):
        items = project_field_activities(self.db, "profile-a", 1)
        self.assertEqual([{
            "version": 1, "scope_id": "profile-a", "field_id": "1",
            "source_ref": {"type": "production", "id": "1"},
            "kind": "harvest", "event_date": "2026-09-10",
            "time_basis": "occurred",
        }], [item for item in items if item["kind"] == "harvest"])

    def test_farm_activity_projection(self):
        items = project_field_activities(self.db, "profile-a", 1)
        self.assertEqual([
            {"version": 1, "scope_id": "profile-a", "field_id": "1",
             "source_ref": {"type": "farm_activity", "id": "1"},
             "kind": "irrigation", "event_date": "2026-09-09",
             "time_basis": "occurred"},
            {"version": 1, "scope_id": "profile-a", "field_id": "1",
             "source_ref": {"type": "farm_activity", "id": "3"},
             "kind": "fertilization", "event_date": "2026-09-08",
             "time_basis": "occurred"},
        ], [item for item in items if item["source_ref"]["type"] == "farm_activity"])

    def test_field_filtering(self):
        items = project_field_activities(self.db, "profile-a", 2)
        self.assertEqual(2, len(items))
        self.assertEqual({"2"}, {item["field_id"] for item in items})
        self.assertEqual({("production", "2"), ("farm_activity", "2")}, {
            (item["source_ref"]["type"], item["source_ref"]["id"]) for item in items
        })

    def test_source_reference_identity(self):
        def keys():
            return [(item["scope_id"], item["source_ref"]["type"],
                     item["source_ref"]["id"], item["field_id"])
                    for item in project_field_activities(self.db, "profile-a", 1)]
        expected = [("profile-a", "production", "1", "1"),
                    ("profile-a", "farm_activity", "1", "1"),
                    ("profile-a", "farm_activity", "3", "1")]
        self.assertEqual(expected, keys())
        self.assertEqual(expected, keys())


class ActivityProjectionDateTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        # Deliberately nullable synthetic slice for defensive NULL reads.
        # Current source schemas remain NOT NULL; no application DDL changes.
        self.db.executescript("""
            CREATE TABLE fields (id INTEGER PRIMARY KEY);
            INSERT INTO fields VALUES (1);
            CREATE TABLE production
                (id INTEGER PRIMARY KEY, field_id INTEGER, entry_date TEXT);
            CREATE TABLE farm_activities
                (id INTEGER PRIMARY KEY, field_id INTEGER, activity_date TEXT, category TEXT);
        """)

    def seed(self, source, identity, raw):
        if source == "production":
            self.db.execute("INSERT INTO production VALUES (?, 1, ?)", (identity, raw))
        else:
            self.db.execute("INSERT INTO farm_activities VALUES (?, 1, ?, 'Πότισμα')", (identity, raw))

    def read(self):
        self.db.commit()
        before = list(self.db.iterdump())
        self.db.execute("PRAGMA query_only=ON")
        try:
            result = project_field_activities(self.db, "profile-a", 1)
            self.assertEqual(before, list(self.db.iterdump()))
            return result
        finally:
            self.db.execute("PRAGMA query_only=OFF")

    def test_valid_dates_normalized_for_both_sources(self):
        self.seed("production", 1, " 2024-02-29 ")
        self.seed("farm_activity", 1, "2026-01-01")
        items = self.read()
        self.assertEqual(["2026-01-01", "2024-02-29"], [i["event_date"] for i in items])
        self.assertEqual(["occurred", "occurred"], [i["time_basis"] for i in items])

    def test_null_and_empty_dates_for_both_sources(self):
        for source in ("production", "farm_activity"):
            for identity, raw in enumerate((None, "", "  \t "), 1):
                self.seed(source, identity, raw)
        items = self.read()
        self.assertEqual(6, len(items))
        self.assertTrue(all(i["event_date"] is None and i["time_basis"] == "unknown" for i in items))

    def test_malformed_and_invalid_dates_for_both_sources(self):
        values = ("not-a-date", "2025-02-29", "2026-13-01", "2026-04-31",
                  "0000-01-01", "20260910", "2026-W37-4", "2026-9-1",
                  "10/09/2026", "2026-09-10T12:00:00Z")
        for source in ("production", "farm_activity"):
            for identity, raw in enumerate(values, 1):
                self.seed(source, identity, raw)
        items = self.read()
        self.assertEqual(20, len(items))
        self.assertTrue(all(i["event_date"] is None and i["time_basis"] == "unknown" for i in items))

    def test_equal_dates_use_lexical_source_and_id(self):
        for source in ("production", "farm_activity"):
            for identity in (2, 10):
                self.seed(source, identity, "2026-09-10")
        self.assertEqual([
            {"type": "farm_activity", "id": "10"},
            {"type": "farm_activity", "id": "2"},
            {"type": "production", "id": "10"},
            {"type": "production", "id": "2"},
        ], [i["source_ref"] for i in self.read()])

    def test_mixed_order_is_repeatable_with_unknown_dates_last(self):
        for source, identity, raw in (
            ("production", 1, None), ("farm_activity", 2, "bad"),
            ("production", 3, "2026-09-11"), ("farm_activity", 4, "2026-09-10"),
            ("production", 5, "2026-09-10"), ("farm_activity", 6, ""),
        ):
            self.seed(source, identity, raw)
        first = self.read()
        self.assertEqual(["3", "4", "5", "2", "6", "1"], [i["source_ref"]["id"] for i in first])
        self.assertEqual(["2026-09-11", "2026-09-10", "2026-09-10", None, None, None],
                         [i["event_date"] for i in first])
        for _ in range(3):
            self.assertEqual(first, self.read())


class ActivityProjectionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys=ON")
        for path, table in (("app/database.py", "fields"),
                            ("app/database.py", "production"),
                            ("app/activities.py", "farm_activities")):
            self.db.execute(declaration(path, table))
        for field in (1, 2):
            insert(self.db, "fields", id=field)
        insert(self.db, "production", id=7, field_id=1, entry_date="2026-09-10")
        insert(self.db, "farm_activities", id=7, field_id=1,
               activity_date="2026-09-09", category="Πότισμα")

    def read(self, field=1, connection=None, scope="profile-a"):
        db = self.db if connection is None else connection
        db.commit()  # Commit fixture mutations before each read-only probe.
        before = list(db.iterdump())
        db.execute("PRAGMA query_only=ON")
        try:
            result = project_field_activities(db, scope, field)
            self.assertEqual(before, list(db.iterdump()))
            return result
        finally:
            db.execute("PRAGMA query_only=OFF")

    def test_update_refreshes_date_kind_and_field_without_duplicates(self):
        original = self.read()
        self.assertEqual(2, len(original))
        self.db.execute("UPDATE production SET entry_date='2026-09-12' WHERE id=7")
        self.db.execute("UPDATE farm_activities SET activity_date='2026-09-13', category='Λίπανση' WHERE id=7")
        updated = self.read()
        self.assertEqual([
            ({"type": "farm_activity", "id": "7"}, "fertilization", "2026-09-13"),
            ({"type": "production", "id": "7"}, "harvest", "2026-09-12"),
        ], [(i["source_ref"], i["kind"], i["event_date"]) for i in updated])
        self.assertEqual(updated, self.read())
        for table in ("production", "farm_activities"):
            self.db.execute(f"UPDATE {table} SET field_id=2 WHERE id=7")
        self.assertEqual([], self.read(1))
        moved = self.read(2)
        self.assertEqual([dict(i, field_id="2") for i in updated], moved)
        self.assertEqual(moved, self.read(2))

    def test_delete_removes_activity_after_previous_read(self):
        self.assertEqual(2, len(self.read()))
        self.db.execute("DELETE FROM production WHERE id=7")
        remaining = self.read()
        self.assertEqual([{"type": "farm_activity", "id": "7"}],
                         [i["source_ref"] for i in remaining])
        self.db.execute("DELETE FROM farm_activities WHERE id=7")
        self.assertEqual([], self.read())
        self.assertEqual([], self.read())

    def test_unlinked_and_dangling_records_excluded_after_previous_read(self):
        self.assertEqual(2, len(self.read()))
        for table in ("production", "farm_activities"):
            self.db.execute(f"UPDATE {table} SET field_id=NULL WHERE id=7")
        self.assertEqual([], self.read())
        self.assertEqual([], self.read(2))
        # farm_activities has no field FK; a dangling link must also be excluded.
        self.db.execute("UPDATE farm_activities SET field_id=999 WHERE id=7")
        self.assertEqual([], self.read(999))
        self.assertEqual([], self.read(1))

    def test_other_profile_connection_does_not_reuse_previous_items(self):
        previous = self.read()
        other = sqlite3.connect(":memory:")
        self.addCleanup(other.close)
        other.executescript("""
            CREATE TABLE fields (id INTEGER PRIMARY KEY);
            INSERT INTO fields VALUES (1);
            CREATE TABLE production (id INTEGER PRIMARY KEY, field_id INTEGER, entry_date TEXT);
            INSERT INTO production VALUES (7, 1, '2025-01-01');
        """)
        self.assertEqual([{
            "version": 1, "scope_id": "profile-b", "field_id": "1",
            "source_ref": {"type": "production", "id": "7"},
            "kind": "harvest", "event_date": "2025-01-01", "time_basis": "occurred",
        }], self.read(connection=other, scope="profile-b"))
        self.assertEqual(previous, self.read())

    def test_missing_optional_columns_and_optional_source_table(self):
        expected = self.read()
        minimal = sqlite3.connect(":memory:")
        self.addCleanup(minimal.close)
        # Synthetic source slice omits non-projected columns (notes, status,
        # quantities, costs, timestamps, etc.), retaining all required inputs.
        minimal.executescript("""
            CREATE TABLE fields (id INTEGER PRIMARY KEY);
            INSERT INTO fields VALUES (1);
            CREATE TABLE production (id INTEGER PRIMARY KEY, field_id INTEGER, entry_date TEXT);
            INSERT INTO production VALUES (7, 1, '2026-09-10');
            CREATE TABLE farm_activities
                (id INTEGER PRIMARY KEY, field_id INTEGER, activity_date TEXT, category TEXT);
            INSERT INTO farm_activities VALUES (7, 1, '2026-09-09', 'Πότισμα');
        """)
        self.assertEqual(expected, self.read(connection=minimal))
        for item in self.read(connection=minimal):
            self.assertEqual({"version", "scope_id", "field_id", "source_ref",
                              "kind", "event_date", "time_basis"}, set(item))
        # Missing optional module: omit it without recreating it or caching rows.
        minimal.execute("DROP TABLE farm_activities")
        self.assertEqual([i for i in expected if i["kind"] == "harvest"],
                         self.read(connection=minimal))
        self.assertIsNone(minimal.execute(
            "SELECT name FROM sqlite_master WHERE name='farm_activities'"
        ).fetchone())


class ActivityProjectionTransactionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / "synthetic.db"
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.assertEqual("wal", self.db.execute("PRAGMA journal_mode=WAL").fetchone()[0])
        self.db.execute("PRAGMA foreign_keys=ON")
        for source, table in (("app/database.py", "fields"),
                              ("app/database.py", "production"),
                              ("app/activities.py", "farm_activities")):
            self.db.execute(declaration(source, table))
        insert(self.db, "fields", id=1)
        insert(self.db, "production", id=1, field_id=1, entry_date="2026-01-01")
        insert(self.db, "farm_activities", id=1, field_id=1,
               activity_date="2026-01-01", category="Πότισμα")
        self.db.commit()
        self.observer = sqlite3.connect(path)
        self.addCleanup(self.observer.close)

    def test_one_snapshot_across_sources_during_concurrent_commit(self):
        commits, failures = [], []

        def between_reads(sql):
            if "FROM farm_activities s" in sql and not commits and not failures:
                try:
                    with self.observer:
                        self.observer.execute("UPDATE production SET entry_date='2026-02-02'")
                        self.observer.execute("UPDATE farm_activities SET activity_date='2026-02-02', category='Λίπανση'")
                    commits.append(True)
                except Exception as error:
                    # SQLite trace callbacks don't propagate exceptions: assert outside.
                    failures.append(error)

        self.db.set_trace_callback(between_reads)
        try:
            first = project_field_activities(self.db, "profile-a", 1)
        finally:
            self.db.set_trace_callback(None)
        self.assertEqual([], failures)
        self.assertEqual([True], commits)
        self.assertEqual(["2026-01-01", "2026-01-01"], [i["event_date"] for i in first])
        self.assertEqual(["irrigation", "harvest"], [i["kind"] for i in first])
        self.assertFalse(self.db.in_transaction)
        second = project_field_activities(self.db, "profile-a", 1)
        self.assertEqual(["2026-02-02", "2026-02-02"], [i["event_date"] for i in second])
        self.assertEqual(["fertilization", "harvest"], [i["kind"] for i in second])

    def test_success_preserves_pending_caller_transaction(self):
        for finish in ("rollback", "commit"):
            with self.subTest(caller_action=finish):
                before = list(self.observer.iterdump())
                self.db.execute("BEGIN")
                self.db.execute("UPDATE production SET entry_date='2026-03-03'")
                changes = self.db.total_changes
                items = project_field_activities(self.db, "profile-a", 1)
                self.assertTrue(self.db.in_transaction)
                self.assertEqual(changes, self.db.total_changes)
                self.assertEqual("2026-03-03", next(i["event_date"] for i in items if i["kind"] == "harvest"))
                self.assertEqual("2026-03-03", self.db.execute("SELECT entry_date FROM production").fetchone()[0])
                self.assertEqual(before, list(self.observer.iterdump()))
                getattr(self.db, finish)()
                self.assertFalse(self.db.in_transaction)
                if finish == "rollback":
                    self.assertEqual(before, list(self.observer.iterdump()))
                    self.assertEqual("2026-01-01", self.db.execute("SELECT entry_date FROM production").fetchone()[0])
                else:
                    self.assertEqual("2026-03-03", self.observer.execute("SELECT entry_date FROM production").fetchone()[0])

    def test_query_failure_preserves_caller_transaction_and_propagates(self):
        for finish in ("rollback", "commit"):
            with self.subTest(caller_action=finish):
                before = list(self.observer.iterdump())
                self.db.execute("BEGIN")
                self.db.execute("UPDATE production SET entry_date='2026-04-04'")
                changes = self.db.total_changes
                denied, traced = [], []

                def deny_activity_read(action, table, column, database, trigger):
                    if action == sqlite3.SQLITE_READ and table == "farm_activities":
                        denied.append(table)
                        return sqlite3.SQLITE_DENY
                    return sqlite3.SQLITE_OK

                self.db.set_authorizer(deny_activity_read)
                self.db.set_trace_callback(traced.append)
                try:
                    with self.assertRaisesRegex(sqlite3.DatabaseError, "prohibited"):
                        project_field_activities(self.db, "profile-a", 1)
                finally:
                    self.db.set_authorizer(None)
                    self.db.set_trace_callback(None)
                self.assertTrue(denied)
                self.assertTrue(any("FROM production s" in sql for sql in traced))
                self.assertFalse(any(sql.strip().upper().startswith(("COMMIT", "ROLLBACK")) for sql in traced))
                self.assertTrue(self.db.in_transaction)
                self.assertEqual(changes, self.db.total_changes)
                self.assertEqual("2026-04-04", self.db.execute("SELECT entry_date FROM production").fetchone()[0])
                self.assertEqual(before, list(self.observer.iterdump()))
                # Connection and caller transaction remain usable after failure.
                self.assertEqual(2, len(project_field_activities(self.db, "profile-a", 1)))
                self.assertTrue(self.db.in_transaction)
                getattr(self.db, finish)()
                if finish == "rollback":
                    self.assertEqual(before, list(self.observer.iterdump()))
                else:
                    self.assertEqual("2026-04-04", self.observer.execute("SELECT entry_date FROM production").fetchone()[0])

    def test_projection_is_read_only_and_leaves_persisted_schema_unchanged(self):
        before = list(self.observer.iterdump())
        schema_version = self.observer.execute("PRAGMA schema_version").fetchone()[0]
        changes = self.db.total_changes
        denied = []

        def reads_only(action, arg1, arg2, database, trigger):
            if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_SAVEPOINT):
                return sqlite3.SQLITE_OK
            denied.append((action, arg1, arg2))
            return sqlite3.SQLITE_DENY

        self.db.execute("PRAGMA query_only=ON")
        self.db.set_authorizer(reads_only)
        try:
            self.assertEqual(2, len(project_field_activities(self.db, "profile-a", 1)))
        finally:
            self.db.set_authorizer(None)
        self.assertEqual([], denied)
        self.assertEqual(changes, self.db.total_changes)
        self.assertFalse(self.db.in_transaction)
        self.assertEqual(1, self.db.execute("PRAGMA query_only").fetchone()[0])
        self.assertEqual(before, list(self.observer.iterdump()))
        self.assertEqual(schema_version, self.observer.execute("PRAGMA schema_version").fetchone()[0])


class CultivationSourceProjectionTests(unittest.TestCase):
    SOURCES = (
        ("planting_batches", "planting_date", "planting_batch", "planting", "app/plantings.py"),
        ("plant_protection_records", "application_date", "plant_protection", "plant_protection", "app/plant_protection.py"),
        ("labor_entries", "work_date", "labor_entry", "cultivation_work", "app/labor.py"),
    )

    def database(self):
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        self.addCleanup(db.close)
        db.execute("PRAGMA foreign_keys=ON")
        for path, table in (("app/database.py", "fields"),
                            ("app/database.py", "production"),
                            ("app/activities.py", "farm_activities"),
                            ("app/labor.py", "workers")):
            db.execute(declaration(path, table))
        for table, _, _, _, path in self.SOURCES:
            db.execute(declaration(path, table))
        insert(db, "workers", id=1)
        for field in (1, 2):
            insert(db, "fields", id=field)
            insert(db, "production", id=field, field_id=field, entry_date="2026-09-10")
            insert(db, "farm_activities", id=field, field_id=field,
                   activity_date="2026-09-10", category="Πότισμα")
            for table, date_column, *_ in self.SOURCES:
                insert(db, table, id=field, field_id=field, **{date_column: "2026-09-10"})
        db.commit()
        return db

    def setUp(self):
        self.db = self.database()

    def read(self, field=1, db=None, scope="profile-a"):
        db = self.db if db is None else db
        before, changes, active = list(db.iterdump()), db.total_changes, db.in_transaction
        db.execute("PRAGMA query_only=ON")
        try:
            items = project_field_activities(db, scope, field)
        finally:
            db.execute("PRAGMA query_only=OFF")
        self.assertEqual(before, list(db.iterdump()))
        self.assertEqual(changes, db.total_changes)
        self.assertEqual(active, db.in_transaction)
        return items

    def test_normal_projection_and_field_filtering_for_each_source(self):
        for field in (1, 2):
            items = self.read(field)
            self.assertEqual(5, len(items))
            for _, _, source, kind, _ in self.SOURCES:
                with self.subTest(field=field, source=source):
                    self.assertEqual([{
                        "version": 1, "scope_id": "profile-a", "field_id": str(field),
                        "source_ref": {"type": source, "id": str(field)},
                        "kind": kind, "event_date": "2026-09-10", "time_basis": "occurred",
                    }], [i for i in items if i["source_ref"]["type"] == source])
        self.assertEqual([], self.read(999))

    def test_updates_and_field_moves_keep_one_source_identity(self):
        self.assertEqual(5, len(self.read()))
        for table, date_column, source, kind, _ in self.SOURCES:
            with self.subTest(source=source):
                self.db.execute(f"UPDATE {table} SET {date_column}='2026-09-11', notes='changed' WHERE id=1")
                matching = [i for i in self.read() if i["source_ref"]["type"] == source]
                self.assertEqual(1, len(matching))
                self.assertEqual("2026-09-11", matching[0]["event_date"])
                self.assertEqual(kind, matching[0]["kind"])
                self.assertEqual({"type": source, "id": "1"}, matching[0]["source_ref"])
                self.db.execute(f"UPDATE {table} SET field_id=2 WHERE id=1")
                self.assertFalse(any(i["source_ref"]["type"] == source for i in self.read()))
                moved = [i for i in self.read(2) if i["source_ref"] == matching[0]["source_ref"]]
                self.assertEqual([dict(matching[0], field_id="2")], moved)
                self.assertEqual(self.read(2), self.read(2))

    def test_delete_and_supported_unlink_remove_previously_read_items(self):
        self.assertEqual(5, len(self.read()))
        self.db.execute("UPDATE labor_entries SET field_id=NULL WHERE id=1")
        self.assertFalse(any(i["source_ref"]["type"] == "labor_entry" for i in self.read()))
        # Plantings/protection cannot have NULL field links under their real DDL.
        for table in ("planting_batches", "plant_protection_records"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(f"UPDATE {table} SET field_id=NULL WHERE id=1")
        for table, _, source, *_ in self.SOURCES:
            self.db.execute(f"DELETE FROM {table} WHERE id=1")
            self.assertFalse(any(i["source_ref"]["type"] == source for i in self.read()))
        self.assertEqual(2, len(self.read()))
        self.assertEqual(5, len(self.read(2)))

    def test_profile_connections_do_not_share_same_local_ids(self):
        previous = self.read()
        other = self.database()
        for table, date_column, *_ in self.SOURCES:
            other.execute(f"UPDATE {table} SET {date_column}='2025-01-01'")
        other.commit()
        items = self.read(db=other, scope="profile-b")
        self.assertEqual({"profile-b"}, {i["scope_id"] for i in items})
        for _, _, source, *_ in self.SOURCES:
            self.assertEqual(["2025-01-01"], [i["event_date"] for i in items if i["source_ref"]["type"] == source])
        self.assertEqual(previous, self.read())

    def test_missing_optional_columns_nullable_values_and_absent_modules(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("CREATE TABLE fields(id INTEGER PRIMARY KEY)")
        db.execute("INSERT INTO fields VALUES(1)")
        # Defensive synthetic slices; real NOT NULL constraints are unchanged.
        for table, date_column, source, kind, _ in self.SOURCES:
            db.execute(f"CREATE TABLE {table}(id INTEGER PRIMARY KEY,field_id INTEGER,{date_column} TEXT,notes TEXT)")
            db.execute(f"INSERT INTO {table} VALUES(1,1,NULL,NULL)")
            db.execute(f"INSERT INTO {table} VALUES(2,999,'2026-01-01',NULL)")
            db.execute(f"INSERT INTO {table} VALUES(3,NULL,'2026-01-01',NULL)")
        items = self.read(db=db)
        self.assertEqual(3, len(items))
        for _, _, source, kind, _ in self.SOURCES:
            self.assertEqual([{
                "version": 1, "scope_id": "profile-a", "field_id": "1",
                "source_ref": {"type": source, "id": "1"}, "kind": kind,
                "event_date": None, "time_basis": "unknown",
            }], [i for i in items if i["source_ref"]["type"] == source])
        for table, _, source, *_ in self.SOURCES:
            db.execute(f"DROP TABLE {table}")
            items = [i for i in items if i["source_ref"]["type"] != source]
            self.assertEqual(items, self.read(db=db))
        self.assertEqual([], self.read(db=db))

    def test_new_sources_use_existing_date_rules(self):
        for raw, normalized in ((" 2024-02-29 ", "2024-02-29"), ("", None),
                                ("2025-02-29", None), ("not-a-date", None)):
            for table, date_column, source, *_ in self.SOURCES:
                with self.subTest(source=source, raw=raw):
                    self.db.execute(f"UPDATE {table} SET {date_column}=? WHERE id=1", (raw,))
                    item = next(i for i in self.read() if i["source_ref"]["type"] == source)
                    self.assertEqual(normalized, item["event_date"])
                    self.assertEqual("unknown" if normalized is None else "occurred", item["time_basis"])

    def test_mixed_order_and_distinct_same_day_identities_are_repeatable(self):
        for table, date_column, *_ in self.SOURCES:
            for identity, raw in ((10, "2026-09-10"), (11, ""), (12, "2026-09-12")):
                insert(self.db, table, id=identity, field_id=1, **{date_column: raw})
        first = self.read()
        keys = [(i["source_ref"]["type"], i["source_ref"]["id"]) for i in first]
        self.assertEqual([
            ("labor_entry", "12"), ("plant_protection", "12"), ("planting_batch", "12"),
            ("farm_activity", "1"), ("labor_entry", "1"), ("labor_entry", "10"),
            ("plant_protection", "1"), ("plant_protection", "10"),
            ("planting_batch", "1"), ("planting_batch", "10"), ("production", "1"),
            ("labor_entry", "11"), ("plant_protection", "11"), ("planting_batch", "11"),
        ], keys)
        self.assertEqual(14, len(set(keys)))
        for _ in range(3):
            self.assertEqual(first, self.read())

    def test_new_source_failure_leaves_pending_changes_under_caller_control(self):
        before = list(self.db.iterdump())
        self.db.execute("BEGIN")
        self.db.execute("UPDATE planting_batches SET planting_date='2026-12-01' WHERE id=1")
        self.assertEqual("2026-12-01", self.read()[0]["event_date"])
        self.db.set_authorizer(lambda action, table, *args:
                               sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == "labor_entries"
                               else sqlite3.SQLITE_OK)
        try:
            with self.assertRaisesRegex(sqlite3.DatabaseError, "prohibited"):
                project_field_activities(self.db, "profile-a", 1)
        finally:
            self.db.set_authorizer(None)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual("2026-12-01", self.read()[0]["event_date"])
        self.db.rollback()
        self.assertEqual(before, list(self.db.iterdump()))


class GisActivityProjectionTests(unittest.TestCase):
    SOURCES = CultivationSourceProjectionTests.SOURCES
    MIDNIGHT = 1704067200000  # 2024-01-01T00:00:00Z

    def database(self):
        db = CultivationSourceProjectionTests.database(self)
        for table in ("parcel_geometry", "geo_points"):
            db.execute(declaration("app/gis/store.py", table))
        for field in (1, 2):
            insert(db, "parcel_geometry", id=f"parcel-{field}", field_id=field)
        insert(db, "geo_points", id="point-a", parcel_id="parcel-1", point_type="note",
               created_at=self.MIDNIGHT + 1, updated_at=self.MIDNIGHT + 86400000)
        insert(db, "geo_points", id="point-b", parcel_id="parcel-2", point_type="problem",
               created_at=self.MIDNIGHT)
        db.commit()
        return db

    def setUp(self):
        self.db = self.database()

    def read(self, field=1, db=None, scope="profile-a"):
        return CultivationSourceProjectionTests.read(self, field, db, scope)

    def observations(self, **kwargs):
        return [i for i in self.read(**kwargs) if i["kind"] == "observation"]

    def test_normal_recorded_projection_and_allowed_point_types(self):
        self.assertEqual([{
            "version": 1, "scope_id": "profile-a", "field_id": "1",
            "source_ref": {"type": "geo_point", "id": "point-a"},
            "kind": "observation", "event_date": "2024-01-01",
            "event_at": self.MIDNIGHT + 1, "time_basis": "recorded",
        }], self.observations())
        self.assertEqual("point-b", self.observations(field=2)[0]["source_ref"]["id"])
        insert(self.db, "geo_points", id="not-observation", parcel_id="parcel-1",
               point_type="boundary", created_at=self.MIDNIGHT)
        self.assertEqual(1, len(self.observations()))
        self.assertEqual([], self.observations(field=999))

    def test_parent_unlink_tombstones_and_source_tombstone(self):
        self.assertEqual(1, len(self.observations()))
        for table, identity in (("geo_points", "point-a"), ("parcel_geometry", "parcel-1")):
            self.db.execute(f"UPDATE {table} SET deleted_at=0 WHERE id=?", (identity,))
            self.assertEqual([], self.observations())
            self.db.execute(f"UPDATE {table} SET deleted_at=NULL WHERE id=?", (identity,))
            self.assertEqual(1, len(self.observations()))
        self.db.execute("UPDATE parcel_geometry SET field_id=NULL WHERE id='parcel-1'")
        self.assertEqual([], self.observations())
        self.assertEqual(1, len(self.observations(field=2)))

    def test_defensive_null_dangling_parents_and_unknown_timestamps(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        # Synthetic damaged/legacy slice only; real constraints stay unchanged.
        db.executescript("""
            CREATE TABLE fields(id INTEGER PRIMARY KEY);
            INSERT INTO fields VALUES(1);
            CREATE TABLE parcel_geometry(id TEXT PRIMARY KEY, field_id INTEGER, deleted_at INTEGER);
            INSERT INTO parcel_geometry VALUES('valid',1,NULL),('unlinked',NULL,NULL),('dangling',99,NULL);
            CREATE TABLE geo_points(id TEXT PRIMARY KEY,parcel_id TEXT,point_type TEXT,created_at,deleted_at INTEGER);
        """)
        for identity, parent in (("null", None), ("missing", "missing"),
                                 ("unlinked", "unlinked"), ("dangling", "dangling")):
            db.execute("INSERT INTO geo_points VALUES(?,?,'note',?,NULL)", (identity, parent, self.MIDNIGHT))
        invalid = (None, "", "invalid", "1704067200000", 1.5, b"bad", 2**63-1, -2**63)
        for index, raw in enumerate(invalid):
            db.execute("INSERT INTO geo_points VALUES(?,'valid','problem',?,NULL)", (f"invalid-{index}", raw))
        items = self.observations(db=db)
        self.assertEqual([f"invalid-{i}" for i in range(len(invalid))], [i["source_ref"]["id"] for i in items])
        for item in items:
            self.assertIsNone(item["event_date"])
            self.assertEqual("unknown", item["time_basis"])
            self.assertNotIn("event_at", item)
        self.assertEqual([], self.observations(db=db, field=99))
        db.execute("DROP TABLE parcel_geometry")
        self.assertEqual([], self.observations(db=db))

    def test_epoch_zero_negative_and_utc_day_boundaries(self):
        for value, day in ((0, "1970-01-01"), (-1, "1969-12-31"),
                           (self.MIDNIGHT-1, "2023-12-31"),
                           (self.MIDNIGHT+86399999, "2024-01-01"),
                           (self.MIDNIGHT+86400000, "2024-01-02")):
            with self.subTest(epoch=value):
                self.db.execute("UPDATE geo_points SET created_at=? WHERE id='point-a'", (value,))
                item = self.observations()[0]
                self.assertEqual(day, item["event_date"])
                self.assertEqual(value, item["event_at"])
                self.assertEqual("recorded", item["time_basis"])

    def test_updates_moves_and_delete_preserve_identity_without_cache(self):
        original = self.observations()[0]
        self.db.execute("UPDATE geo_points SET title='edited',point_type='problem',updated_at=? WHERE id='point-a'", (self.MIDNIGHT+999999,))
        self.assertEqual([original], self.observations())
        self.db.execute("UPDATE geo_points SET created_at=? WHERE id='point-a'", (self.MIDNIGHT+2,))
        updated = self.observations()[0]
        self.assertEqual(original["source_ref"], updated["source_ref"])
        self.assertEqual(self.MIDNIGHT+2, updated["event_at"])
        self.db.execute("UPDATE geo_points SET parcel_id='parcel-2' WHERE id='point-a'")
        self.assertEqual([], self.observations())
        moved = self.observations(field=2)
        self.assertEqual(2, len(moved))
        self.assertEqual(2, len({i["source_ref"]["id"] for i in moved}))
        self.assertEqual(moved, self.observations(field=2))
        self.db.execute("DELETE FROM geo_points WHERE id='point-a'")
        self.assertEqual(["point-b"], [i["source_ref"]["id"] for i in self.observations(field=2)])

    def test_profile_isolation_with_same_point_ids(self):
        other = self.database()
        other.execute("UPDATE geo_points SET created_at=0 WHERE id='point-a'")
        other.commit()
        original = self.observations()
        items = self.observations(db=other, scope="profile-b")
        self.assertEqual(1, len(items))
        self.assertEqual("profile-b", items[0]["scope_id"])
        self.assertEqual(0, items[0]["event_at"])
        self.assertEqual(original, self.observations())

    def test_mixed_source_order_uses_instant_then_date_only_then_unknown(self):
        for table, date_column in (("production", "entry_date"), ("farm_activities", "activity_date"),
                                   *((s[0], s[1]) for s in self.SOURCES)):
            self.db.execute(f"UPDATE {table} SET {date_column}='2024-01-01'")
        for identity, timestamp in (("point-c", self.MIDNIGHT+1), ("point-d", self.MIDNIGHT+2),
                                     ("next-day", self.MIDNIGHT+86400000), ("unknown", "bad")):
            insert(self.db, "geo_points", id=identity, parcel_id="parcel-1", point_type="note", created_at=timestamp)
        self.db.execute("UPDATE production SET entry_date='' WHERE id=1")
        items = self.read()
        self.assertEqual([
            ("geo_point", "next-day"), ("geo_point", "point-d"),
            ("geo_point", "point-a"), ("geo_point", "point-c"),
            ("farm_activity", "1"), ("labor_entry", "1"),
            ("plant_protection", "1"), ("planting_batch", "1"),
            ("geo_point", "unknown"), ("production", "1"),
        ], [(i["source_ref"]["type"], i["source_ref"]["id"]) for i in items])
        self.assertEqual(items, self.read())

    def test_gis_read_and_controlled_failure_preserve_caller_transaction(self):
        before = list(self.db.iterdump())
        self.db.execute("BEGIN")
        self.db.execute("UPDATE geo_points SET created_at=0 WHERE id='point-a'")
        self.assertEqual(0, self.observations()[0]["event_at"])
        self.db.set_authorizer(lambda action, table, *args:
                               sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and table == "geo_points"
                               else sqlite3.SQLITE_OK)
        try:
            with self.assertRaisesRegex(sqlite3.DatabaseError, "prohibited"):
                project_field_activities(self.db, "profile-a", 1)
        finally:
            self.db.set_authorizer(None)
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(0, self.observations()[0]["event_at"])
        self.db.rollback()
        self.assertEqual(before, list(self.db.iterdump()))


if __name__ == "__main__":
    unittest.main()
