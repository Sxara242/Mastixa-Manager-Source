"""Bound the measured UI work without timing-dependent assertions."""
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QAction
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QCalendarWidget, QLabel, QWidget

from tests.language_fixture import scoped_language


class RevampPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_unchanged_icon_pass_does_not_emit_action_changed(self):
        from app.icon_theme import apply_icon_theme
        root = QWidget()
        self.addCleanup(root.deleteLater)
        action = QAction("Παραγωγή", root)
        apply_icon_theme(root)
        self.assertFalse(action.icon().isNull())
        spy = QSignalSpy(action.changed)
        for _ in range(5):
            apply_icon_theme(root)
        self.assertEqual(0, spy.count())

    def test_translation_requests_cover_overlapping_subtrees_once(self):
        with scoped_language(self.app, "el") as controller:
            root = QWidget()
            child = QLabel("Παραγωγή", root)
            other = QWidget()
            try:
                self.app.processEvents()
                with patch.object(controller, "apply_to") as apply:
                    controller._schedule(child)
                    controller._schedule(root)
                    controller._schedule(child)
                    controller._schedule(other)
                    controller._drain_pending()
                    visited = [call.args[0] for call in apply.call_args_list]
                    self.assertEqual(1, visited.count(root))
                    self.assertEqual(1, visited.count(other))
                    self.assertNotIn(child, visited)
            finally:
                root.deleteLater()
                other.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_calendar_style_is_not_reassigned_when_theme_is_unchanged(self):
        from app.date_preferences import _style_calendar
        widget = QCalendarWidget()
        self.addCleanup(widget.deleteLater)
        _style_calendar(widget)
        with patch.object(widget, "setStyleSheet", wraps=widget.setStyleSheet) as setter:
            _style_calendar(widget)
            setter.assert_not_called()
