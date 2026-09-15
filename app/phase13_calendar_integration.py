from __future__ import annotations

from datetime import date

from . import main_window as _main_window
from .farm_calendar import FarmCalendarPage as _BaseFarmCalendarPage
from .task_calendar import task_state


GREEK_MONTHS = (
    "Ιανουάριος",
    "Φεβρουάριος",
    "Μάρτιος",
    "Απρίλιος",
    "Μάιος",
    "Ιούνιος",
    "Ιούλιος",
    "Αύγουστος",
    "Σεπτέμβριος",
    "Οκτώβριος",
    "Νοέμβριος",
    "Δεκέμβριος",
)

_STATE_LABELS = {
    "overdue": "Εκπρόθεσμη",
    "due_today": "Για σήμερα",
    "upcoming": "Εντός 7 ημερών",
    "pending": "Προγραμματισμένη",
    "completed": "Ολοκληρωμένη",
    "skipped": "Παραλείφθηκε",
}

_CATEGORY_LABELS = {
    "irrigation": "Άρδευση",
    "fertilization": "Λίπανση",
    "cultivation": "Καλλιεργητική εργασία",
    "plant_protection": "Φυτοπροστασία",
    "inspection": "Έλεγχος",
    "pruning": "Κλάδεμα",
    "other": "Άλλο",
}


class Phase13FarmCalendarPage(_BaseFarmCalendarPage):
    """Phase 13 extension: planned crop tasks join the read-only unified calendar."""

    _phase13_task_calendar = True

    def __init__(self, db) -> None:
        super().__init__(db)

        current_month = self.month.currentData()
        self.month.blockSignals(True)
        self.month.clear()
        self.month.addItem("Όλοι οι μήνες", None)
        for number, name in enumerate(GREEK_MONTHS, start=1):
            self.month.addItem(name, number)
        index = self.month.findData(current_month)
        self.month.setCurrentIndex(index if index >= 0 else 0)
        self.month.blockSignals(False)

        if self.section.findData("Πρόγραμμα Καλλιέργειας") < 0:
            self.section.addItem(
                "Πρόγραμμα Καλλιέργειας",
                "Πρόγραμμα Καλλιέργειας",
            )
        self.refresh()

    def _refresh_years(self) -> None:
        current = self.year.currentData()
        super()._refresh_years()
        values = {
            str(self.year.itemData(index))
            for index in range(self.year.count())
            if self.year.itemData(index) is not None
        }
        if self._table_exists("crop_tasks"):
            for row in self.db.query(
                """
                SELECT DISTINCT SUBSTR(due_date,1,4) AS year
                FROM crop_tasks
                WHERE due_date IS NOT NULL AND due_date <> ''
                """
            ):
                value = str(row["year"] or "").strip()
                if value:
                    values.add(value)

        self.year.blockSignals(True)
        self.year.clear()
        self.year.addItem("Όλα τα έτη", None)
        for value in sorted(values, reverse=True):
            self.year.addItem(value, value)
        index = self.year.findData(current)
        self.year.setCurrentIndex(index if index >= 0 else 0)
        self.year.blockSignals(False)

    def _load_plantings(self) -> None:
        super()._load_plantings()
        self._load_crop_tasks()

    def _load_crop_tasks(self) -> None:
        if not self._table_exists("crop_tasks"):
            return
        today = date.today()
        rows = self.db.query(
            """
            SELECT
                t.generation_key,t.field_id,t.due_date,t.category,t.title,
                t.notes,t.status,f.name AS field_name
            FROM crop_tasks t
            LEFT JOIN fields f ON CAST(f.id AS TEXT)=t.field_id
            """
        )
        for row in rows:
            field_text = str(row["field_id"] or "")
            field_id = int(field_text) if field_text.isdigit() else None
            state = task_state(
                str(row["status"]),
                str(row["due_date"]),
                today,
            )
            state_label = _STATE_LABELS[state]
            category_label = _CATEGORY_LABELS.get(
                str(row["category"]), str(row["category"])
            )
            title = str(row["title"] or "Προγραμματισμένη εργασία")
            notes = str(row["notes"] or "")
            self._append(
                date=str(row["due_date"] or ""),
                section="Πρόγραμμα Καλλιέργειας",
                field_id=field_id,
                field_name=str(row["field_name"] or "Διαγραμμένο αγροτεμάχιο"),
                description=f"{title} — {state_label}",
                value=category_label,
                page_index=-1,
                record_id=str(row["generation_key"]),
                search_text=(
                    f"{title} {notes} {category_label} {state_label} "
                    f"{row['field_name'] or ''}"
                ),
            )

    def open_selected(self) -> None:
        row = self._selected_row()
        if row is not None and row.get("section") == "Πρόγραμμα Καλλιέργειας":
            window = self.window()
            change_page = getattr(window, "change_page", None)
            pages = getattr(window, "pages", ())
            if callable(change_page):
                for index, item in enumerate(pages):
                    if item[0] == "Πρόγραμμα Καλλιέργειας":
                        change_page(index)
                        return
            return
        super().open_selected()


def install_phase13_calendar_ui() -> None:
    if getattr(_main_window.FarmCalendarPage, "_phase13_task_calendar", False):
        return
    _main_window.FarmCalendarPage = Phase13FarmCalendarPage
