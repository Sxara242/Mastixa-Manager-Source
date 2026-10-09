from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from .numeric_inputs import NumericDoubleSpinBox
from .crud import CrudPage
from .widgets import date_input
from .localized_messages import _language, _text
from .database import Database
from .language import combo_source_text
from .ui_helpers import table_widget
from .year_lock import warn_locked_year
from .year_context_ui import working_year_mutation
from .year_context import is_year_write_blocked as is_year_locked, working_context_date
from .expense_sync import delete_expense, ensure_expense_source_schema, sync_expense


CATEGORIES = ["Τρακτέρ", "Ελκυστήρας", "Ψεκαστικό", "Καταστροφέας", "Αντλία", "Όχημα", "Εργαλείο", "Άλλο"]
STATUSES = ["Ενεργό", "Σε συντήρηση", "Εκτός λειτουργίας", "Πωλήθηκε"]
METER_TYPES = [("Ώρες", "hours"), ("Χιλιόμετρα", "km"), ("Χωρίς μετρητή", "none")]
SERVICE_TYPES = ["Τακτικό service", "Επισκευή", "Αλλαγή λαδιών", "Φίλτρα", "Ελαστικά", "Έλεγχος", "Άλλο"]


class CompactMoneySpinBox(NumericDoubleSpinBox):
    """Money input: keeps cents precision, hides unnecessary trailing zeroes."""

    def textFromValue(self, value: float) -> str:
        text = f"{value:.2f}".rstrip("0").rstrip(".")
        return (text + ('' if self.hasFocus() else getattr(self, '_unit_suffix', ''))) if value else ''


