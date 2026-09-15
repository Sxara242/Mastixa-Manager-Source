import json
import sqlite3
import unittest
from pathlib import Path

from app.inventory_sync import current_stock, delete_consumption, ensure_inventory_source_schema, sync_consumption


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "phase10_inventory_provenance.json"
ANDROID_FIXTURE = (
    ROOT
    / "android"
    / "app"
    / "src"
    / "androidTest"
    / "assets"
    / "phase10_inventory_provenance.json"
)


class _Db:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def execute(self, sql, params=()):
        cursor = self.connection.execute(sql, tuple(params))
        return cursor.lastrowid

    def query(self, sql, params=()):
        return list(self.connection.execute(sql, tuple(params)).fetchall())

    def query_one(self, sql, params=()):
        return self.connection.execute(sql, tuple(params)).fetchone()


class InventoryProvenanceCrossClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = _Db()
        self.addCleanup(self.db.close)
        self.db.execute(
            """
            CREATE TABLE inventory_items(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT 'kg'
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE inventory_movements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_date TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                field_id INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_inventory_source_schema(self.db)
        self.db.execute("INSERT INTO inventory_items(id,name,unit) VALUES(1,'Item A','kg')")
        self.db.execute("INSERT INTO inventory_items(id,name,unit) VALUES(2,'Item B','kg')")
        for item_id in (1, 2):
            self.db.execute(
                """
                INSERT INTO inventory_movements(
                    movement_date,item_id,movement_type,quantity,field_id,notes
                ) VALUES('2026-09-11',?,'Παραλαβή',10,NULL,'opening')
                """,
                (item_id,),
            )

    def test_shared_fixture_is_byte_identical(self):
        self.assertEqual(
            FIXTURE.read_bytes(),
            ANDROID_FIXTURE.read_bytes(),
        )

    def test_source_owned_correction_keeps_one_source_identity(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        source_type = fixture["source_type"]
        source_id = int(fixture["source_id"])

        sync_consumption(
            self.db,
            source_type=source_type,
            source_id=source_id,
            movement_date="2026-09-11",
            item_id=1,
            quantity=float(fixture["initial"]["quantity"]),
            field_id=None,
            notes="initial owner projection",
        )
        first = self.db.query_one(
            """
            SELECT id,item_id,quantity,source_type,source_id
            FROM inventory_movements
            WHERE source_type=? AND source_id=?
            """,
            (source_type, source_id),
        )
        self.assertIsNotNone(first)
        movement_id = int(first["id"])
        self.assertEqual(1, int(first["item_id"]))
        self.assertAlmostEqual(8.0, current_stock(self.db, 1))
        self.assertAlmostEqual(10.0, current_stock(self.db, 2))

        sync_consumption(
            self.db,
            source_type=source_type,
            source_id=source_id,
            movement_date="2026-09-12",
            item_id=2,
            quantity=float(fixture["corrected"]["quantity"]),
            field_id=None,
            notes="corrected by owning source",
        )
        rows = self.db.query(
            """
            SELECT id,item_id,quantity,source_type,source_id,notes
            FROM inventory_movements
            WHERE source_type=? AND source_id=?
            """,
            (source_type, source_id),
        )
        self.assertEqual(1, len(rows))
        corrected = rows[0]
        self.assertEqual(movement_id, int(corrected["id"]))
        self.assertEqual(2, int(corrected["item_id"]))
        self.assertAlmostEqual(float(fixture["corrected"]["quantity"]), float(corrected["quantity"]))
        self.assertEqual(source_type, corrected["source_type"])
        self.assertEqual(source_id, int(corrected["source_id"]))
        self.assertAlmostEqual(10.0, current_stock(self.db, 1))
        self.assertAlmostEqual(7.0, current_stock(self.db, 2))

        delete_consumption(
            self.db,
            source_type=source_type,
            source_id=source_id,
        )
        remaining = self.db.query_one(
            """
            SELECT COUNT(*) AS total
            FROM inventory_movements
            WHERE source_type=? AND source_id=?
            """,
            (source_type, source_id),
        )
        self.assertEqual(0, int(remaining["total"]))
        self.assertAlmostEqual(10.0, current_stock(self.db, 2))


if __name__ == "__main__":
    unittest.main()
