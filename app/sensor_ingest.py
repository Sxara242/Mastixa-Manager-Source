from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Sequence

from .database import Database
from .sensor_data import SensorChannel, SensorDevice, SensorObservation, project_device
from .sensor_data_store import migrate_sensor_data


@dataclass(frozen=True)
class SensorIngestResult:
    device_created: bool
    channels_created: int
    observations_inserted: int
    observations_unchanged: int


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


def ingest_sensor_batch(
    db: Database,
    input_device: SensorDevice,
    input_channels: Sequence[SensorChannel],
    input_observations: Sequence[SensorObservation],
) -> SensorIngestResult:
    """Atomically ingest one normalized provider-neutral sensor batch.

    Every observation must reference a channel descriptor included in this batch.
    Retries are idempotent: an existing observation id is accepted only when its
    immutable payload is byte-for-byte equivalent at the normalized field level.
    Existing local device metadata and channel labels are never overwritten by retry.
    """

    device = _device(input_device)
    channels = [_channel(value) for value in input_channels]
    observations = [_observation(value) for value in input_observations]
    project_device(device, channels, observations)

    now = int(time.time() * 1000)
    device_created = False
    channels_created = 0
    observations_inserted = 0
    observations_unchanged = 0

    with db.connect() as con:
        migrate_sensor_data(con)
        existing_device = con.execute(
            "SELECT provider,external_id,status,deleted_at FROM sensor_devices WHERE id=?",
            (device.id,),
        ).fetchone()

        if existing_device is None:
            if device.field_id:
                field = con.execute(
                    "SELECT 1 FROM fields WHERE CAST(id AS TEXT)=?", (device.field_id,)
                ).fetchone()
                if field is None:
                    raise ValueError("Field does not exist")
            con.execute(
                """
                INSERT INTO sensor_devices(
                    id,name,provider,field_id,external_id,status,notes,
                    created_at,updated_at,deleted_at
                ) VALUES(?,?,?,?,?,?,?,?,?,NULL)
                """,
                (
                    device.id,
                    device.name,
                    device.provider,
                    device.field_id,
                    device.external_id,
                    device.status,
                    device.notes,
                    now,
                    now,
                ),
            )
            effective_status = device.status
            device_created = True
        else:
            if existing_device["deleted_at"] is not None:
                raise ValueError("Deleted sensor device cannot accept ingestion")
            if str(existing_device["provider"]) != device.provider:
                raise ValueError("Sensor device provider identity conflict")
            existing_external = str(existing_device["external_id"] or "")
            if existing_external and device.external_id and existing_external != device.external_id:
                raise ValueError("Sensor device external identity conflict")
            if not existing_external and device.external_id:
                con.execute(
                    "UPDATE sensor_devices SET external_id=?,updated_at=? WHERE id=?",
                    (device.external_id, now, device.id),
                )
            effective_status = str(existing_device["status"])

        if observations and effective_status != "active":
            raise ValueError("Disabled sensor device cannot accept observations")

        for channel in channels:
            existing = con.execute(
                "SELECT device_id,metric,unit FROM sensor_channels WHERE id=?",
                (channel.id,),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["device_id"]) != channel.device_id
                    or str(existing["metric"]) != channel.metric
                    or str(existing["unit"]) != channel.unit
                ):
                    raise ValueError("Sensor channel identity conflict")
                continue
            con.execute(
                """
                INSERT INTO sensor_channels(
                    id,device_id,metric,unit,label,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    channel.id,
                    channel.device_id,
                    channel.metric,
                    channel.unit,
                    channel.label,
                    now,
                    now,
                ),
            )
            channels_created += 1

        for observation in observations:
            existing = con.execute(
                """
                SELECT channel_id,observed_at,numeric_value,quality,source_ref
                FROM sensor_observations WHERE id=?
                """,
                (observation.id,),
            ).fetchone()
            if existing is not None:
                identical = (
                    str(existing["channel_id"]) == observation.channel_id
                    and str(existing["observed_at"]) == observation.observed_at
                    and float(existing["numeric_value"]) == observation.value
                    and str(existing["quality"]) == observation.quality
                    and str(existing["source_ref"] or "") == observation.source_ref
                )
                if not identical:
                    raise ValueError("Sensor observation identity conflict")
                observations_unchanged += 1
                continue
            con.execute(
                """
                INSERT INTO sensor_observations(
                    id,channel_id,observed_at,numeric_value,quality,source_ref,created_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    observation.id,
                    observation.channel_id,
                    observation.observed_at,
                    observation.value,
                    observation.quality,
                    observation.source_ref,
                    now,
                ),
            )
            observations_inserted += 1

    return SensorIngestResult(
        device_created=device_created,
        channels_created=channels_created,
        observations_inserted=observations_inserted,
        observations_unchanged=observations_unchanged,
    )
