import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QStyleOptionComboBox,
    QWidget,
)

from app import icon_theme
from app.alpha2_step4_ui import install_alpha2_step4_ui
from app.alpha2_ui_fixes import install_alpha2_ui_fixes
from app.data_export import DataExportPage
from app.data_quality import DataQualityPage
from app.database import Database
from app.fields import FieldsPage
from app.plant_protection import PlantProtectionPage


class Alpha2Step4UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        install_alpha2_ui_fixes()
        install_alpha2_step4_ui()

    def make_db(self, root: Path) -> Database:
        return Database(root / "farm.db")

    def test_standard_message_box_buttons_keep_qt_mnemonic_not_literal_ampersand(self) -> None:
        box = QMessageBox()
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        yes_button = box.button(QMessageBox.StandardButton.Yes)
        no_button = box.button(QMessageBox.StandardButton.No)
        self.assertIsNotNone(yes_button)
        self.assertIsNotNone(no_button)
        yes_button.setText("&Yes")
        no_button.setText("&No")

        ordinary = QPushButton("Save & Close", box)
        icon_theme._apply_icon_theme_impl(box)

        self.assertEqual("&Yes", yes_button.text())
        self.assertEqual("&No", no_button.text())
        self.assertEqual("Save && Close", ordinary.text())
        box.deleteLater()

    def test_dose_unit_combo_fits_current_and_future_content(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = PlantProtectionPage(self.make_db(Path(folder)))
            try:
                initial_width = page.dose_unit.minimumWidth()
                self.assertGreater(initial_width, 0)
                self.assertGreaterEqual(
                    page.dose_unit.view().minimumWidth(),
                    initial_width - 16,
                )

                page.dose_unit.addItem(
                    "very long future agricultural dose unit description"
                )
                self.assertGreater(page.dose_unit.minimumWidth(), initial_width)
                self.assertGreaterEqual(
                    page.dose_unit.view().minimumWidth(),
                    page.dose_unit.minimumWidth() - 16,
                )

                # Editable/custom values must also fit the CLOSED control even
                # though they do not exist in the combo's item model.
                custom = "custom translated agricultural dose unit"
                page.dose_unit.setEditText(custom)
                self.app.processEvents()

                metrics = page.dose_unit.fontMetrics()
                option = QStyleOptionComboBox()
                page.dose_unit.initStyleOption(option)
                option.currentText = custom
                required = page.dose_unit.style().sizeFromContents(
                    QStyle.ContentsType.CT_ComboBox,
                    option,
                    QSize(metrics.horizontalAdvance(custom), metrics.height()),
                    page.dose_unit,
                ).width()
                self.assertGreaterEqual(
                    page.dose_unit.minimumWidth(),
                    required,
                )
            finally:
                page.deleteLater()

    def test_data_quality_metric_cards_have_safe_vertical_space(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = DataQualityPage(self.make_db(Path(folder)))
            try:
                for box, value_label in (
                    page.error_card,
                    page.warning_card,
                    page.total_card,
                    page.status_card,
                ):
                    self.assertGreaterEqual(box.minimumHeight(), 112)
                    self.assertGreaterEqual(value_label.minimumHeight(), 42)
            finally:
                page.deleteLater()

    def test_data_quality_page_scroll_contains_cards_filters_and_table(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = DataQualityPage(self.make_db(Path(folder)))
            try:
                scroll = page.findChild(QScrollArea, "dataQualityScroll")
                self.assertIsNotNone(scroll)
                self.assertTrue(scroll.widgetResizable())
                content = scroll.widget()
                self.assertIsNotNone(content)

                for card, _value_label in (
                    page.error_card,
                    page.warning_card,
                    page.total_card,
                    page.status_card,
                ):
                    self.assertTrue(content.isAncestorOf(card))

                self.assertTrue(content.isAncestorOf(page.severity_filter))
                self.assertTrue(content.isAncestorOf(page.category_filter))
                self.assertTrue(content.isAncestorOf(page.search))
                self.assertTrue(content.isAncestorOf(page.table))
                self.assertGreaterEqual(page.table.minimumHeight(), 440)
            finally:
                page.deleteLater()

    def test_data_export_selection_uses_explicit_checkbox_boxes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = DataExportPage(self.make_db(Path(folder)))
            try:
                checks = [page.product_filter_check, *page.section_checks.values()]
                self.assertGreater(len(checks), 3)
                for check in checks:
                    with self.subTest(text=check.text()):
                        self.assertGreaterEqual(check.minimumHeight(), 28)
                        style = check.styleSheet()
                        self.assertIn("QCheckBox::indicator", style)
                        self.assertIn("indicator:checked", style)
                        self.assertIn("indicator:unchecked:hover", style)
                        self.assertIn("indicator:checked:hover", style)
                        self.assertIn("image: url(", style)
                        self.assertIn("checkmark.svg", style)
            finally:
                page.deleteLater()

    def test_fields_page_scroll_contains_bottom_actions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = FieldsPage(self.make_db(Path(folder)))
            try:
                scroll = page.findChild(QScrollArea, "fieldsScroll")
                self.assertIsNotNone(scroll)
                content = scroll.widget()
                self.assertIsNotNone(content)
                self.assertTrue(content.isAncestorOf(page.table))
                self.assertTrue(content.isAncestorOf(page.map_button))
                self.assertTrue(content.isAncestorOf(page.coordinates_button))
                self.assertGreaterEqual(page.table.minimumHeight(), 260)
            finally:
                page.deleteLater()


if __name__ == "__main__":
    unittest.main()
