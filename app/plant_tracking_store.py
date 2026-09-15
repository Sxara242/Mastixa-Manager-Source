from __future__ import annotations

import time

from .database import Database
from .plant_tracking import PlantEvent, PlantRecord, project_plant


def migrate_plant_tracking(con) -> None:
    """Create additive Phase 14 persistence without changing planting-batch totals."""
    statements = (
        """
        CREATE TABLE IF NOT EXISTS individual_plants (
            id TEXT PRIMARY KEY,
            field_id TEXT NOT NULL,
            planting_batch_id TEXT NOT NULL DEFAULT '',
            label TEXT NOT NULL DEFAULT '',
            planted_date TEXT NOT NULL DEFAULT '',
            variety TEXT NOT NULL DEFAULT '',
            latitude REAL,
            longitude REAL,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','dead','removed')),
            health TEXT NOT NULL DEFAULT 'unknown'
                CHECK(health IN ('unknown','good','watch','poor')),
            notes TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            deleted_at INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS plant_events (
            id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            event_date TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('note','health','status')),
            value TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            FOREIGN KEY(plant_id) REFERENCES individual_plants(id) ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_individual_plants_field ON individual_plants(field_id,deleted_at)",
        "CREATE INDEX IF NOT EXISTS idx_individual_plants_batch ON individual_plants(planting_batch_id)",
        "CREATE INDEX IF NOT EXISTS idx_plant_events_plant_date ON plant_events(plant_id,event_date,id)",
    )
    for statement in statements:
        con.execute(statement)


def _text(value: object) -> str:
    return str(value or "").strip()


def _normalized_plant(plant: PlantRecord) -> PlantRecord:
    return PlantRecord.from_mapping(
        {
            "id": plant.id,
            "field_id": plant.field_id,
            "planting_batch_id": plant.planting_batch_id,
            "label": plant.label,
            "planted_date": plant.planted_date,
            "variety": plant.variety,
            "latitude": plant.latitude,
            "longitude": plant.longitude,
            "status": plant.status,
            "health": plant.health,
            "notes": plant.notes,
        }
    )


def _normalized_event(event: PlantEvent) -> PlantEvent:
    return PlantEvent.from_mapping(
        {
            "id": event.id,
            "plant_id": event.plant_id,
            "event_date": event.event_date,
            "kind": event.kind,
            "value": event.value,
            "notes": event.notes,
        }
    )


class PlantTrackingStore:
    """Local optional per-plant persistence with immutable event history."""

    def __init__(self, db: Database) -> None:
        self.db = db
        with self.db.connect() as con:
            migrate_plant_tracking(con)

    def _require_field(self, field_id: str) -> None:
        row = self.db.query_one(
            "SELECT 1 FROM fields WHERE CAST(id AS TEXT)=?",
            (field_id,),
        )
        if row is None:
            raise ValueError("Field does not exist")

    def _require_batch(self, batch_id: str, field_id: str) -> None:
        if not batch_id:
            return
        table = self.db.query_one(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='planting_batches'"
        )
        if table is None:
            raise ValueError("Planting batch does not exist")
        row = self.db.query_one(
            "SELECT CAST(field_id AS TEXT) AS field_id FROM planting_batches WHERE CAST(id AS TEXT)=?",
            (batch_id,),
        )
        if row is None:
            raise ValueError("Planting batch does not exist")
        if str(row["field_id"]) != field_id:
            raise ValueError("Planting batch belongs to another field")

    @staticmethod
    def _plant_from_row(row) -> PlantRecord:
        return PlantRecord(
            id=str(row["id"]),
            field_id=str(row["field_id"]),
            planting_batch_id=str(row["planting_batch_id"] or ""),
            label=str(row["label"] or ""),
            planted_date=str(row["planted_date"] or ""),
            variety=str(row["variety"] or ""),
            latitude=None if row["latitude"] is None else float(row["latitude"]),
            longitude=None if row["longitude"] is None else float(row["longitude"]),
            status=str(row["status"]),
            health=str(row["health"]),
            notes=str(row["notes"] or ""),
        )

    @staticmethod
    def _event_from_row(row) -> PlantEvent:
        return PlantEvent(
            id=str(row["id"]),
            plant_id=str(row["plant_id"]),
            event_date=str(row["event_date"]),
            kind=str(row["kind"]),
            value=str(row["value"] or ""),
            notes=str(row["notes"] or ""),
        )

    def save_plant(self, input_plant: PlantRecord) -> None:
        plant = _normalized_plant(input_plant)
        plant.validate()
        self._require_field(plant.field_id)
        self._require_batch(plant.planting_batch_id, plant.field_id)

        existing = self.db.query_one(
            "SELECT deleted_at,created_at FROM individual_plants WHERE id=?",
            (plant.id,),
        )
        if existing is not None and existing["deleted_at"] is not None:
            raise ValueError("Deleted plant must be restored before editing")

        project_plant(plant, self.events(plant.id))
        now = int(time.time() * 1000)
        created_at = now if existing is None else int(existing["created_at"])
        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO individual_plants(
                    id,field_id,planting_batch_id,label,planted_date,variety,
                    latitude,longitude,status,health,notes,created_at,updated_at,deleted_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)
                ON CONFLICT(id) DO UPDATE SET
                    field_id=excluded.field_id,
                    planting_batch_id=excluded.planting_batch_id,
                    label=excluded.label,
                    planted_date=excluded.planted_date,
                    variety=excluded.variety,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    status=excluded.status,
                    health=excluded.health,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                (
                    plant.id,
                    plant.field_id,
                    plant.planting_batch_id,
                    plant.label,
                    plant.planted_date,
                    plant.variety,
                    plant.latitude,
                    plant.longitude,
                    plant.status,
                    plant.health,
                    plant.notes,
                    created_at,
                    now,
                ),
            )

    def plant(self, plant_id: str, *, include_deleted: bool = False) -> PlantRecord:
        clause = "" if include_deleted else " AND deleted_at IS NULL"
        row = self.db.query_one(
            """
            SELECT id,field_id,planting_batch_id,label,planted_date,variety,
                   latitude,longitude,status,health,notes
            FROM individual_plants WHERE id=?
            """
            + clause,
            (_text(plant_id),),
        )
        if row is None:
            raise ValueError("Plant does not exist")
        return self._plant_from_row(row)

    def plants(
        self,
        *,
        field_id: str | int | None = None,
        include_deleted: bool = False,
    ) -> list[PlantRecord]:
        where: list[str] = []
        params: list[object] = []
        if not include_deleted:
            where.append("deleted_at IS NULL")
        if field_id is not None:
            where.append("field_id=?")
            params.append(str(field_id))
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        rows = self.db.query(
            """
            SELECT id,field_id,planting_batch_id,label,planted_date,variety,
                   latitude,longitude,status,health,notes
            FROM individual_plants
            """
            + clause
            + " ORDER BY field_id,label COLLATE NOCASE,id",
            params,
        )
        return [self._plant_from_row(row) for row in rows]

    def events(self, plant_id: str) -> list[PlantEvent]:
        rows = self.db.query(
            """
            SELECT id,plant_id,event_date,kind,value,notes
            FROM plant_events
            WHERE plant_id=?
            ORDER BY event_date,id
            """,
            (_text(plant_id),),
        )
        return [self._event_from_row(row) for row in rows]

    def append_event(self, input_event: PlantEvent) -> None:
        event = _normalized_event(input_event)
        event.validate()
        plant = self.plant(event.plant_id)
        if self.db.query_one("SELECT 1 FROM plant_events WHERE id=?", (event.id,)) is not None:
            raise ValueError("Plant event id already exists")
        history = self.events(event.plant_id)
        project_plant(plant, [*history, event])
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO plant_events(id,plant_id,event_date,kind,value,notes,created_at)
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    event.id,
                    event.plant_id,
                    event.event_date,
                    event.kind,
                    event.value,
                    event.notes,
                    now,
                ),
            )

    def snapshot(self, plant_id: str) -> dict[str, object]:
        plant = self.plant(plant_id)
        return project_plant(plant, self.events(plant.id))

    def delete_plant(self, plant_id: str) -> None:
        key = _text(plant_id)
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                """
                UPDATE individual_plants
                SET deleted_at=?,updated_at=?
                WHERE id=? AND deleted_at IS NULL
                """,
                (now, now, key),
            ).rowcount
            if changed != 1:
                raise ValueError("Plant does not exist")

    def restore_plant(self, plant_id: str) -> None:
        plant = self.plant(plant_id, include_deleted=True)
        self._require_field(plant.field_id)
        self._require_batch(plant.planting_batch_id, plant.field_id)
        key = _text(plant_id)
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                """
                UPDATE individual_plants
                SET deleted_at=NULL,updated_at=?
                WHERE id=? AND deleted_at IS NOT NULL
                """,
                (now, key),
            ).rowcount
            if changed != 1:
                raise ValueError("Deleted plant does not exist")
