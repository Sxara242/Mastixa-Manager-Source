from __future__ import annotations

import unittest

from app.field_activity_timeline import timeline_rows_from_projection


class FieldActivityTimelineTests(unittest.TestCase):
    def test_all_supported_kinds_are_presented_without_reordering(self):
        items = [
            {"kind": "observation", "event_date": "2026-09-11", "event_at": 1789092000000},
            {"kind": "harvest", "event_date": "2026-09-10"},
            {"kind": "irrigation", "event_date": "2026-09-09"},
            {"kind": "fertilization", "event_date": "2026-09-08"},
            {"kind": "planting", "event_date": "2026-09-07"},
            {"kind": "plant_protection", "event_date": "2026-09-06"},
            {"kind": "cultivation_work", "event_date": "2026-09-05"},
        ]

        rows = timeline_rows_from_projection(items)

        self.assertEqual(
            [row[1] for row in rows],
            [
                "Παρατήρηση GIS",
                "Παραγωγή",
                "Άρδευση & Λίπανση",
                "Άρδευση & Λίπανση",
                "Φυτεύσεις",
                "Φυτοπροστασία",
                "Εργατικά",
            ],
        )
        self.assertEqual(rows[1][0], "2026-09-10")
        self.assertEqual(rows[1][2], "Καταχώρηση παραγωγής")

    def test_recorded_gis_timestamp_is_shown_in_utc(self):
        rows = timeline_rows_from_projection(
            [{"kind": "observation", "event_date": "2026-09-11", "event_at": 1789092000000}]
        )
        self.assertEqual(rows[0][0], "2026-09-11 02:00 UTC")

    def test_unknown_date_is_explicit_and_not_invented(self):
        rows = timeline_rows_from_projection(
            [{"kind": "planting", "event_date": None, "time_basis": "unknown"}]
        )
        self.assertEqual(rows, [("Άγνωστη ημερομηνία", "Φυτεύσεις", "Φύτευση", "")])

    def test_year_filter_keeps_only_matching_normalized_dates(self):
        items = [
            {"kind": "harvest", "event_date": "2026-05-01"},
            {"kind": "irrigation", "event_date": "2025-05-01"},
            {"kind": "planting", "event_date": None},
        ]
        rows = timeline_rows_from_projection(items, "2026")
        self.assertEqual(rows, [("2026-05-01", "Παραγωγή", "Καταχώρηση παραγωγής", "")])

    def test_all_years_keeps_unknown_dates(self):
        items = [
            {"kind": "harvest", "event_date": "2026-05-01"},
            {"kind": "planting", "event_date": None},
        ]
        rows = timeline_rows_from_projection(items)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "Άγνωστη ημερομηνία")

    def test_limit_does_not_change_projection_order(self):
        items = [
            {"kind": "harvest", "event_date": "2026-05-03"},
            {"kind": "planting", "event_date": "2026-05-02"},
            {"kind": "irrigation", "event_date": "2026-05-01"},
        ]
        rows = timeline_rows_from_projection(items, limit=2)
        self.assertEqual([row[0] for row in rows], ["2026-05-03", "2026-05-02"])


if __name__ == "__main__":
    unittest.main()
