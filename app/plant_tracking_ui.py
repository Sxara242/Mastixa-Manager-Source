from __future__ import annotations

from datetime import date
from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .language import tr
from .plant_tracking import PlantEvent, PlantRecord
from .plant_tracking_store import PlantTrackingStore
from .ui_helpers import table_widget


STATUS_OPTIONS = (
    ("Ενεργό", "active"),
    ("Νεκρό", "dead"),
    ("Αφαιρέθηκε", "removed"),
)
HEALTH_OPTIONS = (
    ("Άγνωστη", "unknown"),
    ("Καλή", "good"),
    ("Παρακολούθηση", "watch"),
    ("Κακή", "poor"),
)
EVENT_OPTIONS = (
    ("Σημείωση", "note"),
    ("Υγεία", "health"),
    ("Κατάσταση", "status"),
)
STATUS_LABELS = dict((value, label) for label, value in STATUS_OPTIONS)
HEALTH_LABELS = dict((value, label) for label, value in HEALTH_OPTIONS)
EVENT_LABELS = dict((value, label) for label, value in EVENT_OPTIONS)


def _display_date(value: str) -> str:
    parsed = QDate.fromString(value or "", "yyyy-MM-dd")
    return parsed.toString("dd/MM/yyyy") if parsed.isValid() else value


def _optional_float(text: str) -> float | None:
    value = text.strip().replace(",", ".")
    return None if not value else float(value)


def _set_standard_button_text(buttons: QDialogButtonBox) -> None:
    """Use Greek source labels so app language, not the OS locale, owns the UI."""
    for standard_button, label in (
        (QDialogButtonBox.StandardButton.Save, "Αποθήκευση"),
        (QDialogButtonBox.StandardButton.Cancel, "Ακύρωση"),
    ):
        button = buttons.button(standard_button)
        if button is not None:
            button.setText(label)


def _show_warning(parent: QWidget, title: str, message: str) -> None:
    """Show canonical app text without exposing backend exception details."""
    QMessageBox.warning(parent, tr(title), tr(message))


