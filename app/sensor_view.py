from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re


DEFAULT_STALE_AFTER_SECONDS = 24 * 60 * 60
_UTC_SECOND = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@dataclass(frozen=True)
class SensorReadingState:
    has_reading: bool
    stale: bool
    suspect: bool


def _parse_utc(value: str, label: str) -> datetime:
    text = str(value or "").strip()
    if not _UTC_SECOND.fullmatch(text):
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != text:
        raise ValueError(f"{label} must be UTC YYYY-MM-DDTHH:MM:SSZ")
    return parsed


def utc_now_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_reading(
    latest_observed_at: str,
    latest_quality: str,
    now_utc: str,
    *,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> SensorReadingState:
    """Derive presentation-only stale/suspect flags for one latest reading.

    `stale` is true only when the latest reading is strictly older than the
    configured threshold. `suspect` is independent, so one reading may be both.
    Missing readings are neither stale nor suspect.
    """

    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")
    observed = str(latest_observed_at or "").strip()
    quality = str(latest_quality or "").strip()
    if not observed:
        return SensorReadingState(False, False, False)
    if quality not in {"good", "suspect"}:
        raise ValueError("latest quality must be good or suspect")
    observed_at = _parse_utc(observed, "latest_observed_at")
    now = _parse_utc(now_utc, "now_utc")
    age_seconds = (now - observed_at).total_seconds()
    return SensorReadingState(
        True,
        age_seconds > stale_after_seconds,
        quality == "suspect",
    )
