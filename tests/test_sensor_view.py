from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.sensor_view import classify_reading


class SensorViewContractTest(unittest.TestCase):
    def test_shared_fixture_classifies_stale_and_suspect_independently(self) -> None:
        fixture = json.loads(
            (Path(__file__).parents[1] / "shared" / "fixtures" / "phase15_sensor_view.json")
            .read_text(encoding="utf-8")
        )
        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                state = classify_reading(
                    case["observed_at"],
                    case["quality"],
                    fixture["now_utc"],
                    stale_after_seconds=fixture["stale_after_seconds"],
                )
                self.assertEqual(case["has_reading"], state.has_reading)
                self.assertEqual(case["stale"], state.stale)
                self.assertEqual(case["suspect"], state.suspect)

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            classify_reading("2026-09-12T10:00:00Z", "good", "2026-09-12T12:00:00Z", stale_after_seconds=0)
        with self.assertRaisesRegex(ValueError, "quality"):
            classify_reading("2026-09-12T10:00:00Z", "unknown", "2026-09-12T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "UTC"):
            classify_reading("2026-09-12T10:00:00+03:00", "good", "2026-09-12T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
