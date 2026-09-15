from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication, QLabel, QWidget

from app.appearance_theme import ThemeController, _dark_local_style


class ThemeSwitchPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_dark_local_style_conversion_is_cached(self) -> None:
        _dark_local_style.cache_clear()
        original = "QLabel { background: #f5f6f3; color: #21483A; }"

        converted = _dark_local_style(original)
        first = _dark_local_style.cache_info()
        converted_again = _dark_local_style(original)
        second = _dark_local_style.cache_info()

        self.assertEqual(converted, converted_again)
        self.assertIn("#171d21", converted)
        self.assertIn("#e7ecef", converted)
        self.assertEqual(1, first.misses)
        self.assertEqual(first.hits + 1, second.hits)

    def test_full_tree_switch_still_converts_and_restores_local_style(self) -> None:
        original_app_style = self.app.styleSheet()
        original_palette = self.app.palette()
        root = QWidget()
        child = QLabel("Theme child", root)
        original_local = (
            "QLabel { background: #f5f6f3; color: #21483A; "
            "border: 1px solid #d6e0da; }"
        )
        child.setStyleSheet(original_local)
        controller = ThemeController(
            self.app,
            original_app_style,
            original_palette,
        )
        controller._theme = "light"

        try:
            controller.set_theme("dark", persist=False)
            dark_local = child.styleSheet()
            self.assertIn("#171d21", dark_local)
            self.assertIn("#e7ecef", dark_local)
            self.assertIn("#3a454c", dark_local)

            controller.set_theme("light", persist=False)
            self.assertEqual(original_local, child.styleSheet())
        finally:
            self.app.removeEventFilter(controller)
            self.app.setPalette(original_palette)
            self.app.setStyleSheet(original_app_style)
            root.close()


if __name__ == "__main__":
    unittest.main()
