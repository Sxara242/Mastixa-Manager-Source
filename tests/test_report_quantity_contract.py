"""Batch 3: mixed units, report snapshots and source-owned financial costs."""
from contextlib import closing
import csv
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from app.database import Database
from app.dashboard import DashboardPage
from app.reports import ReportsPage
from app.annual_report import AnnualFarmReportPage
from app.sales_report import SalesReportPage
from app.field_finance import FieldFinancePage
from app.inventory import InventoryPage
from app.activities import ActivitiesPage
from app.exporters import export_report_pdf, export_report_xlsx
from app.report_quantities import quantities, quantity_text, grams_per_tree
from app import year_context
from app.year_lock import ensure_year_lock_schema
from app.sale_source_schema import migrate_sale_sources
from tests.language_fixture import scoped_language


class ReportQuantityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = self.enterContext(scoped_language(self.qt, "el"))
        properties = ("mastixaActiveWorkingYear", "mastixaEffectiveWorkingYear", "mastixaCorrectionYear", "mastixaCorrectionReason")
        previous = {key: self.qt.property(key) for key in properties}
        self.addCleanup(lambda: [self.qt.setProperty(key, value) for key, value in previous.items()])
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.db = Database(self.root / "report.db")
        ensure_year_lock_schema(self.db)
        year_context.set_active_working_year(self.db, 2027, audit=False)
        self.addCleanup(year_context.initialize_year_context, self.db)
        self.field = self.db.execute("INSERT INTO fields(name,productive_trees) VALUES('Mixed field',500)")
        self.kg = self.db.execute("INSERT INTO products(name,unit) VALUES('Mastixa','kg')")
        self.pieces = self.db.execute("INSERT INTO products(name,unit) VALUES('QA PRODUCT','pieces')")
        self.db.execute("""CREATE TABLE production_sales(id INTEGER PRIMARY KEY, sale_date TEXT,
            product_id INTEGER, product TEXT, buyer_id INTEGER, buyer_name TEXT,
            quantity_kg REAL, price_per_kg REAL, total_amount REAL, income_id INTEGER,
            payment_method TEXT DEFAULT '', notes TEXT DEFAULT '')""")
        # This fixture creates Sales after Database.initialize; migrate before
        # taking rendering/restart snapshots, just as the real Sales owner does.
        with self.db.connect() as con:
            migrate_sale_sources(con)
        for year, product, name, qty in ((2026,self.kg,'Mastixa',110),(2026,self.pieces,'QA PRODUCT',10),(2027,self.kg,'Mastixa',55)):
            self.db.execute("INSERT INTO production(entry_date,field_id,product_id,product,quantity_kg) VALUES(?,?,?,?,?)",(f"{year}-10-03",self.field,product,name,qty))
        for year, product, name, qty, price in ((2026,self.kg,'Mastixa',20,10),(2026,self.pieces,'QA PRODUCT',2,3),(2027,self.kg,'Mastixa',5,12)):
            income = self.db.execute("INSERT INTO income(entry_date,description,amount) VALUES(?,?,?)", (f"{year}-10-04",'Sale',qty*price))
            self.db.execute("INSERT INTO production_sales(sale_date,product_id,product,buyer_name,quantity_kg,price_per_kg,total_amount,income_id) VALUES(?,?,?,'Buyer',?,?,?,?)",(f"{year}-10-04",product,name,qty,price,qty*price,income))
        for year, value in ((2026,30),(2027,4)):
            self.db.execute("INSERT INTO expenses(entry_date,category,description,amount) VALUES(?,'Other','Expense',?)",(f"{year}-10-04",value))

    def page(self, cls, db=None):
        page = cls(db or self.db)
        self.addCleanup(page.deleteLater)
        self.addCleanup(page.close)
        return page

    def snapshot(self):
        with closing(sqlite3.connect(self.db.path)) as con:
            return tuple(con.iterdump())

    def select(self, combo, data):
        index = combo.findData(data)
        self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)

    def test_dashboard_effective_year_switch_and_correction(self):
        page = self.page(DashboardPage)
        self.assertEqual('55 kg',page.production[1].text())
        self.assertEqual('60,00 €',page.income[1].text())
        self.assertEqual('4,00 €',page.expenses[1].text())
        self.assertEqual('56,00 €',page.balance[1].text())
        year_context.set_active_working_year(self.db,2026,audit=False)
        page.refresh_year_context_ui()
        self.assertIn('110 kg',page.production[1].text())
        self.assertIn('10 pieces',page.production[1].text())
        self.assertEqual('206,00 €',page.income[1].text())
        year_context.set_active_working_year(self.db,2027,audit=False)
        self.db.execute("INSERT INTO year_locks(year,is_locked,reason) VALUES(2026,1,'test')")
        before = self.snapshot()
        year_context.begin_year_correction(self.db,2026,'reason')
        page.refresh_year_context_ui()
        self.assertIn('10 pieces',page.production[1].text())
        year_context.initialize_year_context(Database(self.db.path))
        page.refresh_year_context_ui()
        self.assertEqual('55 kg',page.production[1].text())
        self.assertEqual(before,self.snapshot())

    def test_registry_id_wins_legacy_name_and_unknown_never_assumes_kg(self):
        self.db.execute("UPDATE production SET product='Wrong name' WHERE product_id=?",(self.pieces,))
        self.db.execute("INSERT INTO production(entry_date,product,quantity_kg) VALUES('2027-01-01','Unregistered',9)")
        before=self.snapshot()
        groups=quantities(self.db)
        self.assertIn('10 pieces',quantity_text(groups))
        self.assertIn('Unregistered: 9 [?]',quantity_text(groups))
        self.assertEqual(before,self.snapshot())

    def test_reports_yearly_fields_and_chart_select_one_product(self):
        before=self.snapshot()
        page=self.page(ReportsPage)
        self.select(page.year,'2026')
        self.assertIn('110 kg',page.production_card[1].text())
        self.assertIn('10 pieces',page.fields_table.item(0,3).text())
        self.assertEqual('—',page.fields_table.item(0,4).text())
        self.assertTrue(any('10 pieces' in page.yearly_table.item(r,1).text() for r in range(page.yearly_table.rowCount())))
        self.select(page.chart_product,str(('id',self.pieces)))
        self.assertEqual('pieces',page.production_chart.unit)
        self.assertEqual([10,0],page.production_chart.values)
        self.select(page.chart_product,str(('id',self.kg)))
        self.assertEqual('kg',page.production_chart.unit)
        self.assertEqual([110,55],page.production_chart.values)
        self.select(page.year,'2027')
        self.assertEqual('110.0',page.fields_table.item(0,4).text())
        self.assertEqual(before,self.snapshot())

    def test_grams_only_known_coherent_mass(self):
        self.assertEqual(220,grams_per_tree(quantities(self.db,year=2026,product_id=self.kg),500))
        self.assertIsNone(grams_per_tree(quantities(self.db,year=2026),500))
        self.assertIsNone(grams_per_tree(quantities(self.db,product_id=self.pieces),500))
        self.assertIsNone(grams_per_tree(quantities(self.db,product_id=self.kg),0))
        self.db.execute("UPDATE products SET unit='g' WHERE id=?",(self.kg,))
        self.assertEqual(.22,grams_per_tree(quantities(self.db,year=2026,product_id=self.kg),500))

    def test_annual_carry_over_selected_and_all_products(self):
        before=self.snapshot()
        page=self.page(AnnualFarmReportPage)
        self.select(page.year_filter,2027)
        self.select(page.product_filter,self.kg)
        self.assertEqual('55 kg',page.production_metric[1].text())
        self.assertEqual('5 kg',page.sold_metric[1].text())
        self.assertEqual('140 kg',page.stock_metric[1].text())
        self.assertEqual('12 €/kg',page.avg_price_metric[1].text())
        self.assertEqual('—',page.result_metric[1].text())
        self.select(page.product_filter,self.pieces)
        self.assertEqual('8 pieces',page.stock_metric[1].text())
        self.select(page.year_filter,2026)
        self.assertEqual('3 €/pieces',page.avg_price_metric[1].text())
        self.select(page.product_filter,None)
        self.assertIn('90 kg',page.stock_metric[1].text())
        self.assertIn('8 pieces',page.stock_metric[1].text())
        self.assertEqual('—',page.avg_price_metric[1].text())
        self.assertEqual('176,00 €',page.result_metric[1].text())
        self.assertEqual(before,self.snapshot())

    def test_sales_report_units_revenue_and_current_stock(self):
        page=self.page(SalesReportPage)
        self.select(page.year_filter, None)
        self.assertIn('165 kg',page.production_metric[1].text())
        self.assertIn('10 pieces',page.production_metric[1].text())
        self.assertEqual('—',page.avg_price_metric[1].text())
        self.assertEqual('—',page.buyer_table.item(0,4).text())
        self.select(page.product_filter,self.pieces)
        self.assertEqual('10 pieces',page.production_metric[1].text())
        self.assertEqual('2 pieces',page.sold_metric[1].text())
        self.assertEqual('8 pieces',page.stock_metric[1].text())
        self.assertEqual('6,00 €',page.revenue_metric[1].text())
        self.assertEqual('3 €/pieces',page.avg_price_metric[1].text())
        self.select(page.product_filter,self.kg)
        self.select(page.year_filter,'2026')
        self.assertEqual('110 kg',page.production_metric[1].text())
        self.assertEqual('140 kg',page.stock_metric[1].text())

    def test_field_finance_synced_legacy_manual_and_cost_per_unit(self):
        self.page(InventoryPage)
        activity=self.page(ActivitiesPage)
        activity.date.setDate(QDate(2027,10,3))
        self.select(activity.field,self.field)
        activity.duration.setValue(30)
        activity.cost.setValue(5)
        activity.save_activity()
        self.db.execute("INSERT INTO farm_activities(activity_date,field_id,category,cost) VALUES('2027-10-03',?,'Πότισμα',7)",(self.field,))
        self.db.execute("INSERT INTO expenses(entry_date,field_id,category,description,amount) VALUES('2027-10-03',?,'Άρδευση','manual',3)",(self.field,))
        page=self.page(FieldFinancePage)
        self.select(page.year,'2027')
        self.assertEqual('15,00 €',page.direct_cost_card[1].text())
        self.assertEqual('8,00 €',page.table.item(0,3).text())
        self.assertEqual('7,00 €',page.table.item(0,4).text())
        self.assertTrue(page.table.item(0,10).text().endswith('€/kg'))
        self.select(page.year,None)
        self.assertEqual('—',page.table.item(0,10).text())
        self.db.execute("UPDATE production SET product_id=?,product='QA PRODUCT' WHERE entry_date LIKE '2027%'",(self.pieces,))
        self.select(page.year,'2027')
        self.assertTrue(page.table.item(0,10).text().endswith('€/pieces'))

    def test_field_finance_keeps_other_costs_and_unallocated_money_separate(self):
        for table, date in (('plant_protection_records','application_date'),
                            ('labor_entries','work_date'),('planting_batches','planting_date')):
            self.db.execute(f'CREATE TABLE {table}(field_id INTEGER, {date} TEXT, cost REAL)')
            self.db.execute(f"INSERT INTO {table} VALUES(?,'2027-10-03',2)",(self.field,))
        before=self.snapshot()
        page=self.page(FieldFinancePage)
        self.select(page.year,'2027')
        self.assertEqual('6,00 €',page.direct_cost_card[1].text())
        self.assertEqual('60,00 € / 4,00 €',page.unassigned_card[1].text())
        self.assertEqual('0,00 €',page.assigned_income_card[1].text())
        self.assertEqual(before,self.snapshot())

    def test_legacy_name_resolution_and_same_unit_products_do_not_share_cost_rate(self):
        self.db.execute('UPDATE production SET product_id=NULL WHERE product_id=?',(self.pieces,))
        self.db.execute("UPDATE products SET unit='kg' WHERE id=?",(self.pieces,))
        before=self.snapshot()
        page=self.page(FieldFinancePage)
        self.select(page.year,'2026')
        self.assertIn('QA PRODUCT: 10 kg',page.table.item(0,1).text())
        self.assertIn('Mastixa: 110 kg',page.table.item(0,1).text())
        self.assertEqual('—',page.table.item(0,10).text())
        self.assertEqual(before,self.snapshot())

    def test_report_exports_share_snapshot_and_do_not_parse_widgets(self):
        page=self.page(ReportsPage)
        self.select(page.year,'2026')
        before=page._report_snapshot()
        page.production_card[1].setText('corrupted display')
        self.assertEqual(before,page._report_snapshot())
        path=self.root/'report.xlsx'
        export_report_xlsx(str(path),before)
        with ZipFile(path) as archive:
            text=archive.read('xl/worksheets/sheet1.xml').decode()+archive.read('xl/worksheets/sheet2.xml').decode()
        self.assertIn('110 kg',text)
        self.assertIn('10 pieces',text)
        self.assertNotIn('*1000/',text)
        self.assertNotIn('120 kg',text)
        with patch('app.exporters.QTextDocument') as document:
            export_report_pdf(str(self.root/'report.pdf'),before)
        html=document.return_value.setHtml.call_args.args[0]
        self.assertIn('110 kg',html)
        self.assertIn('10 pieces',html)
        self.assertNotIn('120 kg',html)
        self.assertIn('—',html)
        export_report_pdf(str(self.root/'actual.pdf'),before)
        self.assertTrue((self.root/'actual.pdf').read_bytes().startswith(b'%PDF-'))
        self.language.set_language('en',persist=False)
        self.assertEqual('Year: 2026',page._report_snapshot()['year_label'])

    def test_csv_exports_include_units_and_raw_values_in_both_languages(self):
        for cls,owner in ((AnnualFarmReportPage,'annual_report'),(SalesReportPage,'sales_report'),(FieldFinancePage,'field_finance')):
            page=self.page(cls)
            if owner=='annual_report': self.select(page.year_filter,2026)
            elif owner=='sales_report': self.select(page.year_filter, None)
            else: self.select(page.year, None)
            path=self.root/(owner+'.csv')
            for code in ('el','en','el'):
                self.language.set_language(code,persist=False)
                self.language.apply_to(page)
                with patch(f'app.{owner}.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')),patch(f'app.{owner}._message'):
                    page.export_csv()
                with path.open(encoding='utf-8-sig',newline='') as handle: rows=list(csv.reader(handle,delimiter=';'))
                self.assertIn('pieces',path.read_text(encoding='utf-8-sig'))
                self.assertNotIn('Παραγωγή kg',str(rows))
                self.assertNotIn('Production kg',str(rows))

    def test_profile_and_live_language_rendering_preserve_database(self):
        self.db.execute("UPDATE products SET name='Παραγωγή <b>{year}</b>',unit='τεμάχια {unit}' WHERE id=?",(self.pieces,))
        before=self.snapshot()
        pages=[self.page(cls) for cls in (DashboardPage,ReportsPage,AnnualFarmReportPage,SalesReportPage,FieldFinancePage)]
        self.select(pages[1].year,'2026')
        self.select(pages[2].year_filter,2026)
        self.select(pages[2].product_filter,self.pieces)
        self.select(pages[3].product_filter,self.pieces)
        self.select(pages[3].year_filter, '2026')
        for code in ('el','en','el'):
            self.language.set_language(code,persist=False)
            for page in pages:
                page.refresh()
                self.language.apply_to(page)
            self.assertIn('Παραγωγή <b>{year}</b>: 10 τεμάχια {unit}',pages[1].production_card[1].text())
            self.assertEqual('10 τεμάχια {unit}',pages[2].production_metric[1].text())
            self.assertEqual('10 τεμάχια {unit}',pages[3].production_metric[1].text())
            self.assertEqual('3 €/τεμάχια {unit}',pages[3].avg_price_metric[1].text())
        self.assertEqual(before,self.snapshot())
        other=Database(self.root/'other.db')
        year_context.set_active_working_year(other,2030,audit=False)
        dashboard=self.page(DashboardPage,other)
        self.assertEqual('—',dashboard.production[1].text())
        self.assertEqual('0,00 €',dashboard.income[1].text())
        self.assertEqual(2027,year_context.effective_working_year(self.db))
