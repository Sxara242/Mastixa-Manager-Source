from __future__ import annotations

import json
from math import nan
from pathlib import Path
import unittest

from app.sensor_data import (
    SensorChannel,
    SensorDevice,
    SensorObservation,
    project_device,
)


FIXTURE = Path(__file__).resolve().parents[1] / "shared" / "fixtures" / "phase15_sensor_data.json"


class SensorDataTest(unittest.TestCase):
    def test_shared_fixture_matches_cross_client_sensor_contract(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        device = SensorDevice.from_mapping(fixture["device"])
        channels = [SensorChannel.from_mapping(row) for row in fixture["channels"]]
        observations = [
            SensorObservation.from_mapping(row) for row in fixture["observations"]
        ]
        self.assertEqual(fixture["expected"], project_device(device, channels, observations))

    def test_field_link_is_optional_and_custom_metrics_are_namespaced(self) -> None:
        device = SensorDevice("device-1", "Portable probe", "manual-import")
        channel = SensorChannel(
            "leaf-wetness", "device-1", "custom.leaf_wetness", "percent", "Leaf"
        )
        snapshot = project_device(device, [channel], [])
        self.assertEqual("", snapshot["field_id"])
        self.assertEqual("custom.leaf_wetness", snapshot["channels"][0]["metric"])
        self.assertIsNone(snapshot["channels"][0]["latest_value"])

    def test_ids_ordering_units_timestamps_and_values_are_strict(self) -> None:
        device = SensorDevice("device-1", "Station", "generic")
        good = SensorChannel("air", "device-1", "air_temperature", "celsius")

        with self.assertRaisesRegex(ValueError, "canonical unit"):
            project_device(
                device,
                [SensorChannel("air", "device-1", "air_temperature", "fahrenheit")],
                [],
            )
        with self.assertRaisesRegex(ValueError, "custom"):
            project_device(
                device,
                [SensorChannel("mystery", "device-1", "leaf_wetness", "percent")],
                [],
            )
        with self.assertRaisesRegex(ValueError, "Duplicate sensor channel"):
            project_device(device, [good, good], [])
        with self.assertRaisesRegex(ValueError, "another device"):
            project_device(
                device,
                [SensorChannel("air", "device-2", "air_temperature", "celsius")],
                [],
            )
        with self.assertRaisesRegex(ValueError, "UTC"):
            project_device(
                device,
                [good],
                [SensorObservation("o1", "air", "2026-09-12T01:00:00+03:00", 20.0)],
            )
        with self.assertRaisesRegex(ValueError, "finite"):
            project_device(
                device,
                [good],
                [SensorObservation("o1", "air", "2026-09-12T01:00:00Z", nan)],
            )
        unknown = SensorObservation("o1", "missing", "2026-09-12T01:00:00Z", 20.0)
        with self.assertRaisesRegex(ValueError, "unknown channel"):
            project_device(device, [good], [unknown])
        observation = SensorObservation("o1", "air", "2026-09-12T01:00:00Z", 20.0)
        with self.assertRaisesRegex(ValueError, "Duplicate sensor observation"):
            project_device(device, [good], [observation, observation])


if __name__ == "__main__":
    unittest.main()
