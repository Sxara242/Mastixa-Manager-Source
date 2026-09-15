from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.data_quality import DataQualityPage
from app.database import Database


class Phase16ECrossModuleValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.temp_dir.name)
        self.db = Database(self.root / "phase16e.db")
        # Build the page before optional module tables are introduced so its
        # initial refresh only sees the core Database schema.
        self.page = DataQualityPage(self.db)
        self._create_cross_module_schema()
        self._seed_consistent_links()

    def tearDown(self) -> None:
        self.page.close()
        self.temp_dir.cleanup()

    def _create_cross_module_schema(self) -> None:
        self.db.execute(
            """
            CREATE TABLE business_partners(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                partner_type TEXT NOT NULL DEFAULT 'both'
            )
            """
        )
        self.db.execute("ALTER TABLE income ADD COLUMN partner_id INTEGER")
        self.db.execute("ALTER TABLE expenses ADD COLUMN partner_id INTEGER")

        self.db.execute(
            """
            CREATE TABLE production_sales(
                id INTEGER PRIMARY KEY,
                sale_date TEXT NOT NULL,
                buyer_id INTEGER,
                buyer_name TEXT NOT NULL DEFAULT '',
                product TEXT NOT NULL DEFAULT '',
                quantity_kg REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                income_id INTEGER
            )
            """
        )

        self.db.execute(
            """
            CREATE TABLE equipment(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE equipment_maintenance(
                id INTEGER PRIMARY KEY,
                equipment_id INTEGER,
                service_date TEXT NOT NULL,
                cost REAL NOT NULL,
                expense_id INTEGER
            )
            """
        )

        self.db.execute(
            """
            CREATE TABLE inventory_items(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE inventory_movements(
                id INTEGER PRIMARY KEY,
                item_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total_cost REAL NOT NULL,
                expense_id INTEGER,
                partner_id INTEGER
            )
            """
        )

    def _seed_consistent_links(self) -> None:
        self.db.execute(
            "INSERT INTO business_partners(id,name,partner_type) VALUES(?,?,?)",
            (1, "Αγοραστής Α", "buyer"),
        )
        self.db.execute(
            "INSERT INTO business_partners(id,name,partner_type) VALUES(?,?,?)",
            (2, "Προμηθευτής Α", "supplier"),
        )

        self.db.execute(
            "INSERT INTO production(entry_date,product,quantity_kg) VALUES(?,?,?)",
            ("2026-09-01", "Μαστίχα", 100.0),
        )

        sale_income_id = self.db.execute(
            """
            INSERT INTO income(
                entry_date,description,partner,partner_id,payment_method,amount,notes
            ) VALUES(?,?,?,?,?,?,?)
            """,
            (
                "2026-09-02",
                "Πώληση προϊόντος — πώληση #1",
                "Αγοραστής Α",
                1,
                "Μετρητά",
                200.0,
                "",
            ),
        )
        self.db.execute(
            """
            INSERT INTO production_sales(
                id,sale_date,buyer_id,buyer_name,product,quantity_kg,
                price_per_kg,total_amount,payment_method,notes,income_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                1,
                "2026-09-02",
                1,
                "Αγοραστής Α",
                "Μαστίχα",
                10.0,
                20.0,
                200.0,
                "Μετρητά",
                "",
                sale_income_id,
            ),
        )

        self.db.execute("INSERT INTO equipment(id,name) VALUES(?,?)", (1, "Τρακτέρ"))
        maintenance_expense_id = self.db.execute(
            """
            INSERT INTO expenses(
                entry_date,category,description,supplier,partner_id,
                payment_method,amount,notes
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                "2026-09-03",
                "Συντήρηση",
                "Service",
                "Προμηθευτής Α",
                2,
                "Μετρητά",
                50.0,
                "",
            ),
        )
        self.db.execute(
            """
            INSERT INTO equipment_maintenance(
                id,equipment_id,service_date,cost,expense_id
            ) VALUES(?,?,?,?,?)
            """,
            (1, 1, "2026-09-03", 50.0, maintenance_expense_id),
        )

        self.db.execute(
            "INSERT INTO inventory_items(id,name) VALUES(?,?)",
            (1, "Λίπασμα"),
        )
        receipt_expense_id = self.db.execute(
            """
            INSERT INTO expenses(
                entry_date,category,description,supplier,partner_id,
                payment_method,amount,notes
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                "2026-09-04",
                "Εφόδια",
                "Παραλαβή λιπάσματος",
                "Προμηθευτής Α",
                2,
                "Μετρητά",
                30.0,
                "",
            ),
        )
        self.db.execute(
            """
            INSERT INTO inventory_movements(
                id,item_id,movement_type,quantity,unit_price,total_cost,
                expense_id,partner_id
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (1, 1, "Παραλαβή", 3.0, 10.0, 30.0, receipt_expense_id, 2),
        )

    def _run_cross_module_checks(self) -> list[dict]:
        self.page.all_issues = []
        self.page._check_sales()
        self.page._check_sales_products()
        self.page._check_equipment_expenses()
        self.page._check_partner_links()
        self.page._check_inventory_receipt_expenses()
        return list(self.page.all_issues)

    def test_consistent_cross_module_links_are_clean(self) -> None:
        issues = self._run_cross_module_checks()
        self.assertEqual([], issues)

    def test_cross_module_drift_is_reported_without_mutating_data(self) -> None:
        sale_income_id = int(
            self.db.query_one(
                "SELECT income_id FROM production_sales WHERE id=1"
            )["income_id"]
        )
        maintenance_expense_id = int(
            self.db.query_one(
                "SELECT expense_id FROM equipment_maintenance WHERE id=1"
            )["expense_id"]
        )
        receipt_expense_id = int(
            self.db.query_one(
                "SELECT expense_id FROM inventory_movements WHERE id=1"
            )["expense_id"]
        )

        self.db.execute("DELETE FROM income WHERE id=?", (sale_income_id,))
        self.db.execute(
            "UPDATE expenses SET amount=? WHERE id=?",
            (60.0, maintenance_expense_id),
        )
        self.db.execute(
            "UPDATE expenses SET amount=?,partner_id=?,supplier=? WHERE id=?",
            (35.0, 1, "Παλιό όνομα", receipt_expense_id),
        )
        self.db.execute(
            "UPDATE production_sales SET product=? WHERE id=1",
            ("Άγνωστο προϊόν",),
        )

        before = {
            "sale": tuple(
                self.db.query_one(
                    "SELECT product,income_id FROM production_sales WHERE id=1"
                )
            ),
            "maintenance": tuple(
                self.db.query_one(
                    "SELECT cost,expense_id FROM equipment_maintenance WHERE id=1"
                )
            ),
            "receipt": tuple(
                self.db.query_one(
                    "SELECT total_cost,expense_id,partner_id FROM inventory_movements WHERE id=1"
                )
            ),
        }

        issues = self._run_cross_module_checks()
        problems = "\n".join(issue["problem"] for issue in issues)

        self.assertIn("Δεν βρέθηκε το αυτόματα συνδεδεμένο έσοδο", problems)
        self.assertIn("Το προϊόν «Άγνωστο προϊόν» δεν υπάρχει πλέον", problems)
        self.assertIn("Το αυτόματο έξοδο δεν συμφωνεί με το κόστος συντήρησης", problems)
        self.assertIn("Το αυτόματο έξοδο δεν συμφωνεί με το κόστος παραλαβής", problems)
        self.assertIn("Ο προμηθευτής της παραλαβής δεν συμφωνεί", problems)
        self.assertIn("Το αποθηκευμένο όνομα συνεργάτη", problems)

        after = {
            "sale": tuple(
                self.db.query_one(
                    "SELECT product,income_id FROM production_sales WHERE id=1"
                )
            ),
            "maintenance": tuple(
                self.db.query_one(
                    "SELECT cost,expense_id FROM equipment_maintenance WHERE id=1"
                )
            ),
            "receipt": tuple(
                self.db.query_one(
                    "SELECT total_cost,expense_id,partner_id FROM inventory_movements WHERE id=1"
                )
            ),
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
