import os
import subprocess
import sys
import textwrap
import unittest


class FocusAccessibilityTests(unittest.TestCase):
    def _run_case(self, body: str) -> None:
        code = textwrap.dedent(
            f"""
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtGui import QPalette
            from PySide6.QtWidgets import QApplication

            from app.appearance_theme import ThemeController
            from app.focus_accessibility import (
                DARK_FOCUS_STYLESHEET,
                LIGHT_FOCUS_STYLESHEET,
            )

            app = QApplication.instance() or QApplication([])
            previous_stylesheet = app.styleSheet()
            previous_palette = QPalette(app.palette())
            controller = ThemeController(
                app,
                "QPushButton {{ padding: 9px 16px; }}",
                previous_palette,
            )

            def force_theme(theme: str) -> str:
                controller._theme = ""
                controller.set_theme(theme, persist=False)
                return app.styleSheet()

            {textwrap.indent(textwrap.dedent(body), '            ').lstrip()}
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

    def test_light_theme_has_visible_focus_for_common_keyboard_controls(self):
        self._run_case(
            """
            style = force_theme("light")
            assert "MASTIXA_ACCESSIBLE_FOCUS_LIGHT" in style
            assert "MASTIXA_ACCESSIBLE_FOCUS_DARK" not in style
            assert "QPushButton:focus" in style
            assert "QToolButton:focus" in style
            assert "QLineEdit:focus" in style
            assert "QComboBox:focus" in style
            assert "QCheckBox:focus" in style
            assert "QRadioButton:focus" in style
            assert "#1F5A43" in style
            assert style.count("MASTIXA_ACCESSIBLE_FOCUS_LIGHT") == 1
            """
        )

    def test_dark_theme_overrides_focus_ring_without_duplicate_theme_pass(self):
        self._run_case(
            """
            style = force_theme("dark")
            assert "MASTIXA_ACCESSIBLE_FOCUS_LIGHT" in style
            assert "MASTIXA_ACCESSIBLE_FOCUS_DARK" in style
            assert "#9CCFB2" in style
            assert style.count("MASTIXA_ACCESSIBLE_FOCUS_LIGHT") == 1
            assert style.count("MASTIXA_ACCESSIBLE_FOCUS_DARK") == 1
            assert style.rstrip().endswith(DARK_FOCUS_STYLESHEET.rstrip())

            light_again = force_theme("light")
            assert light_again.count("MASTIXA_ACCESSIBLE_FOCUS_LIGHT") == 1
            assert "MASTIXA_ACCESSIBLE_FOCUS_DARK" not in light_again
            assert light_again.rstrip().endswith(LIGHT_FOCUS_STYLESHEET.rstrip())
            """
        )


if __name__ == "__main__":
    unittest.main()
