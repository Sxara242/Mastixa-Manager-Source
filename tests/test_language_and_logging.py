from __future__ import annotations

import logging
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTextEdit,
    QWidget,
)

from app.appearance_theme import ThemeController
from app.app_logging import _PrivacyFormatter
from app.database import Database
from app.language import (
    LanguageController,
    _has_greek,
    combo_source_text,
    install_language_controller,
)
from app.main_window import MainWindow, STYLESHEET, build_app_palette
from app.profile_manager import ProfileManager
from app.settings import ProfileSelectionDialog
from app.exporters import export_report_xlsx


class LanguageAndLoggingTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_live_language_switch_persists_per_profile_without_restart(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            Database(manager.active_profile.database_path)
            palette = build_app_palette()
            self.app.setPalette(palette)
            self.app.setStyleSheet(STYLESHEET)
            theme = ThemeController(self.app, STYLESHEET, palette)
            language = LanguageController(self.app, manager)
            window = MainWindow(theme, manager, language)
            try:
                original_identity = id(window)
                window.show()
                language.set_language("en")
                QTest.qWait(80)
                self.assertEqual(original_identity, id(window))
                self.assertEqual("en", manager.active_profile.language)
                self.assertEqual("Main", window.category_list.item(0).text())
                settings_page = window.pages[31][1]
                self.assertEqual("Settings", settings_page.findChild(
                    type(settings_page.language_status), "pageTitle"
                ).text())
                self.assertEqual(
                    {"Ελληνικά", "English"},
                    {button.text() for button in settings_page.language_buttons.values()},
                )
                language.set_language("el")
                QTest.qWait(50)
                self.assertEqual("Κύρια", window.category_list.item(0).text())
            finally:
                window._skip_close_backup = True
                window.close()
                window.deleteLater()
                QTest.qWait(30)

    def test_saved_english_profile_starts_key_pages_fully_in_english(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            manager.set_language(manager.active_profile.id, "en")
            db = Database(manager.active_profile.database_path)
            db.execute(
                "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
                ("Test product", "kg"),
            )
            palette = build_app_palette()
            self.app.setPalette(palette)
            self.app.setStyleSheet(STYLESHEET)
            theme = ThemeController(self.app, STYLESHEET, palette)
            language = LanguageController(self.app, manager)
            window = MainWindow(theme, manager, language)
            try:
                window.show()
                QTest.qWait(120)
                self.assertEqual("en", language.language)
                target_pages = {
                    "Fields": window.pages[2][1],
                    "Production": window.pages[3][1],
                    "Income": window.pages[4][1],
                    "Expenses": window.pages[5][1],
                    "Declaration": window.pages[6][1],
                    "Package preview": window.pages[7][1],
                    "Reports": window.pages[8][1],
                    "Irrigation and fertilization": window.pages[12][1],
                    "Inventory": window.pages[13][1],
                    "Year lock": window.pages[14][1],
                    "Suppliers and buyers": window.pages[17][1],
                    "Plant protection": window.pages[19][1],
                    "Costs by field": window.pages[20][1],
                    "Labor": window.pages[21][1],
                    "Global search": window.pages[22][1],
                    "Plantings": window.pages[23][1],
                    "Production sales": window.pages[26][1],
                    "Sales report": window.pages[27][1],
                    "Annual farm report": window.pages[29][1],
                    "Products": window.pages[30][1],
                    "Settings": window.pages[31][1],
                }
                missing: dict[str, list[str]] = {}
                page_indices = (
                    2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 17, 19, 20, 21, 22,
                    23, 26, 27, 29, 30, 31,
                )
                for (page_name, page), page_index in zip(
                    target_pages.items(), page_indices
                ):
                    window.change_page(page_index)
                    QTest.qWait(50)
                    greek = self._static_greek_texts(page)
                    if greek:
                        missing[page_name] = greek
                self.assertEqual({}, missing)
                self.assertEqual(" decares", window.pages[2][1].area.suffix())
                self.assertIn("1,000 m²", window.pages[2][1].area.toolTip())
                self.assertEqual(
                    "kg/decare", window.pages[19][1].dose_unit.currentText()
                )
                global_search = window.pages[22][1]
                global_search.result_label.setText("8 αποτελέσματα")
                package_preview = window.pages[7][1]
                package_preview.validation_status.setText(
                    "⚠ Το πακέτο είναι έτοιμο με προειδοποιήσεις."
                )
                package_preview.validation_details.setText(
                    "Προειδοποίηση: 1 αγροτεμάχιο/α δεν έχουν "
                    "συμπληρωμένο ΚΑΕΚ."
                )
                QTest.qWait(80)
                self.assertEqual("8 results", global_search.result_label.text())
                self.assertEqual(
                    "⚠ The package is ready with warnings.",
                    package_preview.validation_status.text(),
                )
                self.assertEqual(
                    "Warning: 1 field(s) do not have a Land registry ID.",
                    package_preview.validation_details.text(),
                )
                year_lock_table = window.pages[14][1].table
                self.assertTrue(year_lock_table.rowCount() > 0)
                self.assertFalse(
                    any(
                        _has_greek(year_lock_table.item(row, 1).text())
                        for row in range(year_lock_table.rowCount())
                    )
                )
                products_table = window.pages[30][1].table
                self.assertTrue(products_table.rowCount() > 0)
                self.assertFalse(
                    any(
                        _has_greek(products_table.item(row, 2).text())
                        for row in range(products_table.rowCount())
                    )
                )
                reports_page = window.pages[8][1]
                self.assertFalse(
                    _has_greek(reports_page.production_chart.translated_title())
                )
                self.assertFalse(
                    _has_greek(reports_page.balance_chart.translated_title())
                )
                self.assertEqual(
                    "No data available",
                    language.translate("Δεν υπάρχουν δεδομένα"),
                )
            finally:
                window._skip_close_backup = True
                window.close()
                window.deleteLater()
                QTest.qWait(30)

    @staticmethod
    def _static_greek_texts(root: QWidget) -> list[str]:
        missing: set[str] = set()
        for widget in [root, *root.findChildren(QWidget)]:
            candidates = [
                widget.windowTitle(),
                widget.toolTip(),
                widget.statusTip(),
                widget.whatsThis(),
                widget.accessibleName(),
            ]
            if isinstance(widget, (QLabel, QAbstractButton)):
                candidates.append(widget.text())
            if isinstance(widget, QGroupBox):
                candidates.append(widget.title())
            if isinstance(widget, QLineEdit):
                candidates.append(widget.placeholderText())
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                candidates.append(widget.placeholderText())
                if widget.property("mastixaI18nStaticText"):
                    candidates.append(widget.toPlainText())
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                candidates.extend(
                    (widget.prefix(), widget.suffix(), widget.specialValueText())
                )
            if isinstance(widget, QTabWidget):
                candidates.extend(
                    widget.tabText(index) for index in range(widget.count())
                )
            if isinstance(widget, QTableWidget):
                candidates.extend(
                    item.text()
                    for index in range(widget.columnCount())
                    if (item := widget.horizontalHeaderItem(index)) is not None
                )
            if isinstance(widget, QComboBox) and (
                not widget.isEditable()
                or widget.property("mastixaI18nStaticItems")
            ):
                candidates.extend(
                    widget.itemText(index)
                    for index in range(widget.count())
                    if not isinstance(widget.itemData(index), int)
                    and widget.itemText(index) != "Μαστίχα"
                )
            missing.update(
                text
                for text in candidates
                if text
                and _has_greek(text)
                and text != "Ελληνικά"
                and "Κύριο προφίλ" not in text
                and "Database:" not in text
            )
        return sorted(missing)

    def test_profile_chooser_exposes_native_language_names_before_login(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            language = LanguageController(self.app, manager)
            chooser = ProfileSelectionDialog(manager, language)
            try:
                names = {
                    chooser.language_combo.itemText(index)
                    for index in range(chooser.language_combo.count())
                }
                self.assertEqual({"Ελληνικά", "English"}, names)
                chooser.language_combo.setCurrentIndex(
                    chooser.language_combo.findData("en")
                )
                QTest.qWait(30)
                self.assertEqual("Profile selection", chooser.windowTitle())
            finally:
                chooser.close()
                chooser.deleteLater()

    def test_translated_combo_retains_canonical_source_value(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            language = LanguageController(self.app, manager)
            combo = QComboBox()
            combo.addItems(["Ενεργό", "Ανενεργό"])
            language.set_language("en")
            language.apply_to(combo)
            self.assertEqual("Active", combo.currentText())
            self.assertEqual("Ενεργό", combo_source_text(combo))
            combo.setCurrentIndex(1)
            self.assertEqual("Inactive", combo.currentText())
            self.assertEqual("Ανενεργό", combo_source_text(combo))
            language.set_language("el")
            language.apply_to(combo)
            self.assertEqual("Ανενεργό", combo.currentText())

    def test_diagnostic_formatter_redacts_local_paths(self) -> None:
        formatter = _PrivacyFormatter(
            "%(message)s",
            redactions=((r"C:\\Users\\private\\Mastixa", "<APP_DIR>"),),
        )
        record = logging.LogRecord(
            "mastixa.test",
            logging.ERROR,
            __file__,
            1,
            r"Failure at C:\\Users\\private\\Mastixa\\app\\main.py",
            (),
            None,
        )
        rendered = formatter.format(record)
        self.assertIn("<APP_DIR>", rendered)
        self.assertNotIn("private", rendered)

    def test_report_export_uses_active_language(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            manager = ProfileManager(Path(folder))
            language = LanguageController(self.app, manager)
            install_language_controller(language)
            language.set_language("en")
            output = Path(folder) / "report.xlsx"
            export_report_xlsx(
                str(output),
                {
                    "year_label": "Όλα τα έτη",
                    "production": 5.0,
                    "income": 10.0,
                    "expenses": 2.0,
                    "balance": 8.0,
                    "yearly_rows": [],
                    "field_rows": [],
                },
            )
            with zipfile.ZipFile(output) as package:
                text = (
                    package.read("xl/workbook.xml")
                    + package.read("xl/worksheets/sheet1.xml")
                    + package.read("xl/worksheets/sheet2.xml")
                ).decode("utf-8")
            self.assertIn("Summary", text)
            self.assertIn("Production kg", text)
            self.assertNotRegex(text, r"[Α-Ωα-ωάέήίόύώϊϋΐΰ]")


if __name__ == "__main__":
    unittest.main()
