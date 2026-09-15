from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest


class NavigationPerformanceTests(unittest.TestCase):
    def test_already_styled_show_is_skipped_but_new_widget_is_processed(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtGui import QPalette
            from PySide6.QtWidgets import QApplication, QWidget

            from app.appearance_theme import ThemeController
            from app.navigation_performance import install_navigation_performance

            app = QApplication.instance() or QApplication([])
            install_navigation_performance()
            controller = ThemeController(app, app.styleSheet(), QPalette(app.palette()))
            controller._theme = "dark"
            controller._mastixa_style_generation = 7

            root = QWidget()
            controller._apply_local_styles(root)

            calls = []
            original_apply = controller._apply_local_styles

            def counting_apply(widget):
                calls.append(widget)
                original_apply(widget)

            controller._apply_local_styles = counting_apply

            controller._style_new_widget(root)
            assert calls == [], "already styled root should not be rescanned"

            child = QWidget(root)
            controller._style_new_widget(child)
            assert calls == [child], "new child must still receive theme processing"
            assert child._mastixa_theme_style_generation == 7

            app.removeEventFilter(controller)
            root.close()
            """
        )
        env = dict(os.environ)
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=os.getcwd(),
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_installer_is_wired_before_app_start(self) -> None:
        with open("main.py", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("install_navigation_performance()", source)
        self.assertLess(
            source.index("install_navigation_performance()"),
            source.index("main_window.run_app()"),
        )


if __name__ == "__main__":
    unittest.main()
