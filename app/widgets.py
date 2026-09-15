from __future__ import annotations

from PySide6.QtCore import QDate, QLocale
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class EntryForm(QWidget):
    def __init__(self, fields: list[tuple[str, QWidget]], on_save, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        for label, widget in fields:
            form.addRow(label, widget)
        layout.addLayout(form)

        row = QHBoxLayout()
        row.addStretch()
        save = QPushButton("Αποθήκευση")
        save.clicked.connect(on_save)
        row.addWidget(save)
        layout.addLayout(row)


def date_input() -> QDateEdit:
    widget = QDateEdit(QDate.currentDate())
    widget.setCalendarPopup(True)
    widget.setDisplayFormat("dd/MM/yyyy")
    return widget


def _numeric_spinbox(
    *,
    maximum: float,
    decimals: int,
    suffix: str,
    step: float,
) -> QDoubleSpinBox:
    widget = QDoubleSpinBox()

    # Σταθερά "." ως δεκαδικός διαχωριστής ανεξάρτητα από τα Windows/Greek locale.
    widget.setLocale(QLocale.c())

    widget.setRange(0, maximum)
    widget.setDecimals(decimals)
    widget.setSuffix(suffix)
    widget.setSingleStep(step)

    # Χωρίς βελάκια: καθαρή αριθμητική εισαγωγή από το πληκτρολόγιο.
    widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    widget.setAccelerated(True)
    widget.setKeyboardTracking(False)

    return widget


def money_input() -> QDoubleSpinBox:
    return _numeric_spinbox(
        maximum=999_999_999,
        decimals=2,
        suffix=" €",
        step=1.00,
    )



class CompactQuantitySpinBox(QDoubleSpinBox):
    """Keep 3-decimal precision but hide trailing zeroes."""

    def textFromValue(self, value: float) -> str:
        return f"{value:.{self.decimals()}f}".rstrip("0").rstrip(".") or "0"


def quantity_input() -> QDoubleSpinBox:
    widget = CompactQuantitySpinBox()
    widget.setRange(0, 999_999_999)
    widget.setDecimals(3)
    widget.setSuffix(" kg")
    widget.setSingleStep(0.100)
    widget.setKeyboardTracking(False)
    widget.setButtonSymbols(
        QAbstractSpinBox.ButtonSymbols.NoButtons
    )
    return widget


def area_input() -> QDoubleSpinBox:
    widget = CompactQuantitySpinBox()
    widget.setLocale(QLocale.c())
    widget.setRange(0, 999_999)
    widget.setDecimals(3)
    widget.setSuffix(" στρ.")
    widget.setSingleStep(0.001)
    widget.setButtonSymbols(
        QAbstractSpinBox.ButtonSymbols.NoButtons
    )
    widget.setAccelerated(True)
    widget.setKeyboardTracking(False)
    return widget


def required_text(widget: QLineEdit, label: str) -> str | None:
    value = widget.text().strip()
    if not value:
        QMessageBox.warning(widget, "Ελλιπή στοιχεία", f"Συμπλήρωσε το πεδίο «{label}».")
        widget.setFocus()
        return None
    return value
