import logging
import unittest
from pathlib import Path
from app.app_logging import _PrivacyFormatter


class DiagnosticPrivacyTests(unittest.TestCase):
    def test_exception_messages_and_source_context_are_not_logged(self):
        formatter = _PrivacyFormatter("%(message)s", redactions=())
        try:
            raise ValueError("PRIVATE_KAEK token=SECRET polygon=[26,38]")
        except ValueError:
            import sys
            record = logging.LogRecord("mastixa", logging.ERROR, __file__, 1, "Import failed", (), sys.exc_info())
        output = formatter.format(record)
        self.assertIn("ValueError", output)
        self.assertIn("Import failed", output)
        for value in ("PRIVATE_KAEK", "SECRET", "polygon=", str(Path(__file__).parent)):
            self.assertNotIn(value, output)

    def test_cached_exception_text_and_stack_dump_are_not_reused(self):
        formatter = _PrivacyFormatter("%(message)s", redactions=())
        try:
            raise RuntimeError("SECRET")
        except RuntimeError:
            import sys
            record = logging.LogRecord("mastixa", logging.ERROR, __file__, 1, "Failed", (), sys.exc_info())
        record.exc_text = "SECRET cached traceback"
        record.stack_info = "SECRET source line"
        self.assertNotIn("SECRET", formatter.format(record))
        self.assertEqual("SECRET cached traceback", record.exc_text)

    def test_unhandled_exception_console_output_is_redacted(self):
        import io, sys, threading
        from unittest.mock import Mock, patch
        from app.app_logging import _install_exception_hooks
        with patch.object(sys, "excepthook"), patch.object(threading, "excepthook"):
            _install_exception_hooks(Mock())
            with patch.object(sys, "stderr", new_callable=io.StringIO) as output:
                sys.excepthook(ValueError, ValueError("SECRET"), None)
                self.assertNotIn("SECRET", output.getvalue())
                self.assertIn("redacted", output.getvalue())

    def test_windowed_application_without_stderr_keeps_exception_handler_usable(self):
        import sys, threading
        from unittest.mock import Mock, patch
        from app.app_logging import _install_exception_hooks
        logger = Mock()
        with patch.object(sys, "excepthook"), patch.object(threading, "excepthook"), patch.object(sys, "stderr", None):
            _install_exception_hooks(logger)
            sys.excepthook(ValueError, ValueError("SECRET"), None)
        logger.critical.assert_called_once()
