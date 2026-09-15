from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QMainWindow,
    QToolTip,
    QWidget,
)

from . import ui_help


_INSTALLED = False


def _set_assistive_help(widget: QWidget, help_text: str) -> None:
    """Expose an existing visual tooltip to keyboard and assistive APIs."""
    if not widget.accessibleDescription():
        widget.setAccessibleDescription(help_text)
    if not widget.whatsThis():
        widget.setWhatsThis(help_text)


def _focused_help_widget(root: QWidget) -> QWidget | None:
    widget = QApplication.focusWidget()
    if widget is None or not (widget is root or root.isAncestorOf(widget)):
        return None

    current: QWidget | None = widget
    while current is not None:
        if current.toolTip() or current.whatsThis() or current.accessibleDescription():
            return current
        if current is root:
            break
        current = current.parentWidget()
    return None


def _show_focused_help(root: QWidget) -> None:
    widget = _focused_help_widget(root)
    if widget is None:
        return

    text = widget.toolTip() or widget.whatsThis() or widget.accessibleDescription()
    if not text:
        return
    QToolTip.showText(
        widget.mapToGlobal(QPoint(0, widget.height())),
        text,
        widget,
    )


def _install_keyboard_help(root: QWidget) -> None:
    # MainWindow applies help both to itself and to every page. Installing the
    # same F1 shortcut on page widgets would give a focused field overlapping
    # WidgetWithChildren shortcuts and make activation ambiguous.
    if not isinstance(root, (QMainWindow, QDialog)):
        return
    if root.property("mastixaKeyboardHelpInstalled"):
        return

    shortcut = QShortcut(QKeySequence(Qt.Key.Key_F1), root)
    shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    shortcut.activated.connect(lambda r=root: _show_focused_help(r))
    root._mastixa_help_shortcut = shortcut
    root.setProperty("mastixaKeyboardHelpInstalled", True)


def install_help_accessibility() -> None:
    """Add keyboard/assistive access without changing the existing help layout."""
    global _INSTALLED
    if _INSTALLED:
        return

    original_decorate_label = ui_help._decorate_label
    original_set_widget_help = ui_help._set_widget_help
    original_apply_help_tooltips = ui_help.apply_help_tooltips

    def decorate_label(label, help_text: str) -> None:
        original_decorate_label(label, help_text)
        _set_assistive_help(label, help_text)

    def set_widget_help(widget, help_text: str) -> None:
        original_set_widget_help(widget, help_text)
        _set_assistive_help(widget, help_text)

    def apply_help_tooltips(root: QWidget) -> None:
        original_apply_help_tooltips(root)
        context_name = root.__class__.__name__
        for group in root.findChildren(QGroupBox):
            help_text = ui_help._lookup_help(group.title(), context_name)
            if help_text:
                _set_assistive_help(group, help_text)
        _install_keyboard_help(root)

    ui_help._decorate_label = decorate_label
    ui_help._set_widget_help = set_widget_help
    ui_help.apply_help_tooltips = apply_help_tooltips
    _INSTALLED = True
