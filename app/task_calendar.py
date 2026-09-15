from __future__ import annotations

from datetime import date

STATUSES = frozenset({"pending", "completed", "skipped"})
REMINDER_STATES = frozenset({"overdue", "due_today", "upcoming"})


def _iso_date(value: str, label: str) -> date:
    text = str(value or "").strip()
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise ValueError(f"{label} must be YYYY-MM-DD")
    return parsed


def task_state(
    status: str,
    due_date: str,
    today: date | str,
    *,
    horizon_days: int = 7,
) -> str:
    """Return the Phase 13 effective task state without mutating stored status."""
    value = str(status or "").strip()
    if value not in STATUSES:
        raise ValueError(f"Unsupported crop task status: {value}")
    if horizon_days < 0:
        raise ValueError("horizon_days must be nonnegative")

    due = _iso_date(due_date, "due_date")
    current = _iso_date(today, "today") if isinstance(today, str) else today
    if not isinstance(current, date):
        raise ValueError("today must be a date or YYYY-MM-DD")

    if value in {"completed", "skipped"}:
        return value
    if due < current:
        return "overdue"
    if due == current:
        return "due_today"
    if (due - current).days <= horizon_days:
        return "upcoming"
    return "pending"


def reminder_severity(
    status: str,
    due_date: str,
    today: date | str,
    *,
    horizon_days: int = 7,
) -> int | None:
    """0=urgent overdue, 1=due today, 2=upcoming, None=no reminder."""
    state = task_state(status, due_date, today, horizon_days=horizon_days)
    return {"overdue": 0, "due_today": 1, "upcoming": 2}.get(state)
