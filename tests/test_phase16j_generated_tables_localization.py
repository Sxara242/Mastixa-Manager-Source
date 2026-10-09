"""Production body projections, live language changes, and opaque raw values."""
from collections import defaultdict
from contextlib import ExitStack
import copy
import importlib
import json
import os
from pathlib import Path
from string import Formatter
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidget
from app import language
from app.database import Database
from app.year_context import set_active_working_year

RAW = "Παραγωγή Αποθήκευση Ναι Έξοδα Save Production <b>tag</b> {year} User — Παραγωγή Save {2027}"


def record(**values):
    row = defaultdict(str, id=64, name=RAW, unit=RAW, field_name=RAW,
                      description=RAW, notes=RAW, category=RAW, supplier=RAW,
                      cost=12.5, amount=12.5, dose=2, area_stremma=3,
                      harvest_interval_days=4, hours=2, hourly_rate=6.25,
                      default_hourly_rate=6.25, current_stock=2, minimum_stock=3,
                      quantity=2, item_id=42, total=1, purchases=1, sales=2,
                      active=1, is_active=1, activity_date="2027-01-02",
                      entry_date="2027-01-02", work_date="2027-01-02",
                      application_date="2027-01-02", service_date="2027-01-02",
                      movement_date="2027-01-02", invoice_date="2027-01-02")
    row.update(values)
    return row


class GeneratedBodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "body.db")
        set_active_working_year(self.db, 2027, audit=False)
        self.previous = language._active_controller
        self.previous_app = getattr(self.app, "_mastixa_language_controller", None)
        self.previous_enabled = getattr(self.previous_app, "_enabled", False)
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        self.pages = []
        self.stack = ExitStack()
        self.stack.enter_context(patch("app.invoice_documents.INVOICE_FILES_DIR", Path(self.temp.name) / "invoices"))

    def tearDown(self):
        self.stack.close()
        for page in self.pages:
            page.close()
            page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        self.app._mastixa_language_controller = self.previous_app
        if self.previous_app is not None:
            self.previous_app._enabled = self.previous_enabled
            if self.previous_enabled:
                self.app.installEventFilter(self.previous_app)
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def page(self, module, cls, *args):
        page = getattr(importlib.import_module("app." + module), cls)(self.db, *args)
        self.pages.append(page)
        return page

    def skip(self, page, *methods):
        for method in methods:
            self.stack.enter_context(patch.object(page, method))

    def query(self, rows):
        return self.stack.enter_context(patch.object(self.db, "query", return_value=rows))

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump())

    def cycle(self, page, expected, raw=()):
        """Expected entries are (table, row, column, Greek, English)."""
        tables = list(dict.fromkeys(entry[0] for entry in expected + list(raw)))
        cells = [(table, table.rowCount(), [[table.item(r,c) for c in range(table.columnCount())] for r in range(table.rowCount())]) for table in tables]
        for table in tables:
            if table.rowCount():
                table.setCurrentCell(0, 0)
        selected = {table: table.currentRow() for table in tables}
        before = self.snapshot()
        for code in ("el", "en", "el"):
            with self.subTest(language=code):
                with patch.object(self.db, "query", side_effect=AssertionError("language switch queried DB")), patch.object(self.db, "query_one", side_effect=AssertionError("language switch queried DB")), patch.object(self.db, "execute", side_effect=AssertionError("language switch wrote DB")):
                    self.controller.set_language(code, persist=False)
                    self.controller.apply_to(page)
                for table, count, originals in cells:
                    self.assertEqual(table.rowCount(), count)
                    self.assertEqual(table.currentRow(), selected[table])
                    for r, items in enumerate(originals):
                        for c, item in enumerate(items):
                            self.assertIs(table.item(r, c), item)
                for table, r, c, text in raw:
                    self.assertEqual(table.item(r, c).text(), text)
                self.assertEqual(self.snapshot(), before)
                for table, r, c, el, en in expected:
                    self.assertEqual(table.item(r, c).text(), en if code == "en" else el)

    def test_activities(self):
        p = self.page("activities", "ActivitiesPage")
        self.skip(p, "_ensure_schema_and_audit_triggers", "_refresh_field_combos", "_refresh_product_combo", "_refresh_inventory_combo", "_refresh_year_filter")
        row = record(category="Πότισμα", status="Προγραμματισμένη", responsible=RAW, duration_minutes=5, water_quantity_m3=2)
        self.query([row]); p.refresh()
        self.cycle(p, [(p.table,0,2,"Πότισμα","Irrigation"),(p.table,0,3,"Προγραμματισμένη","Scheduled")], [(p.table,0,1,RAW),(p.table,0,7,RAW)])
        self.assertEqual(row["category"], "Πότισμα")

    def test_equipment(self):
        p = self.page("equipment", "EquipmentPage")
        self.skip(p, "_ensure_schema", "_refresh_combos")
        row = record(status="Ενεργό", meter_label="ώρες", current_meter=10, meter_value=3, next_service_meter=5, next_service_date="", equipment_name=RAW, technician=RAW)
        self.query([row]); p.refresh()
        self.cycle(p, [(p.equipment_table,0,4,"10 ώρες","10 hours"),(p.service_table,0,7,"Εκπρόθεσμη","Overdue"),(p.service_table,0,4,"3 ώρες","3 hours")], [(p.equipment_table,0,0,RAW),(p.service_table,0,5,RAW)])

    def test_inventory(self):
        p = self.page("inventory", "InventoryPage")
        self.skip(p, "_ensure_schema_and_audit_triggers", "_refresh_combos", "_refresh_years")
        self.stack.enter_context(patch.object(p.movement_supplier,"refresh_options"))
        row = record(item_name=RAW, item_unit=RAW, movement_type="Παραλαβή", source_type="synthetic")
        self.stack.enter_context(patch.object(p,"_stock_rows",return_value=[row]))
        self.query([row]); p.refresh()
        self.cycle(p, [(p.stock_table,0,5,"Χαμηλό","Low"),(p.movement_table,0,2,"Παραλαβή","Receipt"),(p.movement_table,0,6,"[Αυτόματη] "+RAW,"[Automatic] "+RAW)], [(p.stock_table,0,0,RAW),(p.movement_table,0,4,RAW)])
        self.assertEqual(row["movement_type"], "Παραλαβή")

    def test_labor(self):
        p = self.page("labor", "LaborPage")
        self.skip(p,"_ensure_schema","_refresh_fields","_refresh_workers","_refresh_years")
        self.query([record(field_name="",worker_name=RAW,work_type=RAW,role=RAW)])
        p.refresh()
        self.cycle(p, [(p.entry_table,0,1,"Γενική","General"),(p.worker_table,0,4,"Ενεργός","Active")], [(p.entry_table,0,2,RAW),(p.entry_table,0,3,RAW),(p.worker_table,0,1,RAW)])

    def test_money(self):
        p = self.page("money", "MoneyPage", "expenses")
        self.skip(p,"_ensure_field_link_schema","_refresh_field_choices")
        self.stack.enter_context(patch.object(p.partner,"refresh_options"))
        self.query([record(field_name="",source_type="synthetic")]);p.refresh()
        self.cycle(p, [(p.table,0,1,"Γενικό","General"),(p.table,0,3,"[Αυτόματο] "+RAW,"[Automatic] "+RAW)], [(p.table,0,2,RAW),(p.table,0,4,RAW)])

    def test_partners(self):
        p = self.page("partners", "PartnersPage")
        self.skip(p,"_ensure_schema")
        self.query([record(partner_type="supplier",tax_id=RAW)]);p.refresh()
        self.cycle(p, [(p.table,0,1,"Προμηθευτής","Supplier")], [(p.table,0,0,RAW),(p.table,0,2,RAW)])

    def test_plant_tracking(self):
        from app.plant_tracking import PlantRecord, PlantEvent
        p = self.page("plant_tracking_ui", "PlantTrackingPage")
        self.skip(p,"_refresh_fields")
        plant=PlantRecord(id="plant-64",field_id="1",label=RAW,variety=RAW,notes=RAW)
        self.stack.enter_context(patch.object(p.store,"plants",return_value=[plant]))
        self.stack.enter_context(patch.object(p.store,"snapshot",return_value=dict(status="active",health="good",event_count=1,last_event_date="2027-01-02")))
        self.stack.enter_context(patch.object(p.store,"events",return_value=[PlantEvent(id="event-64",plant_id="plant-64",event_date="2027-01-02",kind="health",value="good",notes=RAW)]))
        p.selected_id="plant-64";p.refresh()
        self.cycle(p, [(p.table,0,4,"Ενεργό","Active"),(p.table,0,5,"Καλή","Good"),(p.history,0,1,"Υγεία","Health"),(p.history,0,2,"Καλή","Good")], [(p.table,0,0,RAW),(p.history,0,3,RAW)])

    def test_plant_protection(self):
        p=self.page("plant_protection","PlantProtectionPage")
        self.skip(p,"_refresh_choices")
        self.query([record(year="2027",product_name=RAW,dose_unit=RAW,applicator=RAW)])
        p.refresh()
        self.cycle(p,[(p.table,0,5,"3 στρ.","3 decares"),(p.table,0,6,"4 ημ.","4 days")],[(p.table,0,3,RAW),(p.table,0,7,RAW)])

    def test_audit(self):
        self.db.execute("CREATE TABLE audit_events(id INTEGER PRIMARY KEY,event_time TEXT,table_name TEXT,action TEXT,record_id TEXT,details TEXT)")
        with patch("app.audit.AuditPage._ensure_schema_and_triggers"):
            p=self.page("audit","AuditPage")
        self.skip(p,"_ensure_schema_and_triggers")
        self.query([record(table_name="fields",action="INSERT",event_time="2027-01-02",record_id="64",details=RAW)])
        p.refresh()
        self.cycle(p,[(p.table,0,1,"Αγροτεμάχια","Fields"),(p.table,0,2,"Προσθήκη","Add")],[(p.table,0,4,RAW)])

    def test_calendar(self):
        self.page("activities","ActivitiesPage")
        self.db.execute("INSERT INTO farm_activities(activity_date,category,status,description,notes) VALUES(?,?,?,?,?)",("2027-01-02","Πότισμα","Προγραμματισμένη",RAW,RAW))
        p=self.page("phase13_calendar_integration","Phase13FarmCalendarPage")
        before=copy.deepcopy(p._rows)
        self.cycle(p,[(p.table,0,1,"Άρδευση & Λίπανση","Irrigation & Fertilization"),(p.table,0,3,"Πότισμα — "+RAW,"Irrigation — "+RAW)])
        self.assertEqual(p._rows,before)
        self.assertEqual(p.count_label.text(),"1 καταχωρήσεις")

    def test_global_search(self):
        p=self.page("global_search","GlobalSearchPage")
        self.stack.enter_context(patch.object(p,"_table_exists",return_value=True))
        self.query([record(kaek=RAW,location=RAW)])
        p._search_fields(RAW);p._render_results()
        before=copy.deepcopy(p._results)
        self.cycle(p,[(p.table,0,0,"Αγροτεμάχια","Fields"),(p.table,0,2,f"ΚΑΕΚ: {RAW} | {RAW} | 3 στρ.",f"KAEK: {RAW} | {RAW} | 3 decares")],[(p.table,0,1,RAW)])
        self.assertEqual(p._results,before)

    def test_field_profile_timeline(self):
        self.db.execute("INSERT INTO fields(name) VALUES(?)",(RAW,))
        p=self.page("field_profile","FieldProfilePage")
        with patch("app.field_profile.load_field_timeline_rows",return_value=[("2027-01-02","Παραγωγή","Καταχώρηση παραγωγής","")]):
            p.field.setCurrentIndex(1)
            p.refresh()
        self.cycle(p,[(p.timeline,0,1,"Παραγωγή","Production"),(p.timeline,0,2,"Καταχώρηση παραγωγής","Production entry"),(p.cost_table,0,0,"Κατανεμημένα έξοδα","Allocated expenses")])

    def test_data_export_preview(self):
        p=self.page("data_export","DataExportPage")
        self.stack.enter_context(patch.object(p,"_selected_sections",return_value=[("activities","Άρδευση & Λίπανση",["absent_table"])]))
        self.stack.enter_context(patch.object(p,"_table_exists",return_value=False))
        p._update_summary()
        self.cycle(p,[(p.summary_table,0,0,"Άρδευση & Λίπανση","Irrigation & Fertilization"),(p.summary_table,0,3,"Δεν υπάρχει ακόμη","Not available yet")],[(p.summary_table,0,1,"absent_table")])

    def test_invoice_documents(self):
        p=self.page("invoice_documents","InvoiceDocumentsPage")
        self.skip(p,"_ensure_schema","_refresh_years")
        row=record(original_filename=RAW,ocr_status="unavailable",financial_entry_type="expenses",financial_entry_id=64)
        self.query([row])
        self.stack.enter_context(patch.object(self.db,"query_one",return_value=row))
        self.stack.enter_context(patch("app.invoice_documents.is_year_locked",return_value=False))
        self.stack.enter_context(patch.object(p.supplier,"setText"))
        self.stack.enter_context(patch.object(p,"_stored_path",return_value=Path(self.temp.name)/"absent.pdf"))
        p.refresh();p._load_by_id(64)
        self.cycle(p,[(p.table,0,7,"μη διαθέσιμο — χειροκίνητη καταχώριση","unavailable — manual entry")],[(p.table,0,2,RAW),(p.table,0,6,RAW)])
        self.controller.set_language("en",persist=False)
        self.assertEqual(p.financial_status.text(),"Linked to Expense #64. No second entry will be created.")
        self.assertEqual(row["ocr_status"],"unavailable")

    def test_products_live(self):
        p=self.page("products","ProductsPage")
        self.skip(p,"_refresh_link_choices","_refresh_links")
        self.query([record()]);p.refresh()
        self.cycle(p,[(p.table,0,2,"Ενεργό","Active")],[(p.table,0,0,RAW),(p.table,0,1,RAW)])
        self.assertEqual(p.table.item(0,0).data(Qt.ItemDataRole.UserRole),64)

    def test_products_english_initial_render_and_single_refresh_hook(self):
        self.controller.set_language("en",persist=False)
        p=self.page("products","ProductsPage")
        self.skip(p,"_refresh_link_choices","_refresh_links")
        self.query([record()])
        for _ in range(3):
            p.refresh()
            self.assertEqual(p.table.item(0,2).text(),"Active")
        with patch.object(p,"_body_render",wraps=p._body_render) as render:
            self.controller.set_language("el",persist=False)
            self.assertEqual(render.call_count,1)
        self.assertEqual(p.table.item(0,2).text(),"Ενεργό")

    def test_unknown_activity_values_are_opaque_even_when_catalog_keys(self):
        p=self.page("activities","ActivitiesPage")
        self.skip(p,"_ensure_schema_and_audit_triggers","_refresh_field_combos","_refresh_product_combo","_refresh_inventory_combo","_refresh_year_filter")
        rows=[record(category="Παραγωγή",status="Αποθήκευση",description=RAW)]
        self.query(rows);p.refresh()
        before=copy.deepcopy(rows)
        self.cycle(p,[(p.table,0,2,"Παραγωγή","Παραγωγή"),(p.table,0,3,"Αποθήκευση","Αποθήκευση")],[(p.table,0,4,RAW)])
        self.assertEqual(rows,before)

    def test_inventory_all_stock_states(self):
        p=self.page("inventory","InventoryPage")
        self.skip(p,"_ensure_schema_and_audit_triggers","_refresh_combos","_refresh_years")
        self.stack.enter_context(patch.object(p.movement_supplier,"refresh_options"))
        rows=[record(id=64+i,current_stock=qty) for i,qty in enumerate((0,2,10))]
        self.stack.enter_context(patch.object(p,"_stock_rows",return_value=rows))
        self.query([]);p.refresh()
        self.cycle(p,[(p.stock_table,0,5,"Εξαντλήθηκε","Out of stock"),(p.stock_table,1,5,"Χαμηλό","Low"),(p.stock_table,2,5,"OK","OK")],[(p.stock_table,i,0,RAW) for i in range(3)])

    def test_money_search_stays_canonical(self):
        p=self.page("money","MoneyPage","expenses")
        self.skip(p,"_ensure_field_link_schema","_refresh_field_choices")
        self.stack.enter_context(patch.object(p.partner,"refresh_options"))
        self.query([record(field_name="",source_type="synthetic")]);p.refresh()
        for code in ("el","en","el"):
            self.controller.set_language(code,persist=False)
            for query,hidden in (("Αυτόματο",False),("Automatic",True),("{year}",False),("Γενικό",False),("General",True)):
                p.search.setText(query)
                self.assertEqual(p.table.isRowHidden(0),hidden,(code,query))
            self.assertEqual(p.table.item(0,3).text(),("[Automatic] " if code=="en" else "[Αυτόματο] ")+RAW)

    def test_crop_task_state_category_count_and_navigation_data(self):
        from app.crop_program_store import CropProgramStore
        CropProgramStore(self.db)
        set_active_working_year(self.db, 2020, audit=False)
        field=self.db.execute("INSERT INTO fields(name) VALUES(?)",(RAW,))
        self.db.execute("INSERT INTO crop_tasks(generation_key,program_id,rule_id,field_id,season_year,due_date,category,title,notes,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",("task-64","program","rule",str(field),2020,"2020-01-02","inspection",RAW,RAW,"pending",1,1))
        before=self.snapshot()
        p=self.page("phase13_calendar_integration","Phase13FarmCalendarPage")
        self.assertEqual(self.snapshot(),before)
        canonical=copy.deepcopy(p._rows)
        self.cycle(p,[(p.table,0,3,RAW+" — Εκπρόθεσμη",RAW+" — Overdue"),(p.table,0,4,"Έλεγχος","Inspection")],[(p.table,0,2,RAW)])
        self.assertEqual(p._rows,canonical)
        self.assertEqual(p.table.item(0,0).data(Qt.ItemDataRole.UserRole),canonical[0])
        self.controller.set_language("en",persist=False)
        self.assertEqual(p.count_label.text(),"1 entries")
        self.assertEqual(self.snapshot(),before)

    def test_search_matching_order_and_identity_stay_canonical(self):
        for ident in (65,64):
            self.db.execute("INSERT INTO fields(id,name,kaek,location,area_stremma) VALUES(?,?,?,?,?)",(ident,RAW,str(ident),RAW,3))
        p=self.page("global_search","GlobalSearchPage")
        before=self.snapshot()
        outputs=[]
        for code in ("el","en","el"):
            self.controller.set_language(code,persist=False)
            p.search.setText("{year}");p.run_search()
            outputs.append(copy.deepcopy(p._results))
            self.assertEqual([r["record_id"] for r in p._results],[64,65])
            for row,result in enumerate(p._results):
                self.assertEqual(p.table.item(row,0).data(Qt.ItemDataRole.UserRole),result)
            p.search.setText("decares");p.run_search()
            self.assertEqual(p._results,[])
        self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[1],outputs[2])
        self.assertEqual(self.snapshot(),before)

    def test_ocr_all_known_and_unknown_codes(self):
        p=self.page("invoice_documents","InvoiceDocumentsPage")
        self.skip(p,"_ensure_schema","_refresh_years")
        codes=["unavailable","failed","no_metadata","metadata_found","Παραγωγή"]
        rows=[record(id=64+i,original_filename=RAW,ocr_status=code) for i,code in enumerate(codes)]
        self.query(rows)
        self.stack.enter_context(patch.object(self.db,"query_one",return_value={"total":5,"missing":0}))
        p.refresh()
        el=["μη διαθέσιμο — χειροκίνητη καταχώριση","αποτυχία — χειροκίνητη καταχώριση","δεν βρέθηκαν ασφαλή μεταδεδομένα","προτάθηκαν ασφαλή μεταδεδομένα","Παραγωγή"]
        en=["unavailable — manual entry","failed — manual entry","no reliable metadata found","reliable metadata suggested","Παραγωγή"]
        self.cycle(p,[(p.table,i,7,el[i],en[i]) for i in range(5)],[(p.table,i,6,RAW) for i in range(5)])
        self.assertEqual([r["ocr_status"] for r in rows],codes)

    def test_catalog_integrity(self):
        root=Path(language.__file__).parent/"locales"
        target=root/"en_phase16j_generated_tables.json"
        entries=json.loads(target.read_text(encoding="utf-8"))["translations"]
        for source,value in entries.items():
            self.assertTrue(value.strip())
            self.assertNotRegex(value,r"[\u0370-\u03ff\u1f00-\u1fff]")
            fields=lambda s: sorted((field,spec,conversion) for _,field,spec,conversion in Formatter().parse(s) if field is not None)
            self.assertEqual(fields(source),fields(value))
        for path in root.glob("*.json"):
            if path!=target:
                self.assertFalse(entries.keys() & json.loads(path.read_text(encoding="utf-8"))["translations"].keys(),path.name)

    def test_prepared_database_page_construction_and_refresh_preserve_state(self):
        owners=[("activities","ActivitiesPage",()),("equipment","EquipmentPage",()),
                ("inventory","InventoryPage",()),("labor","LaborPage",()),
                ("money","MoneyPage",("expenses",)),("partners","PartnersPage",()),
                ("plant_tracking_ui","PlantTrackingPage",()),("plant_protection","PlantProtectionPage",()),
                ("phase13_calendar_integration","Phase13FarmCalendarPage",()),
                ("global_search","GlobalSearchPage",()),("field_profile","FieldProfilePage",()),
                ("data_export","DataExportPage",()),("invoice_documents","InvoiceDocumentsPage",()),
                ("products","ProductsPage",())]
        # Existing constructors initialize their schemas; that fixture preparation
        # is deliberate. Subsequent construction/rendering must preserve the DB.
        for module,cls,args in owners:
            with self.subTest(owner=module):
                self.page(module,cls,*args)
                before=self.snapshot()
                p=self.page(module,cls,*args)
                self.assertEqual(self.snapshot(),before)
                if hasattr(p,"refresh"):
                    p.refresh()
                self.assertEqual(self.snapshot(),before)
        before=self.snapshot()
        for code in ("en","el"):
            with patch.object(self.db,"execute",side_effect=AssertionError("language switch wrote DB")):
                self.controller.set_language(code,persist=False)
            self.assertEqual(self.snapshot(),before)


if __name__ == "__main__":
    unittest.main()
