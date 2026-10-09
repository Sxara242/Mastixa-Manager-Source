"""Late updater results must survive profile-window deletion without Qt errors."""
import threading
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QTabWidget, QWidget
from shiboken6 import delete

from app import update_integration, update_manager
from tests.test_alpha2_updates import _manifest


THREAD = threading.Thread


class UpdateResourceLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def late_result(self, operation, fail):
        page = QWidget()
        page.tabs = QTabWidget(page)
        page._composed_text = lambda label, text, **values: label.setText(text.format(**values))
        update_integration._add_updates_tab(page)
        page._mastixa_update_info = update_manager.parse_manifest(_manifest())
        started, release = threading.Event(), threading.Event()
        threads, errors = [], []

        def thread_factory(**kwargs):
            worker = THREAD(**kwargs)
            threads.append(worker)
            return worker

        def blocked(*args):
            started.set()
            if not release.wait(5):
                raise AssertionError('test did not release worker')
            if fail:
                raise update_manager.UpdateError('controlled failure')
            return page._mastixa_update_info

        function = 'fetch_update_info' if operation == 'check' else 'download_windows_update'
        with patch.object(update_integration.threading, 'Thread', side_effect=thread_factory), \
                patch.object(threading, 'excepthook', side_effect=lambda event: errors.append(event.exc_value)), \
                patch.object(update_integration, function, side_effect=blocked), \
                patch.object(update_integration, 'launch_windows_installer') as launch:
            try:
                button = page._mastixa_check_updates_button if operation == 'check' else page._mastixa_install_update_button
                button.click()
                self.assertTrue(started.wait(2))
                delete(page)
            finally:
                release.set()
                for worker in threads:
                    worker.join(2)
            self.assertTrue(all(not worker.is_alive() for worker in threads))
            self.assertEqual([], errors)
            launch.assert_not_called()

    def test_check_completion_after_window_deletion(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                self.late_result('check', fail)

    def test_download_completion_after_window_deletion(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                self.late_result('download', fail)
