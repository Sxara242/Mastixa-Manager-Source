from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.sensor_data import SensorChannel, SensorDevice, SensorObservation
from app.sensor_data_store import SensorDataStore
from app.sensor_ingest import ingest_sensor_batch


FIXTURE = Path(__file__).resolve().parents[1] / "shared" / "fixtures" / "phase15_sensor_ingest.json"


def load_fixture():
    root = json.loads(FIXTURE.read_text(encoding="utf-8"))
    device = SensorDevice.from_mapping(root["device"])
    channels = [SensorChannel.from_mapping(row) for row in root["channels"]]
    observations = [SensorObservation.from_mapping(row) for row in root["observations"]]
    return root, device, channels, observations


class SensorIngestTest(unittest.TestCase):
    @staticmethod
    def field(db: Database, name: str) -> str:
        return str(db.execute("INSERT INTO fields(name) VALUES(?)", (name,)))

    def test_shared_fixture_first_ingest_replay_and_local_metadata(self) -> None:
        root, device, channels, observations = load_fixture()
        expected = root["expected"]
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "sensor-ingest.db")
            result = ingest_sensor_batch(db, device, channels, observations)
            self.assertTrue(result.device_created)
            self.assertEqual(expected["channels_created"], result.channels_created)
            self.assertEqual(expected["observations_inserted"], result.observations_inserted)
            self.assertEqual(0, result.observations_unchanged)

            store = SensorDataStore(db)
            snapshot = store.snapshot(device.id)
            air = next(row for row in snapshot["channels"] if row["channel_id"] == "ingest-air")
            self.assertEqual(19.25, air["latest_value"])
            self.assertEqual("suspect", air["latest_quality"])
            self.assertEqual(2, air["observation_count"])

            replay = ingest_sensor_batch(db, device, channels, observations)
            self.assertFalse(replay.device_created)
            self.assertEqual(0, replay.channels_created)
            self.assertEqual(0, replay.observations_inserted)
            self.assertEqual(expected["replay_observations_unchanged"], replay.observations_unchanged)

            store.save_device(SensorDevice(
                device.id, "Local station name", device.provider, "", device.external_id,
                "active", "local notes"
            ))
            store.save_channel(SensorChannel(
                "ingest-air", device.id, "air_temperature", "celsius", "Local air label"
            ))
            ingest_sensor_batch(db, device, channels, observations)
            self.assertEqual("Local station name", store.device(device.id).name)
            self.assertEqual("local notes", store.device(device.id).notes)
            self.assertEqual("Local air label", store.channel("ingest-air").label)

    def test_conflicting_retry_is_atomic_and_identity_guards_apply(self) -> None:
        _, device, channels, observations = load_fixture()
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "sensor-conflict.db")
            ingest_sensor_batch(db, device, channels, observations)
            store = SensorDataStore(db)
            before = len(store.observations("ingest-air"))

            conflicting = [
                SensorObservation(
                    "new-before-conflict", "ingest-air", "2026-09-12T08:00:00Z",
                    20.0, "good", "fixture:new"
                ),
                SensorObservation(
                    observations[0].id, observations[0].channel_id,
                    observations[0].observed_at, observations[0].value + 1.0,
                    observations[0].quality, observations[0].source_ref
                ),
            ]
            with self.assertRaisesRegex(ValueError, "observation identity conflict"):
                ingest_sensor_batch(db, device, channels, conflicting)
            self.assertEqual(before, len(store.observations("ingest-air")))
            self.assertIsNone(db.query_one(
                "SELECT id FROM sensor_observations WHERE id='new-before-conflict'"
            ))

            with self.assertRaisesRegex(ValueError, "provider identity conflict"):
                ingest_sensor_batch(
                    db,
                    SensorDevice(device.id, device.name, "other-provider", external_id=device.external_id),
                    channels,
                    [],
                )

            store.save_device(SensorDevice(
                device.id, device.name, device.provider, "", device.external_id, "disabled", ""
            ))
            with self.assertRaisesRegex(ValueError, "Disabled"):
                ingest_sensor_batch(
                    db, device, channels,
                    [SensorObservation(
                        "disabled-reading", "ingest-air", "2026-09-12T09:00:00Z",
                        21.0, "good", "fixture:disabled"
                    )],
                )

    def test_new_device_field_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "sensor-field.db")
            device = SensorDevice("field-device", "Field probe", "fixture", "999")
            channel = SensorChannel("field-soil", device.id, "soil_moisture", "percent")
            with self.assertRaisesRegex(ValueError, "Field"):
                ingest_sensor_batch(db, device, [channel], [])
            self.assertIsNone(db.query_one(
                "SELECT id FROM sensor_devices WHERE id='field-device'"
            ))


if __name__ == "__main__":
    unittest.main()
