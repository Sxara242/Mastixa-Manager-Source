from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.database import Database
from app.sales_report import SalesReportPage


class SalesReportConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db = Database(Path(self.temp_dir.name) / "reports.db")
        self.db.execute(
            """
            CREATE TABLE production_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                buyer_id INTEGER,
                buyer_name TEXT NOT NULL DEFAULT '',
                quantity_kg REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )

        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2026-08-01", "Μαστίχα", 100),
        )
        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2027-08-01", "Μαστίχα", 40),
        )
        self.db.execute(
            """INSERT INTO production_sales(
                sale_date,buyer_name,quantity_kg,price_per_kg,total_amount,
                payment_method,notes
            ) VALUES(?,?,?,?,?,?,?)""",
            ("2026-08-10", "Buyer A", 25, 10, 250, "", ""),
        )
        self.db.execute(
            """INSERT INTO production_sales(
                sale_date,buyer_name,quantity_kg,price_per_kg,total_amount,
                payment_method,notes
            ) VALUES(?,?,?,?,?,?,?)""",
            ("2027-08-10", "Buyer B", 10, 12, 120, "", ""),
        )
        self.page = SalesReportPage(self.db)

    def tearDown(self) -> None:
        self.page.close()
        self.temp_dir.cleanup()

    def _select_year(self, year: str) -> None:
        index = self.page.year_filter.findData(year)
        self.assertGreaterEqual(index, 0)
        self.page.year_filter.setCurrentIndex(index)
        self.page.refresh()

    def test_year_filter_scopes_production_but_keeps_current_stock_all_time(self) -> None:
        self.assertEqual("140 kg", self.page.production_metric[1].text())
        self.assertEqual("35 kg", self.page.sold_metric[1].text())
        self.assertEqual("105 kg", self.page.stock_metric[1].text())

        self._select_year("2026")
        self.assertEqual("100 kg", self.page.production_metric[1].text())
        self.assertEqual("25 kg", self.page.sold_metric[1].text())
        self.assertEqual("105 kg", self.page.stock_metric[1].text())

        self._select_year("2027")
        self.assertEqual("40 kg", self.page.production_metric[1].text())
        self.assertEqual("10 kg", self.page.sold_metric[1].text())
        self.assertEqual("105 kg", self.page.stock_metric[1].text())


if __name__ == "__main__":
    unittest.main()
