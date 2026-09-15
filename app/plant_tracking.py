from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any, Mapping, Sequence


ALLOWED_STATUSES = frozenset({"active", "dead", "removed"})
ALLOWED_HEALTH = frozenset({"unknown", "good", "watch", "poor"})
ALLOWED_EVENT_KINDS = frozenset({"note", "health", "status"})


def _required(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional_text(value: object) -> str:
    return str(value or "").strip()


def _iso_date(value: object, label: str, *, optional: bool = False) -> str:
    text = _optional_text(value)
    if optional and not text:
        return ""
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise ValueError(f"{label} must be YYYY-MM-DD")
    return text


def _coordinate(value: object, label: str) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


@dataclass(frozen=True)
class PlantRecord:
    id: str
    field_id: str
    planting_batch_id: str = ""
    label: str = ""
    planted_date: str = ""
    variety: str = ""
    latitude: float | None = None
    longitude: float | None = None
    status: str = "active"
    health: str = "unknown"
    notes: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PlantRecord":
        return cls(
            id=_required(value.get("id"), "plant id"),
            field_id=_required(value.get("field_id"), "field id"),
            planting_batch_id=_optional_text(value.get("planting_batch_id")),
            label=_optional_text(value.get("label")),
            planted_date=_iso_date(value.get("planted_date"), "planted_date", optional=True),
            variety=_optional_text(value.get("variety")),
            latitude=_coordinate(value.get("latitude"), "latitude"),
            longitude=_coordinate(value.get("longitude"), "longitude"),
            status=_required(value.get("status") or "active", "plant status"),
            health=_required(value.get("health") or "unknown", "plant health"),
            notes=_optional_text(value.get("notes")),
        )

    def validate(self) -> None:
        _required(self.id, "plant id")
        _required(self.field_id, "field id")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported plant status: {self.status}")
        if self.health not in ALLOWED_HEALTH:
            raise ValueError(f"Unsupported plant health: {self.health}")
        if self.planted_date:
            _iso_date(self.planted_date, "planted_date")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        if self.latitude is not None:
            if not isfinite(self.latitude) or not -90 <= self.latitude <= 90:
                raise ValueError("latitude is outside the supported range")
            assert self.longitude is not None
            if not isfinite(self.longitude) or not -180 <= self.longitude <= 180:
                raise ValueError("longitude is outside the supported range")


@dataclass(frozen=True)
class PlantEvent:
    id: str
    plant_id: str
    event_date: str
    kind: str
    value: str = ""
    notes: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PlantEvent":
        return cls(
            id=_required(value.get("id"), "event id"),
            plant_id=_required(value.get("plant_id"), "plant id"),
            event_date=_iso_date(value.get("event_date"), "event_date"),
            kind=_required(value.get("kind"), "event kind"),
            value=_optional_text(value.get("value")),
            notes=_optional_text(value.get("notes")),
        )

    def validate(self) -> None:
        _required(self.id, "event id")
        _required(self.plant_id, "plant id")
        _iso_date(self.event_date, "event_date")
        if self.kind not in ALLOWED_EVENT_KINDS:
            raise ValueError(f"Unsupported plant event kind: {self.kind}")
        if self.kind == "health" and self.value not in ALLOWED_HEALTH:
            raise ValueError(f"Unsupported plant health: {self.value}")
        if self.kind == "status" and self.value not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported plant status: {self.value}")
        if self.kind == "note" and not self.value and not self.notes:
            raise ValueError("note event requires value or notes")


def project_plant(
    plant: PlantRecord,
    events: Sequence[PlantEvent],
) -> dict[str, object]:
    """Project current per-plant state from an optional plant record and immutable events."""

    plant.validate()
    seen: set[str] = set()
    ordered: list[PlantEvent] = []
    planted = date.fromisoformat(plant.planted_date) if plant.planted_date else None

    for event in events:
        event.validate()
        if event.plant_id != plant.id:
            raise ValueError("plant event belongs to another plant")
        if event.id in seen:
            raise ValueError(f"Duplicate plant event id: {event.id}")
        seen.add(event.id)
        if planted is not None and date.fromisoformat(event.event_date) < planted:
            raise ValueError("plant event cannot predate planted_date")
        ordered.append(event)

    ordered.sort(key=lambda item: (item.event_date, item.id))
    status = plant.status
    health = plant.health
    for event in ordered:
        if event.kind == "status":
            status = event.value
        elif event.kind == "health":
            health = event.value

    return {
        "plant_id": plant.id,
        "field_id": plant.field_id,
        "planting_batch_id": plant.planting_batch_id,
        "label": plant.label,
        "planted_date": plant.planted_date,
        "variety": plant.variety,
        "latitude": plant.latitude,
        "longitude": plant.longitude,
        "status": status,
        "health": health,
        "notes": plant.notes,
        "last_event_date": ordered[-1].event_date if ordered else "",
        "event_count": len(ordered),
    }
