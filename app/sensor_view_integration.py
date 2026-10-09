from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

# Phase 15E Windows UI is appended so every existing page index stays stable.
# The sensor/API backend remains in the codebase, but the user-facing page is
# intentionally locked until real device/API integration is finished.
from . import main_window as _main_window


class SensorViewPage(QWidget):
    """Non-interactive placeholder for the unfinished Sensors / API feature."""

    def __init__(self, db: object) -> None:
        super().__init__()
        self.db = db
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(14)
        layout.addStretch(1)

        title = QLabel("Αισθητήρες / API")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(title)

        status = QLabel("ΥΠΟ ΚΑΤΑΣΚΕΥΗ")
        status.setObjectName("sensorUnderConstructionStatus")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        status.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        status.setStyleSheet("font-size: 30px; font-weight: 800; letter-spacing: 2px;")
        layout.addWidget(status)

        detail = QLabel(
            "Η λειτουργία αισθητήρων και API δεν είναι ακόμη διαθέσιμη. "
            "Θα ενεργοποιηθεί όταν ολοκληρωθεί η πραγματική σύνδεση συσκευών και υπηρεσιών."
        )
        detail.setObjectName("pageSubtitle")
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        detail.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        detail.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(detail)

        layout.addStretch(1)

    def refresh(self) -> None:
        # Keep the standard page contract without exposing unfinished behavior.
        return


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
