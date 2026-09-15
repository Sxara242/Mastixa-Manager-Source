from __future__ import annotations

from . import appearance_theme


_INSTALLED = False

LIGHT_FOCUS_STYLESHEET = r"""
/* MASTIXA_ACCESSIBLE_FOCUS_LIGHT */
QPushButton {
    border-width: 2px;
    border-style: solid;
    border-color: transparent;
}
QPushButton:disabled {
    border-color: #C4CEC8;
}
QPushButton:focus,
QToolButton:focus {
    border: 2px solid #1F5A43;
}
QLineEdit,
QTextEdit,
QPlainTextEdit,
QComboBox,
QDateEdit,
QTimeEdit,
QDateTimeEdit,
QSpinBox,
QDoubleSpinBox {
    border-width: 2px;
}
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QDateEdit:focus,
QTimeEdit:focus,
QDateTimeEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 2px solid #1F5A43;
}
QCheckBox,
QRadioButton {
    border: 2px solid transparent;
    border-radius: 4px;
}
QCheckBox:focus,
QRadioButton:focus {
    border-color: #1F5A43;
}
"""

DARK_FOCUS_STYLESHEET = r"""
/* MASTIXA_ACCESSIBLE_FOCUS_DARK */
QPushButton:focus,
QToolButton:focus,
QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QComboBox:focus,
QDateEdit:focus,
QTimeEdit:focus,
QDateTimeEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 2px solid #9CCFB2;
}
QCheckBox:focus,
QRadioButton:focus {
    border-color: #9CCFB2;
}
"""


def install_focus_accessibility() -> None:
    """Add a visible keyboard focus ring without extra theme repaint passes."""
    global _INSTALLED
    if _INSTALLED:
        return

    original_init = appearance_theme.ThemeController.__init__

    def theme_init(self, app, light_stylesheet, light_palette) -> None:
        original_init(
            self,
            app,
            light_stylesheet + "\n" + LIGHT_FOCUS_STYLESHEET,
            light_palette,
        )

    appearance_theme.ThemeController.__init__ = theme_init
    appearance_theme.DARK_STYLESHEET += "\n" + DARK_FOCUS_STYLESHEET
    _INSTALLED = True
