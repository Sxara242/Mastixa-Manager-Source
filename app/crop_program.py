from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Mapping, Any


ALLOWED_CATEGORIES = frozenset(
    {
        "irrigation",
        "fertilization",
        "cultivation",
        "plant_protection",
        "inspection",
        "pruning",
        "other",
    }
)
ALLOWED_SCHEDULES = frozenset({"fixed_date", "interval_window"})
ALLOWED_WITHIN_PERIOD_UNITS = frozenset({"once", "days", "weeks", "months"})


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid schedule number")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Schedule numbers must be integers") from exc
    if isinstance(value, float) and value != number:
        raise ValueError("Schedule numbers must be integers")
    return number


def _positive_int(value: object, label: str) -> int:
    number = _optional_int(value)
    if number is None or number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def _year(value: object, label: str) -> int:
    number = _optional_int(value)
    if number is None or not 1900 <= number <= 9998:
        raise ValueError(f"{label} is outside the supported range")
    return number


def _month_day(month: int, day: int) -> None:
    # Leap year 2000 validates the month/day shape while intentionally allowing
    # 29 February as a recurring agricultural date.
    date(2000, month, day)


def _date_or_none(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        # Explicit leap policy: a recurring 29/02 occurrence is skipped in a
        # non-leap target year and naturally reappears in the next leap year.
        if month == 2 and day == 29:
            return None
        raise


def _add_months(value: date, months: int) -> date:
    total = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True)
class CropProgramRule:
    id: str
    title: str
    category: str
    schedule_kind: str
    notes: str = ""
    month: int | None = None
    day: int | None = None
    start_month: int | None = None
    start_day: int | None = None
    end_month: int | None = None
    end_day: int | None = None
    every_days: int | None = None
    within_period_unit: str | None = None
    within_period_interval: int | None = None
    every_years: int = 1
    base_year: int | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CropProgramRule":
        every_days = _optional_int(value.get("every_days"))
        unit = value.get("within_period_unit")
        interval = _optional_int(value.get("within_period_interval"))
        if unit is None and every_days is not None:
            unit = "days"
        if interval is None and every_days is not None:
            interval = every_days
        return cls(
            id=_required_text(value.get("id"), "rule id"),
            title=_required_text(value.get("title"), "rule title"),
            category=_required_text(value.get("category"), "category"),
            schedule_kind=_required_text(value.get("schedule_kind"), "schedule kind"),
            notes=str(value.get("notes") or ""),
            month=_optional_int(value.get("month")),
            day=_optional_int(value.get("day")),
            start_month=_optional_int(value.get("start_month")),
            start_day=_optional_int(value.get("start_day")),
            end_month=_optional_int(value.get("end_month")),
            end_day=_optional_int(value.get("end_day")),
            every_days=every_days,
            within_period_unit=str(unit) if unit is not None else None,
            within_period_interval=interval,
            every_years=_optional_int(value.get("every_years")) or 1,
            base_year=_optional_int(value.get("base_year")),
        )

    def effective_within_period(self) -> tuple[str, int | None]:
        if self.schedule_kind != "interval_window":
            return "once", None
        if self.within_period_unit:
            unit = self.within_period_unit
            interval = self.within_period_interval
        elif self.every_days is not None:
            unit = "days"
            interval = self.every_days
        else:
            unit = "once"
            interval = None
        return unit, interval

    def validate(self, season_year: int) -> None:
        _required_text(self.id, "rule id")
        _required_text(self.title, "rule title")
        _year(season_year, "season_year")
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Unsupported crop-program category: {self.category}")
        if self.schedule_kind not in ALLOWED_SCHEDULES:
            raise ValueError(f"Unsupported crop-program schedule: {self.schedule_kind}")
        _positive_int(self.every_years, "every_years")
        if self.base_year is not None:
            _year(self.base_year, "base_year")

        if self.schedule_kind == "fixed_date":
            if self.month is None or self.day is None:
                raise ValueError("fixed_date requires month and day")
            _month_day(self.month, self.day)
            return

        values = (
            self.start_month,
            self.start_day,
            self.end_month,
            self.end_day,
        )
        if any(value is None for value in values):
            raise ValueError("interval_window requires start/end month/day")
        assert self.start_month is not None
        assert self.start_day is not None
        assert self.end_month is not None
        assert self.end_day is not None
        _month_day(self.start_month, self.start_day)
        _month_day(self.end_month, self.end_day)

        unit, interval = self.effective_within_period()
        if unit not in ALLOWED_WITHIN_PERIOD_UNITS:
            raise ValueError(f"Unsupported within-period unit: {unit}")
        if unit == "once":
            return
        _positive_int(interval, "within_period_interval")

    def applies_to_year(self, season_year: int, anchor_year: int) -> bool:
        interval = _positive_int(self.every_years, "every_years")
        anchor = self.base_year if self.base_year is not None else anchor_year
        anchor = _year(anchor, "anchor_year")
        if season_year < anchor:
            return False
        return (season_year - anchor) % interval == 0


