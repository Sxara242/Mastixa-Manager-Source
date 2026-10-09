from __future__ import annotations

from PySide6.QtCore import QDate


_YEAR_SOURCES = (
    ("production", "CAST(SUBSTR(entry_date, 1, 4) AS INTEGER)", "entry_date IS NOT NULL AND entry_date <> ''"),
    ("income", "CAST(SUBSTR(entry_date, 1, 4) AS INTEGER)", "entry_date IS NOT NULL AND entry_date <> ''"),
    ("expenses", "CAST(SUBSTR(entry_date, 1, 4) AS INTEGER)", "entry_date IS NOT NULL AND entry_date <> ''"),
    ("cultivation_declarations", "declaration_year", "declaration_year IS NOT NULL"),
    ("farm_activities", "CAST(SUBSTR(activity_date, 1, 4) AS INTEGER)", "activity_date IS NOT NULL AND activity_date <> ''"),
    ("inventory_movements", "CAST(SUBSTR(movement_date, 1, 4) AS INTEGER)", "movement_date IS NOT NULL AND movement_date <> ''"),
    ("year_locks", "year", "year IS NOT NULL"),
    ("plant_protection_records", "CAST(SUBSTR(application_date, 1, 4) AS INTEGER)", "application_date IS NOT NULL AND application_date <> ''"),
    ("labor_entries", "CAST(SUBSTR(work_date, 1, 4) AS INTEGER)", "work_date IS NOT NULL AND work_date <> ''"),
    ("planting_batches", "CAST(SUBSTR(planting_date, 1, 4) AS INTEGER)", "planting_date IS NOT NULL AND planting_date <> ''"),
    ("production_sales", "CAST(SUBSTR(sale_date, 1, 4) AS INTEGER)", "sale_date IS NOT NULL AND sale_date <> ''"),
    ("equipment_maintenance", "CAST(SUBSTR(service_date, 1, 4) AS INTEGER)", "service_date IS NOT NULL AND service_date <> ''"),
    ("plant_events", "CAST(SUBSTR(event_date, 1, 4) AS INTEGER)", "event_date IS NOT NULL AND event_date <> ''"),
    ("crop_tasks", "CAST(SUBSTR(due_date, 1, 4) AS INTEGER)", "due_date IS NOT NULL AND due_date <> ''"),
    ("planting_replantings", "CAST(SUBSTR(replanting_date, 1, 4) AS INTEGER)", "replanting_date IS NOT NULL AND replanting_date <> ''"),
)


def _table_exists(db, table: str) -> bool:
    row = db.query_one(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return row is not None


def _available_years(self) -> list[int]:
    years = {QDate.currentDate().year()}

    for table, expression, where_clause in _YEAR_SOURCES:
        if not _table_exists(self.db, table):
            continue
        rows = self.db.query(
            f"SELECT DISTINCT {expression} AS year FROM {table} WHERE {where_clause}"
        )
        for row in rows:
            try:
                years.add(int(row["year"]))
            except (TypeError, ValueError):
                continue

    return sorted(years, reverse=True)


def install_year_lock_robustness() -> None:
    from .year_lock import YearLockPage

    if getattr(YearLockPage, "_alpha2_optional_year_sources", False):
        return

    YearLockPage._available_years = _available_years
    YearLockPage._alpha2_optional_year_sources = True
