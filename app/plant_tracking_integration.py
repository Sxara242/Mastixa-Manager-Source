from __future__ import annotations

# Phase 14C Windows UI is appended so every existing page index stays stable.
from . import main_window as _main_window
from .plant_tracking_ui import PlantTrackingPage


def install_plant_tracking_ui() -> None:
    current = _main_window.MainWindow
    if getattr(current, "_phase14_plant_tracking_ui", False):
        return

    class PlantTrackingMainWindow(current):
        _phase14_plant_tracking_ui = True

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            page_index = len(self.pages)
            self.pages.append(
                ("Μεμονωμένα Φυτά / Δέντρα", PlantTrackingPage(self.db))
            )
            self.recording_groups[0][1].append(
                ("Μεμονωμένα Φυτά / Δέντρα", page_index)
            )

    PlantTrackingMainWindow.__name__ = current.__name__
    PlantTrackingMainWindow.__qualname__ = current.__qualname__
    PlantTrackingMainWindow.__module__ = current.__module__
    _main_window.MainWindow = PlantTrackingMainWindow
