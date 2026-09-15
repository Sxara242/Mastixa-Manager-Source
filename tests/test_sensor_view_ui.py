from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from app.database import Database
from app.sensor_data import SensorChannel, SensorDevice, SensorObservation
from app.sensor_data_store import SensorDataStore
from app.sensor_view_ui import SensorViewPage


class SensorViewUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_page_shows_latest_history_and_stale_suspect_indicators(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "sensor-view.db")
            field_id = str(db.execute("INSERT INTO fields(name) VALUES(?)", ("North",)))
            sensors = SensorDataStore(db)
            sensors.save_device(SensorDevice("station", "Field station", "generic-http", field_id))
            sensors.save_channel(SensorChannel("air", "station", "air_temperature", "celsius", "Air"))
            sensors.save_channel(SensorChannel("soil", "station", "soil_moisture", "percent", "Soil"))
            sensors.save_channel(SensorChannel("tank", "station", "water_level", "millimeter", "Tank"))
            sensors.append_observation(SensorObservation("a1", "air", "2026-09-12T11:30:00Z", 24.5, "good", "p1"))
            sensors.append_observation(SensorObservation("s1", "soil", "2026-09-12T11:00:00Z", 31.0, "suspect", "p2"))
            sensors.append_observation(SensorObservation("t1", "tank", "2026-09-10T08:00:00Z", 420.0, "good", "p3"))

            page = SensorViewPage(db, now_provider=lambda: "2026-09-12T12:00:00Z")
            try:
                self.assertEqual(3, page.latest.rowCount())
                statuses = {page.latest.item(row, 3).text() for row in range(page.latest.rowCount())}
                self.assertIn("ΟΚ", statuses)
                self.assertIn("Ύποπτη", statuses)
                self.assertIn("Παρωχημένη", statuses)
                self.assertIn("generic-http", page.device_info.text())
                self.assertIn("North", page.device_info.text())

                index = page.channel.findData("soil")
                page.channel.setCurrentIndex(index)
                QApplication.processEvents()
                self.assertEqual(1, page.history.rowCount())
                self.assertEqual("Ύποπτη", page.history.item(0, 2).text())
                self.assertEqual("p2", page.history.item(0, 3).text())
            finally:
                page.deleteLater()

    def test_page_explains_stale_threshold_and_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            page = SensorViewPage(Database(Path(folder) / "empty.db"), now_provider=lambda: "2026-09-12T12:00:00Z")
            try:
                texts = [label.text() for label in page.findChildren(QLabel)]
                self.assertIn("Αισθητήρες / API", texts)
                self.assertTrue(any("24 ώρες" in value for value in texts))
                self.assertEqual("Δεν υπάρχουν αποθηκευμένοι αισθητήρες.", page.empty.text())
            finally:
                page.deleteLater()

    def test_startup_integration_appends_sensor_view_without_shifting_existing_indices(self) -> None:
        from app import crop_program_integration, main_window, plant_tracking_integration, sensor_view_integration

        original_window = main_window.MainWindow
        original_crop_page = crop_program_integration.CropProgramsPage
        original_plant_page = plant_tracking_integration.PlantTrackingPage
        original_sensor_page = sensor_view_integration.SensorViewPage

        class BaseWindow:
            def __init__(self, *args, **kwargs) -> None:
                self.db = object()
                self.pages = [
                    ("Ρυθμίσεις" if index == 31 else f"page-{index}", object())
                    for index in range(32)
                ]
                self.recording_groups = [("Καταγραφή", [])]

        class StubPage:
            def __init__(self, db: object, kind: str) -> None:
                self.db = db
                self.kind = kind

        try:
            main_window.MainWindow = BaseWindow
            crop_program_integration.CropProgramsPage = lambda db: StubPage(db, "crop")
            plant_tracking_integration.PlantTrackingPage = lambda db: StubPage(db, "plant")
            sensor_view_integration.SensorViewPage = lambda db: StubPage(db, "sensor")

            crop_program_integration.install_crop_program_ui()
            plant_tracking_integration.install_plant_tracking_ui()
            sensor_view_integration.install_sensor_view_ui()
            window = main_window.MainWindow()

            self.assertEqual(35, len(window.pages))
            self.assertEqual("Ρυθμίσεις", window.pages[31][0])
            self.assertEqual("Πρόγραμμα Καλλιέργειας", window.pages[32][0])
            self.assertEqual("Μεμονωμένα Φυτά / Δέντρα", window.pages[33][0])
            self.assertEqual("Αισθητήρες / API", window.pages[34][0])
            self.assertEqual("sensor", window.pages[34][1].kind)
            self.assertIn(("Αισθητήρες / API", 34), window.recording_groups[0][1])
        finally:
            main_window.MainWindow = original_window
            crop_program_integration.CropProgramsPage = original_crop_page
            plant_tracking_integration.PlantTrackingPage = original_plant_page
            sensor_view_integration.SensorViewPage = original_sensor_page


if __name__ == "__main__":
    unittest.main()
