from __future__ import annotations

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

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CropProgramRule":
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
            every_days=_optional_int(value.get("every_days")),
        )

    def validate(self, season_year: int) -> None:
        _required_text(self.id, "rule id")
        _required_text(self.title, "rule title")
        if self.category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Unsupported crop-program category: {self.category}")
        if self.schedule_kind not in ALLOWED_SCHEDULES:
            raise ValueError(f"Unsupported crop-program schedule: {self.schedule_kind}")

        if self.schedule_kind == "fixed_date":
            if self.month is None or self.day is None:
                raise ValueError("fixed_date requires month and day")
            date(season_year, self.month, self.day)
            return

        values = (
            self.start_month,
            self.start_day,
            self.end_month,
            self.end_day,
            self.every_days,
        )
        if any(value is None for value in values):
            raise ValueError(
                "interval_window requires start/end month/day and every_days"
            )
        assert self.start_month is not None
        assert self.start_day is not None
        assert self.end_month is not None
        assert self.end_day is not None
        assert self.every_days is not None
        if self.every_days <= 0:
            raise ValueError("every_days must be positive")
        start = date(season_year, self.start_month, self.start_day)
        end_year = season_year
        end = date(end_year, self.end_month, self.end_day)
        if end < start:
            end_year += 1
            date(end_year, self.end_month, self.end_day)


def generate_crop_tasks(
    program_id: str,
    field_id: str | int,
    season_year: int,
    rules: list[CropProgramRule] | tuple[CropProgramRule, ...],
) -> list[dict[str, object]]:
    """Generate deterministic planned task specifications without database side effects."""

    program = _required_text(program_id, "program id")
    field = _required_text(field_id, "field id")
    if isinstance(season_year, bool) or not isinstance(season_year, int):
        raise ValueError("season_year must be an integer")
    if not 1900 <= season_year <= 9998:
        raise ValueError("season_year is outside the supported range")

    seen: set[str] = set()
    tasks: list[dict[str, object]] = []

    for rule in rules:
        rule.validate(season_year)
        if rule.id in seen:
            raise ValueError(f"Duplicate crop-program rule id: {rule.id}")
        seen.add(rule.id)

        dates: list[date]
        if rule.schedule_kind == "fixed_date":
            assert rule.month is not None and rule.day is not None
            dates = [date(season_year, rule.month, rule.day)]
        else:
            assert rule.start_month is not None
            assert rule.start_day is not None
            assert rule.end_month is not None
            assert rule.end_day is not None
            assert rule.every_days is not None
            start = date(season_year, rule.start_month, rule.start_day)
            end = date(season_year, rule.end_month, rule.end_day)
            if end < start:
                end = date(season_year + 1, rule.end_month, rule.end_day)
            dates = []
            current = start
            step = timedelta(days=rule.every_days)
            while current <= end:
                dates.append(current)
                current += step

        for due in dates:
            due_date = due.isoformat()
            tasks.append(
                {
                    "generation_key": f"{program}:{field}:{rule.id}:{due_date}",
                    "program_id": program,
                    "rule_id": rule.id,
                    "field_id": field,
                    "season_year": season_year,
                    "due_date": due_date,
                    "category": rule.category,
                    "title": rule.title,
                    "notes": rule.notes,
                    "status": "pending",
                }
            )

    tasks.sort(key=lambda row: (str(row["due_date"]), str(row["rule_id"])))
    return tasks
