import copy
import csv
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QMessageBox, QWidget
from app import language
from app.database import Database
from app.localized_messages import _message
from app.data_quality import DataQualityPage
from app.inventory_report import InventoryReportPage
from app.annual_report import AnnualFarmReportPage
from app.annual_report_exports import AnnualProduct, AnnualSnapshot
from app.sales_report import SalesReportPage
from app.reports import ReportsPage
from app.data_export import DataExportPage

RAW = "PermissionError: Save Αποθήκευση {path} <raw> Ω & Ναι"
MEMBER = "tables/Αποθήκευση {2027} & Ω.csv"


class ExportDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Δοκιμή Save Αποθήκευση"
        self.root.mkdir()
        self.db = Database(self.root / "source.db")
        self.previous = language._active_controller
        self.controller = language.LanguageController(self.app, SimpleNamespace(active_profile=SimpleNamespace(language="el")))
        language.install_language_controller(self.controller)
        # Real export methods on a minimal QWidget owner: no unrelated page setup.
        self.page = QWidget()
        self.page.year = QComboBox(self.page)
        self.page.year.addItem("2027",2027)
        self.page.year_filter = self.page.year
        self.page.product_filter = QComboBox(self.page)
        self.page.product_filter.addItem(RAW,1)
        self.page._report_snapshot = Mock(return_value={"raw":RAW,"amount":12.5})
        self.page._rows_cache = [dict(name=RAW,category=RAW,unit=RAW,stock=2,minimum=3,receipt_qty=4,consumed_qty=2,avg_price=5,stock_value=10,status="Χαμηλό",product=RAW,produced=4,sold=2,revenue=10,avg=5)]
        self.page._annual_report_snapshot = lambda: AnnualSnapshot(
            2027, 1, RAW, (AnnualProduct(RAW, 1, ("id", 1), RAW, 4, 2, 10, 5, 2),), 10, 0, 0)
        self.page._sales_rows = lambda: [dict(product_name=RAW,unit=RAW,sale_date="2027-01-01",buyer_name=RAW,quantity_kg=2,price_per_kg=5,total_amount=10,payment_method=RAW,notes=RAW)]
        self.page._filtered_issues = lambda: [dict(severity="ERROR",category="fields",record=RAW,problem="Δεν έχει συμπληρωθεί ΚΑΕΚ.",fix="Συμπλήρωσε το ΚΑΕΚ αν είναι διαθέσιμο.")]
        self.page._issue_values = DataQualityPage._issue_values
        self.zip_page = DataExportPage(self.db)
        for key, check in self.zip_page.section_checks.items():
            check.setChecked(key=="producer")
        self.before = self.snapshot()
        self.rows = copy.deepcopy(self.page._rows_cache)

    def tearDown(self):
        for page in (self.page,self.zip_page):
            page.close()
            page.deleteLater()
        self.app.processEvents()
        self.app.removeEventFilter(self.controller)
        self.controller._enabled = False
        language.install_language_controller(self.previous)
        self.temp.cleanup()

    def snapshot(self):
        with self.db.connect() as con:
            return tuple(con.iterdump())

    def modal(self, action, el, en, title_el, title_en, icon, inspect=None):
        errors=[]
        timer=QTimer()
        timer.setSingleShot(True)
        def visit():
            box=self.app.activeModalWidget()
            try:
                self.assertIsInstance(box,QMessageBox)
                for code in ("el","en","el"):
                    self.controller.set_language(code,persist=False)
                    self.controller.apply_to(box)
                    self.assertIs(self.app.activeModalWidget(),box)
                    self.assertEqual(box.text(),en if code=="en" else el)
                    self.assertEqual(box.windowTitle(),title_en if code=="en" else title_el)
                    self.assertEqual(box.icon(),icon)
                    self.assertEqual(box.standardButtons(),QMessageBox.StandardButton.Ok)
                    if inspect:
                        inspect(code)
            except BaseException as error:
                errors.append(error)
            finally:
                if isinstance(box,QMessageBox):
                    box.button(QMessageBox.StandardButton.Ok).click()
        timer.timeout.connect(visit)
        timer.start(0)
        try:
            action()
        finally:
            timer.stop()
        if errors:
            raise errors[0]
        self.assertEqual(self.snapshot(),self.before)
        self.assertEqual(self.page._rows_cache,self.rows)
        self.assertEqual(self.page.year.currentData(),2027)
        self.assertEqual(self.page.product_filter.currentData(),1)

    def test_helper_information_and_existing_icons(self):
        path = str(self.root / "report {2027} & Ω.csv")
        for kind,icon in (("information",QMessageBox.Icon.Information),("warning",QMessageBox.Icon.Warning),("question",QMessageBox.Icon.Question),("critical",QMessageBox.Icon.Critical)):
            self.modal(lambda:_message(self.page,kind,"Σφάλμα","{raw}",raw=path+RAW), path+RAW,path+RAW,"Σφάλμα","Error",icon)

    def csv_case(self,owner,failure=False):
        cls={"data_quality":DataQualityPage,"inventory_report":InventoryReportPage,"annual_report":AnnualFarmReportPage,"sales_report":SalesReportPage}[owner]
        path=self.root / "report {2027} & Ω.csv"
        title="Έλεγχος Δεδομένων" if owner=="data_quality" else "Εξαγωγή CSV"
        title_en="Data Checks" if owner=="data_quality" else "CSV export"
        action=lambda:cls.export_csv(self.page)
        with patch(f"app.{owner}.QFileDialog.getSaveFileName",return_value=(str(path),"CSV")):
            if failure:
                with patch.object(Path,"open",side_effect=OSError(RAW)):
                    self.modal(action, "Η εξαγωγή απέτυχε.\n\n"+RAW if owner=="data_quality" else RAW, "Export failed.\n\n"+RAW if owner=="data_quality" else RAW, title if owner=="data_quality" else "Σφάλμα εξαγωγής", title_en if owner=="data_quality" else "Export error",QMessageBox.Icon.Critical)
            else:
                el=("Το CSV δημιουργήθηκε επιτυχώς:\n" if owner=="data_quality" else "Η αναφορά αποθηκεύτηκε:\n")+str(path)
                en=("CSV created successfully:\n" if owner=="data_quality" else "Report saved:\n")+str(path)
                contents=[]
                self.modal(action,el,en,title,title_en,QMessageBox.Icon.Information,lambda code:contents.append(path.read_bytes()))
                self.assertTrue(contents[0].startswith(b'\xef\xbb\xbf'))
                self.assertEqual(contents,[contents[0]]*3)
                with path.open(encoding='utf-8-sig',newline='') as handle:
                    rows=list(csv.reader(handle,delimiter=';'))
                self.assertTrue(any(RAW in row for row in rows))

    def test_quality_success(self): self.csv_case("data_quality")
    def test_quality_error(self): self.csv_case("data_quality",True)
    def test_inventory_success(self): self.csv_case("inventory_report")
    def test_inventory_error(self): self.csv_case("inventory_report",True)
    def test_annual_success(self): self.csv_case("annual_report")
    def test_annual_error(self): self.csv_case("annual_report",True)
    def test_sales_success(self): self.csv_case("sales_report")

    def annual_new_format_case(self, failure=False):
        for kind in ("pdf", "xlsx"):
            path = self.root / f"report {{2027}} & Ω.{kind}"
            with patch("app.annual_report.QFileDialog.getSaveFileName", return_value=(str(path), "")), \
                 patch(f"app.annual_report.export_annual_{kind}", side_effect=OSError(RAW) if failure else None) as export:
                self.modal(lambda: getattr(AnnualFarmReportPage, "export_" + kind)(self.page),
                           RAW if failure else "Η αναφορά αποθηκεύτηκε:\n" + str(path),
                           RAW if failure else "Report saved:\n" + str(path),
                           "Σφάλμα εξαγωγής" if failure else "Εξαγωγή " + kind.upper(),
                           "Export error" if failure else kind.upper() + " export",
                           QMessageBox.Icon.Critical if failure else QMessageBox.Icon.Information)
                export.assert_called_once_with(path, self.page._annual_report_snapshot())

    def test_annual_pdf_xlsx_success(self): self.annual_new_format_case()
    def test_annual_pdf_xlsx_error(self): self.annual_new_format_case(True)

    def quality_xlsx_case(self, failure=False):
        path = self.root / "report {2027} & Ω.xlsx"
        with patch("app.data_quality.QFileDialog.getSaveFileName", return_value=(str(path), "")), \
             patch("app.data_quality.export_issue_xlsx", side_effect=OSError(RAW) if failure else None) as export:
            self.modal(lambda: DataQualityPage.export_xlsx(self.page),
                       "Η εξαγωγή απέτυχε.\n\n" + RAW if failure else "Το XLSX δημιουργήθηκε επιτυχώς:\n" + str(path),
                       "Export failed.\n\n" + RAW if failure else "XLSX created successfully:\n" + str(path),
                       "Έλεγχος Δεδομένων", "Data Checks",
                       QMessageBox.Icon.Critical if failure else QMessageBox.Icon.Information)
            self.assertEqual(export.call_args.args[0], path)
            self.assertEqual(export.call_args.args[2][0][2], RAW)

    def test_quality_xlsx_success(self): self.quality_xlsx_case()
    def test_quality_xlsx_error(self): self.quality_xlsx_case(True)

    def report_case(self,kind,failure=False):
        extension="pdf" if kind=="PDF" else "xlsx"
        method=ReportsPage.export_pdf if kind=="PDF" else ReportsPage.export_excel
        path=str(self.root/f"report {{2027}} & Ω.{extension}")
        with patch("app.reports.QFileDialog.getSaveFileName",return_value=(path,"")), patch(f"app.reports.export_report_{extension}",side_effect=OSError(RAW) if failure else None) as export:
            self.modal(lambda:method(self.page), "Η εξαγωγή απέτυχε.\n\n"+RAW if failure else f"Το {kind} δημιουργήθηκε:\n{path}", "Export failed.\n\n"+RAW if failure else f"{kind} created:\n{path}", f"Αποτυχία εξαγωγής {kind}" if failure else f"Εξαγωγή {kind}", f"{kind} export failed" if failure else f"{kind} export", QMessageBox.Icon.Critical if failure else QMessageBox.Icon.Information)
            export.assert_called_once_with(path,{"raw":RAW,"amount":12.5})

    def test_pdf_success(self): self.report_case("PDF")
    def test_pdf_error(self): self.report_case("PDF",True)
    def test_excel_success(self): self.report_case("Excel")
    def test_excel_error(self): self.report_case("Excel",True)

    def test_zip_creation_error(self):
        with patch("app.data_export.QFileDialog.getSaveFileName",return_value=(str(self.root/"export.zip"),"")), patch("app.data_export.zipfile.ZipFile",side_effect=OSError(RAW)):
            self.modal(self.zip_page.export_zip,"Η δημιουργία ZIP απέτυχε.\n\n"+RAW,"ZIP creation failed.\n\n"+RAW,"Εξαγωγή Δεδομένων","Data Export",QMessageBox.Icon.Critical)

    def test_zip_success_last_label_and_bytes(self):
        path=self.root/"report {2027} & Ω.zip"
        contents=[]
        def inspect(code):
            self.controller.apply_to(self.zip_page)
            self.assertEqual(self.zip_page.last_export_label.text(),("Last ZIP: " if code=="en" else "Τελευταίο ZIP: ")+str(path))
            self.assertEqual(self.zip_page.last_export_path,path)
            contents.append(path.read_bytes())
        with patch("app.data_export.QFileDialog.getSaveFileName",return_value=(str(path),"")):
            self.modal(self.zip_page.export_zip,"Το ZIP δημιουργήθηκε και ελέγχθηκε επιτυχώς.\n\n"+str(path),"ZIP created and verified successfully.\n\n"+str(path),"Εξαγωγή Δεδομένων","Data Export",QMessageBox.Icon.Information,inspect)
        self.assertEqual(contents,[contents[0]]*3)
        self.assertEqual(self.zip_page.last_export_label.textFormat(),Qt.TextFormat.PlainText)
        self.assertEqual(self.zip_page._verify_archive(path),(True,"OK"))

    def verification(self,path,el,en,icon=QMessageBox.Icon.Critical):
        self.zip_page.last_export_path=path
        self.modal(self.zip_page.verify_zip,el,en,"Έλεγχος ZIP","ZIP check",icon)

    def test_verify_raw_exception(self):
        with patch("app.data_export.zipfile.ZipFile",side_effect=OSError(RAW)):
            self.verification(self.root/"missing.zip","Ο έλεγχος απέτυχε.\n\n"+RAW,"Verification failed.\n\n"+RAW)

    def test_verify_missing_member(self):
        path=self.root/"member.zip"
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('README.txt','unchanged')
            z.writestr('manifest.json',json.dumps(dict(schema='mastixa-manager-portable-export-v1',tables=[dict(status='exported',file=MEMBER)])))
        before=path.read_bytes()
        self.assertEqual(str(self.zip_page._verify_archive(path)[1]),"Λείπει το αναμενόμενο αρχείο: "+MEMBER)
        self.verification(path,"Ο έλεγχος απέτυχε.\n\nΛείπει το αναμενόμενο αρχείο: "+MEMBER,"Verification failed.\n\nExpected file is missing: "+MEMBER)
        self.assertEqual(path.read_bytes(),before)

    def test_verify_crc_member(self):
        with patch("app.data_export.zipfile.ZipFile") as archive:
            archive.return_value.__enter__.return_value.testzip.return_value=MEMBER
            self.verification(self.root/'crc.zip',"Ο έλεγχος απέτυχε.\n\nCRC πρόβλημα στο αρχείο: "+MEMBER,"Verification failed.\n\nCRC problem in file: "+MEMBER)

    def test_verify_success(self):
        path=self.root/'valid.zip'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('README.txt','unchanged')
            z.writestr('manifest.json',json.dumps(dict(schema='mastixa-manager-portable-export-v1',tables=[])))
        self.verification(path,"Το τελευταίο ZIP είναι ακέραιο και έχει σωστή δομή.","The latest ZIP is intact and has a valid structure.",QMessageBox.Icon.Information)

    def test_verify_owned_structure_errors(self):
        for name, entries, el, en in (
            ("manifest", {}, "Λείπει το manifest.json.", "manifest.json is missing."),
            ("readme", {"manifest.json": "{}"}, "Λείπει το README.txt.", "README.txt is missing."),
            ("schema", {"manifest.json": "{}", "README.txt": "raw"}, "Μη αναμενόμενο schema στο manifest.", "Unexpected schema in manifest."),
        ):
            with self.subTest(name=name):
                path = self.root / (name + ".zip")
                with zipfile.ZipFile(path, "w") as archive:
                    for member, content in entries.items():
                        archive.writestr(member, content)
                self.assertEqual(self.zip_page._verify_archive(path), (False, el))
                before = path.read_bytes()
                self.verification(path, "Ο έλεγχος απέτυχε.\n\n" + el, "Verification failed.\n\n" + en)
                self.assertEqual(path.read_bytes(), before)

    def test_export_verification_warning(self):
        from app.data_export import _VerificationMessage
        for detail, el, en in (
            (RAW, RAW, RAW),
            (_VerificationMessage("CRC πρόβλημα στο αρχείο: {file}", file=MEMBER),
             "CRC πρόβλημα στο αρχείο: " + MEMBER, "CRC problem in file: " + MEMBER),
        ):
            with self.subTest(detail=detail):
                path = self.root / "warning.zip"
                contents = []
                with patch("app.data_export.QFileDialog.getSaveFileName", return_value=(str(path), "")), patch.object(self.zip_page, "_verify_archive", return_value=(False, detail)):
                    self.modal(self.zip_page.export_zip,
                               "Το ZIP δημιουργήθηκε, αλλά ο έλεγχος βρήκε πρόβλημα.\n\n" + el,
                               "ZIP created, but verification found a problem.\n\n" + en,
                               "Εξαγωγή Δεδομένων", "Data Export", QMessageBox.Icon.Warning,
                               lambda code: contents.append(path.read_bytes()))
                self.assertEqual(contents, [contents[0]] * 3)
