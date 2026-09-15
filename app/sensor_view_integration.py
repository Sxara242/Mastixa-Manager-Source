from __future__ import annotations

# Phase 15E Windows UI is appended so every existing page index stays stable.
from . import main_window as _main_window
from .sensor_view_ui import SensorViewPage


def install_sensor_view_ui() -> None:
    current = _main_window.MainWindow
    if getattr(current, "_phase15_sensor_view_ui", False):
        return

    class SensorViewMainWindow(current):
        _phase15_sensor_view_ui = True

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            page_index = len(self.pages)
            self.pages.append(("Αισθητήρες / API", SensorViewPage(self.db)))
            self.recording_groups[0][1].append(("Αισθητήρες / API", page_index))

    SensorViewMainWindow.__name__ = current.__name__
    SensorViewMainWindow.__qualname__ = current.__qualname__
    SensorViewMainWindow.__module__ = current.__module__
    _main_window.MainWindow = SensorViewMainWindow
