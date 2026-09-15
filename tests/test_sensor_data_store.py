from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.sensor_data import SensorChannel, SensorDevice, SensorObservation
from app.sensor_data_store import SensorDataStore


class SensorDataStoreTest(unittest.TestCase):
    @staticmethod
    def field(db: Database, name: str) -> str:
        return str(db.execute("INSERT INTO fields(name) VALUES(?)", (name,)))

    def test_persistence_projection_soft_delete_and_profile_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            first_db = Database(Path(folder) / "first.db")
            second_db = Database(Path(folder) / "second.db")
            # Integer field ids are profile-local and may legitimately collide across
            # separate databases, so use an id that is absent from the second profile
            # when checking rejection of a non-local field reference.
            self.field(first_db, "North archive")
            first_field = self.field(first_db, "North")
            second_field = self.field(second_db, "South")
            sensors = SensorDataStore(first_db)
            sensors.save_device(SensorDevice("station-1", "Weather", "manual", first_field))
            sensors.save_channel(SensorChannel("air", "station-1", "air_temperature", "celsius", "Air"))
            sensors.append_observation(SensorObservation("obs-2", "air", "2026-06-01T10:00:00Z", 28.5))
            sensors.append_observation(SensorObservation("obs-1", "air", "2026-06-01T09:00:00Z", 27.0))

            snapshot = sensors.snapshot("station-1")
            self.assertEqual(1, len(snapshot["channels"]))
            self.assertEqual(28.5, snapshot["channels"][0]["latest_value"])
            self.assertEqual("2026-06-01T10:00:00Z", snapshot["channels"][0]["latest_observed_at"])
            self.assertEqual(["obs-1", "obs-2"], [row.id for row in sensors.observations("air")])

            sensors.delete_device("station-1")
            self.assertEqual([], sensors.devices())
            self.assertEqual(2, len(sensors.observations("air")))
            with self.assertRaisesRegex(ValueError, "does not exist"):
                sensors.append_observation(SensorObservation("obs-3", "air", "2026-06-01T11:00:00Z", 29.0))
            sensors.restore_device("station-1")
            self.assertEqual(1, len(sensors.devices()))

            other = SensorDataStore(second_db)
            with self.assertRaisesRegex(ValueError, "Field"):
                other.save_device(SensorDevice("wrong", "Wrong", "manual", first_field))
            other.save_device(SensorDevice("station-2", "Other", "manual", second_field))
            self.assertEqual(["station-2"], [row.id for row in other.devices()])
            self.assertEqual(["station-1"], [row.id for row in sensors.devices()])

    def test_observations_are_immutable_and_freeze_channel_identity(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "sensor.db")
            field = self.field(db, "A")
            sensors = SensorDataStore(db)
            sensors.save_device(SensorDevice("station", "Station", "provider", field))
            sensors.save_channel(SensorChannel("soil", "station", "soil_moisture", "percent", "Probe"))
            observation = SensorObservation(
                "obs", "soil", "2026-06-01T08:00:00Z", 31.2, "good", "packet-1"
            )
            sensors.append_observation(observation)
            with self.assertRaisesRegex(ValueError, "already exists"):
                sensors.append_observation(observation)

            sensors.save_channel(SensorChannel("soil", "station", "soil_moisture", "percent", "Renamed probe"))
            self.assertEqual("Renamed probe", sensors.channel("soil").label)
            with self.assertRaisesRegex(ValueError, "identity"):
                sensors.save_channel(SensorChannel("soil", "station", "air_humidity", "percent", "Bad rewrite"))

            sensors.save_device(SensorDevice("station", "Station", "provider", field, status="disabled"))
            with self.assertRaisesRegex(ValueError, "Disabled"):
                sensors.append_observation(
                    SensorObservation("later", "soil", "2026-06-01T09:00:00Z", 30.0)
                )

    def test_unknown_metrics_still_require_custom_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "custom.db")
            sensors = SensorDataStore(db)
            sensors.save_device(SensorDevice("station", "Station", "provider"))
            with self.assertRaisesRegex(ValueError, "custom"):
                sensors.save_channel(SensorChannel("bad", "station", "leaf_wetness", "percent"))
            sensors.save_channel(SensorChannel("ok", "station", "custom.leaf_wetness", "percent"))
            self.assertEqual("custom.leaf_wetness", sensors.channel("ok").metric)


if __name__ == "__main__":
    unittest.main()
