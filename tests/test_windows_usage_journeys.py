"""Compound Windows journeys across real pages, persistence and profile copies."""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDate, Qt, QEvent, QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox
from app.database import Database
from app.profile_manager import ProfileManager
from app.backup_manager import BackupManager
from app.production import ProductionPage
from app.sales import SalesPage
from app.money import MoneyPage
from app.dashboard import DashboardPage
from app.report_quantities import sale_availability
from app.crop_program import CropProgramRule
from app.crop_program_store import CropProgramStore
from app.plantings import PlantingsPage
from app.plant_tracking import PlantRecord, PlantEvent
from app.plant_tracking_store import PlantTrackingStore
from app.planting_history import PlantingHistoryStore
from app.gis.geometry import normalize
from app.gis.store import GeometryStore
from app import year_context
from app.year_lock import ensure_year_lock_schema
from tests.language_fixture import scoped_language


class WindowsUsageJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.enterContext(scoped_language(self.qt, 'el'))
        keys = ('mastixaActiveWorkingYear', 'mastixaEffectiveWorkingYear',
                'mastixaCorrectionYear', 'mastixaCorrectionReason')
        previous = {key: self.qt.property(key) for key in keys}
        self.addCleanup(lambda: [self.qt.setProperty(k, v) for k, v in previous.items()])
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.manager = ProfileManager(self.root / 'profiles')
        self.db = Database(self.manager.active_profile.database_path)
        ensure_year_lock_schema(self.db)
        year_context.set_active_working_year(self.db, 2027, audit=False)
        self.addCleanup(year_context.initialize_year_context, self.db)
        self.pages = []
        self.addCleanup(self.close_pages)
        self.enterContext(patch.object(QMessageBox, 'warning', side_effect=AssertionError('Unexpected warning')))
        self.enterContext(patch.object(QMessageBox, 'exec', side_effect=AssertionError('Unexpected modal')))
        self.field = self.db.execute("INSERT INTO fields(name,productive_trees) VALUES('Journey Ω {raw}',100)")

    def close_pages(self):
        for page in self.pages:
            page.close()
            page.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def page(self, kind, db=None, *args):
        page = kind(db or self.db, *args)
        page.confirm_delete = lambda *_: True
        self.pages.append(page)
        return page

    def choose(self, combo, value):
        index = combo.findData(value)
        self.assertGreaterEqual(index, 0, repr(value))
        combo.setCurrentIndex(index)

    def load(self, page, identity, method):
        page.refresh()
        for row in range(page.table.rowCount()):
            if page.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == identity:
                getattr(page, method)(row, 0)
                return
        self.fail(f'Missing {type(page).__name__} row {identity}')

    @staticmethod
    def snapshot(db):
        with closing(sqlite3.connect(db.path)) as con:
            return tuple(con.iterdump())

    def commercial_journey(self, unit):
        product = self.db.execute("INSERT INTO products(name,unit) VALUES(?,?)", ('Crop Ω {raw}', unit))
        production = self.page(ProductionPage)
        sales = self.page(SalesPage)  # Its normal owner initializes partner tables.
        buyer = self.db.execute("INSERT INTO business_partners(name,partner_type) VALUES('Buyer','buyer')")
        self.choose(production.field, self.field)
        self.choose(production.product, product)
        production.date.setDate(QDate(2027, 3, 4))
        production.quantity.setValue(20)
        production.save_production()
        produced = self.db.query_one('SELECT id FROM production')[0]
        sales.refresh()
        self.choose(sales.product, product)
        self.choose(sales.buyer, buyer)
        self.choose(sales.source, self.field)
        sales.sale_date.setDate(QDate(2027, 3, 5))
        sales.quantity.setValue(4)
        sales.price_per_kg.setValue(3)
        sales.save_sale()
        identity, income = self.db.query_one('SELECT id,income_id FROM production_sales')
        for quantity in (6, 5):
            self.load(sales, identity, 'load_sale')
            sales.quantity.setValue(quantity)
            sales.save_sale()
            row = self.db.query_one('SELECT income_id,total_amount FROM production_sales')
            self.assertEqual((income, quantity * 3), tuple(row))
            self.assertEqual(quantity * 3, self.db.query_one('SELECT amount FROM income WHERE id=?', (income,))[0])
        money = self.page(MoneyPage, self.db, 'income')
        self.assertEqual(1, money.table.rowCount())
        dashboard = self.page(DashboardPage)
        self.assertEqual(f'20 {unit}', dashboard.production[1].text())
        self.assertEqual('15,00 €', dashboard.income[1].text())
        self.assertEqual(15, sale_availability(self.db, product, self.field))
        self.load(production, produced, 'load_selected')
        production.quantity.setValue(4)
        before = self.snapshot(self.db)
        with patch('app.production._message') as warning:
            production.save_production()
        warning.assert_called_once()
        self.assertEqual(before, self.snapshot(self.db))
        manager = BackupManager(self.db.path, self.root / 'backups')
        backup = manager.create_backup(prefix='compound')
        self.db.execute("INSERT INTO year_locks(year,is_locked,reason) VALUES(2027,1,'audit')")
        year_context.begin_year_correction(self.db, 2027, 'compound edit')
        self.load(sales, identity, 'load_sale')
        sales.quantity.setValue(7)
        sales.save_sale()
        self.assertEqual(21, self.db.query_one('SELECT amount FROM income WHERE id=?', (income,))[0])
        year_context.finish_year_correction(self.db)
        # Reopen resets the in-memory correction grant, preserving physical lock.
        reopened = Database(self.db.path)
        year_context.initialize_year_context(reopened)
        self.assertTrue(year_context.is_year_write_blocked(reopened, 2027))
        self.assertIsNone(year_context.correction_state(reopened))
        archive = self.manager.export_profile(self.manager.active_profile.id, self.root / 'commercial')
        imported = self.manager.import_profile(archive)
        copy_db = Database(imported.database_path)
        copied_before = self.snapshot(copy_db)
        self.assertEqual((product, self.field, income, 7, 21), tuple(copy_db.query_one(
            'SELECT product_id,source_field_id,income_id,quantity_kg,total_amount FROM production_sales')))
        self.assertEqual(21, copy_db.query_one('SELECT amount FROM income')[0])
        manager.restore_backup(backup)
        self.assertEqual(before, self.snapshot(self.db))
        year_context.initialize_year_context(self.db)
        self.load(sales, identity, 'load_sale')
        sales.delete_sale()
        self.assertEqual(0, self.db.query_one('SELECT COUNT(*) FROM income')[0])
        self.load(production, produced, 'load_selected')
        production.delete_production()
        self.assertEqual(0, self.db.query_one('SELECT COUNT(*) FROM production')[0])
        self.assertEqual(copied_before, self.snapshot(copy_db))
        self.choose(production.field, self.field)
        self.choose(production.product, product)
        production.quantity.setValue(9)
        production.save_production()
        self.assertEqual(9, sale_availability(self.db, product))
        dashboard.refresh()
        self.assertEqual('0,00 €', dashboard.income[1].text())
        self.assertEqual(f'9 {unit}', dashboard.production[1].text())

    def test_production_sale_income_reports_correction_backup_profile_kg(self):
        self.commercial_journey('kg')

    def test_production_sale_income_reports_correction_backup_profile_pieces(self):
        self.commercial_journey('pieces')

    def test_crop_tasks_plant_history_geometry_profile_restore_isolation(self):
        crop = CropProgramStore(self.db)
        rule = CropProgramRule(id='check', title='Check Ω', category='inspection',
                               schedule_kind='fixed_date', month=3, day=15)
        crop.save_program('program', 'Program Ω', [rule])
        first = crop.generate_for_field('program', self.field, 2027)
        key = first[0]['generation_key']
        crop.set_task_status(key, 'completed')
        crop.save_rules('program', [replace(rule, title='Edited Ω')])
        self.assertEqual('completed', crop.generate_for_field('program', self.field, 2027)[0]['status'])
        self.assertEqual(1, len(crop.tasks()))
        self.page(PlantingsPage)  # Normal owner initializes its schema.
        batch = self.db.execute('INSERT INTO planting_batches(planting_date,field_id,trees_planted,trees_alive) VALUES(?,?,?,?)',
                                ('2027-03-01', self.field, 10, 9))
        plants = PlantTrackingStore(self.db)
        plants.save_plant(PlantRecord(id='plant', field_id=str(self.field), planting_batch_id=str(batch),
                                     label='P Ω', planted_date='2027-03-01'))
        plants.append_event(PlantEvent('loss', 'plant', '2027-04-01', 'status', 'dead', 'raw Ω'))
        history = PlantingHistoryStore(self.db)
        history.add_replanting(str(batch), '2027-04-02', 1, event_id='replacement')
        geometry = GeometryStore(self.db)
        identity = geometry.save(self.field, normalize({'type':'Polygon', 'coordinates':[
            [[26,38],[26.001,38],[26.001,38.001],[26,38.001],[26,38]]]}, 'EPSG:4326'))
        point = geometry.save_point(identity, 'tree', 'P Ω', '', 26.0005, 38.0005, 5)
        geometry.save_track(identity, dict(title='Walk', positions=[[26,38,5,1000]], segment_starts=[0],
                            state='stopped', started_at=1000, ended_at=1100, duration_ms=100, distance_m=0))
        before = self.snapshot(self.db)
        backup = BackupManager(self.db.path, self.root / 'backups')
        source = backup.create_backup(prefix='compound')
        package = self.manager.export_profile(self.manager.active_profile.id, self.root / 'farm')
        imported = self.manager.import_profile(package)
        copy_db = Database(imported.database_path)
        for database in (Database(self.db.path), copy_db):
            self.assertEqual('completed', CropProgramStore(database).tasks()[0]['status'])
            self.assertEqual('dead', PlantTrackingStore(database).snapshot('plant')['status'])
            self.assertEqual(1, PlantingHistoryStore(database).totals(str(batch)).replantings)
            geo = GeometryStore(database)
            self.assertEqual(identity, geo.get(self.field)['id'])
            self.assertEqual(point, geo.points(identity)[0]['id'])
            self.assertEqual(1, len(geo.tracks(identity)))
        copied_before = self.snapshot(copy_db)
        crop.archive_program('program')
        plants.delete_plant('plant')
        changed = normalize({'type':'Polygon', 'coordinates':[
            [[26,38],[26.002,38],[26.002,38.002],[26,38.002],[26,38]]]}, 'EPSG:4326')
        geometry.save(self.field, changed, expected_revision=1)
        backup.restore_backup(source)
        self.assertEqual(before, self.snapshot(self.db))
        self.assertEqual(copied_before, self.snapshot(copy_db))
        self.assertEqual('dead', PlantTrackingStore(Database(self.db.path)).snapshot('plant')['status'])
        self.manager.set_active(imported.id)
        self.manager.set_active(self.manager.profiles()[0].id)
        self.assertEqual(before, self.snapshot(self.db))


if __name__ == '__main__':
    unittest.main()
