"""Batch 4 source attribution, pooled limits, atomicity and report reconciliation."""
from contextlib import closing
from pathlib import Path
import csv
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from app.database import Database
from app.sales import SalesPage
from app.production import ProductionPage
from app.sales_report import SalesReportPage
from app.annual_report import AnnualFarmReportPage
from app.field_finance import FieldFinancePage
from app.report_quantities import sale_availability, sale_source_quantities
from app.backup_manager import BackupManager
from app.profile_manager import ProfileManager
from app.settings import SettingsPage
from app import year_context
from app.year_lock import ensure_year_lock_schema
from tests.language_fixture import scoped_language


class SaleSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = self.enterContext(scoped_language(self.qt, "el"))
        keys = ("mastixaActiveWorkingYear", "mastixaEffectiveWorkingYear", "mastixaCorrectionYear", "mastixaCorrectionReason")
        old = {key: self.qt.property(key) for key in keys}
        self.addCleanup(lambda: [self.qt.setProperty(k,v) for k,v in old.items()])
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.manager = ProfileManager(self.root / "profiles")
        self.db = Database(self.manager.active_profile.database_path)
        ensure_year_lock_schema(self.db)
        year_context.set_active_working_year(self.db, 2027, audit=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY,event_time TEXT,table_name TEXT,action TEXT,record_id TEXT,details TEXT)")
        self.a = self.db.execute("INSERT INTO fields(name) VALUES('Field A')")
        self.b = self.db.execute("INSERT INTO fields(name) VALUES('Field B')")
        self.kg = self.db.execute("INSERT INTO products(name,unit) VALUES('Mastixa','kg')")
        self.pieces = self.db.execute("INSERT INTO products(name,unit) VALUES('QA','pieces')")
        for product, name, field, qty in ((self.kg,'Mastixa',self.a,10),(self.kg,'Mastixa',self.b,10),(self.pieces,'QA',self.a,8)):
            self.db.execute("INSERT INTO production(entry_date,product_id,product,field_id,quantity_kg) VALUES('2026-01-01',?,?,?,?)",(product,name,field,qty))
        self.page = self.keep(SalesPage(self.db))
        self.buyer = self.db.execute("INSERT INTO business_partners(name,partner_type) VALUES('Buyer','buyer')")
        self.page.refresh()
        self.configure()
        self.enterContext(patch.object(QMessageBox, 'warning', side_effect=AssertionError('Unexpected warning')))
        self.enterContext(patch.object(QMessageBox, 'exec', side_effect=AssertionError('Unexpected modal')))

    def keep(self, page):
        page.confirm_delete = lambda *_: True
        self.addCleanup(page.deleteLater)
        self.addCleanup(page.close)
        return page

    def choose(self, combo, value):
        index = combo.findData(value)
        self.assertGreaterEqual(index,0,repr(value))
        combo.setCurrentIndex(index)

    def configure(self, source=None, qty=4, product=None):
        self.choose(self.page.product, product or self.kg)
        self.choose(self.page.buyer, self.buyer)
        self.choose(self.page.source, source)
        self.page.quantity.setValue(qty)
        self.page.price_per_kg.setValue(3)
        self.page.sale_date.setDate(QDate(2027,10,4))

    def create(self, source=None, qty=4, product=None):
        self.page.clear_form()
        self.configure(source,qty,product)
        self.page.save_sale()
        return self.db.query_one('SELECT MAX(id) FROM production_sales')[0]

    def row(self, identity):
        return dict(self.db.query_one('SELECT * FROM production_sales WHERE id=?',(identity,)))

    def income(self, identity):
        return dict(self.db.query_one('SELECT * FROM income WHERE id=?',(self.row(identity)['income_id'],)))

    def load(self, identity):
        self.page.refresh()
        for row in range(self.page.table.rowCount()):
            if self.page.table.item(row,0).data(Qt.ItemDataRole.UserRole)==identity:
                self.page.load_sale(row,0)
                return
        self.fail('Missing sale')

    def snapshot(self):
        with closing(sqlite3.connect(self.db.path)) as con:
            return tuple(con.iterdump())

    def reject(self):
        before=self.snapshot()
        with patch('app.sales._message') as warning:
            self.page.save_sale()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())

        return warning

    def test_legacy_additive_migration_is_pooled_without_data_loss(self):
        legacy=Database(self.root/'legacy.db')
        legacy.execute('CREATE TABLE production_sales(id INTEGER PRIMARY KEY,product_id INTEGER,product TEXT,sale_date TEXT,quantity_kg REAL,total_amount REAL)')
        legacy.execute("INSERT INTO production_sales VALUES(42,NULL,'raw','2020-01-01',2,7)")
        legacy=Database(legacy.path)
        row=dict(legacy.query_one('SELECT * FROM production_sales'))
        self.assertEqual((42,'raw',2,7,None,''),tuple(row[k] for k in ('id','product','quantity_kg','total_amount','source_field_id','source_field_name')))
        _,sales,_=sale_source_quantities(legacy,source='pooled')
        self.assertEqual(2,sales[0]['quantity'])
        before=tuple(legacy.query_one('SELECT * FROM production_sales'))
        legacy.initialize()
        self.assertEqual(before,tuple(legacy.query_one('SELECT * FROM production_sales')))

    def test_pooled_create_has_no_field_and_reduces_only_total(self):
        identity=self.create(qty=15)
        self.assertIsNone(self.row(identity)['source_field_id'])
        self.assertIsNone(self.income(identity)['field_id'])
        self.assertEqual(5,sale_availability(self.db,self.kg))
        for field in (self.a,self.b):
            _,sales,stock=sale_source_quantities(self.db,self.kg,source=field)
            self.assertEqual([],sales)
            self.assertEqual(10,stock[0]['quantity'])
            self.assertEqual(5,sale_availability(self.db,self.kg,field))

    def test_field_create_identity_and_linked_income(self):
        identity=self.create(self.a)
        self.assertEqual((self.a,'Field A'),tuple(self.row(identity)[k] for k in ('source_field_id','source_field_name')))
        self.assertEqual(self.a,self.income(identity)['field_id'])
        self.assertEqual(6,sale_availability(self.db,self.kg,self.a))
        self.assertEqual(10,sale_availability(self.db,self.kg,self.b))

    def test_field_cap_rejects_without_writes(self):
        self.configure(self.a,11)
        self.reject()

    def test_production_edit_cannot_invalidate_explicit_field_sales(self):
        self.create(self.a,4)
        production=self.keep(ProductionPage(self.db))
        production.selected_production_id=self.db.query_one('SELECT id FROM production WHERE product_id=? AND field_id=?',(self.kg,self.a))[0]
        self.choose(production.product,self.kg)
        self.choose(production.field,self.a)
        production.date.setDate(QDate(2026,1,1))
        production.quantity.setValue(1)
        before=self.snapshot()
        with patch('app.production._message') as warning:
            production.save_production()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())

        # A field move, product change or deletion also releases old production.
        production.quantity.setValue(10)
        self.choose(production.field,self.b)
        with patch('app.production._message') as warning:
            production.save_production()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())
        self.choose(production.field,self.a)
        self.choose(production.product,self.pieces)
        with patch('app.production._message') as warning:
            production.save_production()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())
        with patch('app.production._message') as warning:
            production.delete_production()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())
        self.choose(production.product,self.kg)
        production.quantity.setValue(4)
        production.save_production()
        self.assertEqual(0,sale_availability(self.db,self.kg,self.a))

    def test_total_cap_after_pooled_sale_and_source_labels(self):
        self.create(qty=15)
        self.configure(self.a,6)
        self.assertIn('5 kg',self.page.source.currentText())
        self.reject()
        self.page.quantity.setValue(5)
        self.page.save_sale()
        self.assertEqual(0,sale_availability(self.db,self.kg))

    def test_transaction_rechecks_availability_without_partial_writes(self):
        self.create(qty=15)
        self.configure(qty=6)
        with patch.object(self.page,'_available_for_sale',return_value=20):
            self.reject()

    def test_field_numeric_tolerance_matches_total_guard(self):
        self.configure(self.a,4)
        self.db.execute('UPDATE production SET quantity_kg=3.999998 WHERE product_id=? AND field_id=?',(self.kg,self.a))
        self.reject()
        self.db.execute('UPDATE production SET quantity_kg=3.9999995 WHERE product_id=? AND field_id=?',(self.kg,self.a))
        self.page.save_sale()
        self.assertEqual(4,self.row(1)['quantity_kg'])

    def test_report_year_buyer_search_and_source_compose(self):
        self.create(self.a,4)
        other=self.create(self.b,3)
        self.load(other)
        self.page.sale_date.setDate(QDate(2028,1,1))
        self.page.notes.setText('other year')
        self.page.save_sale()
        report=self.keep(SalesReportPage(self.db))
        self.choose(report.year_filter,'2027')
        self.choose(report.product_filter,self.kg)
        self.choose(report.buyer_filter,self.buyer)
        self.choose(report.source_filter,self.a)
        self.assertEqual('4 kg',report.sold_metric[1].text())
        self.assertEqual('6 kg',report.stock_metric[1].text())
        report.search.setText('does not match')
        self.assertEqual(0,report.detail_table.rowCount())
        self.assertEqual('0,00 €',report.revenue_metric[1].text())
        report.search.clear()
        self.assertEqual(1,report.detail_table.rowCount())

    def test_edit_quantity_excludes_current_sale(self):
        identity=self.create(self.a)
        self.load(identity)
        self.assertIn('10 kg',self.page.source.currentText())
        self.page.quantity.setValue(8)
        self.page.save_sale()
        self.assertEqual(8,self.row(identity)['quantity_kg'])
        self.assertEqual(24,self.income(identity)['amount'])

    def test_switch_field_releases_old_and_validates_new(self):
        identity=self.create(self.a,8)
        self.create(self.b,5)
        self.load(identity)
        self.choose(self.page.source,self.b)
        self.reject()
        self.page.quantity.setValue(5)
        self.page.save_sale()
        self.assertEqual(self.b,self.row(identity)['source_field_id'])
        self.assertEqual(10,sale_availability(self.db,self.kg,self.a))
        self.assertEqual(0,sale_availability(self.db,self.kg,self.b))

    def test_field_to_total_and_back_preserves_income_identity(self):
        identity=self.create(self.a)
        income=self.income(identity)['id']
        for source in (None,self.b,self.a):
            self.load(identity)
            self.choose(self.page.source,source)
            self.page.save_sale()
            self.assertEqual(source,self.row(identity)['source_field_id'])
            self.assertEqual(source,self.income(identity)['field_id'])
            self.assertEqual(income,self.income(identity)['id'])
        self.assertEqual(1,self.db.query_one('SELECT COUNT(*) FROM income')[0])

    def test_edit_product_metadata_and_date(self):
        identity=self.create(self.a)
        self.load(identity)
        self.choose(self.page.product,self.pieces)
        self.choose(self.page.source,self.a)
        self.page.price_per_kg.setValue(7)
        self.page.notes.setText('raw notes')
        self.page.payment.setCurrentIndex(2)
        self.page.sale_date.setDate(QDate(2028,2,3))
        buyer=self.db.execute("INSERT INTO business_partners(name,partner_type) VALUES('Other','buyer')")
        self.page._refresh_buyers()
        self.choose(self.page.buyer,buyer)
        self.page.save_sale()
        self.assertEqual((self.pieces,28,'2028-02-03','raw notes','Other'),tuple(self.row(identity)[k] for k in ('product_id','total_amount','sale_date','notes','buyer_name')))
        self.assertEqual(20,sale_availability(self.db,self.kg))
        self.assertEqual(4,sale_availability(self.db,self.pieces,self.a))

    def test_delete_field_and_pooled_releases_availability(self):
        for source in (self.a,None):
            identity=self.create(source)
            self.load(identity)
            self.page.delete_sale()
            self.assertEqual(20,sale_availability(self.db,self.kg))
            self.assertEqual(10,sale_availability(self.db,self.kg,self.a))
            self.assertEqual(0,self.db.query_one('SELECT COUNT(*) FROM income')[0])

    def rollback(self, operation):
        if operation!='create':
            identity=self.create(self.a)
            self.load(identity)
            self.choose(self.page.source,self.b)
        else:
            self.configure(self.a)
        table='production_sales' if operation=='delete' else 'income'
        event={'create':'INSERT','update':'UPDATE','delete':'DELETE'}[operation]
        self.db.execute(f"CREATE TRIGGER injected BEFORE {event} ON {table} BEGIN SELECT RAISE(ABORT,'injected'); END")
        before=self.snapshot()
        action=self.page.delete_sale if operation=='delete' else self.page.save_sale
        with self.assertRaisesRegex(sqlite3.IntegrityError,'injected'):
            action()
        self.assertEqual(before,self.snapshot())
        self.db.execute('DROP TRIGGER injected')
        action()
        if operation!='delete':
            self.assertEqual(1,self.db.query_one('SELECT COUNT(*) FROM production_sales s JOIN income i ON s.income_id=i.id AND s.source_field_id=i.field_id')[0])

    def test_create_rollback(self): self.rollback('create')
    def test_update_rollback(self): self.rollback('update')
    def test_delete_rollback(self): self.rollback('delete')

    def test_locked_year_correction_and_cross_year_edit(self):
        for year in (2026,2027):
            self.db.execute("INSERT INTO year_locks(year,is_locked,reason) VALUES(?,1,'locked')",(year,))
        self.configure(self.a)
        before=self.snapshot()
        with patch('app.sales.warn_locked_year') as warning:
            self.page.save_sale()
        warning.assert_called_once()
        self.assertEqual(before,self.snapshot())
        # The accepted rejected-create behavior clears the draft. Re-enter it
        # before testing correction; retain all lock/cross-year assertions.
        self.assertIsNone(self.page.selected_sale_id)
        self.assertEqual(0, self.page.quantity.value())
        self.configure(self.a)
        year_context.begin_year_correction(self.db,2027,'reason')
        self.page.save_sale()
        self.load(1)
        self.page.sale_date.setDate(QDate(2026,1,1))
        with patch('app.sales.warn_locked_year') as warning:
            self.page.save_sale()
        warning.assert_called_once()
        self.assertEqual('2027-10-04',self.row(1)['sale_date'])
        year_context.initialize_year_context(self.db)
        self.page.sale_date.setDate(QDate(2028,1,1))
        with patch('app.sales.warn_locked_year') as warning:
            self.page.save_sale()
        warning.assert_called_once()
        with patch('app.sales.warn_locked_year') as warning:
            self.page.delete_sale()
        warning.assert_called_once()

    def test_units_choices_and_product_switch(self):
        self.choose(self.page.product,self.pieces)
        self.assertEqual(-1,self.page.source.findData(self.b))
        self.choose(self.page.source,self.a)
        self.assertIn('8 pieces',self.page.source.currentText())
        self.page.quantity.setValue(9)
        warning=self.reject()
        self.assertEqual('8 pieces',warning.call_args.kwargs['value1'])

    def test_report_field_pool_and_total_reconciliation(self):
        self.create(self.a,4)
        self.create(self.b,3)
        self.create(None,5)
        report=self.keep(SalesReportPage(self.db))
        self.choose(report.product_filter,self.kg)
        self.assertEqual('12 kg',report.sold_metric[1].text())
        self.assertEqual('8 kg',report.stock_metric[1].text())
        self.assertEqual('36,00 €',report.revenue_metric[1].text())
        for source,sold,revenue,stock in ((self.a,'4 kg','12,00 €','6 kg'),(self.b,'3 kg','9,00 €','7 kg'),('pooled','5 kg','15,00 €','—')):
            self.choose(report.source_filter,source)
            self.assertEqual(sold,report.sold_metric[1].text())
            self.assertEqual(revenue,report.revenue_metric[1].text())
            self.assertEqual(stock,report.stock_metric[1].text())
            self.assertEqual(1,report.detail_table.rowCount())
        self.assertEqual('—',report.production_metric[1].text())

    def test_report_mixed_units_and_annual_carry_over(self):
        self.create(self.a,4)
        self.create(None,2,self.pieces)
        report=self.keep(SalesReportPage(self.db))
        self.assertIn('4 kg',report.sold_metric[1].text())
        self.assertIn('2 pieces',report.sold_metric[1].text())
        annual=self.keep(AnnualFarmReportPage(self.db))
        self.choose(annual.year_filter,2027)
        self.choose(annual.product_filter,self.kg)
        self.assertEqual('16 kg',annual.stock_metric[1].text())
        finance=self.keep(FieldFinancePage(self.db))
        self.choose(finance.year,'2027')
        self.assertEqual('12,00 €',finance.assigned_income_card[1].text())
        self.assertIn('6,00 €',finance.unassigned_card[1].text())

    def test_default_total_and_by_field_requires_explicit_choice(self):
        self.assertEqual('pooled',self.db.get_app_setting('default_sale_source'))
        self.assertIsNone(self.page.source.currentData())
        self.db.save_app_settings({'default_sale_source':'field'})
        self.page.clear_form()
        self.choose(self.page.product,self.kg)
        self.choose(self.page.buyer,self.buyer)
        self.page.quantity.setValue(4)
        self.assertEqual('choose_field',self.page.source.currentData())
        self.reject()
        self.choose(self.page.source,None)
        self.choose(self.page.product,self.pieces)
        self.assertIsNone(self.page.source.currentData())
        self.page.save_sale()
        self.load(1)
        self.assertIsNone(self.page.source.currentData())

    def test_setting_ui_save_restart_reset_and_profile_isolation(self):
        theme=Mock(theme='light')
        settings=self.keep(SettingsPage(self.db,theme,self.manager,self.language))
        self.choose(settings.default_sale_source,'field')
        with patch.object(QMessageBox,'information'):
            settings.save()
        reopened=Database(self.db.path)
        self.assertEqual('field',reopened.get_app_setting('default_sale_source'))
        other=Database(self.manager.create('Other').database_path)
        self.assertEqual('pooled',other.get_app_setting('default_sale_source'))
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Yes),patch.object(QMessageBox,'information'):
            settings.reset_defaults()
        self.assertEqual('pooled',self.db.get_app_setting('default_sale_source'))

    def test_no_fields_total_stock_still_works(self):
        self.db.execute('UPDATE production SET field_id=NULL')
        self.page.refresh()
        self.configure(qty=4)
        self.assertEqual(2,self.page.source.count())
        self.page.save_sale()
        self.assertIsNone(self.row(1)['source_field_id'])

    def test_restart_backup_and_profile_package_preserve_source(self):
        identity=self.create(self.a)
        expected=self.row(identity)
        reopened=Database(self.db.path)
        self.assertEqual(expected,dict(reopened.query_one('SELECT * FROM production_sales WHERE id=?',(identity,))))
        backup=BackupManager(self.db.path,self.root/'backups')
        archive=backup.create_backup(prefix='batch4')
        self.load(identity)
        self.page.delete_sale()
        backup.restore_backup(archive)
        self.db.initialize()
        self.assertEqual(expected,self.row(identity))
        package=self.manager.export_profile(self.manager.active_profile.id,self.root/'source')
        imported=self.manager.import_profile(package)
        imported_db=Database(imported.database_path)
        self.assertEqual(expected,dict(imported_db.query_one('SELECT * FROM production_sales WHERE id=?',(identity,))))
        self.assertEqual([],imported_db.query('PRAGMA foreign_key_check'))

    def test_field_delete_protected_and_name_history_retained(self):
        identity=self.create(self.a)
        self.db.execute("UPDATE fields SET name='Renamed' WHERE id=?",(self.a,))
        self.assertEqual('Field A',self.row(identity)['source_field_name'])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM fields WHERE id=?',(self.a,))
        self.assertEqual('Field A',self.row(identity)['source_field_name'])
        self.load(identity)
        self.page.delete_sale()
        self.db.execute('DELETE FROM fields WHERE id=?',(self.a,))

    def test_audit_actual_units_and_source(self):
        identity=self.create(self.a,2,self.pieces)
        details=[r['details'] for r in self.db.query("SELECT details FROM audit_events WHERE table_name='production_sales' AND record_id=?",(str(identity),))]
        self.assertTrue(details)
        self.assertTrue(all('pieces' in d and 'Field A' in d and ' kg' not in d for d in details))

    def test_live_localization_raw_values_and_csv_source(self):
        raw='Παραγωγή <b>{year}</b>'
        self.db.execute('UPDATE fields SET name=? WHERE id=?',(raw,self.a))
        self.db.execute("UPDATE products SET unit='τεμάχια {unit}' WHERE id=?",(self.pieces,))
        self.create(self.a,2,self.pieces)
        self.load(1)
        report=self.keep(SalesReportPage(self.db))
        before=self.snapshot()
        for code in ('el','en','el'):
            self.language.set_language(code,persist=False)
            self.assertIn(raw,self.page.source.currentText())
            self.assertIn('τεμάχια {unit}',self.page.source.currentText())
            self.assertIn('available' if code=='en' else 'διαθέσιμο',self.page.source.currentText())
            self.assertEqual(raw,report.source_filter.itemText(report.source_filter.findData(self.a)))
            path=self.root/'sales.csv'
            with patch('app.sales_report.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')),patch('app.sales_report._message'):
                report.export_csv()
            with path.open(encoding='utf-8-sig',newline='') as handle:
                rows=list(csv.reader(handle,delimiter=';'))
            self.assertEqual(raw,rows[1][-1])
            self.assertEqual('τεμάχια {unit}',rows[1][-2])
            self.assertEqual('Production source' if code=='en' else 'Πηγή παραγωγής',rows[0][-1])
        self.assertEqual(before,self.snapshot())

    def test_pooled_table_label_refreshes_in_same_open_page(self):
        pooled=self.create()
        self.create(self.a)
        before=self.snapshot()
        for code in ('el','en','el'):
            self.language.set_language(code,persist=False)
            self.load(pooled)
            # The language signal itself must update the existing table body.
            self.language.set_language('en' if code=='el' else 'el',persist=False)
            expected='Total-stock / unallocated sales' if code=='el' else 'Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις'
            row=next(i for i in range(self.page.table.rowCount()) if self.page.table.item(i,0).data(Qt.ItemDataRole.UserRole)==pooled)
            self.assertEqual(expected,self.page.table.item(row,8).text())
        self.assertEqual(before,self.snapshot())
