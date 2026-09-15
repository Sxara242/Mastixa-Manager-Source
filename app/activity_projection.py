"""Minimal Windows activity projection; no persistence or UI integration."""

from datetime import date, datetime, timedelta, timezone
import re
import sqlite3
import uuid

from .activity_identity import lookup_sync_ref


def _event_date(value: object) -> str | None:
    """Accept ISO calendar dates only, allowing surrounding whitespace."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _recorded_date(value: object) -> str | None:
    """SQLite integer UTC epoch milliseconds, without platform timestamp limits."""
    if type(value) is not int:
        return None
    try:
        instant = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=value)
        return instant.date().isoformat()
    except OverflowError:
        return None


def _canonical_uuid(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = str(uuid.UUID(value))
    except (ValueError, AttributeError):
        return None
    return parsed if parsed == value else None


def _verified_gis_sync_ref(
    connection: sqlite3.Connection,
    tables: set[str],
    dataset_id: str | None,
    source_uuid: object,
    field_uuid: object,
) -> dict | None:
    """Return portable GIS identity only when both records are acknowledged in one dataset."""
    dataset = _canonical_uuid(dataset_id)
    source = _canonical_uuid(source_uuid)
    field = _canonical_uuid(field_uuid)
    if dataset is None or source is None or field is None or "gis_sync_state" not in tables:
        return None
    rows = connection.execute(
        "SELECT id FROM gis_sync_state WHERE dataset=? AND id IN (?,?)",
        (dataset, source, field),
    ).fetchall()
    if {str(row[0]) for row in rows} != {source, field}:
        return None
    return {"dataset_id": dataset, "source_uuid": source, "field_uuid": field}


def _registry_sync_ref(
    connection: sqlite3.Connection,
    scope_id: str,
    dataset_id: str | None,
    source_type: str,
    source_id: object,
    field_id: object,
) -> dict | None:
    if dataset_id is None:
        return None
    return lookup_sync_ref(
        connection, scope_id, dataset_id, source_type, source_id, field_id
    )


def project_field_activities(
    connection: sqlite3.Connection,
    scope_id: str,
    field_id: int,
    dataset_id: str | None = None,
) -> list[dict]:
    """Read one field from the caller's already authorized profile connection.

    The caller must pair scope_id with that profile's connection; scope_id is
    a local identity, not a database path or a cross-device identity. Dates are
    normalized without inventing times. Unknown dates sort last; equal dates
    use lexical source type/ID order. No profile switching happens here.

    dataset_id is optional. A portable sync_ref is emitted only when the
    dataset-scoped registry has an explicit verified source+field mapping. GIS
    observations may also use the already verified GIS sync journal directly.
    """
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise ValueError("A non-empty profile scope_id is required")
    if dataset_id is not None and _canonical_uuid(dataset_id) is None:
        raise ValueError("A canonical dataset UUID is required")

    items = []
    connection.execute("SAVEPOINT activity_projection_read")
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        sources = (
            ("production", "entry_date", "production", "NULL", "harvest"),
            ("farm_activities", "activity_date", "farm_activity", "s.category", None),
            ("planting_batches", "planting_date", "planting_batch", "NULL", "planting"),
            ("plant_protection_records", "application_date", "plant_protection", "NULL", "plant_protection"),
            ("labor_entries", "work_date", "labor_entry", "NULL", "cultivation_work"),
        )
        for table, date_column, source_type, category_column, source_kind in sources:
            if table not in tables:
                continue
            rows = connection.execute(
                f"SELECT s.id, s.field_id, s.{date_column}, {category_column} "
                f"FROM {table} s JOIN fields f ON f.id=s.field_id "
                "WHERE f.id=? ORDER BY s.id", (field_id,)
            )
            for source_id, source_field, event_date, category in rows:
                kind = source_kind if source_kind is not None else {
                    "Πότισμα": "irrigation", "Λίπανση": "fertilization"
                }.get(category)
                if kind is None:
                    continue
                event_date = _event_date(event_date)
                item = {
                    "version": 1,
                    "scope_id": scope_id,
                    "field_id": str(source_field),
                    "source_ref": {"type": source_type, "id": str(source_id)},
                    "kind": kind,
                    "event_date": event_date,
                    "time_basis": "occurred" if event_date is not None else "unknown",
                }
                sync_ref = _registry_sync_ref(
                    connection, scope_id, dataset_id, source_type, source_id, source_field
                )
                if sync_ref is not None:
                    item["sync_ref"] = sync_ref
                items.append(item)
        if {"geo_points", "parcel_geometry"} <= tables:
            rows = connection.execute(
                "SELECT g.id, p.field_id, g.created_at, p.id FROM geo_points g "
                "JOIN parcel_geometry p ON p.id=g.parcel_id "
                "JOIN fields f ON f.id=p.field_id "
                "WHERE f.id=? AND g.deleted_at IS NULL AND p.deleted_at IS NULL "
                "AND g.point_type IN ('note', 'problem')", (field_id,)
            )
            for source_id, source_field, recorded_at, parcel_id in rows:
                event_date = _recorded_date(recorded_at)
                item = {
                    "version": 1, "scope_id": scope_id, "field_id": str(source_field),
                    "source_ref": {"type": "geo_point", "id": str(source_id)},
                    "kind": "observation", "event_date": event_date,
                    "time_basis": "recorded" if event_date is not None else "unknown",
                }
                if event_date is not None:
                    item["event_at"] = recorded_at
                sync_ref = _registry_sync_ref(
                    connection, scope_id, dataset_id, "geo_point", source_id, source_field
                )
                if sync_ref is None:
                    sync_ref = _verified_gis_sync_ref(
                        connection, tables, dataset_id, source_id, parcel_id
                    )
                if sync_ref is not None:
                    item["sync_ref"] = sync_ref
                items.append(item)
    finally:
        connection.execute("RELEASE SAVEPOINT activity_projection_read")
    items.sort(key=lambda item: (
        -date.fromisoformat(item["event_date"]).toordinal()
        if item["event_date"] is not None else 0,
        "event_at" not in item,
        -item.get("event_at", 0),
        item["source_ref"]["type"], item["source_ref"]["id"],
    ))
    return items
