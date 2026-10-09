"""Numeric editors with visual placeholders and comma/dot decimal entry."""
import math
from PySide6.QtCore import QLocale
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox, QLineEdit, QSpinBox


def decimal_text(text):
    value = text.strip()
    # Do not silently interpret a mixed decimal/thousands separator.
    if ',' in value and '.' in value:
        return value
    return value.replace(',', '.')


class NumericDoubleSpinBox(QDoubleSpinBox):
    """Units are presentation only; the focused editor contains a number."""
    def __init__(self, parent=None):
        self._unit_suffix = ''
        super().__init__(parent)
        self.setLocale(QLocale.c())
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setKeyboardTracking(False)
        self._update_placeholder()
        self.lineEdit().clear()

    def _update_placeholder(self):
        self.lineEdit().setPlaceholderText('0' + ('.' + '0' * self.decimals() if self.decimals() else '') + self._unit_suffix)

    def setDecimals(self, decimals):
        super().setDecimals(decimals)
        self._update_placeholder()

    def setSuffix(self, suffix):
        self._unit_suffix = suffix
        super().setSuffix('')
        self._update_placeholder()
        self.setValue(super().value())

    def suffix(self):
        return self._unit_suffix

    def textFromValue(self, value):
        if value == 0:
            return ''
        text = super().textFromValue(value)
        return text if self.hasFocus() else text + getattr(self, '_unit_suffix', '')

    def _number_text(self, text):
        value = text.strip()
        suffix = self._unit_suffix.strip()
        if suffix and value.endswith(suffix):
            value = value[:-len(suffix)].strip()
        return decimal_text(value)

    def validate(self, text, position):
        value = self._number_text(text)
        if value == '':
            return QDoubleValidator.State.Intermediate, text, position
        state, _, _ = super().validate(value, min(position, len(value)))
        return state, text, position

    def valueFromText(self, text):
        value = self._number_text(text)
        if not value:
            return max(self.minimum(), min(self.maximum(), 0.0))
        return super().valueFromText(value)

    def setValue(self, value):
        super().setValue(value)
        if super().value() == 0:
            self.lineEdit().clear()

    def interpretText(self):
        if not self.lineEdit().text().strip():
            self.setValue(max(0, self.minimum()))
        else:
            super().interpretText()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        value = super().value()
        self.lineEdit().setText(super().textFromValue(value) if value else '')
        self.lineEdit().selectAll()

    def focusOutEvent(self, event):
        # Clearing commits zero, respecting fields with a positive minimum.
        if not self.lineEdit().text().strip():
            self.setValue(max(0, self.minimum()))
        super().focusOutEvent(event)
        self.lineEdit().setText(self.textFromValue(super().value()))


class DecimalValidator(QDoubleValidator):
    def __init__(self, *args):
        super().__init__(*args)
        self.setLocale(QLocale.c())
        self.setNotation(QDoubleValidator.Notation.StandardNotation)

    def validate(self, text, position):
        state, _, _ = super().validate(decimal_text(text), position)
        return state, text, position


class NumericSpinBox(QSpinBox):
    """Count inputs keep integer bounds; zero has an empty visual state."""
    def __init__(self, parent=None):
        self._unit_suffix = ''
        super().__init__(parent)
        self.lineEdit().setPlaceholderText('0')
        self.lineEdit().clear()

    def setSuffix(self, suffix):
        self._unit_suffix = suffix
        super().setSuffix('')
        self.lineEdit().setPlaceholderText('0' + suffix)
        self.setValue(super().value())

    def suffix(self):
        return self._unit_suffix

    def textFromValue(self, value):
        if value == 0:
            return ''
        return str(value) + ('' if self.hasFocus() else self._unit_suffix)

    def valueFromText(self, text):
        return int(text.strip().removesuffix(self._unit_suffix.strip()).strip() or '0')

    def validate(self, text, position):
        value = text.strip().removesuffix(self._unit_suffix.strip()).strip()
        if not value:
            return QDoubleValidator.State.Intermediate, text, position
        state, _, _ = super().validate(value, min(position, len(value)))
        return state, text, position

    def setValue(self, value):
        super().setValue(value)
        if super().value() == 0:
            self.lineEdit().clear()

    def interpretText(self):
        if not self.lineEdit().text().strip():
            self.setValue(max(0, self.minimum()))
        else:
            super().interpretText()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.lineEdit().setText(str(super().value()) if super().value() else '')
        self.lineEdit().selectAll()

    def focusOutEvent(self, event):
        if not self.lineEdit().text().strip():
            self.setValue(max(0, self.minimum()))
        super().focusOutEvent(event)
        self.lineEdit().setText(self.textFromValue(super().value()))


class NumericLineEdit(QLineEdit):
    def setText(self, text):
        value = str(text).strip()
        try:
            zero = math.isfinite(float(decimal_text(value))) and float(decimal_text(value)) == 0
        except ValueError:
            zero = False
        super().setText('' if zero else value)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()
