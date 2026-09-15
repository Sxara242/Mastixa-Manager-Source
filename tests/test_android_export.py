import csv
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from app.database import Database
from app.data_export import DataExportPage


class AndroidExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_export_products_links_and_dependencies_without_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / 'test.db')
            db.execute("INSERT INTO fields(name,kaek) VALUES('Πυργί','001')")
            field = db.query_one('SELECT id FROM fields')['id']
            product = db.execute("INSERT INTO products(name,unit) VALUES('Δοκιμή','kg')")
            db.execute("INSERT INTO product_fields(product_id,field_id,variety,planting_date) VALUES(?,?,?,?)", (product, field, 'Ποικιλία', '2024-03-15'))
            db.execute("ALTER TABLE products ADD COLUMN api_key TEXT DEFAULT 'must-not-export'")
            page = DataExportPage(db)
            page._set_all(False)
            page.section_checks['products'].setChecked(True)
            page.section_checks['fields'].setChecked(True)
            self.assertEqual(page.summary_table.rowCount(), 3)
            target = Path(tmp) / 'export.zip'
            with patch('app.data_export.QFileDialog.getSaveFileName', return_value=(str(target), 'ZIP')), patch('app.data_export.QMessageBox.information'):
                page.export_zip()
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(len(archive.namelist()), len(set(archive.namelist())))
                self.assertIn('tables/products.csv', archive.namelist())
                rows = list(csv.DictReader(io.StringIO(archive.read('tables/products.csv').decode('utf-8-sig')), delimiter=';'))
                self.assertEqual(rows[0]['name'], 'Δοκιμή')
                self.assertNotIn('api_key', rows[0])
                links = list(csv.DictReader(io.StringIO(archive.read('tables/product_fields.csv').decode('utf-8-sig')), delimiter=';'))
                self.assertEqual(links[0]['variety'], 'Ποικιλία')
                manifest = json.loads(archive.read('manifest.json'))
                self.assertEqual(len(manifest['tables']), 3)
            query, args = page._filtered_query('products', product)
            self.assertEqual(len(db.query(query, args)), 1)
            query, args = page._filtered_query('product_fields', product)
            self.assertEqual(len(db.query(query, args)), 1)
            page.close()


if __name__ == '__main__':
    unittest.main()
