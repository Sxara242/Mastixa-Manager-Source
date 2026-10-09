"""Real page operations, persistent snapshots, and injected linked-write failures."""
from contextlib import closing
from pathlib import Path
import sqlite3
import gc
import warnings
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QMessageBox
from app.database import Database
from app.sales import SalesPage
from app.money import MoneyPage
from app.inventory import InventoryPage
from app.activities import ActivitiesPage
from app.plant_protection import PlantProtectionPage
from app.equipment import EquipmentPage
from app.invoice_documents import InvoiceDocumentsPage
from app.inventory_sync import current_stock
from app.year_lock import ensure_year_lock_schema
from tests.language_fixture import scoped_language


class LinkedWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.enterContext(scoped_language(self.qt, "el"))
        root = self.enterContext(tempfile.TemporaryDirectory())
        self.db = Database(Path(root) / "atomic.db")
        ensure_year_lock_schema(self.db)
        self.pages = []
        self.addCleanup(self.close_pages)
        self.enterContext(patch.object(QMessageBox, "warning", side_effect=AssertionError("unexpected validation")))
        self.enterContext(patch.object(QMessageBox, "exec", side_effect=AssertionError("unexpected modal")))
        self.field = self.db.execute("INSERT INTO fields(name) VALUES('Field')")
        self.product = self.db.execute("INSERT INTO products(name,unit) VALUES('Crop','kg')")
        self.inventory = self.keep(InventoryPage(self.db))
        self.item = self.db.execute("INSERT INTO inventory_items(name,category,unit) VALUES('Input','Λιπάσματα','kg')")
        self.db.execute("INSERT INTO inventory_movements(movement_date,item_id,movement_type,quantity) VALUES('2026-01-01',?,'Παραλαβή',100)", (self.item,))

    def keep(self, page):
        self.pages.append(page)
        page.confirm_delete = lambda *_: True
        return page

    def close_pages(self):
        for page in self.pages:
            page.close()
            page.deleteLater()

    def snapshot(self):
        # A new independent connection sees only persisted state, including audit,
        # links, amounts, stock movements and sqlite_sequence after rollback.
        with closing(sqlite3.connect(self.db.path)) as con:
            return tuple(con.iterdump())

    def manual_money_insert(self, kind):
        partner_name = "Manual partner / συνεργάτης"
        partner_id = self.db.execute(
            "INSERT INTO business_partners(name,partner_type) VALUES(?,'both')",
            (partner_name,),
        )
        page = self.keep(MoneyPage(self.db, kind))
        page.date.setDate(QDate(2026, 2, 17))
        page.field.setCurrentIndex(page.field.findData(self.field))
        page.description.setText("Manual description")
        page.partner.setText(partner_name, partner_id)
        page.payment.setCurrentIndex(page.payment.findText("Κάρτα"))
        page.amount.setValue(123.45)
        page.notes.setText("Distinct notes / σημείωση")
        expected = {
            "entry_date": "2026-02-17", "field_id": self.field,
            "description": "Manual description", "partner_id": partner_id,
            "payment_method": "Κάρτα", "amount": 123.45,
            "notes": "Distinct notes / σημείωση",
            "partner" if kind == "income" else "supplier": partner_name,
        }
        if kind == "expenses":
            page.category.setCurrentIndex(page.category.findText("Μεταφορές"))
            expected["category"] = "Μεταφορές"

        page.save_money()

        # A fresh connection checks committed values and one row per save.
        with closing(sqlite3.connect(self.db.path)) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(f"SELECT * FROM {kind}").fetchall()
        self.assertEqual(1, len(rows))
        self.assertEqual(expected, {key: rows[0][key] for key in expected})
        self.assertEqual(1, page.table.rowCount())
        self.assertEqual("", page.description.text())

    def test_manual_income_insert(self):
        self.manual_money_insert("income")

    def test_manual_expense_insert(self):
        self.manual_money_insert("expenses")

    def sales_analysis_fixture(self):
        page = self.keep(SalesPage(self.db))
        buyer = self.db.execute("INSERT INTO business_partners(name,partner_type) VALUES('Buyer','buyer')")
        products = []
        for name, unit, produced, sold, price in (
            ("Mastixa", "kg", 110, 20, 5),
            ("QA PRODUCT -1", "pieces", 10, 3, 7),
            ("Custom", "κιβώτια / XL", 6, 1, 9),
        ):
            product = self.db.execute("INSERT INTO products(name,unit) VALUES(?,?)", (name, unit))
            self.db.execute("INSERT INTO production(entry_date,field_id,product,product_id,quantity_kg) VALUES('2026-02-17',?,?,?,?)", (self.field, name, product, produced))
            self.db.execute("INSERT INTO production_sales(sale_date,buyer_id,buyer_name,product,product_id,quantity_kg,price_per_kg,total_amount) VALUES('2026-02-17',?,'Buyer',?,?,?,?,?)", (buyer, name, product, sold, price, sold * price))
            products.append((product, unit, produced, sold, price))
        page.refresh()
        return page, buyer, products

    def test_sales_analysis_product_quantities_units_and_revenue(self):
        page, _buyer, products = self.sales_analysis_fixture()
        metrics = (page.produced_metric, page.sold_metric, page.stock_metric)
        self.assertEqual(["—"] * 3, [metric[1].text() for metric in metrics])
        self.assertEqual("130,00 €", page.revenue_metric[1].text())
        self.assertEqual(3, page.table.rowCount())
        layout = page.product_filter.parentWidget().layout()
        selector_index = next(i for i in range(layout.count()) if layout.itemAt(i).layout() and layout.itemAt(i).layout().indexOf(page.product_filter) >= 0)
        cards_index = next(i for i in range(layout.count()) if layout.itemAt(i).layout() and layout.itemAt(i).layout().indexOf(page.produced_metric[0]) >= 0)
        self.assertLess(selector_index, cards_index)
        before = self.snapshot()
        for product, unit, produced, sold, price in products:
            page.product_filter.setCurrentIndex(page.product_filter.findData(product))
            self.assertEqual([f"{value} {unit}" for value in (produced, sold, produced - sold)], [metric[1].text() for metric in metrics])
            self.assertEqual(page._money(sold * price), page.revenue_metric[1].text())
            self.assertEqual(1, page.table.rowCount())
            self.assertEqual(f"{sold} {unit}", page.table.item(0, 3).text())
            self.assertEqual(page._money(price) + f"/{unit}", page.table.item(0, 4).text())
            page.product.setCurrentIndex(page.product.findData(product))
            self.assertEqual(f" {unit}", page.quantity.suffix())
            self.assertEqual(f" €/{unit}", page.price_per_kg.suffix())
        page.product_filter.setCurrentIndex(0)
        self.assertEqual(["—"] * 3, [metric[1].text() for metric in metrics])
        self.assertEqual(3, page.table.rowCount())
        self.assertEqual(before, self.snapshot())

    def test_sales_analysis_preserves_product_specific_oversale_guard(self):
        page, buyer, products = self.sales_analysis_fixture()
        page.product_filter.setCurrentIndex(page.product_filter.findData(products[0][0]))
        page.product.setCurrentIndex(page.product.findData(products[1][0]))
        page.buyer.setCurrentIndex(page.buyer.findData(buyer))
        page.quantity.setValue(8)  # Only seven pieces remain, despite 90 kg elsewhere.
        before = self.snapshot()
        with patch("app.sales._message") as warning:
            page.save_sale()
        warning.assert_called_once()
        self.assertEqual("7 pieces", warning.call_args.kwargs["value1"])
        self.assertEqual(before, self.snapshot())

    def setup_flow(self, kind):
        if kind == "sale":
            self.page = self.keep(SalesPage(self.db))
            self.buyer = self.db.execute("INSERT INTO business_partners(name,partner_type) VALUES('Buyer','buyer')")
            self.db.execute("INSERT INTO production(entry_date,field_id,product,product_id,quantity_kg) VALUES('2026-01-01',?,'Crop',?,100)", (self.field, self.product))
            self.table, self.selected, self.save, self.delete = "production_sales", "selected_sale_id", self.page.save_sale, self.page.delete_sale
        elif kind == "activity":
            self.page = self.keep(ActivitiesPage(self.db))
            self.table, self.selected, self.save, self.delete = "farm_activities", "selected_activity_id", self.page.save_activity, self.page.delete_activity
        elif kind == "protection":
            self.page = self.keep(PlantProtectionPage(self.db))
            self.table, self.selected, self.save, self.delete = "plant_protection_records", "selected_id", self.page.save_record, self.page.delete_record
        elif kind == "receipt":
            self.page = self.inventory
            self.table, self.selected, self.save, self.delete = "inventory_movements", "selected_movement_id", self.page.save_movement, self.page.delete_movement
        else:
            self.page = self.keep(EquipmentPage(self.db))
            self.equipment = self.db.execute("INSERT INTO equipment(name,meter_type) VALUES('Tractor','hours')")
            self.table, self.selected, self.save, self.delete = "equipment_maintenance", "selected_service_id", self.page.save_service, self.page.delete_service
        self.kind = kind
        self.configure(2)

    def configure(self, quantity):
        p = self.page
        p.refresh()
        if self.kind == "sale":
            p.buyer.setCurrentIndex(p.buyer.findData(self.buyer))
            p.product.setCurrentIndex(p.product.findData(self.product))
            p.quantity.setValue(quantity)
            p.price_per_kg.setValue(3)
        elif self.kind == "activity":
            p.category.setCurrentIndex(p.category.findData("fertilization"))
            p.status.setCurrentText("Ολοκληρώθηκε")
            p.product.setEditText("Input")
            p.dose.setValue(1)
            p.field.setCurrentIndex(p.field.findData(self.field))
            p.inventory_item.setCurrentIndex(p.inventory_item.findData(self.item))
            p.inventory_quantity.setValue(quantity)
        elif self.kind == "protection":
            p.field.setCurrentIndex(p.field.findData(self.field))
            p.product.setCurrentIndex(p.product.findData(self.item))
            p.purpose.setText("Protection")
            p.inventory_quantity.setValue(quantity)
        elif self.kind == "receipt":
            p.movement_item.setCurrentIndex(p.movement_item.findData(self.item))
            p.movement_type.setCurrentText("Παραλαβή")
            p.movement_quantity.setText(str(quantity))
            p.movement_unit_price.setText("3")
        else:
            p.service_equipment.setCurrentIndex(p.service_equipment.findData(self.equipment))
            p.service_type.setEditText("Service")
            p.service_cost.setValue(quantity * 3)
            p.service_meter.setValue(quantity * 10)

    def fail_trigger(self, table, event):
        self.db.execute(f"CREATE TRIGGER injected BEFORE {event} ON {table} BEGIN SELECT RAISE(ABORT,'injected linked failure'); END")

    def lifecycle(self, kind, operation):
        self.setup_flow(kind)
        if operation != "create":
            self.save()
            record = self.db.query_one(f"SELECT MAX(id) FROM {self.table}")[0]
            self.configure(4)
            setattr(self.page, self.selected, record)
        if kind in ("sale", "activity", "protection"):
            target = self.table if operation == "delete" else ("income" if kind == "sale" else "inventory_movements")
            event = {"create": "INSERT", "edit": "UPDATE", "delete": "DELETE"}[operation]
        else:
            target, event = ("expenses", "DELETE") if operation == "delete" else (self.table, "UPDATE OF expense_id")
        self.fail_trigger(target, event)
        before = self.snapshot()
        stock = current_stock(self.db, self.item)
        action = self.delete if operation == "delete" else self.save
        with self.assertRaisesRegex(sqlite3.IntegrityError, "injected linked failure"):
            action()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(stock, current_stock(self.db, self.item))
        self.db.execute("DROP TRIGGER injected")
        action()  # Same UI action can retry after rollback, on a fresh transaction.
        if operation == "delete":
            self.assertIsNone(self.db.query_one(f"SELECT id FROM {self.table} WHERE id=?", (record,)))
        elif kind == "sale":
            self.assertEqual(1, self.db.query_one("SELECT COUNT(*) FROM production_sales s JOIN income i ON i.id=s.income_id AND i.amount=s.total_amount")[0])
        elif kind in ("activity", "protection"):
            source = "farm_activity" if kind == "activity" else "plant_protection"
            self.assertEqual(1, self.db.query_one("SELECT COUNT(*) FROM inventory_movements WHERE source_type=?", (source,))[0])
            self.assertEqual(100 - (4 if operation == "edit" else 2), current_stock(self.db, self.item))
        else:
            self.assertEqual(1, self.db.query_one(f"SELECT COUNT(*) FROM {self.table} s JOIN expenses e ON e.id=s.expense_id")[0])

    def test_sale_first_write_failure(self):
        self.setup_flow("sale")
        self.fail_trigger("production_sales", "INSERT")
        before = self.snapshot()
        with patch.object(self.page, "_sync_income") as child, self.assertRaises(sqlite3.IntegrityError):
            self.save()
        child.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_sale_third_write_failure(self):
        self.setup_flow("sale")
        self.fail_trigger("production_sales", "UPDATE OF income_id")
        before = self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            self.save()
        self.assertEqual(before, self.snapshot())

    def test_sale_synchronizer_python_exception(self):
        self.setup_flow("sale")
        before = self.snapshot()
        with patch.object(self.page, "_sync_income", side_effect=RuntimeError("sync failed")), self.assertRaisesRegex(RuntimeError, "sync failed"):
            self.save()
        self.assertEqual(before, self.snapshot())
        self.save()
        self.assertEqual(1, self.db.query_one("SELECT COUNT(*) FROM income")[0])

    def invoice_post(self, document_type):
        page = self.keep(InvoiceDocumentsPage(self.db))
        page.selected_id = self.db.execute("INSERT INTO invoice_documents(original_filename,stored_filename) VALUES('synthetic.pdf','synthetic.pdf')")
        page.document_type.setCurrentIndex(page.document_type.findData(document_type))
        page.date_enabled.setChecked(True)
        page.amount.setText("25")
        self.fail_trigger("invoice_documents", "UPDATE OF financial_entry_id")
        before = self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            page.create_financial_entry(require_confirmation=False)
        self.assertEqual(before, self.snapshot())
        self.db.execute("DROP TRIGGER injected")
        entry = page.create_financial_entry(require_confirmation=False)
        self.assertEqual(entry, self.db.query_one("SELECT financial_entry_id FROM invoice_documents")[0])

    def test_invoice_income_post_rollback(self): self.invoice_post("sale")
    def test_invoice_expense_post_rollback(self): self.invoice_post("purchase")

    def synchronizer_failure(self, kind):
        self.setup_flow(kind)
        module, helper = {
            "activity": ("activities", "sync_consumption"),
            "protection": ("plant_protection", "sync_consumption"),
            "receipt": ("inventory", "sync_expense"),
            "equipment": ("equipment", "sync_expense"),
        }[kind]
        before = self.snapshot()
        with patch(f"app.{module}.{helper}", side_effect=RuntimeError("sync failed")), self.assertRaisesRegex(RuntimeError, "sync failed"):
            self.save()
        self.assertEqual(before, self.snapshot())
        self.save()


