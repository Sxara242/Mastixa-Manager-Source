"""Protected template dialogs shared by scoped localization owners."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox


def _language():
    controller = getattr(QApplication.instance(), "_mastixa_language_controller", None)
    return controller if controller is not None and controller._enabled else None


def _text(template: str, **values) -> str:
    controller = _language()
    translated = controller.translate_exact(template) if controller else template
    return translated.format(**values)


def _message(parent, kind, title, template, buttons=QMessageBox.StandardButton.Ok,
             default=QMessageBox.StandardButton.NoButton, **values):
    """Translate owned templates, never their interpolated user/domain values."""
    def render():
        return _text(template, **{key: value() if callable(value) else value
                                 for key, value in values.items()})

    controller = _language()
    if controller is None:
        return getattr(QMessageBox, kind)(parent, title, render(), buttons, default)
    box = QMessageBox(parent)
    box.setIcon({"warning": QMessageBox.Icon.Warning, "question": QMessageBox.Icon.Question, "critical": QMessageBox.Icon.Critical, "information": QMessageBox.Icon.Information}[kind])
    box.setStandardButtons(buttons)
    box.setDefaultButton(default)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setProperty("mastixaI18nSkipText", True)

    def refresh():
        box.setWindowTitle(_text(title))
        box.setText(render())
        for label in box.findChildren(QLabel):
            label.setProperty("mastixaI18nSkipText", True)
        controller.apply_to(box)

    refresh()
    controller.language_changed.connect(refresh)
    try:
        return box.exec()
    finally:
        controller.language_changed.disconnect(refresh)
        box.deleteLater()
