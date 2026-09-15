from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from app.database import Database
from app.product_registry import ensure_product_links


class _CountingDatabase(Database):
    def __init__(self, path: Path) -> None:
        self.connect_calls = 0
        super().__init__(path)

    def connect(self):
        self.connect_calls += 1
        return super().connect()


class ProductLinkPerformanceTests(unittest.TestCase):
    def test_link_repair_uses_one_connection_and_preserves_backfill(self) -> None:
        with TemporaryDirectory() as temp_dir:
            db = _CountingDatabase(Path(temp_dir) / "profile.db")

            with db.connect() as con:
                product_id = int(
                    con.execute(
                        "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
                        ("Μαστίχα", "kg"),
                    ).lastrowid
                )
                con.executemany(
                    """
                    INSERT INTO production(
                        entry_date,field_id,product,product_id,quantity_kg,notes
                    ) VALUES('2026-09-15',NULL,?,?,1,'')
                    """,
                    [("Μαστίχα", product_id)] * 200,
                )
                con.execute(
                    """
                    INSERT INTO production(
                        entry_date,field_id,product,product_id,quantity_kg,notes
                    ) VALUES('2026-09-15',NULL,'Νέο προϊόν',NULL,2,'')
                    """
                )
                con.execute(
                    """
                    CREATE TABLE production_sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product TEXT NOT NULL DEFAULT ''
                    )
                    """
                )
                con.execute(
                    "INSERT INTO production_sales(product) VALUES('Μαστίχα')"
                )

            db.connect_calls = 0
            ensure_product_links(db)
            self.assertEqual(1, db.connect_calls)

            with db.connect() as con:
                new_product = con.execute(
                    "SELECT id FROM products WHERE name='Νέο προϊόν'"
                ).fetchone()
                self.assertIsNotNone(new_product)

                unlinked = con.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM production p
                    LEFT JOIN products pr ON pr.id=p.product_id
                    WHERE TRIM(COALESCE(p.product,''))<>'' AND pr.id IS NULL
                    """
                ).fetchone()["count"]
                self.assertEqual(0, int(unlinked))

                sale = con.execute(
                    "SELECT product_id FROM production_sales LIMIT 1"
                ).fetchone()
                self.assertEqual(product_id, int(sale["product_id"]))


if __name__ == "__main__":
    unittest.main()