def _lifecycle_test(kind, operation):
    def test(self): self.lifecycle(kind, operation)
    return test


for _kind in ("sale", "activity", "protection", "receipt", "equipment"):
    for _operation in ("create", "edit", "delete"):
        setattr(LinkedWriteTests, f"test_{_kind}_{_operation}_rollback_retry", _lifecycle_test(_kind, _operation))

for _kind in ("activity", "protection", "receipt", "equipment"):
    def _python_failure(self, kind=_kind): self.synchronizer_failure(kind)
    setattr(LinkedWriteTests, f"test_{_kind}_python_exception", _python_failure)


class TransactionApiTests(unittest.TestCase):
    def setUp(self):
        root = self.enterContext(tempfile.TemporaryDirectory())
        self.db = Database(Path(root) / "api.db")
        self.db.execute("CREATE TABLE probe(id INTEGER PRIMARY KEY, value TEXT)")

    def test_one_connection_one_commit_and_closed_handle(self):
        connection = self.db.connect()
        statements = []
        connection.set_trace_callback(statements.append)
        with patch.object(self.db, "connect", return_value=connection) as connect:
            with self.db.transaction() as tx:
                self.assertEqual(1, tx.query_one("PRAGMA foreign_keys")[0])
                tx.execute("INSERT INTO probe VALUES(1,'one')")
                tx.execute("INSERT INTO probe VALUES(2,'two')")
                self.assertEqual(2, len(tx.query("SELECT * FROM probe")))
                self.assertFalse(hasattr(tx, "commit"))
                self.assertFalse(hasattr(tx, "connect"))
                self.assertFalse(hasattr(tx, "transaction"))
            connect.assert_called_once()
        self.assertEqual(1, statements.count("BEGIN"))
        self.assertEqual(1, statements.count("COMMIT"))
        with self.assertRaises(sqlite3.ProgrammingError): connection.execute("SELECT 1")
        self.assertEqual(2, self.db.query_one("SELECT COUNT(*) FROM probe")[0])

    def test_database_error_rolls_back_and_retry_succeeds(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.transaction() as tx:
                tx.execute("INSERT INTO probe VALUES(1,'first')")
                tx.execute("INSERT INTO probe VALUES(1,'duplicate')")
        self.assertEqual(0, self.db.query_one("SELECT COUNT(*) FROM probe")[0])
        with self.db.transaction() as tx: tx.execute("INSERT INTO probe VALUES(1,'retry')")
        self.assertEqual("retry", self.db.query_one("SELECT value FROM probe")[0])

    def test_base_exception_rolls_back_without_resource_warnings(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            for _ in range(10):
                with self.assertRaises(KeyboardInterrupt):
                    with self.db.transaction() as tx:
                        tx.execute("INSERT INTO probe VALUES(1,'interrupted')")
                        raise KeyboardInterrupt()
            gc.collect()
        self.assertFalse([w for w in caught if issubclass(w.category, ResourceWarning)])
        self.assertEqual(0, self.db.query_one("SELECT COUNT(*) FROM probe")[0])

    def test_independent_execute_keeps_autocommit_behavior(self):
        self.db.execute("INSERT INTO probe VALUES(1,'independent')")
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO probe VALUES(1,'duplicate')")
        self.assertEqual("independent", self.db.query_one("SELECT value FROM probe")[0])
