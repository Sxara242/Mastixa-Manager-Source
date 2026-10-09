"""Shared managed-year choices and page-entry/effective-context defaults."""
from PySide6.QtWidgets import QWidget
from .year_context import effective_working_year, active_working_year, MIN_YEAR, MAX_YEAR
from .year_lock_robustness import _YEAR_SOURCES
from .localized_messages import _text


def managed_years(db):
    years = {active_working_year(db), effective_working_year(db)}
    with db.connect(_read_only_query=True) as con:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, expression, where in _YEAR_SOURCES:
            if table not in tables:
                continue
            for row in con.execute(f'SELECT DISTINCT {expression} FROM {table} WHERE {where}'):
                try:
                    year = int(row[0])
                except (ValueError, TypeError):
                    continue
                if MIN_YEAR <= year <= MAX_YEAR:
                    years.add(year)
    return sorted(years, reverse=True)


def populate_year_filter(page, combo, *, strings=False, all_years=True, all_value=None):
    context = effective_working_year(page.db)
    previous_context = combo.property('mastixaFilterContext')
    selected = combo.currentData()
    if previous_context != context or combo.property('mastixaDefaultOnEntry'):
        selected = str(context) if strings else context
    blocked = combo.blockSignals(True)
    try:
        combo.clear()
        if all_years:
            combo.addItem(_text('Όλα τα έτη'), all_value)
        for year in managed_years(page.db):
            combo.addItem(str(year), str(year) if strings else year)
        index = combo.findData(selected)
        combo.setCurrentIndex(index if index >= 0 else combo.findText(str(context)))
        combo.setProperty('mastixaFilterContext', context)
        combo.setProperty('mastixaDefaultOnEntry', False)
    finally:
        combo.blockSignals(blocked)


class YearFilteredPage(QWidget):
    def _year_combo(self):
        return getattr(self, 'year_filter', getattr(self, 'year', None))

    def showEvent(self, event):
        super().showEvent(event)
        combo = self._year_combo()
        if combo is not None and combo.property('mastixaFilterContext') is not None:
            combo.setProperty('mastixaDefaultOnEntry', True)
            self.refresh()

    def refresh_year_context_ui(self):
        self.refresh()
        from .year_context_ui import refresh_transaction_controls
        refresh_transaction_controls(self)