class EquipmentPage(CrudPage):
    """Μητρώο μηχανημάτων, ιστορικό και προγραμματισμός συντήρησης."""


    @staticmethod
    def _body_render(spec):
        template, values, labels = spec
        return _text(template, **dict(values, **{k: _text(v) for k, v in labels.items()}))

    def _set_body(self, item, template, *, _labels=None, **values):
        spec = (template, values, _labels or {})
        item.setData(2367, spec)
        item.setText(self._body_render(spec))

    def _body_label(self, label, template, **values):
        label.setProperty("mastixaI18nSkipText", True)
        label.setTextFormat(label.textFormat().PlainText)
        spec = (template, values, {})
        label.setProperty("mastixaBodyTemplate", spec)
        label.setText(self._body_render(spec))

    def _refresh_body_language(self, *_args):
        # Only explicitly owned cells are projected; canonical rows remain opaque.
        for name in ('equipment_table', 'service_table'):
            table = getattr(self, name, None)
            if table is None:
                continue
            blocked = table.blockSignals(True)
            try:
                for row in range(table.rowCount()):
                    for column in range(table.columnCount()):
                        item = table.item(row, column)
                        spec = item.data(2367) if item is not None else None
                        if spec is not None:
                            text = self._body_render(spec)
                            if item.toolTip():
                                item.setToolTip(text)
                            item.setText(text)
            finally:
                table.blockSignals(blocked)
        for name in ():
            label = getattr(self, name, None)
            spec = label.property("mastixaBodyTemplate") if label is not None else None
            if spec is not None:
                label.setText(self._body_render(spec))

    def __init__(self, db: Database) -> None:
        super().__init__()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self._refresh_body_language)
        self.db = db
        self.selected_equipment_id: int | None = None
        self.selected_service_id: int | None = None
        self._ensure_schema()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)

        title = QLabel("Μηχανήματα & Συντήρηση")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("Μητρώο εξοπλισμού, ιστορικό service και υπενθυμίσεις συντήρησης")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        metrics = QHBoxLayout()
        self.total_metric = self._metric("Μηχανήματα")
        self.upcoming_metric = self._metric("Επερχόμενα service")
        self.overdue_metric = self._metric("Εκπρόθεσμα")
        for card, _ in (self.total_metric, self.upcoming_metric, self.overdue_metric):
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        self.equipment_box = QGroupBox("Νέο μηχάνημα")
        form = QFormLayout(self.equipment_box)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Π.χ. Τρακτέρ κτήματος")
        self.category = QComboBox(); self.category.setEditable(True); self.category.setProperty("mastixaI18nStaticItems", True); self.category.addItems(CATEGORIES)
        self.brand_model = QLineEdit()
        self.code = QLineEdit()
        self.has_purchase_date = QCheckBox("Καταχώριση ημερομηνίας αγοράς")
        self.purchase_date = date_input(self.db, selection="selected_equipment_id"); self.purchase_date.setCalendarPopup(True); self.purchase_date.setDisplayFormat("dd/MM/yyyy")
        self.has_purchase_date.toggled.connect(self.purchase_date.setEnabled)
        self.purchase_date.setEnabled(False)
        purchase_row = QHBoxLayout(); purchase_row.addWidget(self.has_purchase_date); purchase_row.addWidget(self.purchase_date)
        self.meter_type = QComboBox()
        for label, value in METER_TYPES: self.meter_type.addItem(label, value)
        self.current_meter = self._number()
        self.fuel = QLineEdit(); self.fuel.setPlaceholderText("Π.χ. Πετρέλαιο")
        self.status = QComboBox(); self.status.addItems(STATUSES)
        self.equipment_notes = QLineEdit()
        form.addRow("Όνομα", self.name); form.addRow("Κατηγορία", self.category)
        form.addRow("Μάρκα / μοντέλο", self.brand_model); form.addRow("Αριθμός / κωδικός", self.code)
        form.addRow("Ημερομηνία αγοράς", purchase_row); form.addRow("Τύπος μετρητή", self.meter_type)
        form.addRow("Τρέχων μετρητής", self.current_meter); form.addRow("Καύσιμο", self.fuel)
        form.addRow("Κατάσταση", self.status); form.addRow("Σημειώσεις", self.equipment_notes)
        eq_buttons = QHBoxLayout()
        self.equipment_save = QPushButton("Προσθήκη μηχανήματος"); self.equipment_save.clicked.connect(self.save_equipment)
        self.equipment_cancel = QPushButton("Ακύρωση"); self.equipment_cancel.clicked.connect(self.clear_equipment); self.equipment_cancel.setEnabled(False)
        self.equipment_delete = QPushButton("Διαγραφή"); self.equipment_delete.clicked.connect(self.delete_equipment); self.equipment_delete.setEnabled(False)
        for button in (self.equipment_save, self.equipment_cancel, self.equipment_delete): eq_buttons.addWidget(button)
        eq_buttons.addStretch(); form.addRow("", eq_buttons); layout.addWidget(self.equipment_box)

        equipment_list = QGroupBox("Μητρώο μηχανημάτων")
        equipment_layout = QVBoxLayout(equipment_list)
        self.equipment_search = QLineEdit(); self.equipment_search.setPlaceholderText("Αναζήτηση μηχανήματος..."); self.equipment_search.setClearButtonEnabled(True); self.equipment_search.textChanged.connect(self.refresh)
        equipment_layout.addWidget(self.equipment_search)
        self.equipment_table = table_widget(["Όνομα", "Κατηγορία", "Μάρκα / μοντέλο", "Κωδικός", "Μετρητής", "Κατάσταση", "Επόμενο service"])
        self.equipment_table.cellClicked.connect(self.load_equipment); self.equipment_table.setMinimumHeight(220)
        equipment_layout.addWidget(self.equipment_table); layout.addWidget(equipment_list)

        self.service_box = QGroupBox("Νέα συντήρηση / υπενθύμιση")
        service_form = QFormLayout(self.service_box)
        service_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.service_equipment = QComboBox()
        self.service_date = date_input(self.db, selection="selected_service_id"); self.service_date.setCalendarPopup(True); self.service_date.setDisplayFormat("dd/MM/yyyy")
        self.service_type = QComboBox(); self.service_type.setEditable(True); self.service_type.setProperty("mastixaI18nStaticItems", True); self.service_type.addItems(SERVICE_TYPES)
        self.service_cost = CompactMoneySpinBox()
        self.service_cost.setRange(0, 999999999)
        self.service_cost.setDecimals(2)
        self.service_cost.setMinimumHeight(36)
        self.service_cost.setSuffix(" €")
        self.service_cost.setKeyboardTracking(False)
        self.service_meter = self._number()
        self.technician = QLineEdit()
        self.next_date_enabled = QCheckBox("Υπενθύμιση σε ημερομηνία")
        self.next_date = QDateEdit(working_context_date(self.db).addMonths(6)); self.next_date.setCalendarPopup(True); self.next_date.setDisplayFormat("dd/MM/yyyy"); self.next_date.setEnabled(False)
        self.service_date.dateChanged.connect(self._default_next_service_date)
        self.next_date_enabled.toggled.connect(self.next_date.setEnabled)
        next_date_row = QHBoxLayout(); next_date_row.addWidget(self.next_date_enabled); next_date_row.addWidget(self.next_date)
        self.next_meter_enabled = QCheckBox("Υπενθύμιση σε μετρητή")
        self.next_meter = self._number(); self.next_meter.setEnabled(False); self.next_meter_enabled.toggled.connect(self.next_meter.setEnabled)
        next_meter_row = QHBoxLayout(); next_meter_row.addWidget(self.next_meter_enabled); next_meter_row.addWidget(self.next_meter)
        self.service_notes = QLineEdit()
        service_form.addRow("Μηχάνημα", self.service_equipment); service_form.addRow("Ημερομηνία", self.service_date)
        service_form.addRow("Είδος service", self.service_type); service_form.addRow("Κόστος", self.service_cost)
        service_form.addRow("Μετρητής", self.service_meter); service_form.addRow("Τεχνικός / προμηθευτής", self.technician)
        service_form.addRow("Επόμενο service", next_date_row); service_form.addRow("Επόμενος μετρητής", next_meter_row)
        service_form.addRow("Σημειώσεις", self.service_notes)
        service_buttons = QHBoxLayout()
        self.service_save = QPushButton("Προσθήκη συντήρησης"); self.service_save.clicked.connect(self.save_service)
        self.service_cancel = QPushButton("Ακύρωση"); self.service_cancel.clicked.connect(self.clear_service); self.service_cancel.setEnabled(False)
        self.service_delete = QPushButton("Διαγραφή"); self.service_delete.clicked.connect(self.delete_service); self.service_delete.setEnabled(False)
        for button in (self.service_save, self.service_cancel, self.service_delete): service_buttons.addWidget(button)
        service_buttons.addStretch(); service_form.addRow("", service_buttons); layout.addWidget(self.service_box)

        history = QGroupBox("Ιστορικό & προγραμματισμένες συντηρήσεις")
        history_layout = QVBoxLayout(history)
        filters = QGridLayout()
        self.year_filter = QComboBox(); self.year_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Έτος"), 1, 0); filters.addWidget(self.year_filter, 1, 1)
        self.service_filter = QComboBox(); self.service_filter.currentIndexChanged.connect(self.refresh)
        self.reminder_filter = QComboBox(); self.reminder_filter.addItem("Όλες", None); self.reminder_filter.addItem("Επερχόμενες", "upcoming"); self.reminder_filter.addItem("Εκπρόθεσμες", "overdue"); self.reminder_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Μηχάνημα"), 0, 0); filters.addWidget(self.service_filter, 0, 1)
        filters.addWidget(QLabel("Υπενθυμίσεις"), 0, 2); filters.addWidget(self.reminder_filter, 0, 3)
        history_layout.addLayout(filters)
        self.service_table = table_widget(["Ημερομηνία", "Μηχάνημα", "Service", "Κόστος", "Μετρητής", "Τεχνικός", "Επόμενο", "Κατάσταση"])
        self.service_table.cellClicked.connect(self.load_service); self.service_table.setMinimumHeight(250)
        history_layout.addWidget(self.service_table); layout.addWidget(history); layout.addStretch()
        self.refresh()

    @staticmethod
    def _number(decimals: int = 1) -> QDoubleSpinBox:
        widget = NumericDoubleSpinBox(); widget.setRange(0, 999999999); widget.setDecimals(decimals); widget.setMinimumHeight(36); return widget

    @staticmethod
    def _metric(caption: str):
        box = QGroupBox(); box.setObjectName("metricCard"); row = QVBoxLayout(box)
        label = QLabel(caption); label.setObjectName("metricCaption"); value = QLabel("0"); value.setObjectName("metricValue")
        row.addWidget(label); row.addWidget(value); return box, value

    def _ensure_schema(self) -> None:
        self.db.execute("""CREATE TABLE IF NOT EXISTS equipment(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,category TEXT NOT NULL DEFAULT '',brand_model TEXT NOT NULL DEFAULT '',equipment_code TEXT NOT NULL DEFAULT '',purchase_date TEXT,fuel TEXT NOT NULL DEFAULT '',meter_type TEXT NOT NULL DEFAULT 'hours',current_meter REAL NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'Ενεργό',notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS equipment_maintenance(id INTEGER PRIMARY KEY AUTOINCREMENT,equipment_id INTEGER NOT NULL,service_date TEXT NOT NULL,service_type TEXT NOT NULL,cost REAL NOT NULL DEFAULT 0,meter_value REAL NOT NULL DEFAULT 0,technician TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',next_service_date TEXT,next_service_meter REAL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(equipment_id) REFERENCES equipment(id) ON DELETE RESTRICT)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_date ON equipment_maintenance(service_date)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_equipment ON equipment_maintenance(equipment_id)")
        maintenance_columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(equipment_maintenance)"
            )
        }
        if "expense_id" not in maintenance_columns:
            self.db.execute(
                "ALTER TABLE equipment_maintenance ADD COLUMN expense_id INTEGER"
            )
        ensure_expense_source_schema(self.db)
        if self.db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_events'") is None: return
        for sql in (
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_insert AFTER INSERT ON equipment BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment','INSERT',CAST(NEW.id AS TEXT),'Μηχάνημα: '||NEW.name); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_update AFTER UPDATE ON equipment BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment','UPDATE',CAST(NEW.id AS TEXT),'Μηχάνημα: '||NEW.name); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_delete AFTER DELETE ON equipment BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment','DELETE',CAST(OLD.id AS TEXT),'Μηχάνημα: '||OLD.name); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_maintenance_insert AFTER INSERT ON equipment_maintenance BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment_maintenance','INSERT',CAST(NEW.id AS TEXT),'Service: '||NEW.service_date||' | '||NEW.service_type); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_maintenance_update AFTER UPDATE ON equipment_maintenance BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment_maintenance','UPDATE',CAST(NEW.id AS TEXT),'Service: '||NEW.service_date||' | '||NEW.service_type); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_equipment_maintenance_delete AFTER DELETE ON equipment_maintenance BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'equipment_maintenance','DELETE',CAST(OLD.id AS TEXT),'Service: '||OLD.service_date); END""",
        ): self.db.execute(sql)

    @working_year_mutation(selection="selected_equipment_id", reset="clear_equipment")
    def save_equipment(self) -> None:
        name = self.name.text().strip()
        if not name: QMessageBox.warning(self,"Ελλιπή στοιχεία","Συμπλήρωσε το όνομα του μηχανήματος."); return
        meter_type = self.meter_type.currentData()
        if self.selected_equipment_id is not None:
            current = self.db.query_one(
                "SELECT meter_type FROM equipment WHERE id=?",
                (self.selected_equipment_id,),
            )
            if current is not None and (current["meter_type"] or "") != (meter_type or ""):
                history = self.db.query_one(
                    "SELECT 1 AS found FROM equipment_maintenance WHERE equipment_id=? LIMIT 1",
                    (self.selected_equipment_id,),
                )
                if history is not None:
                    QMessageBox.warning(
                        self,
                        "Αλλαγή μετρητή",
                        "Η μονάδα μετρητή δεν αλλάζει όταν υπάρχει ιστορικό service.",
                    )
                    return
        values=(name,combo_source_text(self.category).strip(),self.brand_model.text().strip(),self.code.text().strip(),self.purchase_date.date().toString("yyyy-MM-dd") if self.has_purchase_date.isChecked() else None,self.fuel.text().strip(),meter_type,self.current_meter.value(),combo_source_text(self.status),self.equipment_notes.text().strip())
        if self.selected_equipment_id is None: self.db.execute("INSERT INTO equipment(name,category,brand_model,equipment_code,purchase_date,fuel,meter_type,current_meter,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",values)
        else: self.db.execute("UPDATE equipment SET name=?,category=?,brand_model=?,equipment_code=?,purchase_date=?,fuel=?,meter_type=?,current_meter=?,status=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(*values,self.selected_equipment_id))
        self.clear_equipment(); self.refresh()

    def load_equipment(self,row:int,_column:int)->None:
        item=self.equipment_table.item(row,0); equipment_id=item.data(Qt.ItemDataRole.UserRole) if item else None
        record=self.db.query_one("SELECT * FROM equipment WHERE id=?",(equipment_id,)) if equipment_id else None
        if record is None:return
        self.selected_equipment_id=int(record["id"]); self.name.setText(record["name"] or ""); self.category.setEditText(record["category"] or ""); self.brand_model.setText(record["brand_model"] or ""); self.code.setText(record["equipment_code"] or "")
        parsed=QDate.fromString(record["purchase_date"] or "","yyyy-MM-dd"); self.has_purchase_date.setChecked(parsed.isValid()); self.purchase_date.setDate(parsed if parsed.isValid() else working_context_date(self.db))
        self.fuel.setText(record["fuel"] or ""); index=self.meter_type.findData(record["meter_type"]); self.meter_type.setCurrentIndex(index if index>=0 else 0); self.current_meter.setValue(float(record["current_meter"] or 0)); self.status.setCurrentText(record["status"] or "Ενεργό"); self.equipment_notes.setText(record["notes"] or "")
        self.equipment_box.setTitle("Επεξεργασία μηχανήματος"); self.equipment_save.setText("Αποθήκευση"); self.equipment_cancel.setEnabled(True); self.equipment_delete.setEnabled(True)

    def clear_equipment(self)->None:
        self.selected_equipment_id=None; self.name.clear(); self.category.setCurrentIndex(0); self.brand_model.clear(); self.code.clear(); self.has_purchase_date.setChecked(False); self.purchase_date.setDate(working_context_date(self.db)); self.meter_type.setCurrentIndex(0); self.current_meter.setValue(0); self.fuel.clear(); self.status.setCurrentIndex(0); self.equipment_notes.clear(); self.equipment_box.setTitle("Νέο μηχάνημα"); self.equipment_save.setText("Προσθήκη μηχανήματος"); self.equipment_cancel.setEnabled(False); self.equipment_delete.setEnabled(False); self.equipment_table.clearSelection()

    @working_year_mutation()
    def delete_equipment(self)->None:
        if self.selected_equipment_id is None:return
        count=self.db.query_one("SELECT COUNT(*) total FROM equipment_maintenance WHERE equipment_id=?",(self.selected_equipment_id,))
        if count and int(count["total"] or 0)>0: QMessageBox.warning(self,"Δεν επιτρέπεται διαγραφή","Το μηχάνημα έχει ιστορικό συντήρησης. Διέγραψε πρώτα τις σχετικές εγγραφές."); return
        if self.confirm_delete(self,"Διαγραφή μηχανήματος","Να διαγραφεί το επιλεγμένο μηχάνημα;"): self.db.execute("DELETE FROM equipment WHERE id=?",(self.selected_equipment_id,)); self.clear_equipment(); self.refresh()

    def _service_year(self,service_id:int)->int|None:
        row=self.db.query_one("SELECT service_date FROM equipment_maintenance WHERE id=?",(service_id,)); parsed=QDate.fromString(row["service_date"] if row else "","yyyy-MM-dd"); return parsed.year() if parsed.isValid() else None

    def _service_locked(self)->bool:
        target=self.service_date.date().year()
        if is_year_locked(self.db,target):warn_locked_year(self,self.db,target);return True
        original=self._service_year(self.selected_service_id) if self.selected_service_id else None
        if original and original!=target and is_year_locked(self.db,original):warn_locked_year(self,self.db,original);return True
        return False

    def save_service(self) -> None:
        if self._service_locked():
            if self.selected_service_id is None:
                self.clear_service()
            return

        equipment_id = self.service_equipment.currentData()
        service_type = combo_source_text(self.service_type).strip()

        if equipment_id is None or not service_type:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Επίλεξε μηχάνημα και είδος service.",
            )
            return

        service_date = self.service_date.date().toString("yyyy-MM-dd")
        cost = self.service_cost.value()
        technician = self.technician.text().strip()
        notes = self.service_notes.text().strip()

        values = (
            equipment_id,
            service_date,
            service_type,
            cost,
            self.service_meter.value(),
            technician,
            notes,
            (
                self.next_date.date().toString("yyyy-MM-dd")
                if self.next_date_enabled.isChecked()
                else None
            ),
            (
                self.next_meter.value()
                if self.next_meter_enabled.isChecked()
                else None
            ),
        )

        with self.db.transaction() as tx:
            if self.selected_service_id is None:
                service_id = int(
                    tx.execute(
                        """
                        INSERT INTO equipment_maintenance(
                            equipment_id,
                            service_date,
                            service_type,
                            cost,
                            meter_value,
                            technician,
                            notes,
                            next_service_date,
                            next_service_meter
                        )
                        VALUES(?,?,?,?,?,?,?,?,?)
                        """,
                        values,
                    )
                )
            else:
                service_id = self.selected_service_id
                tx.execute(
                    """
                    UPDATE equipment_maintenance
                    SET
                        equipment_id=?,
                        service_date=?,
                        service_type=?,
                        cost=?,
                        meter_value=?,
                        technician=?,
                        notes=?,
                        next_service_date=?,
                        next_service_meter=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (*values, service_id),
                )

            equipment_row = tx.query_one(
                "SELECT name FROM equipment WHERE id=?",
                (equipment_id,),
            )
            equipment_name = (
                equipment_row["name"]
                if equipment_row
                else f"Μηχάνημα #{equipment_id}"
            )

            expense_id = sync_expense(
                tx,
                source_type="equipment_maintenance",
                source_id=int(service_id),
                entry_date=service_date,
                category="Μηχανήματα & Συντήρηση",
                description=f"{service_type} — {equipment_name}",
                supplier=technician,
                payment_method="",
                amount=cost,
                notes=(
                    f"Αυτόματο έξοδο από συντήρηση μηχανήματος #{service_id}"
                    + (f" | {notes}" if notes else "")
                ),
            )

            tx.execute(
                """
                UPDATE equipment_maintenance
                SET expense_id=?
                WHERE id=?
                """,
                (expense_id, service_id),
            )

            tx.execute(
                """
                UPDATE equipment
                SET
                    current_meter=MAX(current_meter,?),
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (self.service_meter.value(), equipment_id),
            )

        self.clear_service()
        self.refresh()

    def load_service(self,row:int,_column:int)->None:
        item=self.service_table.item(row,0); service_id=item.data(Qt.ItemDataRole.UserRole) if item else None; record=self.db.query_one("SELECT * FROM equipment_maintenance WHERE id=?",(service_id,)) if service_id else None
        if record is None:return
        self.selected_service_id=int(record["id"]); self.service_equipment.setCurrentIndex(max(0,self.service_equipment.findData(record["equipment_id"]))); parsed=QDate.fromString(record["service_date"],"yyyy-MM-dd"); self.service_date.setDate(parsed); self.service_type.setEditText(record["service_type"] or ""); self.service_cost.setValue(float(record["cost"] or 0)); self.service_meter.setValue(float(record["meter_value"] or 0)); self.technician.setText(record["technician"] or ""); self.service_notes.setText(record["notes"] or "")
        next_date=QDate.fromString(record["next_service_date"] or "","yyyy-MM-dd"); self.next_date_enabled.setChecked(next_date.isValid()); self.next_date.setDate(next_date if next_date.isValid() else working_context_date(self.db).addMonths(6)); self.next_meter_enabled.setChecked(record["next_service_meter"] is not None); self.next_meter.setValue(float(record["next_service_meter"] or 0))
        year=parsed.year(); locked=is_year_locked(self.db,year); self.service_box.setTitle(f"Προβολή συντήρησης — ΚΛΕΙΔΩΜΕΝΟ {year}" if locked else "Επεξεργασία συντήρησης"); self.service_save.setText("Κλειδωμένο" if locked else "Αποθήκευση"); self.service_save.setEnabled(not locked); self.service_cancel.setEnabled(True); self.service_delete.setEnabled(not locked)

    def clear_service(self)->None:
        self.selected_service_id=None; self.service_date.setDate(working_context_date(self.db)); self.service_type.setCurrentIndex(0); self.service_cost.setValue(0); self.service_meter.setValue(0); self.technician.clear(); self.next_date_enabled.setChecked(False); self.next_date.setDate(working_context_date(self.db).addMonths(6)); self.next_meter_enabled.setChecked(False); self.next_meter.setValue(0); self.service_notes.clear(); self.service_box.setTitle("Νέα συντήρηση / υπενθύμιση"); self.service_save.setText("Προσθήκη συντήρησης"); self.service_save.setEnabled(True); self.service_cancel.setEnabled(False); self.service_delete.setEnabled(False); self.service_table.clearSelection()

    def delete_service(self) -> None:
        if self.selected_service_id is None:
            return

        year = self._service_year(self.selected_service_id)
        if year and is_year_locked(self.db, year):
            warn_locked_year(self, self.db, year)
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή συντήρησης",
            (
                "Να διαγραφεί η επιλεγμένη εγγραφή συντήρησης;\n\n"
                "Αν υπάρχει αυτόματα συνδεδεμένο έξοδο, θα διαγραφεί επίσης."
            ),
        ):
            return

        with self.db.transaction() as tx:
            delete_expense(
                tx,
                source_type="equipment_maintenance",
                source_id=self.selected_service_id,
            )

            tx.execute(
                "DELETE FROM equipment_maintenance WHERE id=?",
                (self.selected_service_id,),
            )

        self.clear_service()
        self.refresh()

    def _refresh_combos(self)->None:
        rows=self.db.query("SELECT id,name FROM equipment ORDER BY name,id")
        for combo,all_label in ((self.service_equipment,None),(self.service_filter,"Όλα")):
            current=combo.currentData(); combo.blockSignals(True); combo.clear()
            if all_label:combo.addItem(all_label,None)
            for row in rows:combo.addItem(row["name"],row["id"])
            index=combo.findData(current); combo.setCurrentIndex(index if index>=0 else 0); combo.blockSignals(False)

    def _default_next_service_date(self, date) -> None:
        if self.selected_service_id is None and not self.next_date_enabled.isChecked():
            self.next_date.setDate(date.addMonths(6))

    def _reminder_status(self,row)->tuple[str,str]:
        today=QDate.currentDate(); due_date=QDate.fromString(row["next_service_date"] or "","yyyy-MM-dd"); due_meter=row["next_service_meter"]; current=float(row["current_meter"] or 0)
        overdue=(due_date.isValid() and due_date<today) or (due_meter is not None and current>=float(due_meter))
        upcoming=(due_date.isValid() and today.daysTo(due_date)<=30) or (due_meter is not None and float(due_meter)-current<=50)
        details=[]
        if due_date.isValid():details.append(due_date.toString("dd/MM/yyyy"))
        if due_meter is not None:details.append(f"{float(due_meter):g} {row['meter_label']}")
        return ("Εκπρόθεσμη" if overdue else "Επερχόμενη" if upcoming else "Προγραμματισμένη" if details else "—"," / ".join(details) or "—")

    def refresh(self,*_args)->None:
        self._ensure_schema(); self._refresh_combos(); search=self.equipment_search.text().strip(); params=[]; where=""
        if search:where="WHERE e.name LIKE ? OR e.category LIKE ? OR e.brand_model LIKE ? OR e.equipment_code LIKE ?"; token=f"%{search}%";params=[token]*4
        equipment=self.db.query(f"""SELECT e.*,CASE e.meter_type WHEN 'km' THEN 'km' WHEN 'hours' THEN 'ώρες' ELSE '' END meter_label,(SELECT next_service_date FROM equipment_maintenance m WHERE m.equipment_id=e.id AND (m.next_service_date IS NOT NULL OR m.next_service_meter IS NOT NULL) ORDER BY m.service_date DESC,m.id DESC LIMIT 1) next_service_date,(SELECT next_service_meter FROM equipment_maintenance m WHERE m.equipment_id=e.id AND (m.next_service_date IS NOT NULL OR m.next_service_meter IS NOT NULL) ORDER BY m.service_date DESC,m.id DESC LIMIT 1) next_service_meter FROM equipment e {where} ORDER BY e.name,e.id""",params)
        self.equipment_table.setRowCount(len(equipment)); overdue_count=0; upcoming_count=0
        for i,row in enumerate(equipment):
            state,next_text=self._reminder_status(row); overdue_count+=state=="Εκπρόθεσμη"; upcoming_count+=state=="Επερχόμενη"
            values=[row["name"],row["category"],row["brand_model"],row["equipment_code"],f"{float(row['current_meter'] or 0):g} {row['meter_label']}",row["status"],next_text]
            for c,value in enumerate(values):
                item=QTableWidgetItem(str(value or ""))
                if c==0: item.setData(Qt.ItemDataRole.UserRole,int(row["id"]))
                if c == 4:
                    self._set_body(item, "{number} {unit}", number=f"{float(row['current_meter'] or 0):g}", _labels={"unit": row["meter_label"]})
                elif c == 5 and row["status"] in STATUSES:
                    self._set_body(item, row["status"])
                elif c == 6 and row["meter_label"] == "ώρες" and row["next_service_meter"] is not None:
                    self._set_body(item, "{date}{number} {unit}", date=(QDate.fromString(row["next_service_date"] or "", "yyyy-MM-dd").toString("dd/MM/yyyy") + " / ") if QDate.fromString(row["next_service_date"] or "", "yyyy-MM-dd").isValid() else "", number=f"{float(row['next_service_meter']):g}", _labels={"unit": "ώρες"})
                self.equipment_table.setItem(i,c,item)
        self.total_metric[1].setText(str(len(equipment))); self.upcoming_metric[1].setText(str(upcoming_count)); self.overdue_metric[1].setText(str(overdue_count))
        equipment_id=self.service_filter.currentData(); params=[]; condition=""
        if equipment_id is not None:condition="WHERE m.equipment_id=?";params=[equipment_id]
        populate_year_filter(self, self.year_filter, strings=True)
        year = self.year_filter.currentData()
        if year is not None:
            condition += (" AND " if condition else "WHERE ") + "substr(m.service_date,1,4)=?"
            params.append(year)
        services=self.db.query(f"""SELECT m.*,e.name equipment_name,e.current_meter,CASE e.meter_type WHEN 'km' THEN 'km' WHEN 'hours' THEN 'ώρες' ELSE '' END meter_label FROM equipment_maintenance m JOIN equipment e ON e.id=m.equipment_id {condition} ORDER BY m.service_date DESC,m.id DESC""",params)
        reminder=self.reminder_filter.currentData(); visible=[]
        for row in services:
            state,next_text=self._reminder_status(row)
            if reminder=="upcoming" and state!="Επερχόμενη":continue
            if reminder=="overdue" and state!="Εκπρόθεσμη":continue
            visible.append((row,state,next_text))
        self.service_table.setRowCount(len(visible))
        for i,(row,state,next_text) in enumerate(visible):
            values=[row["service_date"],row["equipment_name"],row["service_type"],f"{float(row['cost'] or 0):.2f} €",f"{float(row['meter_value'] or 0):g} {row['meter_label']}",row["technician"],next_text,state]
            for c,value in enumerate(values):
                item=QTableWidgetItem(str(value or ""))
                if c==0: item.setData(Qt.ItemDataRole.UserRole,int(row["id"]))
                if c == 4:
                    self._set_body(item, "{number} {unit}", number=f"{float(row['meter_value'] or 0):g}", _labels={"unit": row["meter_label"]})
                elif c == 7:
                    self._set_body(item, state)
                elif c == 6 and row["meter_label"] == "ώρες" and row["next_service_meter"] is not None:
                    self._set_body(item, "{date}{number} {unit}", date=(QDate.fromString(row["next_service_date"] or "", "yyyy-MM-dd").toString("dd/MM/yyyy") + " / ") if QDate.fromString(row["next_service_date"] or "", "yyyy-MM-dd").isValid() else "", number=f"{float(row['next_service_meter']):g}", _labels={"unit": "ώρες"})
                self.service_table.setItem(i,c,item)
