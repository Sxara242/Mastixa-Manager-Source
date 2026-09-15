from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDialogButtonBox

from . import settings


_INSTALLED = False


def install_profile_login_keyboard() -> None:
    """Make Enter reliably activate the profile login Open action.

    QLineEdit.returnPressed remains wired by ProfileSelectionDialog itself. This
    adds the standard default-button behaviour plus explicit Return/Keypad Enter
    shortcuts as a Windows/keyboard fallback, all routed through the dialog's
    existing accept() method so PIN validation is unchanged.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    dialog_cls = settings.ProfileSelectionDialog
    original_init = dialog_cls.__init__

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)

        button_box = self.findChild(QDialogButtonBox)
        if button_box is not None:
            open_button = button_box.button(
                QDialogButtonBox.StandardButton.Open
            )
            if open_button is not None:
                open_button.setDefault(True)
                open_button.setAutoDefault(True)
                self._mastixa_login_open_button = open_button

        shortcuts = []
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(self.accept)
            shortcuts.append(shortcut)
        self._mastixa_login_enter_shortcuts = shortcuts

    dialog_cls.__init__ = init
    _INSTALLED = True
