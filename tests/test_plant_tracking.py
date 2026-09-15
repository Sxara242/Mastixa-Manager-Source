from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.plant_tracking import PlantEvent, PlantRecord, project_plant


class PlantTrackingTest(unittest.TestCase):
    def test_shared_fixture_matches_phase14_contract(self) -> None:
        fixture = json.loads(
            Path("shared/fixtures/phase14_plant_tracking.json").read_text(
                encoding="utf-8"
            )
        )
        plant = PlantRecord.from_mapping(fixture["plant"])
        events = [PlantEvent.from_mapping(row) for row in fixture["events"]]
        self.assertEqual(fixture["expected"], project_plant(plant, events))

    def test_optional_tracking_does_not_require_batch_or_coordinates(self) -> None:
        plant = PlantRecord(id="plant-2", field_id="field-a")
        self.assertEqual(
            {
                "plant_id": "plant-2",
                "field_id": "field-a",
                "planting_batch_id": "",
                "label": "",
                "planted_date": "",
                "variety": "",
                "latitude": None,
                "longitude": None,
                "status": "active",
                "health": "unknown",
                "notes": "",
                "last_event_date": "",
                "event_count": 0,
            },
            project_plant(plant, []),
        )

    def test_invalid_identity_dates_coordinates_and_events_fail(self) -> None:
        with self.assertRaises(ValueError):
            project_plant(PlantRecord(id="", field_id="field-a"), [])
        with self.assertRaises(ValueError):
            project_plant(
                PlantRecord(id="p", field_id="f", latitude=38.0, longitude=None), []
            )
        with self.assertRaises(ValueError):
            project_plant(
                PlantRecord(id="p", field_id="f", latitude=91.0, longitude=20.0), []
            )
        plant = PlantRecord(id="p", field_id="f", planted_date="2026-03-01")
        with self.assertRaises(ValueError):
            project_plant(
                plant,
                [PlantEvent("e", "p", "2026-02-28", "note", "before planting")],
            )
        with self.assertRaises(ValueError):
            project_plant(
                plant,
                [PlantEvent("e", "other", "2026-03-02", "note", "wrong plant")],
            )
        with self.assertRaises(ValueError):
            project_plant(
                plant,
                [
                    PlantEvent("e", "p", "2026-03-02", "note", "one"),
                    PlantEvent("e", "p", "2026-03-03", "note", "two"),
                ],
            )
        with self.assertRaises(ValueError):
            project_plant(
                plant,
                [PlantEvent("e", "p", "2026-03-02", "health", "excellent")],
            )


if __name__ == "__main__":
    unittest.main()