def generate_crop_tasks(
    program_id: str,
    field_id: str | int,
    season_year: int,
    rules: list[CropProgramRule] | tuple[CropProgramRule, ...],
    *,
    anchor_year: int | None = None,
) -> list[dict[str, object]]:
    """Generate deterministic planned task specifications without database side effects."""

    program = _required_text(program_id, "program id")
    field = _required_text(field_id, "field id")
    _year(season_year, "season_year")

    anchor = season_year if anchor_year is None else anchor_year
    anchor = _year(anchor, "anchor_year")

    seen: set[str] = set()
    tasks: list[dict[str, object]] = []

    for rule in rules:
        if rule.id in seen:
            raise ValueError(f"Duplicate crop-program rule id: {rule.id}")
        seen.add(rule.id)

        rule.validate(season_year)
        if not rule.applies_to_year(season_year, anchor):
            continue

        occurrences: list[tuple[date, date | None]]
        if rule.schedule_kind == "fixed_date":
            assert rule.month is not None and rule.day is not None
            due = _date_or_none(season_year, rule.month, rule.day)
            if due is None:
                continue
            occurrences = [(due, None)]
        else:
            assert rule.start_month is not None
            assert rule.start_day is not None
            assert rule.end_month is not None
            assert rule.end_day is not None

            start = _date_or_none(season_year, rule.start_month, rule.start_day)
            if start is None:
                continue
            wraps_year = (rule.end_month, rule.end_day) < (
                rule.start_month,
                rule.start_day,
            )
            end_year = season_year + 1 if wraps_year else season_year
            end = _date_or_none(end_year, rule.end_month, rule.end_day)
            if end is None:
                continue

            unit, interval = rule.effective_within_period()
            if unit == "once":
                occurrences = [(start, end)]
            elif unit in {"days", "weeks"}:
                assert interval is not None
                occurrences = []
                current = start
                day_step = interval if unit == "days" else interval * 7
                step = timedelta(days=day_step)
                while current <= end:
                    occurrences.append((current, None))
                    current += step
            else:
                assert unit == "months"
                assert interval is not None
                occurrences = []
                occurrence_index = 0
                while True:
                    current = _add_months(start, occurrence_index * interval)
                    if current > end:
                        break
                    occurrences.append((current, None))
                    occurrence_index += 1

        for due, window_end in occurrences:
            due_date = due.isoformat()
            tasks.append(
                {
                    "generation_key": f"{program}:{field}:{rule.id}:{due_date}",
                    "program_id": program,
                    "rule_id": rule.id,
                    "field_id": field,
                    "season_year": season_year,
                    "due_date": due_date,
                    "window_end_date": window_end.isoformat() if window_end else None,
                    "category": rule.category,
                    "title": rule.title,
                    "notes": rule.notes,
                    "status": "pending",
                }
            )

    tasks.sort(key=lambda row: (str(row["due_date"]), str(row["rule_id"])))
    return tasks
