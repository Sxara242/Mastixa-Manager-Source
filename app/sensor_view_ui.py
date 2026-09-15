from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .sensor_data_store import SensorDataStore
from .sensor_view import classify_reading, utc_now_text
from .ui_helpers import compact_decimal, table_widget


METRIC_LABELS = {
    "air_temperature": "Θερμοκρασία αέρα",
    "soil_temperature": "Θερμοκρασία εδάφους",
    "air_humidity": "Υγρασία αέρα",
    "soil_moisture": "Υγρασία εδάφους",
    "rainfall": "Βροχόπτωση",
    "battery": "Μπαταρία",
    "water_level": "Στάθμη νερού",
    "pressure": "Πίεση",
    "wind_speed": "Ταχύτητα ανέμου",
    "soil_ec": "Αγωγιμότητα εδάφους",
    "soil_ph": "pH εδάφους",
}
UNIT_LABELS = {
    "celsius": "°C",
    "percent": "%",
    "millimeter": "mm",
    "hectopascal": "hPa",
    "meter_per_second": "m/s",
    "microsiemens_per_cm": "µS/cm",
    "ph": "pH",
}


def _metric_label(metric: str) -> str:
    return METRIC_LABELS.get(metric, metric.removeprefix("custom.").replace("_", " "))


def _unit_label(unit: str) -> str:
    return UNIT_LABELS.get(unit, unit)


