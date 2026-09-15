from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableWidget


def table_widget(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    return table


def compact_decimal(value: float | int | None, max_decimals: int = 3) -> str:
    """Up to max_decimals, without forced trailing zeroes."""
    number = float(value or 0)
    threshold = 0.5 * (10 ** (-max_decimals))
    if abs(number) < threshold:
        number = 0.0
    return f"{number:.{max_decimals}f}".rstrip("0").rstrip(".")


def format_kg(value: float | int | None) -> str:
    return f"{compact_decimal(value, 3)} kg"
