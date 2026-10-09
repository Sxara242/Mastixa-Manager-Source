from __future__ import annotations

from functools import wraps

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QScrollArea, QWidget, QVBoxLayout, QLayout, QFormLayout


def scrollable_entry_layout(page):
    """Keep form/actions and a usable table reachable in a small viewport."""
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea(page)
    scroll.setObjectName("entryPageScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
    scroll.setWidget(content)
    outer.addWidget(scroll)
    return layout


def table_widget(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    header = table.horizontalHeader()
    header.setMinimumSectionSize(100)
    header.setResizeContentsPrecision(100)
    header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    return table


def batched_table_refresh(refresh):
    """Resize/paint a populated CRUD table once, keeping model notifications."""
    @wraps(refresh)
    def batched(page, *args, **kwargs):
        table = page.table
        header = table.horizontalHeader()
        modes = [header.sectionResizeMode(column) for column in range(header.count())]
        enabled = table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            # ResizeToContents on a visible table recomputes cell geometry for
            # every replacement item. Keep existing widths during population;
            # restore each column's policy once the full data is available.
            for column in range(header.count()):
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
            return refresh(page, *args, **kwargs)
        finally:
            for column, mode in enumerate(modes):
                header.setSectionResizeMode(column, mode)
            table.setUpdatesEnabled(enabled)
    return batched


def configure_combo_popup(combo):
    """Keep long status rows readable without widening the entry form."""
    view = combo.view()
    view.setMouseTracking(True)
    if hasattr(view, "setSpacing"):
        view.setSpacing(2)
    metrics = view.fontMetrics()
    width = max((metrics.horizontalAdvance(combo.itemText(i)) for i in range(combo.count())), default=0)
    screen = combo.screen()
    limit = screen.availableGeometry().width() - 40 if screen else 1000
    view.setMinimumWidth(min(limit, max(combo.width(), width + 40)))


def compact_decimal(value: float | int | None, max_decimals: int = 3) -> str:
    """Up to max_decimals, without forced trailing zeroes."""
    number = float(value or 0)
    threshold = 0.5 * (10 ** (-max_decimals))
    if abs(number) < threshold:
        number = 0.0
    return f"{number:.{max_decimals}f}".rstrip("0").rstrip(".")


def format_kg(value: float | int | None) -> str:
    return f"{compact_decimal(value, 3)} kg"
