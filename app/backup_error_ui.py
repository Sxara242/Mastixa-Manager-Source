"""Presentation of BackupError metadata; raw errors and paths stay opaque."""
from PySide6.QtWidgets import QMessageBox
from .localized_messages import _message, _text


def backup_error_text(error):
    template = getattr(error, "ui_template", None)
    if template is None:
        return str(error)
    return _text(template, **error.ui_values)


def show_backup_error(parent, kind, title, error, template="{error}",
                      buttons=QMessageBox.StandardButton.Ok,
                      default=QMessageBox.StandardButton.NoButton):
    return _message(parent, kind, title, template, buttons, default,
                    error=lambda: backup_error_text(error))
