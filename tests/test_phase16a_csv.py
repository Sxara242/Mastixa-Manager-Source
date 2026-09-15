"""16A Windows portable CSV compatibility, without constructing Qt pages."""

import csv
import io
import sqlite3
import unittest
from decimal import Decimal

from app.data_export import DataExportPage


class PortableExportProbe:
    # Exercise production export methods using a synthetic SQLite data source.
    _csv_bytes = staticmethod(DataExportPage._csv_bytes)
    _table_export_bytes = DataExportPage._table_export_bytes
    _table_exists = DataExportPage._table_exists
    _filtered_query = DataExportPage._filtered_query

    def __init__(self, connection):
        self.connection = connection
        self.db = self

    def query(self, sql, params=()):
        return self.connection.execute(sql, params).fetchall()

    def query_one(self, sql, params=()):
        return self.connection.execute(sql, params).fetchone()


class PortableCsvCompatibilityTests(unittest.TestCase):
    @staticmethod
    def parse(data):
        return list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), delimiter=";", strict=True))

    def test_unicode_quotes_newlines_ids_units_dates_and_decimal_values(self):
        headers = ["id", "name", "notes", "value", "unit", "date", "observed_at", "optional"]
        rows = [["001234", 'Χωράφι; «Α» "β"', "γραμμή 1\r\nγραμμή 2", Decimal("-12.3400"),
                 "celsius", "2024-02-29", "2026-09-12T01:02:03Z", None]]
        data = DataExportPage._csv_bytes(headers, rows)
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertEqual([headers, ["001234", 'Χωράφι; «Α» "β"', "γραμμή 1\r\nγραμμή 2",
                                   "-12.3400", "celsius", "2024-02-29", "2026-09-12T01:02:03Z", ""]], self.parse(data))
        self.assertEqual(data, DataExportPage._csv_bytes(headers, rows))

    def test_table_export_preserves_source_values_and_product_filter(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory = sqlite3.Row
            db.executescript("""
                CREATE TABLE production(id INTEGER PRIMARY KEY, product_id INTEGER,
                    field_id INTEGER, entry_date TEXT, quantity_kg REAL, notes TEXT);
                INSERT INTO production VALUES(7,1,4,'2026-09-12',12.375,'Μαστίχα');
                INSERT INTO production VALUES(8,2,NULL,'',0,NULL);
            """)
            probe = PortableExportProbe(db)
            before = list(db.iterdump())
            db.execute("PRAGMA query_only=ON")
            data, count = probe._table_export_bytes("production", 1)
            self.assertEqual(1, count)
            self.assertEqual(["7", "1", "4", "2026-09-12", "12.375", "Μαστίχα"], self.parse(data)[1])
            data, count = probe._table_export_bytes("production")
            self.assertEqual(2, count)
            self.assertEqual(["8", "2", "", "", "0.0", ""], self.parse(data)[2])
            self.assertEqual(before, list(db.iterdump()))

    def test_portable_credential_exclusion_and_legacy_activity_policy(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory = sqlite3.Row
            db.executescript("""
                CREATE TABLE products(id INTEGER, name TEXT, unit TEXT, api_key TEXT);
                INSERT INTO products VALUES(1,'Λίπασμα','kg','SYNTHETIC-DO-NOT-EXPORT');
                CREATE TABLE farm_activities(id INTEGER, activity_date TEXT, category TEXT,
                    quantity REAL, unit TEXT, dose REAL, dose_unit TEXT);
                INSERT INTO farm_activities VALUES(1,'2026-09-12','Λίπανση',99,'legacy',1.25,'kg');
            """)
            probe = PortableExportProbe(db)
            db.execute("PRAGMA query_only=ON")
            data, count = probe._table_export_bytes("products")
            self.assertEqual(1, count)
            self.assertEqual([["id", "name", "unit"], ["1", "Λίπασμα", "kg"]], self.parse(data))
            self.assertNotIn(b"SYNTHETIC-DO-NOT-EXPORT", data)
            data, count = probe._table_export_bytes("farm_activities")
            self.assertEqual(1, count)
            self.assertEqual([["id", "activity_date", "category", "dose", "dose_unit"],
                              ["1", "2026-09-12", "Λίπανση", "1.25", "kg"]], self.parse(data))

    def test_absent_and_empty_sources_do_not_create_tables(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory = sqlite3.Row
            db.execute("CREATE TABLE production(id INTEGER, entry_date TEXT)")
            before = list(db.iterdump())
            probe = PortableExportProbe(db)
            db.execute("PRAGMA query_only=ON")
            data, count = probe._table_export_bytes("production")
            self.assertEqual(0, count)
            self.assertEqual([["id", "entry_date"]], self.parse(data))
            data, count = probe._table_export_bytes("missing_optional")
            self.assertEqual(0, count)
            self.assertEqual([[]], self.parse(data))
            self.assertEqual(before, list(db.iterdump()))


if __name__ == "__main__":
    unittest.main()
