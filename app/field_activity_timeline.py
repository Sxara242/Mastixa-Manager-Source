"""Presentation adapter for the read-only Phase 9 activity projection."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .activity_projection import project_field_activities
from .database import Database


_KIND_PRESENTATION = {
    "harvest": ("Παραγωγή", "Καταχώρηση παραγωγής"),
    "irrigation": ("Άρδευση & Λίπανση", "Πότισμα"),
    "fertilization": ("Άρδευση & Λίπανση", "Λίπανση"),
    "planting": ("Φυτεύσεις", "Φύτευση"),
    "plant_protection": ("Φυτοπροστασία", "Επέμβαση φυτοπροστασίας"),
    "cultivation_work": ("Εργατικά", "Καλλιεργητική εργασία"),
    "observation": ("Παρατήρηση GIS", "Παρατήρηση πεδίου"),
}


def _scope_id_for_database(path: Path) -> str:
    """Return the local profile identity implied by the profile database layout."""
    resolved = Path(path).resolve()
    parent_name = resolved.parent.name.strip()
    if resolved.name == "mastixa_manager.db" and parent_name and parent_name != "data":
        return parent_name
    return "default"


def _display_when(item: dict) -> str:
    recorded_at = item.get("event_at")
    if type(recorded_at) is int:
        try:
            instant = datetime.fromtimestamp(recorded_at / 1000, tz=timezone.utc)
            return instant.strftime("%Y-%m-%d %H:%M UTC")
        except (OverflowError, OSError, ValueError):
            pass
    event_date = item.get("event_date")
    if isinstance(event_date, str) and event_date:
        return event_date
    return "Άγνωστη ημερομηνία"


def timeline_rows_from_projection(
    items: Iterable[dict],
    year: str | None = None,
    *,
    limit: int = 60,
) -> list[tuple[str, str, str, str]]:
    """Adapt projected activities for the existing field-card table.

    The projection's order is preserved exactly. Year filtering only removes
    items whose normalized event date does not belong to the selected year;
    unknown dates remain visible only in the all-years view.
    """
    rows: list[tuple[str, str, str, str]] = []
    selected_year = str(year).strip() if year is not None else None

    for item in items:
        event_date = item.get("event_date")
        if selected_year is not None:
            if not isinstance(event_date, str) or not event_date.startswith(
                selected_year + "-"
            ):
                continue

        kind = str(item.get("kind") or "")
        section, description = _KIND_PRESENTATION.get(
            kind,
            ("Δραστηριότητα", "Καταχώρηση δραστηριότητας"),
        )
        rows.append((_display_when(item), section, description, ""))
        if len(rows) >= max(0, int(limit)):
            break

    return rows


def load_field_timeline_rows(
    db: Database,
    field_id: int,
    year: str | None = None,
    *,
    limit: int = 60,
) -> list[tuple[str, str, str, str]]:
    """Load one field timeline through the shared read-only projection."""
    scope_id = _scope_id_for_database(db.path)
    with db.connect() as connection:
        items = project_field_activities(connection, scope_id, int(field_id))
    return timeline_rows_from_projection(items, year, limit=limit)
