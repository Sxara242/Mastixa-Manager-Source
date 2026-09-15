from __future__ import annotations

import time

from .database import Database
from .sensor_data import SensorChannel, SensorDevice, SensorObservation, project_device


def migrate_sensor_data(con) -> None:
    """Create the additive Phase 15 sensor persistence tables."""
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS sensor_devices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            provider TEXT NOT NULL,
            field_id TEXT NOT NULL DEFAULT '',
            external_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','disabled')),
            notes TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            deleted_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS sensor_channels (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            unit TEXT NOT NULL,
            label TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY(device_id) REFERENCES sensor_devices(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS sensor_observations (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            numeric_value REAL NOT NULL,
            quality TEXT NOT NULL DEFAULT 'good'
                CHECK(quality IN ('good','suspect')),
            source_ref TEXT NOT NULL DEFAULT '',
            created_at INTEGER NOT NULL,
            FOREIGN KEY(channel_id) REFERENCES sensor_channels(id) ON DELETE RESTRICT
        );
        CREATE INDEX IF NOT EXISTS idx_sensor_devices_field
            ON sensor_devices(field_id,deleted_at);
        CREATE INDEX IF NOT EXISTS idx_sensor_channels_device
            ON sensor_channels(device_id,id);
        CREATE INDEX IF NOT EXISTS idx_sensor_observations_channel_time
            ON sensor_observations(channel_id,observed_at,id);
        """
    )


def _device(value: SensorDevice) -> SensorDevice:
    return SensorDevice.from_mapping(
        {
            "id": value.id,
            "name": value.name,
            "provider": value.provider,
            "field_id": value.field_id,
            "external_id": value.external_id,
            "status": value.status,
            "notes": value.notes,
        }
    )


def _channel(value: SensorChannel) -> SensorChannel:
    return SensorChannel.from_mapping(
        {
            "id": value.id,
            "device_id": value.device_id,
            "metric": value.metric,
            "unit": value.unit,
            "label": value.label,
        }
    )


def _observation(value: SensorObservation) -> SensorObservation:
    return SensorObservation.from_mapping(
        {
            "id": value.id,
            "channel_id": value.channel_id,
            "observed_at": value.observed_at,
            "value": value.value,
            "quality": value.quality,
            "source_ref": value.source_ref,
        }
    )


class SensorDataStore:
    """Profile-local sensor metadata plus append-only observations.

    Network endpoints and credentials are deliberately excluded. A channel that has
    observations may still have its display label changed, but its device/metric/unit
    identity is frozen so old measurements cannot silently change meaning.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        with db.connect() as con:
            migrate_sensor_data(con)

    def _require_field(self, field_id: str) -> None:
        if not field_id:
            return
        if self.db.query_one(
            "SELECT 1 FROM fields WHERE CAST(id AS TEXT)=?", (field_id,)
        ) is None:
            raise ValueError("Field does not exist")

    @staticmethod
    def _device_from_row(row) -> SensorDevice:
        return SensorDevice(
            id=str(row["id"]), name=str(row["name"]), provider=str(row["provider"]),
            field_id=str(row["field_id"] or ""), external_id=str(row["external_id"] or ""),
            status=str(row["status"]), notes=str(row["notes"] or ""),
        )

    @staticmethod
    def _channel_from_row(row) -> SensorChannel:
        return SensorChannel(
            id=str(row["id"]), device_id=str(row["device_id"]), metric=str(row["metric"]),
            unit=str(row["unit"]), label=str(row["label"] or ""),
        )

    @staticmethod
    def _observation_from_row(row) -> SensorObservation:
        return SensorObservation(
            id=str(row["id"]), channel_id=str(row["channel_id"]),
            observed_at=str(row["observed_at"]), value=float(row["numeric_value"]),
            quality=str(row["quality"]), source_ref=str(row["source_ref"] or ""),
        )

    def save_device(self, input_device: SensorDevice) -> None:
        device = _device(input_device)
        project_device(device, [], [])
        self._require_field(device.field_id)
        existing = self.db.query_one(
            "SELECT created_at,deleted_at FROM sensor_devices WHERE id=?", (device.id,)
        )
        if existing is not None and existing["deleted_at"] is not None:
            raise ValueError("Deleted sensor device must be restored before editing")
        now = int(time.time() * 1000)
        created = now if existing is None else int(existing["created_at"])
        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO sensor_devices(
                    id,name,provider,field_id,external_id,status,notes,created_at,updated_at,deleted_at
                ) VALUES(?,?,?,?,?,?,?,?,?,NULL)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,provider=excluded.provider,field_id=excluded.field_id,
                    external_id=excluded.external_id,status=excluded.status,notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                (device.id, device.name, device.provider, device.field_id, device.external_id,
                 device.status, device.notes, created, now),
            )

    def device(self, device_id: str, *, include_deleted: bool = False) -> SensorDevice:
        clause = "" if include_deleted else " AND deleted_at IS NULL"
        row = self.db.query_one(
            "SELECT id,name,provider,field_id,external_id,status,notes "
            "FROM sensor_devices WHERE id=?" + clause,
            (str(device_id).strip(),),
        )
        if row is None:
            raise ValueError("Sensor device does not exist")
        return self._device_from_row(row)

    def devices(self, *, include_deleted: bool = False) -> list[SensorDevice]:
        clause = "" if include_deleted else " WHERE deleted_at IS NULL"
        return [
            self._device_from_row(row)
            for row in self.db.query(
                "SELECT id,name,provider,field_id,external_id,status,notes FROM sensor_devices"
                + clause + " ORDER BY name COLLATE NOCASE,id"
            )
        ]

    def save_channel(self, input_channel: SensorChannel) -> None:
        channel = _channel(input_channel)
        owner = self.device(channel.device_id)
        project_device(owner, [channel], [])
        existing = self.db.query_one(
            "SELECT device_id,metric,unit,created_at FROM sensor_channels WHERE id=?",
            (channel.id,),
        )
        now = int(time.time() * 1000)
        created = now
        if existing is not None:
            created = int(existing["created_at"])
            count = self.db.query_one(
                "SELECT COUNT(*) AS n FROM sensor_observations WHERE channel_id=?", (channel.id,)
            )
            if int(count["n"]) > 0 and (
                str(existing["device_id"]) != channel.device_id
                or str(existing["metric"]) != channel.metric
                or str(existing["unit"]) != channel.unit
            ):
                raise ValueError("Observed channel identity cannot be changed")
        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO sensor_channels(id,device_id,metric,unit,label,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    device_id=excluded.device_id,metric=excluded.metric,unit=excluded.unit,
                    label=excluded.label,updated_at=excluded.updated_at
                """,
                (channel.id, channel.device_id, channel.metric, channel.unit, channel.label, created, now),
            )

    def channel(self, channel_id: str) -> SensorChannel:
        row = self.db.query_one(
            "SELECT id,device_id,metric,unit,label FROM sensor_channels WHERE id=?",
            (str(channel_id).strip(),),
        )
        if row is None:
            raise ValueError("Sensor channel does not exist")
        return self._channel_from_row(row)

    def channels(self, device_id: str) -> list[SensorChannel]:
        return [
            self._channel_from_row(row)
            for row in self.db.query(
                "SELECT id,device_id,metric,unit,label FROM sensor_channels "
                "WHERE device_id=? ORDER BY id", (str(device_id).strip(),)
            )
        ]

    def append_observation(self, input_observation: SensorObservation) -> None:
        observation = _observation(input_observation)
        if self.db.query_one(
            "SELECT 1 FROM sensor_observations WHERE id=?", (observation.id,)
        ) is not None:
            raise ValueError("Sensor observation id already exists")
        channel = self.channel(observation.channel_id)
        owner = self.device(channel.device_id)
        if owner.status != "active":
            raise ValueError("Disabled sensor device cannot accept observations")
        project_device(owner, [channel], [observation])
        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO sensor_observations(
                    id,channel_id,observed_at,numeric_value,quality,source_ref,created_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (observation.id, observation.channel_id, observation.observed_at,
                 observation.value, observation.quality, observation.source_ref,
                 int(time.time() * 1000)),
            )

    def observations(self, channel_id: str) -> list[SensorObservation]:
        return [
            self._observation_from_row(row)
            for row in self.db.query(
                "SELECT id,channel_id,observed_at,numeric_value,quality,source_ref "
                "FROM sensor_observations WHERE channel_id=? ORDER BY observed_at,id",
                (str(channel_id).strip(),),
            )
        ]

    def snapshot(self, device_id: str) -> dict[str, object]:
        device = self.device(device_id)
        channels = self.channels(device.id)
        observations: list[SensorObservation] = []
        for channel in channels:
            observations.extend(self.observations(channel.id))
        return project_device(device, channels, observations)

    def delete_device(self, device_id: str) -> None:
        key = str(device_id).strip()
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                "UPDATE sensor_devices SET deleted_at=?,updated_at=? "
                "WHERE id=? AND deleted_at IS NULL", (now, now, key)
            ).rowcount
            if changed != 1:
                raise ValueError("Sensor device does not exist")

    def restore_device(self, device_id: str) -> None:
        device = self.device(device_id, include_deleted=True)
        self._require_field(device.field_id)
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                "UPDATE sensor_devices SET deleted_at=NULL,updated_at=? "
                "WHERE id=? AND deleted_at IS NOT NULL", (now, device.id)
            ).rowcount
            if changed != 1:
                raise ValueError("Deleted sensor device does not exist")
