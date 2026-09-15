from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest


class IconNavigationPerformanceTests(unittest.TestCase):
    def test_navigation_signals_are_scoped_to_the_emitting_container(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtWidgets import (
                QApplication,
                QListWidget,
                QStackedWidget,
                QTabWidget,
                QToolBox,
                QWidget,
            )
            from app.icon_navigation_performance import _connect_scoped_navigation

            app = QApplication.instance() or QApplication([])
            root = QWidget()
            tabs = QTabWidget(root)
            tabs.addTab(QWidget(), "One")
            tabs.addTab(QWidget(), "Two")
            stack = QStackedWidget(root)
            stack.addWidget(QWidget())
            stack.addWidget(QWidget())
            toolbox = QToolBox(root)
            toolbox.addItem(QWidget(), "One")
            toolbox.addItem(QWidget(), "Two")
            category = QListWidget(root)
            category.addItems(["One", "Two"])

            class Recorder:
                def __init__(self):
                    self.calls = []
                def schedule(self, target, delay=0):
                    self.calls.append((target, delay))

            recorder = Recorder()
            _connect_scoped_navigation(root, recorder)

            tabs.setCurrentIndex(1)
            stack.setCurrentIndex(1)
            toolbox.setCurrentIndex(1)
            category.setCurrentRow(1)

            assert (tabs, 0) in recorder.calls
            assert (tabs, 120) in recorder.calls
            assert (stack, 0) in recorder.calls
            assert (stack, 120) in recorder.calls
            assert (toolbox, 0) in recorder.calls
            assert (root, 0) in recorder.calls
            assert (root, 120) in recorder.calls

            tab_calls = [call for call in recorder.calls if call[0] is tabs]
            stack_calls = [call for call in recorder.calls if call[0] is stack]
            assert tab_calls == [(tabs, 0), (tabs, 120)]
            assert stack_calls == [(stack, 0), (stack, 120)]
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

    def test_scheduler_coalesces_duplicate_target_and_delay(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtWidgets import QApplication, QWidget
            from app import icon_theme
            from app.icon_navigation_performance import _ScopedIconScheduler

            app = QApplication.instance() or QApplication([])
            root = QWidget()
            target = QWidget(root)
            calls = []
            original_apply = icon_theme.apply_icon_theme
            icon_theme.apply_icon_theme = lambda widget: calls.append(widget) or 0
            try:
                scheduler = _ScopedIconScheduler(root)
                for _ in range(8):
                    scheduler.schedule(target, 0)
                app.processEvents()
                assert calls == [target], calls
            finally:
                icon_theme.apply_icon_theme = original_apply
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

    def test_navigation_installer_patches_main_window_icon_installer(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtWidgets import QApplication
            from app import icon_theme, main_window
            from app.icon_navigation_performance import (
                _install_icon_theme_scoped,
                install_scoped_icon_navigation,
            )

            app = QApplication.instance() or QApplication([])
            install_scoped_icon_navigation()
            assert icon_theme.install_icon_theme is _install_icon_theme_scoped
            assert main_window.install_icon_theme is _install_icon_theme_scoped
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
