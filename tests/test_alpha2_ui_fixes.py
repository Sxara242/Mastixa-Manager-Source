import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox, QTabWidget, QWidget

from app import appearance_theme, icon_normalization, icon_theme, main_window
from app.alpha2_ui_fixes import (
    _apply_themed_tab_icons,
    _literal_ampersands,
    install_alpha2_ui_fixes,
)
from app.language import LanguageController


class Alpha2UiFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        install_alpha2_ui_fixes()

    def test_ampersand_rendering_is_literal_and_idempotent(self):
        source = "Άρδευση & Λίπανση"
        escaped = "Άρδευση && Λίπανση"
        self.assertEqual(escaped, _literal_ampersands(source))
        self.assertEqual(escaped, _literal_ampersands(escaped))

    def test_english_pack_contains_escaped_ampersand_variants(self):
        packs = LanguageController._load_packs()
        english = packs["en"].translations
        self.assertIn("Άρδευση && Λίπανση", english)
        self.assertIn("&&", english["Άρδευση && Λίπανση"])

    def test_alpha2_new_and_report_pages_have_exact_themed_icons(self):
        expected = {
            "Προϊόντα και καλλιέργειες": "products.png",
            "Πρόγραμμα Καλλιέργειας": "calendar.png",
            "Μεμονωμένα Φυτά / Δέντρα": "field_profile.png",
            "Αισθητήρες / API": "settings.png",
            "Εξαγωγή Δεδομένων": "package_preview.png",
            "Ιστορικό Ενεργειών": "reports.png",
            "Αναφορά Πωλήσεων & Stock": "sales.png",
            "Αναφορά Αποθήκης & Αξίας Stock": "warehouse.png",
            "Έλεγχος & Δεδομένα": "data_quality.png",
        }
        for label, filename in expected.items():
            with self.subTest(label=label):
                path = icon_theme._path_for_text(label)
                self.assertIsNotNone(path)
                self.assertEqual(filename, path.name)

    def test_appended_cultivation_tabs_do_not_duplicate_parent_icons(self):
        cultivation_parent = icon_theme._path_for_text("Καλλιέργεια")
        program = icon_theme._path_for_text("Πρόγραμμα Καλλιέργειας")
        plantings_parent = icon_theme._path_for_text("Φυτεύσεις & Δέντρα")
        individual = icon_theme._path_for_text("Μεμονωμένα Φυτά / Δέντρα")

        self.assertIsNotNone(cultivation_parent)
        self.assertIsNotNone(program)
        self.assertIsNotNone(plantings_parent)
        self.assertIsNotNone(individual)
        self.assertNotEqual(cultivation_parent.name, program.name)
        self.assertNotEqual(plantings_parent.name, individual.name)

    def test_appended_page_tab_uses_theme_icon_before_legacy_placeholder(self):
        class DummyWindow:
            pages = [("Πρόγραμμα Καλλιέργειας", object())]

        icon = main_window.MainWindow._tab_icon_for_page(DummyWindow(), 0)
        self.assertIsNotNone(icon)
        self.assertFalse(icon.isNull())

    def test_visible_appended_tabs_replace_generic_file_placeholders(self):
        tabs = QTabWidget()
        labels = (
            "Πρόγραμμα Καλλιέργειας",
            "Μεμονωμένα Φυτά / Δέντρα",
            "Αισθητήρες / API",
        )
        pages = []
        for label in labels:
            page = QWidget()
            pages.append(page)
            tabs.addTab(page, QIcon(), label)

        self.assertTrue(all(tabs.tabIcon(i).isNull() for i in range(tabs.count())))
        changed = _apply_themed_tab_icons(tabs)

        self.assertEqual(len(labels), changed)
        self.assertTrue(all(not tabs.tabIcon(i).isNull() for i in range(tabs.count())))
        tabs.deleteLater()

    def test_first_page_icon_refresh_is_scoped_and_runs_only_once(self):
        class DummyPage(QWidget):
            def __init__(self):
                super().__init__()
                self.refresh_count = 0

            def refresh(self):
                self.refresh_count += 1

        page = DummyPage()

        class DummyWindow:
            pages = [("Πρόγραμμα Καλλιέργειας", page)]

            @staticmethod
            def _current_page_index():
                return 0

        calls = []
        original_apply = icon_theme.apply_icon_theme
        try:
            icon_theme.apply_icon_theme = lambda target: calls.append(target) or 0
            main_window.MainWindow._refresh_current_tab(DummyWindow())
            main_window.MainWindow._refresh_current_tab(DummyWindow())
        finally:
            icon_theme.apply_icon_theme = original_apply

        self.assertEqual(2, page.refresh_count)
        self.assertEqual([page], calls)
        page.deleteLater()

    def test_shaped_badge_removes_outer_white_but_preserves_metallic_and_dark_rim(self):
        image = QImage(128, 128, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#E8E8E8"))
        painter.drawEllipse(QRect(8, 8, 112, 112))
        painter.setBrush(QColor("#A8A8A8"))
        painter.drawEllipse(QRect(16, 16, 96, 96))
        painter.setBrush(QColor("#62666A"))
        painter.drawEllipse(QRect(23, 23, 82, 82))
        painter.setBrush(QColor("#124F86"))
        painter.drawEllipse(QRect(29, 29, 70, 70))
        painter.end()

        self.assertTrue(icon_normalization._has_shaped_transparency(image))
        normalized = icon_normalization._normalize_image(image)
        self.assertFalse(normalized.isNull())

        medium_metallic = 0
        outer_white = 0
        dark_rim = 0
        for y in range(normalized.height()):
            for x in range(normalized.width()):
                color = normalized.pixelColor(x, y)
                if color.alpha() <= icon_normalization._ALPHA_CUTOFF:
                    continue
                channels = (color.red(), color.green(), color.blue())
                chroma = max(channels) - min(channels)
                if 125 <= min(channels) <= 205 and chroma <= 40:
                    medium_metallic += 1
                if min(channels) >= 222 and chroma <= 30:
                    outer_white += 1
                if 60 <= min(channels) <= 115 and chroma <= 40:
                    dark_rim += 1

        self.assertGreater(medium_metallic, 1000)
        self.assertLess(outer_white, 200)
        self.assertGreater(dark_rim, 100)

    def test_outer_white_ring_is_removed_without_touching_metallic_badge(self):
        image = QImage(160, 160, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FAFAFA"))
        painter.drawEllipse(QRect(5, 5, 150, 150))
        painter.setBrush(QColor("#A8A8A8"))
        painter.drawEllipse(QRect(18, 18, 124, 124))
        painter.setBrush(QColor("#5E646A"))
        painter.drawEllipse(QRect(29, 29, 102, 102))
        painter.setBrush(QColor("#124F86"))
        painter.drawEllipse(QRect(37, 37, 86, 86))
        painter.end()

        cleaned = icon_normalization._clear_outer_light_neutral_ring(image)
        self.assertFalse(cleaned.isNull())

        metallic = 0
        outer_white = 0
        dark_outline = 0
        for y in range(cleaned.height()):
            for x in range(cleaned.width()):
                color = cleaned.pixelColor(x, y)
                if color.alpha() <= icon_normalization._ALPHA_CUTOFF:
                    continue
                channels = (color.red(), color.green(), color.blue())
                chroma = max(channels) - min(channels)
                if 125 <= min(channels) <= 205 and chroma <= 40:
                    metallic += 1
                if min(channels) >= 222 and chroma <= 30:
                    outer_white += 1
                if 55 <= min(channels) <= 115 and chroma <= 40:
                    dark_outline += 1

        self.assertGreater(metallic, 1000)
        self.assertLess(outer_white, 200)
        self.assertGreater(dark_outline, 100)

    def test_dark_mode_has_specific_activity_background_override(self):
        self.assertIn("QWidget#activitiesContent", appearance_theme.DARK_STYLESHEET)
        self.assertIn("QScrollArea#activitiesScroll", appearance_theme.DARK_STYLESHEET)

    def test_dark_message_box_gets_dialog_local_high_contrast_style(self):
        controller = appearance_theme.ThemeController(
            self.app,
            "",
            QPalette(self.app.palette()),
        )
        controller._theme = "dark"
        box = QMessageBox()
        box.setText("Dark body text")
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        try:
            self.assertEqual("", box.styleSheet())
            controller._apply_local_styles(box)

            style = box.styleSheet()
            self.assertIn("QMessageBox QLabel", style)
            self.assertIn("#F2F6F4", style)
            self.assertIn("#20272C", style)
            self.assertIn("QMessageBox QPushButton", style)

            controller._theme = "light"
            controller._apply_local_styles(box)
            self.assertEqual("", box.styleSheet())
        finally:
            controller.deleteLater()
            box.deleteLater()

    def test_dark_local_style_is_converted_synchronously_on_show(self):
        controller = appearance_theme.ThemeController(
            self.app,
            "",
            QPalette(self.app.palette()),
        )
        controller._theme = "dark"
        widget = QWidget()
        widget.setStyleSheet("QWidget { background: #f5f6f3; }")

        controller.eventFilter(widget, QEvent(QEvent.Type.Show))

        self.assertIn("#171d21", widget.styleSheet().casefold())
        controller.deleteLater()
        widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
