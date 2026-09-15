from __future__ import annotations

# Kept as a small startup extension so the mature main-window navigation stays stable
# while Phase 12 UI is introduced. The page is appended; no existing page index moves.
from . import main_window as _main_window
from .crop_programs import CropProgramsPage


def install_crop_program_ui() -> None:
    current = _main_window.MainWindow
    if getattr(current, "_phase12_crop_program_ui", False):
        return

    class CropProgramMainWindow(current):
        _phase12_crop_program_ui = True

        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            page_index = len(self.pages)
            self.pages.append(
                ("Πρόγραμμα Καλλιέργειας", CropProgramsPage(self.db))
            )
            self.recording_groups[0][1].append(
                ("Πρόγραμμα Καλλιέργειας", page_index)
            )

    CropProgramMainWindow.__name__ = current.__name__
    CropProgramMainWindow.__qualname__ = current.__qualname__
    CropProgramMainWindow.__module__ = current.__module__
    _main_window.MainWindow = CropProgramMainWindow
