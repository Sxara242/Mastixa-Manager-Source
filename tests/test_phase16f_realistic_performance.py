from __future__ import annotations

import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.backup_manager import BackupManager
from app.dashboard import DashboardPage
from app.data_quality import DataQualityPage
from app.database import Database


class Phase16FRealisticPerformanceTests(unittest.TestCase):
    """Release gate for realistic multi-year desktop workloads.

    The thresholds are intentionally generous. They are meant to catch severe
    regressions (for example accidental O(n^2) behaviour), not tiny benchmark
    fluctuations between machines.
    """

    FIELD_COUNT = 250
    PRODUCT_COUNT = 12
    PRODUCTION_COUNT = 8000
    INCOME_COUNT = 5000
    EXPENSE_COUNT = 5000

    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp_dir.name)
        self.db = Database(self.root / "phase16f.db")
        self._seed_realistic_dataset()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def _date_for(index: int) -> str:
        year = 2020 + (index % 6)
        month = 1 + (index % 12)
        day = 1 + (index % 28)
        return f"{year:04d}-{month:02d}-{day:02d}"

    def _seed_realistic_dataset(self) -> None:
        with self.db.connect() as con:
            con.execute(
                "UPDATE producer SET name=?,tax_id=?,phone=?,email=? WHERE id=1",
                ("Performance Farm", "123456789", "2100000000", "farm@example.test"),
            )

            con.executemany(
                """
                INSERT INTO fields(
                    id,name,kaek,location,area_stremma,productive_trees,notes
                ) VALUES(?,?,?,?,?,?,?)
                """,
                [
                    (
                        field_id,
                        f"Field {field_id}",
                        f"KAEK-{field_id:06d}",
                        f"Location {field_id % 25}",
                        1.0 + (field_id % 30) / 10.0,
                        20 + (field_id % 180),
                        "",
                    )
                    for field_id in range(1, self.FIELD_COUNT + 1)
                ],
            )

            con.executemany(
                "INSERT INTO products(id,name,unit,is_active) VALUES(?,?,?,1)",
                [
                    (product_id, f"Product {product_id}", "kg")
                    for product_id in range(1, self.PRODUCT_COUNT + 1)
                ],
            )

            con.executemany(
                """
                INSERT INTO production(
                    entry_date,field_id,product,product_id,quantity_kg,notes
                ) VALUES(?,?,?,?,?,?)
                """,
                [
                    (
                        self._date_for(i),
                        1 + (i % self.FIELD_COUNT),
                        f"Product {1 + (i % self.PRODUCT_COUNT)}",
                        1 + (i % self.PRODUCT_COUNT),
                        1.0 + (i % 40) / 4.0,
                        "",
                    )
                    for i in range(self.PRODUCTION_COUNT)
                ],
            )

            con.executemany(
                """
                INSERT INTO income(
                    entry_date,field_id,description,partner,payment_method,amount,notes
                ) VALUES(?,?,?,?,?,?,?)
                """,
                [
                    (
                        self._date_for(i),
                        1 + (i % self.FIELD_COUNT),
                        f"Income {i}",
                        f"Buyer {i % 40}",
                        "Τραπεζική μεταφορά",
                        20.0 + (i % 500),
                        "",
                    )
                    for i in range(self.INCOME_COUNT)
                ],
            )

            con.executemany(
                """
                INSERT INTO expenses(
                    entry_date,field_id,category,description,supplier,
                    payment_method,amount,notes
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                [
                    (
                        self._date_for(i),
                        1 + (i % self.FIELD_COUNT),
                        f"Category {i % 12}",
                        f"Expense {i}",
                        f"Supplier {i % 35}",
                        "Μετρητά",
                        5.0 + (i % 250),
                        "",
                    )
                    for i in range(self.EXPENSE_COUNT)
                ],
            )

            con.commit()

    def test_realistic_dashboard_quality_and_backup_stay_responsive(self) -> None:
        counts = {
            "fields": self.FIELD_COUNT,
            "production": self.PRODUCTION_COUNT,
            "income": self.INCOME_COUNT,
            "expenses": self.EXPENSE_COUNT,
        }
        for table, expected in counts.items():
            actual = int(
                self.db.query_one(f"SELECT COUNT(*) AS total FROM {table}")["total"]
            )
            self.assertEqual(expected, actual)

        started = time.perf_counter()
        dashboard = DashboardPage(self.db)
        dashboard_seconds = time.perf_counter() - started
        self.addCleanup(dashboard.close)

        started = time.perf_counter()
        quality = DataQualityPage(self.db)
        quality_seconds = time.perf_counter() - started
        self.addCleanup(quality.close)

        errors = [
            issue for issue in quality.all_issues
            if issue["severity"] == "ERROR"
        ]
        self.assertEqual([], errors)

        manager = BackupManager(
            database_path=self.db.path,
            backup_dir=self.root / "backups",
        )
        started = time.perf_counter()
        backup = manager.create_backup(prefix="phase16f")
        backup_seconds = time.perf_counter() - started

        self.assertTrue(backup.is_file())
        with sqlite3.connect(backup) as con:
            for table, expected in counts.items():
                actual = int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                self.assertEqual(expected, actual)

        # Generous release thresholds: catch serious regressions, not noise.
        self.assertLess(
            dashboard_seconds,
            4.0,
            f"Dashboard took {dashboard_seconds:.3f}s for the realistic dataset",
        )
        self.assertLess(
            quality_seconds,
            8.0,
            f"Data Quality took {quality_seconds:.3f}s for the realistic dataset",
        )
        self.assertLess(
            backup_seconds,
            8.0,
            f"Backup took {backup_seconds:.3f}s for the realistic dataset",
        )

        # Keep timings visible in verbose CI logs for future comparisons.
        print(
            "Phase16F timings: "
            f"dashboard={dashboard_seconds:.3f}s, "
            f"quality={quality_seconds:.3f}s, "
            f"backup={backup_seconds:.3f}s, "
            f"rows={sum(counts.values())}"
        )


if __name__ == "__main__":
    unittest.main()
