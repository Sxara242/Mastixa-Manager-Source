from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.expense_sync import delete_expense, ensure_expense_source_schema, sync_expense


class EquipmentMaintenanceAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Database(Path(self.tempdir.name) / "phase11b.db")
        self.db.execute(
            """
            CREATE TABLE equipment(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                brand_model TEXT NOT NULL DEFAULT '',
                equipment_code TEXT NOT NULL DEFAULT '',
                purchase_date TEXT,
                fuel TEXT NOT NULL DEFAULT '',
                meter_type TEXT NOT NULL DEFAULT 'hours',
                current_meter REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Ενεργό',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE equipment_maintenance(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                service_date TEXT NOT NULL,
                service_type TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0,
                meter_value REAL NOT NULL DEFAULT 0,
                technician TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                next_service_date TEXT,
                next_service_meter REAL,
                expense_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE RESTRICT
            )
            """
        )
        ensure_expense_source_schema(self.db)
        self.equipment_id = int(
            self.db.execute(
                """
                INSERT INTO equipment(
                    name,category,equipment_code,meter_type,current_meter,status
                ) VALUES('Τρακτέρ','Τρακτέρ','EQ-11','hours',100,'Ενεργό')
                """
            )
        )

    def _service(self, *, cost: float = 75, meter: float = 120) -> int:
        return int(
            self.db.execute(
                """
                INSERT INTO equipment_maintenance(
                    equipment_id,service_date,service_type,cost,meter_value,
                    technician,notes,next_service_date,next_service_meter
                ) VALUES(?, '2026-09-11', 'Τακτικό service', ?, ?,
                         'Service Test', 'phase11', '2026-10-01', 160)
                """,
                (self.equipment_id, cost, meter),
            )
        )

    def _expense(self, service_id: int):
        return self.db.query_one(
            """
            SELECT * FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=?
            ORDER BY id LIMIT 1
            """,
            (service_id,),
        )

    def test_service_statement_projects_expense_and_advances_meter(self) -> None:
        service_id = self._service()
        expense = self._expense(service_id)
        self.assertIsNotNone(expense)
        self.assertAlmostEqual(75.0, float(expense["amount"]))
        self.assertEqual("Service Test", expense["supplier"])
        self.assertEqual(
            "Τακτικό service — Τρακτέρ",
            expense["description"],
        )
        self.assertAlmostEqual(
            120.0,
            float(
                self.db.query_one(
                    "SELECT current_meter FROM equipment WHERE id=?",
                    (self.equipment_id,),
                )["current_meter"]
            ),
        )

        expense_id = int(expense["id"])
        self.db.execute(
            """
            UPDATE equipment_maintenance
            SET cost=90,meter_value=110,technician='Service Edited',notes='edited'
            WHERE id=?
            """,
            (service_id,),
        )
        expense = self._expense(service_id)
        self.assertEqual(expense_id, int(expense["id"]))
        self.assertAlmostEqual(90.0, float(expense["amount"]))
        self.assertEqual("Service Edited", expense["supplier"])
        self.assertAlmostEqual(
            120.0,
            float(
                self.db.query_one(
                    "SELECT current_meter FROM equipment WHERE id=?",
                    (self.equipment_id,),
                )["current_meter"]
            ),
        )

        # Existing UI compatibility calls are idempotent after trigger projection.
        self.assertEqual(
            expense_id,
            sync_expense(
                self.db,
                source_type="equipment_maintenance",
                source_id=service_id,
                entry_date="2026-09-11",
                category="Μηχανήματα & Συντήρηση",
                description="Τακτικό service — Τρακτέρ",
                supplier="Service Edited",
                payment_method="",
                amount=90,
                notes="compatibility",
            ),
        )
        count = self.db.query_one(
            """
            SELECT COUNT(*) AS total FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=?
            """,
            (service_id,),
        )
        self.assertEqual(1, int(count["total"]))

    def test_expense_failure_rolls_back_service_and_meter(self) -> None:
        self.db.execute(
            """
            CREATE TRIGGER reject_service_expense
            BEFORE INSERT ON expenses
            WHEN NEW.source_type='equipment_maintenance'
            BEGIN
                SELECT RAISE(ABORT, 'forced_service_expense_failure');
            END
            """
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "forced_service_expense_failure",
        ):
            self._service(cost=50, meter=150)

        self.assertEqual(
            0,
            int(
                self.db.query_one(
                    "SELECT COUNT(*) AS total FROM equipment_maintenance"
                )["total"]
            ),
        )
        self.assertAlmostEqual(
            100.0,
            float(
                self.db.query_one(
                    "SELECT current_meter FROM equipment WHERE id=?",
                    (self.equipment_id,),
                )["current_meter"]
            ),
        )

    def test_delete_is_source_owned_and_atomic(self) -> None:
        service_id = self._service(cost=60)
        self.assertIsNotNone(self._expense(service_id))

        # Legacy UI calls this first. The expense must stay until source deletion.
        delete_expense(
            self.db,
            source_type="equipment_maintenance",
            source_id=service_id,
        )
        self.assertIsNotNone(self._expense(service_id))

        self.db.execute(
            """
            CREATE TRIGGER reject_service_expense_delete
            BEFORE DELETE ON expenses
            WHEN OLD.source_type='equipment_maintenance'
            BEGIN
                SELECT RAISE(ABORT, 'forced_service_delete_failure');
            END
            """
        )
        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "forced_service_delete_failure",
        ):
            self.db.execute(
                "DELETE FROM equipment_maintenance WHERE id=?", (service_id,)
            )
        self.assertIsNotNone(
            self.db.query_one(
                "SELECT id FROM equipment_maintenance WHERE id=?", (service_id,)
            )
        )
        self.assertIsNotNone(self._expense(service_id))

        self.db.execute("DROP TRIGGER reject_service_expense_delete")
        self.db.execute(
            "DELETE FROM equipment_maintenance WHERE id=?", (service_id,)
        )
        self.assertIsNone(self._expense(service_id))

    def test_meter_type_is_locked_after_service_history(self) -> None:
        # Without history a meter type correction is allowed.
        self.db.execute(
            "UPDATE equipment SET meter_type='km' WHERE id=?",
            (self.equipment_id,),
        )
        self.db.execute(
            "UPDATE equipment SET meter_type='hours' WHERE id=?",
            (self.equipment_id,),
        )
        self._service(cost=0)

        with self.assertRaisesRegex(
            sqlite3.IntegrityError,
            "equipment_meter_type_locked",
        ):
            self.db.execute(
                "UPDATE equipment SET meter_type='km' WHERE id=?",
                (self.equipment_id,),
            )
        self.assertEqual(
            "hours",
            self.db.query_one(
                "SELECT meter_type FROM equipment WHERE id=?",
                (self.equipment_id,),
            )["meter_type"],
        )


if __name__ == "__main__":
    unittest.main()
