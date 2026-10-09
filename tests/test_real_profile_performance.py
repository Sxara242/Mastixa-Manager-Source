"""First navigation must populate once; later external writes still refresh."""
import sqlite3
import unittest
from unittest.mock import patch

from app.annual_report import AnnualFarmReportPage
from app.settings import SettingsPage
from app.year_lock import YearLockPage
from app.partner_links import ensure_partner_link_schema
from tests.test_first_open_performance import FirstOpenPerformanceTests


class RealProfileNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FirstOpenPerformanceTests.setUpClass()

    def setUp(self):
        from tests.test_ui_revamp_phase1 import UiRevampTests
        self.case = UiRevampTests('test_small_window_scroll_and_dark_palette')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def test_reports_settings_and_year_lock_populate_once(self):
        for key,cls in [('annual_report',AnnualFarmReportPage),('settings',SettingsPage),('year_lock',YearLockPage)]:
            with self.subTest(page=key):
                calls=[]
                original=cls.refresh
                def counted(page,*args,**kwargs):
                    calls.append(page)
                    return original(page,*args,**kwargs)
                with patch.object(cls,'refresh',counted):
                    self.case.nav.open(key)
                    holder=self.case.window.pages[self.case.nav.targets[key].page][1]
                    page=holder.resolved_page()
                    # EnhancedYearLockPage refreshes again after adding its
                    # correction controls; that constructor refresh is required.
                    initial=2 if key=='year_lock' else 1
                    self.assertEqual([page]*initial,calls)
                    self.case.nav.open('home')
                    # An independent DB handle changes the required presentation token.
                    from app.database import Database
                    other=Database(self.case.db.path)
                    other.set_app_setting('farm_name','external QA farm '+key)
                    self.case.nav.open(key)
                    self.assertIs(page,holder.resolved_page())
                    self.assertEqual([page]*(initial+1),calls)
                    if key=='settings':
                        self.assertEqual('external QA farm '+key,page.farm_name.text())

    def test_partner_schema_retains_legacy_backfill_on_repeated_calls(self):
        db=self.case.db
        ensure_partner_link_schema(db)
        partner=db.execute("INSERT INTO business_partners(name) VALUES('QA supplier')")
        for index in range(2):
            record=db.execute("INSERT INTO expenses(entry_date,description,category,amount,supplier) VALUES('2027-09-17',?,'Other',4,' qa SUPPLIER ')",(str(index),))
            ensure_partner_link_schema(db)
            self.assertEqual(partner,db.query_one('SELECT partner_id FROM expenses WHERE id=?',(record,))['partner_id'])

    def test_partner_schema_error_rolls_back_backfill(self):
        db=self.case.db
        ensure_partner_link_schema(db)
        db.execute("INSERT INTO business_partners(name) VALUES('QA supplier')")
        record=db.execute("INSERT INTO expenses(entry_date,description,category,amount,supplier) VALUES('2027-09-17','QA','Other',4,'QA supplier')")
        db.execute('DROP TRIGGER partner_link_cleanup_before_delete')
        original=db.transaction
        from contextlib import contextmanager
        @contextmanager
        def failing_transaction():
            with original() as tx:
                execute=tx.execute
                def execute_until_cleanup(sql,params=()):
                    if 'CREATE TRIGGER IF NOT EXISTS partner_link_cleanup_before_delete' in sql:
                        raise sqlite3.OperationalError('injected schema failure')
                    return execute(sql,params)
                tx.execute=execute_until_cleanup
                yield tx
        with patch.object(db,'transaction',failing_transaction):
            with self.assertRaisesRegex(sqlite3.OperationalError,'injected schema failure'):
                ensure_partner_link_schema(db)
        self.assertIsNone(db.query_one('SELECT partner_id FROM expenses WHERE id=?',(record,))['partner_id'])
        ensure_partner_link_schema(db)
        self.assertIsNotNone(db.query_one('SELECT partner_id FROM expenses WHERE id=?',(record,))['partner_id'])

    def test_inventory_schema_failure_leaves_no_partial_catalog(self):
        from app.inventory import InventoryPage
        from app.database import Database
        from contextlib import contextmanager
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            db=Database(Path(folder)/'schema.db')
            original=db.transaction
            @contextmanager
            def failing_transaction():
                with original() as tx:
                    execute=tx.execute
                    def fail_movements(sql,params=()):
                        if 'CREATE TABLE IF NOT EXISTS inventory_movements' in sql:
                            raise sqlite3.OperationalError('injected inventory schema failure')
                        return execute(sql,params)
                    tx.execute=fail_movements
                    yield tx
            from types import SimpleNamespace
            owner=SimpleNamespace(db=db,_ensure_inventory_schema=InventoryPage._ensure_inventory_schema)
            with patch.object(db,'transaction',failing_transaction):
                with self.assertRaisesRegex(sqlite3.OperationalError,'injected inventory schema failure'):
                    InventoryPage._ensure_schema_and_audit_triggers(owner)
            self.assertIsNone(db.query_one("SELECT name FROM sqlite_master WHERE name='inventory_items'"))
            InventoryPage._ensure_schema_and_audit_triggers(owner)
            self.assertIsNotNone(db.query_one("SELECT name FROM sqlite_master WHERE name='inventory_items'"))


if __name__=='__main__':
    unittest.main()