class PlantDialog(QDialog):
    def __init__(
        self,
        db: Database,
        plant: PlantRecord | None = None,
        *,
        history_exists: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.db = db
        self._plant_id = plant.id if plant is not None else str(uuid4())
        self.setWindowTitle("Μεμονωμένο φυτό / δέντρο")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.field = QComboBox()
        self.field.currentIndexChanged.connect(self._refresh_batches)
        form.addRow("Αγροτεμάχιο *", self.field)

        self.batch = QComboBox()
        form.addRow("Παρτίδα φύτευσης", self.batch)

        self.label = QLineEdit()
        self.label.setPlaceholderText("Π.χ. Α-001 ή Δέντρο 17")
        form.addRow("Ετικέτα / κωδικός", self.label)

        self.planted_date = QLineEdit()
        self.planted_date.setPlaceholderText("YYYY-MM-DD (προαιρετικό)")
        form.addRow("Ημερομηνία φύτευσης", self.planted_date)

        self.variety = QLineEdit()
        self.variety.setPlaceholderText("Ποικιλία / κλώνος")
        form.addRow("Ποικιλία", self.variety)

        self.latitude = QLineEdit()
        self.latitude.setPlaceholderText("π.χ. 38.3672")
        self.longitude = QLineEdit()
        self.longitude.setPlaceholderText("π.χ. 26.1358")
        form.addRow("Γεωγραφικό πλάτος (WGS84)", self.latitude)
        form.addRow("Γεωγραφικό μήκος (WGS84)", self.longitude)

        self.status = QComboBox()
        self.status.setProperty("mastixaI18nStaticItems", True)
        for label, value in STATUS_OPTIONS:
            self.status.addItem(label, value)
        form.addRow("Αρχική κατάσταση", self.status)

        self.health = QComboBox()
        self.health.setProperty("mastixaI18nStaticItems", True)
        for label, value in HEALTH_OPTIONS:
            self.health.addItem(label, value)
        form.addRow("Αρχική υγεία", self.health)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(82)
        self.notes.setPlaceholderText("Σημειώσεις για το συγκεκριμένο φυτό...")
        form.addRow("Σημειώσεις", self.notes)
        layout.addLayout(form)

        if history_exists:
            note = QLabel(
                "Υπάρχει ιστορικό συμβάντων. Η τρέχουσα κατάσταση/υγεία αλλάζει "
                "με νέο συμβάν και όχι από τα αρχικά πεδία."
            )
            note.setWordWrap(True)
            layout.addWidget(note)
            self.status.setEnabled(False)
            self.health.setEnabled(False)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        _set_standard_button_text(buttons)
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_fields(plant.field_id if plant else "")
        if plant is not None:
            self.label.setText(plant.label)
            self.planted_date.setText(plant.planted_date)
            self.variety.setText(plant.variety)
            self.latitude.setText("" if plant.latitude is None else str(plant.latitude))
            self.longitude.setText("" if plant.longitude is None else str(plant.longitude))
            status_index = self.status.findData(plant.status)
            health_index = self.health.findData(plant.health)
            if status_index >= 0:
                self.status.setCurrentIndex(status_index)
            if health_index >= 0:
                self.health.setCurrentIndex(health_index)
            self.notes.setPlainText(plant.notes)
            self._refresh_batches(plant.planting_batch_id)

    def _refresh_fields(self, selected: str = "") -> None:
        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Επίλεξε αγροτεμάχιο", "")
        for row in self.db.query("SELECT id,name FROM fields ORDER BY name,id"):
            self.field.addItem(str(row["name"]), str(row["id"]))
        index = self.field.findData(str(selected))
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)
        self._refresh_batches()

    def _refresh_batches(self, selected: str | None = None) -> None:
        if not hasattr(self, "batch"):
            return
        current = self.batch.currentData() if selected is None else selected
        field_id = str(self.field.currentData() or "")
        self.batch.blockSignals(True)
        self.batch.clear()
        self.batch.addItem("Χωρίς σύνδεση παρτίδας", "")
        exists = self.db.query_one(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='planting_batches'"
        )
        if field_id and exists is not None:
            rows = self.db.query(
                """
                SELECT id,planting_date,variety,trees_planted
                FROM planting_batches
                WHERE CAST(field_id AS TEXT)=?
                ORDER BY planting_date DESC,id DESC
                """,
                (field_id,),
            )
            for row in rows:
                label = f"{_display_date(str(row['planting_date'] or ''))} · {row['trees_planted']}"
                if row["variety"]:
                    label += f" · {row['variety']}"
                self.batch.addItem(label, str(row["id"]))
        index = self.batch.findData(str(current or ""))
        self.batch.setCurrentIndex(index if index >= 0 else 0)
        self.batch.blockSignals(False)

    def _accept_if_valid(self) -> None:
        if not self.field.currentData():
            _show_warning(self, "Μεμονωμένα Φυτά / Δέντρα", "Επίλεξε αγροτεμάχιο.")
            return
        try:
            self.record().validate()
        except (TypeError, ValueError):
            _show_warning(self, "Μη έγκυρα στοιχεία", "Έλεγξε τα στοιχεία του φυτού.")
            return
        self.accept()

    def record(self) -> PlantRecord:
        return PlantRecord(
            id=self._plant_id,
            field_id=str(self.field.currentData() or ""),
            planting_batch_id=str(self.batch.currentData() or ""),
            label=self.label.text().strip(),
            planted_date=self.planted_date.text().strip(),
            variety=self.variety.text().strip(),
            latitude=_optional_float(self.latitude.text()),
            longitude=_optional_float(self.longitude.text()),
            status=str(self.status.currentData()),
            health=str(self.health.currentData()),
            notes=self.notes.toPlainText().strip(),
        )


