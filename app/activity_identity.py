"""Dataset-scoped identity registry for Phase 9 activity synchronization.

The registry is additive and lazy: callers may migrate an existing profile database
without changing business tables or inventing identities. It stores only mappings
that a synchronization adapter has explicitly verified.
"""

from __future__ import annotations

import sqlite3
import time
import uuid


SOURCE_TYPES = {
    "production",
    "farm_activity",
    "planting_batch",
    "plant_protection",
    "labor_entry",
    "geo_point",
}


def _uuid(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a canonical UUID")
    try:
        parsed = str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError) as error:
        raise ValueError(f"{label} must be a canonical UUID") from error
    if parsed != value:
        raise ValueError(f"{label} must be a canonical UUID")
    return value


def _text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def migrate(connection: sqlite3.Connection) -> None:
    """Create the additive Phase 9F mapping registry if it is absent."""
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS activity_sync_fields(
            scope_id TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            local_field_id TEXT NOT NULL,
            field_uuid TEXT NOT NULL,
            updated_at INTEGER NOT NULL CHECK(updated_at >= 0),
            PRIMARY KEY(scope_id,dataset_id,local_field_id),
            UNIQUE(scope_id,dataset_id,field_uuid)
        );
        CREATE TABLE IF NOT EXISTS activity_sync_sources(
            scope_id TEXT NOT NULL,
            dataset_id TEXT NOT NULL,
            source_type TEXT NOT NULL,
            local_source_id TEXT NOT NULL,
            local_field_id TEXT NOT NULL,
            source_uuid TEXT NOT NULL,
            updated_at INTEGER NOT NULL CHECK(updated_at >= 0),
            PRIMARY KEY(scope_id,dataset_id,source_type,local_source_id),
            UNIQUE(scope_id,dataset_id,source_type,source_uuid),
            FOREIGN KEY(scope_id,dataset_id,local_field_id)
                REFERENCES activity_sync_fields(scope_id,dataset_id,local_field_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_activity_sync_sources_field
            ON activity_sync_sources(scope_id,dataset_id,local_field_id);
        """
    )
    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='migration_flags'"
    ).fetchone():
        connection.execute(
            "INSERT OR IGNORE INTO migration_flags(name) VALUES(?)",
            ("activity_sync_identity_v1",),
        )


def register_field(
    connection: sqlite3.Connection,
    scope_id: str,
    dataset_id: str,
    local_field_id: object,
    field_uuid: str,
    *,
    updated_at: int | None = None,
) -> None:
    """Record a verified local↔portable field identity without silent remapping."""
    migrate(connection)
    scope = _text(scope_id, "scope_id")
    dataset = _uuid(dataset_id, "dataset_id")
    local = _text(local_field_id, "local_field_id")
    shared = _uuid(field_uuid, "field_uuid")
    stamp = time.time_ns() // 1_000_000 if updated_at is None else updated_at
    if type(stamp) is not int or stamp < 0:
        raise ValueError("updated_at must be a non-negative integer")

    existing = connection.execute(
        "SELECT field_uuid FROM activity_sync_fields "
        "WHERE scope_id=? AND dataset_id=? AND local_field_id=?",
        (scope, dataset, local),
    ).fetchone()
    if existing is not None and existing[0] != shared:
        raise ValueError("Local field already maps to another shared identity")
    reverse = connection.execute(
        "SELECT local_field_id FROM activity_sync_fields "
        "WHERE scope_id=? AND dataset_id=? AND field_uuid=?",
        (scope, dataset, shared),
    ).fetchone()
    if reverse is not None and reverse[0] != local:
        raise ValueError("Shared field identity already maps to another local field")

    connection.execute(
        """INSERT INTO activity_sync_fields
           (scope_id,dataset_id,local_field_id,field_uuid,updated_at)
           VALUES(?,?,?,?,?)
           ON CONFLICT(scope_id,dataset_id,local_field_id) DO UPDATE SET
             updated_at=max(updated_at,excluded.updated_at)
           WHERE field_uuid=excluded.field_uuid""",
        (scope, dataset, local, shared, stamp),
    )


def register_source(
    connection: sqlite3.Connection,
    scope_id: str,
    dataset_id: str,
    source_type: str,
    local_source_id: object,
    local_field_id: object,
    source_uuid: str,
    *,
    updated_at: int | None = None,
) -> None:
    """Record a verified source identity; reassignment requires a mapped target field."""
    migrate(connection)
    scope = _text(scope_id, "scope_id")
    dataset = _uuid(dataset_id, "dataset_id")
    kind = _text(source_type, "source_type")
    if kind not in SOURCE_TYPES:
        raise ValueError("Unsupported activity source type")
    source_local = _text(local_source_id, "local_source_id")
    field_local = _text(local_field_id, "local_field_id")
    shared = _uuid(source_uuid, "source_uuid")
    stamp = time.time_ns() // 1_000_000 if updated_at is None else updated_at
    if type(stamp) is not int or stamp < 0:
        raise ValueError("updated_at must be a non-negative integer")

    field = connection.execute(
        "SELECT 1 FROM activity_sync_fields "
        "WHERE scope_id=? AND dataset_id=? AND local_field_id=?",
        (scope, dataset, field_local),
    ).fetchone()
    if field is None:
        raise ValueError("Source target field has no verified shared identity")

    existing = connection.execute(
        "SELECT source_uuid FROM activity_sync_sources "
        "WHERE scope_id=? AND dataset_id=? AND source_type=? AND local_source_id=?",
        (scope, dataset, kind, source_local),
    ).fetchone()
    if existing is not None and existing[0] != shared:
        raise ValueError("Local source already maps to another shared identity")
    reverse = connection.execute(
        "SELECT local_source_id FROM activity_sync_sources "
        "WHERE scope_id=? AND dataset_id=? AND source_type=? AND source_uuid=?",
        (scope, dataset, kind, shared),
    ).fetchone()
    if reverse is not None and reverse[0] != source_local:
        raise ValueError("Shared source identity already maps to another local source")

    connection.execute(
        """INSERT INTO activity_sync_sources
           (scope_id,dataset_id,source_type,local_source_id,local_field_id,source_uuid,updated_at)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(scope_id,dataset_id,source_type,local_source_id) DO UPDATE SET
             local_field_id=excluded.local_field_id,
             updated_at=max(updated_at,excluded.updated_at)
           WHERE source_uuid=excluded.source_uuid""",
        (scope, dataset, kind, source_local, field_local, shared, stamp),
    )


def lookup_sync_ref(
    connection: sqlite3.Connection,
    scope_id: str,
    dataset_id: str,
    source_type: str,
    local_source_id: object,
    local_field_id: object,
) -> dict[str, str] | None:
    """Return a portable reference only when source and field mappings agree."""
    scope = _text(scope_id, "scope_id")
    dataset = _uuid(dataset_id, "dataset_id")
    kind = _text(source_type, "source_type")
    if kind not in SOURCE_TYPES:
        raise ValueError("Unsupported activity source type")
    source_local = _text(local_source_id, "local_source_id")
    field_local = _text(local_field_id, "local_field_id")

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('activity_sync_fields','activity_sync_sources')"
        )
    }
    if tables != {"activity_sync_fields", "activity_sync_sources"}:
        return None

    row = connection.execute(
        """SELECT s.source_uuid,f.field_uuid
           FROM activity_sync_sources s
           JOIN activity_sync_fields f
             ON f.scope_id=s.scope_id AND f.dataset_id=s.dataset_id
            AND f.local_field_id=s.local_field_id
           WHERE s.scope_id=? AND s.dataset_id=? AND s.source_type=?
             AND s.local_source_id=? AND s.local_field_id=?""",
        (scope, dataset, kind, source_local, field_local),
    ).fetchone()
    if row is None:
        return None
    return {"dataset_id": dataset, "source_uuid": row[0], "field_uuid": row[1]}