class SensorViewPage(QWidget):
    """Read-only Phase 15 sensor dashboard backed by the profile-local store."""

    def __init__(
        self,
        db: Database,
        parent: QWidget | None = None,
        *,
        now_provider: Callable[[], str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self.store = SensorDataStore(db)
        self.now_provider = now_provider or utc_now_text

        root = QVBoxLayout(self)
        title = QLabel("Αισθητήρες / API")
        title.setObjectName("sensorViewTitle")
        font = title.font()
        font.setPointSize(max(font.pointSize(), 18))
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)

        description = QLabel(
            "Τελευταίες μετρήσεις και ιστορικό από τοπικά αποθηκευμένα δεδομένα. "
            "Η ένδειξη Παρωχημένη εμφανίζεται όταν η τελευταία μέτρηση είναι πάνω από 24 ώρες παλιά."
        )
        description.setWordWrap(True)
        root.addWidget(description)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Συσκευή"))
        self.device = QComboBox()
        self.device.setMinimumWidth(260)
        self.device.currentIndexChanged.connect(self._refresh_device)
        controls.addWidget(self.device, 1)
        self.refresh_button = QPushButton("Ανανέωση")
        self.refresh_button.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_button)
        root.addLayout(controls)

        self.device_info = QLabel("")
        self.device_info.setWordWrap(True)
        root.addWidget(self.device_info)

        root.addWidget(QLabel("Τελευταίες μετρήσεις"))
        self.latest = table_widget(
            ["Κανάλι", "Μετρική", "Τιμή", "Κατάσταση", "Τελευταία μέτρηση (UTC)", "Σύνολο"]
        )
        self.latest.setObjectName("sensorLatestTable")
        self.latest.setSelectionMode(self.latest.SelectionMode.SingleSelection)
        self.latest.itemSelectionChanged.connect(self._latest_selection_changed)
        root.addWidget(self.latest, 2)

        history_controls = QHBoxLayout()
        history_controls.addWidget(QLabel("Ιστορικό καναλιού"))
        self.channel = QComboBox()
        self.channel.currentIndexChanged.connect(self._refresh_history)
        history_controls.addWidget(self.channel, 1)
        root.addLayout(history_controls)

        self.history = table_widget(["Χρόνος (UTC)", "Τιμή", "Ποιότητα", "Πηγή"])
        self.history.setObjectName("sensorHistoryTable")
        root.addWidget(self.history, 2)

        self.empty = QLabel("")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.empty)

        self.refresh()

    def refresh(self) -> None:
        selected = str(self.device.currentData() or "")
        self.device.blockSignals(True)
        self.device.clear()
        rows = self.store.devices()
        for row in rows:
            self.device.addItem(row.name, row.id)
        index = self.device.findData(selected)
        self.device.setCurrentIndex(index if index >= 0 else (0 if rows else -1))
        self.device.blockSignals(False)
        self.empty.setText("Δεν υπάρχουν αποθηκευμένοι αισθητήρες." if not rows else "")
        self._refresh_device()

    def _field_name(self, field_id: str) -> str:
        if not field_id:
            return "Χωρίς αγροτεμάχιο"
        row = self.db.query_one("SELECT name FROM fields WHERE CAST(id AS TEXT)=?", (field_id,))
        return str(row["name"]) if row is not None else "Διαγραμμένο αγροτεμάχιο"

    def _status_text(self, observed_at: str, quality: str) -> str:
        state = classify_reading(observed_at, quality, self.now_provider())
        if not state.has_reading:
            return "Χωρίς μέτρηση"
        flags: list[str] = []
        if state.suspect:
            flags.append("Ύποπτη")
        if state.stale:
            flags.append("Παρωχημένη")
        return " · ".join(flags) if flags else "ΟΚ"

    def _refresh_device(self) -> None:
        device_id = str(self.device.currentData() or "")
        self.latest.setRowCount(0)
        self.channel.blockSignals(True)
        previous_channel = str(self.channel.currentData() or "")
        self.channel.clear()
        if not device_id:
            self.channel.blockSignals(False)
            self.device_info.setText("")
            self._refresh_history()
            return

        snapshot = self.store.snapshot(device_id)
        status = "Ενεργή" if snapshot["status"] == "active" else "Απενεργοποιημένη"
        self.device_info.setText(
            f"{snapshot['provider']} · {self._field_name(str(snapshot['field_id']))} · {status}"
        )
        for channel in snapshot["channels"]:
            row = self.latest.rowCount()
            self.latest.insertRow(row)
            label = str(channel["label"] or "") or _metric_label(str(channel["metric"]))
            value = "—"
            if channel["latest_value"] is not None:
                value = f"{compact_decimal(float(channel['latest_value']), 3)} {_unit_label(str(channel['unit']))}"
            values = [
                label,
                _metric_label(str(channel["metric"])),
                value,
                self._status_text(str(channel["latest_observed_at"]), str(channel["latest_quality"])),
                str(channel["latest_observed_at"] or "—"),
                str(channel["observation_count"]),
            ]
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, str(channel["channel_id"]))
                self.latest.setItem(row, column, item)
            self.channel.addItem(label, str(channel["channel_id"]))

        channel_index = self.channel.findData(previous_channel)
        self.channel.setCurrentIndex(channel_index if channel_index >= 0 else (0 if self.channel.count() else -1))
        self.channel.blockSignals(False)
        self._refresh_history()

    def _latest_selection_changed(self) -> None:
        row = self.latest.currentRow()
        if row < 0:
            return
        item = self.latest.item(row, 0)
        if item is None:
            return
        channel_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        index = self.channel.findData(channel_id)
        if index >= 0:
            self.channel.setCurrentIndex(index)

    def _refresh_history(self) -> None:
        self.history.setRowCount(0)
        channel_id = str(self.channel.currentData() or "")
        if not channel_id:
            return
        channel = self.store.channel(channel_id)
        rows = self.store.observations(channel_id)
        for observation in reversed(rows[-200:]):
            row = self.history.rowCount()
            self.history.insertRow(row)
            quality = "Ύποπτη" if observation.quality == "suspect" else "Καλή"
            values = [
                observation.observed_at,
                f"{compact_decimal(observation.value, 3)} {_unit_label(channel.unit)}",
                quality,
                observation.source_ref or "—",
            ]
            for column, value in enumerate(values):
                self.history.setItem(row, column, QTableWidgetItem(value))