class PlantEventDialog(QDialog):
    def __init__(self, plant_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.plant_id = plant_id
        self.setWindowTitle("Νέο συμβάν φυτού")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.event_date = QDateEdit()
        self.event_date.setCalendarPopup(True)
        self.event_date.setDisplayFormat("dd/MM/yyyy")
        self.event_date.setDate(QDate.currentDate())
        form.addRow("Ημερομηνία", self.event_date)

        self.kind = QComboBox()
        self.kind.setProperty("mastixaI18nStaticItems", True)
        for label, value in EVENT_OPTIONS:
            self.kind.addItem(label, value)
        self.kind.currentIndexChanged.connect(self._kind_changed)
        form.addRow("Τύπος", self.kind)

        self.value_text = QLineEdit()
        self.value_text.setPlaceholderText("Σύντομη σημείωση")
        form.addRow("Τιμή", self.value_text)

        self.value_choice = QComboBox()
        self.value_choice.setProperty("mastixaI18nStaticItems", True)
        form.addRow("Νέα τιμή", self.value_choice)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(80)
        self.notes.setPlaceholderText("Πρόσθετες σημειώσεις...")
        form.addRow("Σημειώσεις", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        _set_standard_button_text(buttons)
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._kind_changed()

    def _kind_changed(self) -> None:
        kind = str(self.kind.currentData())
        is_note = kind == "note"
        self.value_text.setVisible(is_note)
        self.value_choice.setVisible(not is_note)
        self.value_choice.clear()
        if kind == "health":
            for label, value in HEALTH_OPTIONS:
                self.value_choice.addItem(label, value)
        elif kind == "status":
            for label, value in STATUS_OPTIONS:
                self.value_choice.addItem(label, value)

    def _accept_if_valid(self) -> None:
        try:
            self.plant_event().validate()
        except ValueError:
            _show_warning(self, "Μη έγκυρα στοιχεία", "Έλεγξε τα στοιχεία του συμβάντος.")
            return
        self.accept()

    def plant_event(self) -> PlantEvent:
        kind = str(self.kind.currentData())
        value = self.value_text.text().strip() if kind == "note" else str(self.value_choice.currentData() or "")
        return PlantEvent(
            id=str(uuid4()),
            plant_id=self.plant_id,
            event_date=self.event_date.date().toString("yyyy-MM-dd"),
            kind=kind,
            value=value,
            notes=self.notes.toPlainText().strip(),
        )


class PlantTrackingPage(QWidget):
    """Optional Phase 14 per-tree UI. Aggregate planting counts stay independent."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.store = PlantTrackingStore(db)
        self.selected_id: str | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("plantTrackingContent")
        content.setStyleSheet("QWidget#plantTrackingContent { background: #f5f6f3; }")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Μεμονωμένα Φυτά / Δέντρα")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Προαιρετική καρτέλα ανά φυτό με ετικέτα, θέση και ιστορικό. "
            "Δεν αλλάζει αυτόματα τα συνολικά φυτεμένα/ζωντανά της παρτίδας."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        self.new_button = QPushButton("+ Νέο φυτό")
        self.new_button.clicked.connect(self.new_plant)
        self.edit_button = QPushButton("Επεξεργασία")
        self.edit_button.clicked.connect(self.edit_plant)
        self.event_button = QPushButton("+ Συμβάν")
        self.event_button.clicked.connect(self.add_event)
        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_selected)
        self.restore_button = QPushButton("Επαναφορά")
        self.restore_button.clicked.connect(self.restore_selected)
        for button in (self.new_button, self.edit_button, self.event_button, self.delete_button, self.restore_button):
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)
        self.field_filter = QComboBox()
        self.field_filter.currentIndexChanged.connect(self.refresh)
        self.status_filter = QComboBox()
        self.status_filter.setProperty("mastixaI18nStaticItems", True)
        self.status_filter.addItem("Όλες οι καταστάσεις", "")
        for label, value in STATUS_OPTIONS:
            self.status_filter.addItem(label, value)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText("Αναζήτηση ετικέτας, ποικιλίας ή σημειώσεων...")
        self.search.textChanged.connect(self.refresh)
        self.include_deleted = QCheckBox("Εμφάνιση διαγραμμένων")
        self.include_deleted.toggled.connect(self.refresh)
        filters.addWidget(QLabel("Αγροτεμάχιο"))
        filters.addWidget(self.field_filter)
        filters.addWidget(QLabel("Κατάσταση"))
        filters.addWidget(self.status_filter)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.include_deleted)
        layout.addWidget(filters_box)

        self.summary = QLabel()
        layout.addWidget(self.summary)

        self.table = table_widget([
            "Ετικέτα", "Αγροτεμάχιο", "Ποικιλία", "Φύτευση", "Κατάσταση",
            "Υγεία", "Συμβάντα", "Τελευταίο συμβάν", "GPS"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.setMinimumHeight(320)
        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        history_box = QGroupBox("Ιστορικό επιλεγμένου φυτού")
        history_layout = QVBoxLayout(history_box)
        self.history = table_widget(["Ημερομηνία", "Τύπος", "Τιμή", "Σημειώσεις"])
        self.history.setMinimumHeight(180)
        self.history.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history)
        layout.addWidget(history_box)
        layout.addStretch()

        self._refresh_fields()
        self.refresh()

    def _refresh_fields(self) -> None:
        current = self.field_filter.currentData()
        self.field_filter.blockSignals(True)
        self.field_filter.clear()
        self.field_filter.addItem("Όλα τα αγροτεμάχια", "")
        for row in self.db.query("SELECT id,name FROM fields ORDER BY name,id"):
            self.field_filter.addItem(str(row["name"]), str(row["id"]))
        index = self.field_filter.findData(str(current or ""))
        self.field_filter.setCurrentIndex(index if index >= 0 else 0)
        self.field_filter.blockSignals(False)

    def _field_names(self) -> dict[str, str]:
        return {str(row["id"]): str(row["name"]) for row in self.db.query("SELECT id,name FROM fields")}

    def _deleted_ids(self) -> set[str]:
        return {
            str(row["id"])
            for row in self.db.query("SELECT id FROM individual_plants WHERE deleted_at IS NOT NULL")
        }

    def refresh(self) -> None:
        selected = self.selected_id
        self._refresh_fields()
        field_id = str(self.field_filter.currentData() or "")
        plants = self.store.plants(field_id=field_id or None, include_deleted=self.include_deleted.isChecked())
        deleted = self._deleted_ids()
        names = self._field_names()
        status_filter = str(self.status_filter.currentData() or "")
        query = self.search.text().strip().casefold()

        rows: list[tuple[PlantRecord, dict[str, object], bool]] = []
        for plant in plants:
            snapshot = self.store.snapshot(plant.id) if plant.id not in deleted else {
                **plant.__dict__, "event_count": len(self.store.events(plant.id)),
                "last_event_date": self.store.events(plant.id)[-1].event_date if self.store.events(plant.id) else "",
            }
            if status_filter and snapshot["status"] != status_filter:
                continue
            haystack = f"{plant.label} {plant.variety} {plant.notes} {names.get(plant.field_id, '')}".casefold()
            if query and query not in haystack:
                continue
            rows.append((plant, snapshot, plant.id in deleted))

        self.table.setRowCount(len(rows))
        for row_index, (plant, snapshot, is_deleted) in enumerate(rows):
            gps = ""
            if plant.latitude is not None and plant.longitude is not None:
                gps = f"{plant.latitude:.6f}, {plant.longitude:.6f}"
            values = [
                plant.label or plant.id,
                names.get(plant.field_id, plant.field_id),
                plant.variety,
                _display_date(plant.planted_date),
                STATUS_LABELS.get(str(snapshot["status"]), str(snapshot["status"])),
                HEALTH_LABELS.get(str(snapshot["health"]), str(snapshot["health"])),
                str(snapshot["event_count"]),
                _display_date(str(snapshot["last_event_date"])),
                gps,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, plant.id)
                    item.setData(Qt.ItemDataRole.UserRole + 1, is_deleted)
                self.table.setItem(row_index, column, item)

        self.summary.setText(f"{len(rows)} εγγραφές")
        self.selected_id = selected if any(p.id == selected for p, _, _ in rows) else None
        if self.selected_id is not None:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) == self.selected_id:
                    self.table.selectRow(row)
                    break
        self._refresh_history()
        self._update_buttons()

    def _selection_changed(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        self.selected_id = None if not rows else str(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole))
        self._refresh_history()
        self._update_buttons()

    def _selected_deleted(self) -> bool:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return False
        return bool(self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole + 1))

    def _update_buttons(self) -> None:
        chosen = self.selected_id is not None
        deleted = self._selected_deleted() if chosen else False
        self.edit_button.setEnabled(chosen and not deleted)
        self.event_button.setEnabled(chosen and not deleted)
        self.delete_button.setEnabled(chosen and not deleted)
        self.restore_button.setEnabled(chosen and deleted)

    def _refresh_history(self) -> None:
        events = self.store.events(self.selected_id) if self.selected_id else []
        self.history.setRowCount(len(events))
        for row, event in enumerate(events):
            values = [
                _display_date(event.event_date),
                EVENT_LABELS.get(event.kind, event.kind),
                HEALTH_LABELS.get(event.value, STATUS_LABELS.get(event.value, event.value)),
                event.notes,
            ]
            for column, value in enumerate(values):
                self.history.setItem(row, column, QTableWidgetItem(value))

    def new_plant(self) -> None:
        dialog = PlantDialog(self.db, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.store.save_plant(dialog.record())
        except (TypeError, ValueError):
            _show_warning(self, "Αποτυχία αποθήκευσης", "Δεν ήταν δυνατή η αποθήκευση του φυτού.")
            return
        self.selected_id = dialog.record().id
        self.refresh()

    def edit_plant(self) -> None:
        if self.selected_id is None or self._selected_deleted():
            return
        plant = self.store.plant(self.selected_id)
        dialog = PlantDialog(
            self.db,
            plant,
            history_exists=bool(self.store.events(plant.id)),
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            edited = dialog.record()
            if self.store.events(plant.id):
                edited = PlantRecord(
                    id=edited.id, field_id=edited.field_id,
                    planting_batch_id=edited.planting_batch_id, label=edited.label,
                    planted_date=edited.planted_date, variety=edited.variety,
                    latitude=edited.latitude, longitude=edited.longitude,
                    status=plant.status, health=plant.health, notes=edited.notes,
                )
            self.store.save_plant(edited)
        except (TypeError, ValueError):
            _show_warning(self, "Αποτυχία αποθήκευσης", "Δεν ήταν δυνατή η αποθήκευση του φυτού.")
            return
        self.refresh()

    def add_event(self) -> None:
        if self.selected_id is None or self._selected_deleted():
            return
        dialog = PlantEventDialog(self.selected_id, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.store.append_event(dialog.plant_event())
        except ValueError:
            _show_warning(self, "Αποτυχία αποθήκευσης", "Δεν ήταν δυνατή η αποθήκευση του συμβάντος.")
            return
        self.refresh()

    def delete_selected(self) -> None:
        if self.selected_id is None or self._selected_deleted():
            return
        answer = QMessageBox.question(
            self,
            "Διαγραφή φυτού",
            "Η εγγραφή θα κρυφτεί, αλλά το ιστορικό της διατηρείται και μπορεί να επανέλθει. Συνέχεια;",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.store.delete_plant(self.selected_id)
        self.selected_id = None
        self.refresh()

    def restore_selected(self) -> None:
        if self.selected_id is None or not self._selected_deleted():
            return
        try:
            self.store.restore_plant(self.selected_id)
        except ValueError:
            _show_warning(self, "Αποτυχία επαναφοράς", "Δεν ήταν δυνατή η επαναφορά του φυτού.")
            return
        self.refresh()
