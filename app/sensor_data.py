from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
import re
from typing import Any, Mapping, Sequence


DEVICE_STATUSES = frozenset({"active", "disabled"})
OBSERVATION_QUALITIES = frozenset({"good", "suspect"})
CANONICAL_UNITS = {
    "air_temperature": "celsius",
    "soil_temperature": "celsius",
    "air_humidity": "percent",
    "soil_moisture": "percent",
    "rainfall": "millimeter",
    "battery": "percent",
    "water_level": "millimeter",
    "pressure": "hectopascal",
    "wind_speed": "meter_per_second",
    "soil_ec": "microsiemens_per_cm",
    "soil_ph": "ph",
}
_MACHINE_ID = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_UNIT_ID = re.compile(r"^[a-z][a-z0-9_./-]{0,31}$")
_UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _required(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _optional(value: object) -> str:
    return str(value or "").strip()


def _machine_id(value: object, label: str, *, unit: bool = False) -> str:
    text = _required(value, label)
    pattern = _UNIT_ID if unit else _MACHINE_ID
    if not pattern.fullmatch(text):
        raise ValueError(f"{label} must be a stable lowercase machine identifier")
    return text


def _utc_timestamp(value: object, label: str) -> str:
    text = _required(value, label)
    if not _UTC_SECOND.fullmatch(text):
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ")
    return text


def _number(value: object, label: str) -> float:
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
class SensorDevice:
    id: str
    name: str
    provider: str
    field_id: str = ""
    external_id: str = ""
    status: str = "active"
    notes: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SensorDevice":
        return cls(
            id=_required(value.get("id"), "device id"),
            name=_required(value.get("name"), "device name"),
            provider=_required(value.get("provider"), "provider"),
            field_id=_optional(value.get("field_id")),
            external_id=_optional(value.get("external_id")),
            status=_required(value.get("status") or "active", "device status"),
            notes=_optional(value.get("notes")),
        )

    def validate(self) -> None:
        _required(self.id, "device id")
        _required(self.name, "device name")
        _required(self.provider, "provider")
        if self.status not in DEVICE_STATUSES:
            raise ValueError(f"Unsupported device status: {self.status}")


@dataclass(frozen=True)
class SensorChannel:
    id: str
    device_id: str
    metric: str
    unit: str
    label: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SensorChannel":
        return cls(
            id=_required(value.get("id"), "channel id"),
            device_id=_required(value.get("device_id"), "device id"),
            metric=_machine_id(value.get("metric"), "metric"),
            unit=_machine_id(value.get("unit"), "unit", unit=True),
            label=_optional(value.get("label")),
        )

    def validate(self) -> None:
        _required(self.id, "channel id")
        _required(self.device_id, "device id")
        metric = _machine_id(self.metric, "metric")
        unit = _machine_id(self.unit, "unit", unit=True)
        expected = CANONICAL_UNITS.get(metric)
        if expected is not None and unit != expected:
            raise ValueError(f"Metric {metric} requires canonical unit {expected}")
        if expected is None and not metric.startswith("custom."):
            raise ValueError("Unknown metric must use the custom. namespace")


@dataclass(frozen=True)
class SensorObservation:
    id: str
    channel_id: str
    observed_at: str
    value: float
    quality: str = "good"
    source_ref: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SensorObservation":
        return cls(
            id=_required(value.get("id"), "observation id"),
            channel_id=_required(value.get("channel_id"), "channel id"),
            observed_at=_utc_timestamp(value.get("observed_at"), "observed_at"),
            value=_number(value.get("value"), "observation value"),
            quality=_required(value.get("quality") or "good", "observation quality"),
            source_ref=_optional(value.get("source_ref")),
        )

    def validate(self) -> None:
        _required(self.id, "observation id")
        _required(self.channel_id, "channel id")
        _utc_timestamp(self.observed_at, "observed_at")
        _number(self.value, "observation value")
        if self.quality not in OBSERVATION_QUALITIES:
            raise ValueError(f"Unsupported observation quality: {self.quality}")


def project_device(
    device: SensorDevice,
    channels: Sequence[SensorChannel],
    observations: Sequence[SensorObservation],
) -> dict[str, object]:
    """Normalize one sensor/API device into deterministic channel snapshots.

    This is deliberately transport-free: network credentials, endpoints and polling
    state do not belong to the shared observation contract.
    """

    device.validate()
    channel_by_id: dict[str, SensorChannel] = {}
    for channel in channels:
        channel.validate()
        if channel.device_id != device.id:
            raise ValueError("sensor channel belongs to another device")
        if channel.id in channel_by_id:
            raise ValueError(f"Duplicate sensor channel id: {channel.id}")
        channel_by_id[channel.id] = channel

    observation_ids: set[str] = set()
    grouped: dict[str, list[SensorObservation]] = {key: [] for key in channel_by_id}
    for observation in observations:
        observation.validate()
        if observation.id in observation_ids:
            raise ValueError(f"Duplicate sensor observation id: {observation.id}")
        observation_ids.add(observation.id)
        if observation.channel_id not in channel_by_id:
            raise ValueError("sensor observation references an unknown channel")
        grouped[observation.channel_id].append(observation)

    channel_snapshots: list[dict[str, object]] = []
    for channel_id in sorted(channel_by_id):
        channel = channel_by_id[channel_id]
        ordered = sorted(
            grouped[channel_id], key=lambda item: (item.observed_at, item.id)
        )
        latest = ordered[-1] if ordered else None
        channel_snapshots.append(
            {
                "channel_id": channel.id,
                "metric": channel.metric,
                "unit": channel.unit,
                "label": channel.label,
                "latest_value": None if latest is None else latest.value,
                "latest_quality": "" if latest is None else latest.quality,
                "latest_observed_at": "" if latest is None else latest.observed_at,
                "latest_source_ref": "" if latest is None else latest.source_ref,
                "observation_count": len(ordered),
            }
        )

    return {
        "device_id": device.id,
        "field_id": device.field_id,
        "name": device.name,
        "provider": device.provider,
        "external_id": device.external_id,
        "status": device.status,
        "notes": device.notes,
        "channels": channel_snapshots,
    }
