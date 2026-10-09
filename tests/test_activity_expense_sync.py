"""Farm activity financial projections: real workflows and committed DB state."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.activities import ActivitiesPage
from app.audit import AuditPage
from app.backup_manager import BackupManager
from app.database import Database
from app.declaration import DeclarationPage
from app.expense_sync import ensure_expense_source_schema
from app.inventory import InventoryPage
from app.inventory_sync import current_stock
from app.money import MoneyPage
from app.profile_manager import ProfileManager
from app.upload_center import UploadCenterPage
from app import year_context
from app.year_lock import ensure_year_lock_schema
from tests.language_fixture import scoped_language


class ActivityExpenseSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.enterContext(scoped_language(self.qt, "el"))
        properties = ("mastixaActiveWorkingYear", "mastixaEffectiveWorkingYear", "mastixaCorrectionYear", "mastixaCorrectionReason")
        previous = {key: self.qt.property(key) for key in properties}
        self.addCleanup(lambda: [self.qt.setProperty(key, value) for key, value in previous.items()])
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.db = Database(self.root / "activity.db")
        ensure_year_lock_schema(self.db)
        ensure_expense_source_schema(self.db)
        year_context.set_active_working_year(self.db, 2027, audit=False)
        self.addCleanup(year_context.initialize_year_context, self.db)
        self.enterContext(patch.object(QMessageBox, "warning", side_effect=AssertionError("unexpected warning")))
        self.enterContext(patch.object(QMessageBox, "exec", side_effect=AssertionError("unexpected modal")))
        self.field = self.db.execute("INSERT INTO fields(name) VALUES('QA FIELD 01 EDIT')")
        # Match startup order so the real audit triggers have their source tables.
        self.keep(DeclarationPage(self.db))
        self.keep(UploadCenterPage(self.db))
        self.keep(AuditPage(self.db))
        self.keep(InventoryPage(self.db))  # Normal desktop startup initializes supplies first.
        self.page = self.keep(ActivitiesPage(self.db))
        self.configure()

    def keep(self, page):
        self.addCleanup(page.deleteLater)
        self.addCleanup(page.close)
        page.confirm_delete = lambda *_: True
        return page

    def configure(self, cost=5, page=None, field=None):
        page = page or self.page
        page.date.setDate(QDate(2027, 10, 3))
        page.field.setCurrentIndex(page.field.findData(self.field if field is None else field))
        page.category.setCurrentIndex(page.category.findData("irrigation"))
        page.duration.setValue(30)
        page.cost.setValue(cost)
        page.notes.setText("raw {year} / σημείωση")

    def create(self, cost=5):
        self.configure(cost)
        self.page.save_activity()
        return int(self.db.query_one("SELECT MAX(id) FROM farm_activities")[0])

    def load(self, record):
        self.page.refresh()
        for row in range(self.page.table.rowCount()):
            if self.page.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == record:
                self.page.load_selected(row, 0)
                return
        self.fail("Activity missing from table")

    def expenses(self, record, db=None):
        return (db or self.db).query("SELECT * FROM expenses WHERE source_type='farm_activity' AND source_id=?", (record,))

    def expense(self, record, db=None):
        rows = self.expenses(record, db)
        self.assertEqual(1, len(rows))
        return rows[0]

    def snapshot(self, db=None):
        with closing(sqlite3.connect((db or self.db).path)) as con:
            return tuple(con.iterdump())

    def test_create_positive_cost_metadata_and_money_ownership(self):
        record = self.create()
        expense = self.expense(record)
        self.assertEqual(("2027-10-03", 5, self.field, "Άρδευση"), tuple(expense[k] for k in ("entry_date", "amount", "field_id", "category")))
        self.assertIn("Πότισμα", expense["description"])
        self.assertIn(f"#{record}", expense["notes"])
        self.assertIn("raw {year} / σημείωση", expense["notes"])
        money = self.keep(MoneyPage(self.db, "expenses"))
        self.assertEqual(1, money.table.rowCount())
        money.load_selected(0, 0)
        self.assertFalse(money.save_button.isEnabled())
        self.assertFalse(money.delete_button.isEnabled())

    def test_zero_cost_creates_no_expense(self):
        record = self.create(0)
        self.assertEqual([], self.expenses(record))
        self.assertEqual(0, self.db.query_one("SELECT cost FROM farm_activities WHERE id=?", (record,))[0])

    def test_repeated_edit_and_reopen_preserve_expense_identity(self):
        record = self.create()
        expense_id = self.expense(record)["id"]
        for cost in (6, 7, 7):
            self.load(record)
            self.page.cost.setValue(cost)
            self.page.save_activity()
            expense = self.expense(record)
            self.assertEqual((expense_id, cost), (expense["id"], expense["amount"]))
        reopened = Database(self.db.path)
        self.page = self.keep(ActivitiesPage(reopened))
        self.load(record)
        self.page.save_activity()
        self.assertEqual(expense_id, self.expense(record, reopened)["id"])
        self.assertEqual(1, reopened.query_one("SELECT COUNT(*) FROM expenses")[0])

    def test_date_and_metadata_edit(self):
        record = self.create()
        expense_id = self.expense(record)["id"]
        other_field = self.db.execute("INSERT INTO fields(name) VALUES('Other raw field')")
        self.load(record)
        self.page.date.setDate(QDate(2028, 2, 4))
        self.page.field.setCurrentIndex(self.page.field.findData(other_field))
        self.page.category.setCurrentIndex(self.page.category.findData("fertilization"))
        self.page.product.setEditText("Raw <product> {year}")
        self.page.dose.setValue(2)
        self.page.notes.setText("Changed raw note")
        self.page.save_activity()
        expense = self.expense(record)
        self.assertEqual((expense_id, "2028-02-04", other_field, "Λίπανση"), tuple(expense[k] for k in ("id", "entry_date", "field_id", "category")))
        self.assertIn("Raw <product> {year}", expense["description"])
        self.assertIn("Changed raw note", expense["notes"])
        self.page.year_filter.setCurrentIndex(self.page.year_filter.findData(2028))
        self.load(record)
        self.page.field.setCurrentIndex(0)
        self.page.save_activity()
        self.assertIsNone(self.expense(record)["field_id"])

    def test_positive_zero_positive_transition(self):
        record = self.create()
        self.load(record)
        self.page.cost.setValue(0)
        self.page.save_activity()
        self.assertEqual([], self.expenses(record))
        self.load(record)
        self.page.cost.setValue(9)
        self.page.save_activity()
        self.assertEqual(9, self.expense(record)["amount"])

    def test_delete_removes_only_owned_expense(self):
        record = self.create()
        other = self.create(8)
        manual = self.db.execute("INSERT INTO expenses(entry_date,category,description,amount) VALUES('2027-10-03','Άρδευση','Πότισμα',5)")
        self.load(record)
        self.page.delete_activity()
        self.assertIsNone(self.db.query_one("SELECT id FROM farm_activities WHERE id=?", (record,)))
        self.assertEqual([], self.expenses(record))
        self.assertEqual(8, self.expense(other)["amount"])
        self.assertIsNotNone(self.db.query_one("SELECT id FROM expenses WHERE id=?", (manual,)))

    def failure(self, action, table, event):
        self.db.execute(f"CREATE TRIGGER injected BEFORE {event} ON {table} BEGIN SELECT RAISE(ABORT,'injected'); END")
        before = self.snapshot()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "injected"):
            action()
        self.assertEqual(before, self.snapshot(), "Every persisted row, audit event and sequence must roll back")
        self.db.execute("DROP TRIGGER injected")
        action()

    def test_expense_create_failure_rolls_back_and_retries(self):
        self.failure(self.page.save_activity, "expenses", "INSERT")
        self.assertEqual(1, len(self.db.query("SELECT * FROM farm_activities")))
        self.expense(1)

    def test_expense_update_failure_rolls_back_and_retries(self):
        record = self.create()
        self.load(record)
        self.page.cost.setValue(9)
        self.failure(self.page.save_activity, "expenses", "UPDATE")
        self.assertEqual(9, self.expense(record)["amount"])

    def test_expense_delete_failure_rolls_back_activity_delete(self):
        record = self.create()
        self.load(record)
        self.failure(self.page.delete_activity, "expenses", "DELETE")
        self.assertEqual([], self.expenses(record))

    def test_expense_delete_failure_rolls_back_zero_cost(self):
        record = self.create()
        self.load(record)
        self.page.cost.setValue(0)
        self.failure(self.page.save_activity, "expenses", "DELETE")
        self.assertEqual([], self.expenses(record))

    def test_activity_delete_failure_preserves_expense(self):
        record = self.create()
        self.load(record)
        self.failure(self.page.delete_activity, "farm_activities", "DELETE")
        self.assertEqual([], self.expenses(record))

    def lock(self, year):
        self.db.execute("INSERT OR REPLACE INTO year_locks(year,is_locked,reason) VALUES(?,1,'physical')", (year,))

    def blocked(self, action):
        before = self.snapshot()
        with patch("app.activities.warn_locked_year") as warning:
            action()
        warning.assert_called_once()
        self.assertEqual(before, self.snapshot())

    def test_locked_create_correction_other_year_and_restart(self):
        self.lock(2027)
        self.lock(2026)
        self.blocked(self.page.save_activity)
        # Rejected new entries intentionally reset their draft; re-enter it
        # before testing the authorized correction write.
        self.assertEqual('', self.page.notes.text())
        self.assertEqual(0, self.page.cost.value())
        year_context.begin_year_correction(self.db, 2027, "raw reason")
        self.configure()
        self.page.save_activity()
        self.assertEqual(5, self.expense(1)["amount"])
        self.assertTrue(year_context.is_year_physically_locked(self.db, 2027))
        self.configure()
        self.page.date.setDate(QDate(2026, 10, 3))
        self.blocked(self.page.save_activity)
        year_context.initialize_year_context(Database(self.db.path))
        self.load(1)
        self.blocked(self.page.save_activity)
        self.blocked(self.page.delete_activity)

    def test_cross_year_edit_checks_source_and_target(self):
        record = self.create()
        self.load(record)
        self.lock(2026)
        self.page.date.setDate(QDate(2026, 10, 3))
        self.blocked(self.page.save_activity)
        self.lock(2027)
        self.page.date.setDate(QDate(2028, 10, 3))
        self.blocked(self.page.save_activity)
        year_context.begin_year_correction(self.db, 2027, "correct source")
        self.page.save_activity()
        self.assertEqual("2028-10-03", self.expense(record)["entry_date"])

    def test_correction_edit_zero_restore_and_delete(self):
        record = self.create()
        expense_id = self.expense(record)["id"]
        self.lock(2027)
        year_context.begin_year_correction(self.db, 2027, "raw reason")
        self.load(record)
        self.page.cost.setValue(6)
        self.page.save_activity()
        self.assertEqual((expense_id, 6), tuple(self.expense(record)[k] for k in ("id", "amount")))
        self.load(record)
        self.page.cost.setValue(0)
        self.page.save_activity()
        self.assertEqual([], self.expenses(record))
        self.load(record)
        self.page.cost.setValue(7)
        self.page.save_activity()
        self.expense(record)
        self.load(record)
        self.page.delete_activity()
        self.assertEqual([], self.expenses(record))
        self.assertTrue(year_context.is_year_physically_locked(self.db, 2027))

    def test_activity_and_expense_audit_events_commit_together(self):
        record = self.create()
        expense_id = self.expense(record)["id"]
        self.load(record)
        self.page.cost.setValue(6)
        self.page.save_activity()
        self.load(record)
        self.page.delete_activity()
        for table, identity in (("farm_activities", record), ("expenses", expense_id)):
            actions = self.db.query("SELECT action FROM audit_events WHERE table_name=? AND record_id=? ORDER BY id", (table, str(identity)))
            self.assertEqual(["INSERT", "UPDATE", "DELETE"], [row["action"] for row in actions])

    def test_legacy_cost_row_read_only_until_explicit_save_no_fuzzy_link(self):
        record = self.db.execute("INSERT INTO farm_activities(activity_date,field_id,category,duration_minutes,cost) VALUES('2027-10-03',?,'Πότισμα',30,5)", (self.field,))
        manual = self.db.execute("INSERT INTO expenses(entry_date,category,description,amount) VALUES('2027-10-03','Άρδευση','Πότισμα',5)")
        before = self.snapshot()
        self.load(record)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], self.expenses(record))
        self.page.save_activity()
        self.assertNotEqual(manual, self.expense(record)["id"])
        self.assertEqual(2, self.db.query_one("SELECT COUNT(*) FROM expenses")[0])

    def test_profile_isolation_and_package_round_trip(self):
        manager = ProfileManager(self.root / "profiles")
        source = manager.create("Source")
        target = manager.create("Other")
        source_db = Database(source.database_path)
        year_context.set_active_working_year(source_db, 2027, audit=False)
        field = source_db.execute("INSERT INTO fields(name) VALUES('Source field')")
        self.keep(InventoryPage(source_db))
        source_page = self.keep(ActivitiesPage(source_db))
        self.configure(page=source_page, field=field)
        source_page.save_activity()
        source_expense = dict(self.expense(1, source_db))
        other_db = Database(target.database_path)
        self.keep(ActivitiesPage(other_db))
        self.assertEqual([], other_db.query("SELECT * FROM farm_activities"))
        self.assertEqual([], other_db.query("SELECT * FROM expenses"))
        package = manager.export_profile(source.id, self.root / "roundtrip")
        imported = manager.import_profile(package)
        imported_db = Database(imported.database_path)
        self.assertEqual(source_expense, dict(self.expense(1, imported_db)))
        imported_page = self.keep(ActivitiesPage(imported_db))
        imported_page.load_selected(0, 0)
        imported_page.cost.setValue(8)
        imported_page.save_activity()
        self.assertEqual(8, self.expense(1, imported_db)["amount"])
        self.assertEqual(source_expense, dict(self.expense(1, source_db)))

    def test_database_backup_restore_preserves_linkage(self):
        record = self.create()
        expected = dict(self.expense(record))
        backup = BackupManager(self.db.path, self.root / "backups")
        archive = backup.create_backup(prefix="batch2")
        self.load(record)
        self.page.delete_activity()
        backup.restore_backup(archive)
        self.db.initialize()
        self.assertEqual(expected, dict(self.expense(record)))
        self.load(record)
        self.page.cost.setValue(12)
        self.page.save_activity()
        self.assertEqual((expected["id"], 12), tuple(self.expense(record)[k] for k in ("id", "amount")))

    def test_consumption_and_expense_share_rollback(self):
        self.keep(InventoryPage(self.db))
        item = self.db.execute("INSERT INTO inventory_items(name,category,unit) VALUES('Raw supply','Λίπασμα','kg')")
        self.db.execute("INSERT INTO inventory_movements(movement_date,item_id,movement_type,quantity) VALUES('2027-01-01',?,'Παραλαβή',10)", (item,))
        self.page.refresh()
        self.configure()
        self.page.category.setCurrentIndex(self.page.category.findData("fertilization"))
        self.page.product.setEditText("Raw supply")
        self.page.dose.setValue(1)
        self.page.inventory_item.setCurrentIndex(self.page.inventory_item.findData(item))
        self.page.inventory_quantity.setValue(2)
        self.failure(self.page.save_activity, "expenses", "INSERT")
        self.assertEqual(8, current_stock(self.db, item))
        self.expense(1)
        self.load(1)
        self.failure(self.page.delete_activity, "expenses", "DELETE")
        self.assertEqual(10, current_stock(self.db, item))

    def test_python_sync_failure_rolls_back(self):
        before = self.snapshot()
        with patch("app.activities.sync_expense", side_effect=RuntimeError("sync failed")), self.assertRaisesRegex(RuntimeError, "sync failed"):
            self.page.save_activity()
        self.assertEqual(before, self.snapshot())
