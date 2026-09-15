from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest


class IconThemePerformanceTests(unittest.TestCase):
    def test_repeated_title_icon_pass_does_not_repeat_geometry_mutations(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtCore import QSize
            from PySide6.QtWidgets import QApplication, QLabel, QWidget
            import app.icon_theme as icon_theme
            import app.icon_theme_performance as perf

            app = QApplication.instance() or QApplication([])

            class CountingLabel(QLabel):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.calls = {
                        "max_height": 0,
                        "min_height": 0,
                        "margins": 0,
                        "fixed_size": 0,
                        "pixmap": 0,
                        "move": 0,
                        "show": 0,
                        "raise": 0,
                    }

                def setMaximumHeight(self, value):
                    self.calls["max_height"] += 1
                    return super().setMaximumHeight(value)

                def setMinimumHeight(self, value):
                    self.calls["min_height"] += 1
                    return super().setMinimumHeight(value)

                def setContentsMargins(self, *args):
                    self.calls["margins"] += 1
                    return super().setContentsMargins(*args)

                def setFixedSize(self, *args):
                    self.calls["fixed_size"] += 1
                    return super().setFixedSize(*args)

                def setPixmap(self, pixmap):
                    self.calls["pixmap"] += 1
                    return super().setPixmap(pixmap)

                def move(self, *args):
                    self.calls["move"] += 1
                    return super().move(*args)

                def show(self):
                    self.calls["show"] += 1
                    return super().show()

                def raise_(self):
                    self.calls["raise"] += 1
                    return super().raise_()

            perf.QLabel = CountingLabel
            root = QWidget()
            title = CountingLabel("Παραγωγή", root)
            title.setObjectName("pageTitle")

            assert perf._apply_page_title_icons_idempotent(root) == 1
            child = title._mastixa_title_icon_label
            normalized_size = icon_theme._TITLE_ICON_SIZE
            assert child.minimumSize() == normalized_size
            assert child.maximumSize() == normalized_size

            title_before = dict(title.calls)
            child_before = dict(child.calls)

            assert perf._apply_page_title_icons_idempotent(root) == 1
            assert title.calls == title_before, (
                "second identical pass must not repeat title geometry setters",
                title_before,
                title.calls,
            )
            assert child.calls == child_before, (
                "second identical pass must not resize/repaint/move/show the icon",
                child_before,
                child.calls,
            )

            # A genuine icon change at the same normalized size updates only the pixmap.
            title.setText("Πωλήσεις Παραγωγής")
            assert perf._apply_page_title_icons_idempotent(root) == 1
            assert child.calls["fixed_size"] == child_before["fixed_size"]
            assert child.calls["pixmap"] == child_before["pixmap"] + 1
            assert child.minimumSize() == normalized_size
            assert child.maximumSize() == normalized_size

            # A genuine size change must still update both geometry and pixmap.
            before_size_change = dict(child.calls)
            custom_size = QSize(normalized_size.width() + 4, normalized_size.height() + 4)
            icon_theme._CUSTOM_TITLE_ICON_SIZES["sales.png"] = custom_size
            assert perf._apply_page_title_icons_idempotent(root) == 1
            assert child.calls["fixed_size"] == before_size_change["fixed_size"] + 1
            assert child.calls["pixmap"] == before_size_change["pixmap"] + 1
            assert child.minimumSize() == custom_size
            assert child.maximumSize() == custom_size

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

    def test_navigation_installer_enables_idempotent_title_icons(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtWidgets import QApplication
            from app.navigation_performance import install_navigation_performance
            import app.icon_theme as icon_theme
            import app.icon_theme_performance as perf

            app = QApplication.instance() or QApplication([])
            install_navigation_performance()
            assert icon_theme._apply_page_title_icons is perf._apply_page_title_icons_idempotent
            assert icon_theme._mastixa_idempotent_title_icons is True
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


if __name__ == "__main__":
    unittest.main()
