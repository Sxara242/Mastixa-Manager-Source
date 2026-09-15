from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget,
)

from .crud import CrudPage
from .database import Database
from .language import combo_source_text
from .ui_helpers import table_widget
from .widgets import area_input, date_input, money_input, quantity_input
from .year_lock import is_year_locked, warn_locked_year
from .inventory_sync import InventoryStockError, delete_consumption, ensure_can_consume, ensure_inventory_source_schema, sync_consumption


class PlantProtectionPage(CrudPage):
    """Field-level plant-protection log with traceability metadata."""

    def __init__(self, db: Database) -> None:
        super().__init__(); self.db = db; self.selected_id: int | None = None
        self._ensure_schema()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("plantProtectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            """
            QScrollArea#plantProtectionScroll {
                border: none;
                background: #f5f6f3;
            }
            QScrollArea#plantProtectionScroll QWidget#qt_scrollarea_viewport {
                background: #f5f6f3;
            }
            QWidget#plantProtectionContent {
                background: #f5f6f3;
            }
            """
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("plantProtectionContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 28, 14, 16)
        layout.setSpacing(10)
        scroll.setWidget(content)

        title = QLabel("Ημερολόγιο Φυτοπροστασίας")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(46)
        title.setContentsMargins(0, 2, 0, 2)
        layout.addWidget(title)

        subtitle = QLabel(
            "Καταγραφές ψεκασμών και επεμβάσεων ανά αγροτεμάχιο"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setMinimumHeight(30)
        subtitle.setContentsMargins(0, 1, 0, 4)
        layout.addWidget(subtitle)
        self.form_box = QGroupBox("Νέα επέμβαση"); form = QFormLayout(self.form_box)
        self.date = date_input(); self.field = QComboBox(); self.purpose = QLineEdit(); self.purpose.setPlaceholderText("Εχθρός, ασθένεια ή σκοπός επέμβασης")
        self.product = QComboBox(); self.product.setEditable(True); self.active_ingredient = QLineEdit(); self._authorization_number = ""
        self.dose = quantity_input(); self.dose.setSuffix(""); self.dose_unit = QComboBox(); self.dose_unit.setEditable(True); self.dose_unit.setProperty("mastixaI18nStaticItems", True); self.dose_unit.addItems(["kg/στρ.", "g/στρ.", "ml/στρ.", "L/στρ.", "%"])
        dose_row = QHBoxLayout(); dose_row.addWidget(self.dose, 1); dose_row.addWidget(self.dose_unit)
        self.inventory_quantity = quantity_input(); self.inventory_quantity.setSuffix(""); self.spray_volume = quantity_input(); self.spray_volume.setSuffix(" L"); self.area = area_input(); self.applicator = QLineEdit(); self.weather = QLineEdit()
        self.harvest_interval = QSpinBox(); self.harvest_interval.setRange(0, 365); self.harvest_interval.setSuffix(" ημέρες")
        self.cost = money_input(); self.notes = QTextEdit(); self.notes.setMaximumHeight(70)
        for label, widget in (("Ημερομηνία", self.date), ("Αγροτεμάχιο", self.field), ("Στόχος / αιτία", self.purpose), ("Σκεύασμα / προϊόν", self.product), ("Δραστική ουσία", self.active_ingredient)):
            form.addRow(label, widget)
        form.addRow("Δόση", dose_row); form.addRow("Κατανάλωση αποθήκης", self.inventory_quantity); form.addRow("Όγκος ψεκαστικού υγρού", self.spray_volume); form.addRow("Έκταση εφαρμογής", self.area); form.addRow("Εφαρμοστής", self.applicator); form.addRow("Καιρικές συνθήκες", self.weather); form.addRow("Αναμονή πριν συγκομιδή", self.harvest_interval); form.addRow("Κόστος", self.cost); form.addRow("Σημειώσεις", self.notes)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_record)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_record)
        self.delete_button.setEnabled(False)

        action_button_style = """
            QPushButton {
                background: #3F765B;
                color: #FFFFFF;
                border: 1px solid #35664F;
                border-radius: 7px;
                padding: 9px 18px;
                min-width: 90px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #315F49;
            }
            QPushButton:pressed {
                background: #274D3B;
            }
            QPushButton:disabled {
                background: #D5DDD8;
                color: #58665F;
                border: 1px solid #C4CEC8;
            }
        """

        for button in (
            self.save_button,
            self.cancel_button,
            self.delete_button,
        ):
            button.setStyleSheet(action_button_style)
            buttons.addWidget(button)

        buttons.addStretch()
        form.addRow("", buttons)
        layout.addWidget(self.form_box)
        filters = QHBoxLayout(); self.year_filter = QComboBox(); self.year_filter.currentIndexChanged.connect(self.refresh); self.search = QLineEdit(); self.search.setPlaceholderText("Αναζήτηση σε αγροτεμάχιο, προϊόν, στόχο ή εφαρμοστή..."); self.search.setClearButtonEnabled(True); self.search.textChanged.connect(self.refresh); filters.addWidget(QLabel("Έτος")); filters.addWidget(self.year_filter); filters.addWidget(self.search, 1); layout.addLayout(filters)
        self.table = table_widget(["Ημερομηνία", "Αγροτεμάχιο", "Στόχος", "Προϊόν", "Δόση", "Έκταση", "Αναμονή", "Εφαρμοστής", "Κόστος"]); self.table.cellClicked.connect(self.load_record); self.table.setMinimumHeight(260); layout.addWidget(self.table); self.refresh()

    def _ensure_schema(self) -> None:
        self.db.execute("""CREATE TABLE IF NOT EXISTS plant_protection_records(id INTEGER PRIMARY KEY AUTOINCREMENT,application_date TEXT NOT NULL,field_id INTEGER NOT NULL,inventory_item_id INTEGER,purpose TEXT NOT NULL,product_name TEXT NOT NULL,active_ingredient TEXT NOT NULL DEFAULT '',authorization_number TEXT NOT NULL DEFAULT '',dose REAL NOT NULL DEFAULT 0,dose_unit TEXT NOT NULL DEFAULT '',spray_volume_l REAL NOT NULL DEFAULT 0,area_stremma REAL NOT NULL DEFAULT 0,applicator TEXT NOT NULL DEFAULT '',weather TEXT NOT NULL DEFAULT '',harvest_interval_days INTEGER NOT NULL DEFAULT 0,cost REAL NOT NULL DEFAULT 0,notes TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE RESTRICT)""")
        columns = {row["name"] for row in self.db.query("PRAGMA table_info(plant_protection_records)")}
        if "inventory_quantity" not in columns:
            self.db.execute("ALTER TABLE plant_protection_records ADD COLUMN inventory_quantity REAL NOT NULL DEFAULT 0")
        ensure_inventory_source_schema(self.db)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_plant_protection_date ON plant_protection_records(application_date)"); self.db.execute("CREATE INDEX IF NOT EXISTS idx_plant_protection_field ON plant_protection_records(field_id)")
        if self.db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_events'") is None: return
        for sql in (
            """CREATE TRIGGER IF NOT EXISTS audit_plant_protection_insert AFTER INSERT ON plant_protection_records BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'plant_protection_records','INSERT',CAST(NEW.id AS TEXT),'Φυτοπροστασία: '||NEW.product_name||' | '||NEW.application_date); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_plant_protection_update AFTER UPDATE ON plant_protection_records BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'plant_protection_records','UPDATE',CAST(NEW.id AS TEXT),'Φυτοπροστασία: '||NEW.product_name||' | '||NEW.application_date); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_plant_protection_delete AFTER DELETE ON plant_protection_records BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details) VALUES(datetime('now','localtime'),'plant_protection_records','DELETE',CAST(OLD.id AS TEXT),'Φυτοπροστασία: '||OLD.product_name||' | '||OLD.application_date); END""",
        ):
            self.db.execute(sql)

    def _refresh_choices(self, field_id=None, item_id=None, product_text="") -> None:
        self.field.clear(); self.field.addItem("Επίλεξε αγροτεμάχιο", None)
        for row in self.db.query("SELECT id,name FROM fields ORDER BY name"): self.field.addItem(row["name"], row["id"])
        index = self.field.findData(field_id); self.field.setCurrentIndex(index if index >= 0 else 0)
        self.product.clear(); self.product.addItem("", None)
        if self.db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_items'"):
            for row in self.db.query("SELECT id,name FROM inventory_items ORDER BY name"): self.product.addItem(row["name"], row["id"])
        index = self.product.findData(item_id) if item_id is not None else -1
        if index >= 0: self.product.setCurrentIndex(index)
        else: self.product.setEditText(product_text)

    def _record_year(self, record_id: int) -> int | None:
        row = self.db.query_one("SELECT application_date FROM plant_protection_records WHERE id=?", (record_id,)); date = QDate.fromString(row["application_date"] if row else "", "yyyy-MM-dd"); return date.year() if date.isValid() else None

    def save_record(self) -> None:
        year = self.date.date().year()
        if is_year_locked(self.db, year):
            warn_locked_year(self, self.db, year)
            return
        original_year = self._record_year(self.selected_id) if self.selected_id else None
        if original_year and original_year != year and is_year_locked(self.db, original_year):
            warn_locked_year(self, self.db, original_year)
            return
        if self.field.currentData() is None:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Επίλεξε αγροτεμάχιο.")
            return
        product = combo_source_text(self.product).strip()
        purpose = self.purpose.text().strip()
        if not product or not purpose:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Συμπλήρωσε στόχο και σκεύασμα/προϊόν.")
            return
        inventory_item_id = self.product.currentData()
        inventory_quantity = self.inventory_quantity.value()
        if inventory_quantity > 0 and inventory_item_id is None:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Για αυτόματη κατανάλωση επίλεξε προϊόν από την Αποθήκη.")
            return
        try:
            ensure_can_consume(self.db, item_id=inventory_item_id, quantity=inventory_quantity, source_type="plant_protection", source_id=self.selected_id)
        except InventoryStockError as exc:
            QMessageBox.warning(self, "Ανεπαρκές απόθεμα", f"Δεν υπάρχει αρκετό απόθεμα. Διαθέσιμο: {exc.available:g}")
            return
        values=(self.date.date().toString("yyyy-MM-dd"), self.field.currentData(), inventory_item_id, purpose, product, self.active_ingredient.text().strip(), self._authorization_number, self.dose.value(), combo_source_text(self.dose_unit).strip(), self.spray_volume.value(), self.area.value(), self.applicator.text().strip(), self.weather.text().strip(), self.harvest_interval.value(), self.cost.value(), self.notes.toPlainText().strip(), inventory_quantity)
        if self.selected_id is None:
            record_id=self.db.execute("""INSERT INTO plant_protection_records(application_date,field_id,inventory_item_id,purpose,product_name,active_ingredient,authorization_number,dose,dose_unit,spray_volume_l,area_stremma,applicator,weather,harvest_interval_days,cost,notes,inventory_quantity) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
        else:
            self.db.execute("""UPDATE plant_protection_records SET application_date=?,field_id=?,inventory_item_id=?,purpose=?,product_name=?,active_ingredient=?,authorization_number=?,dose=?,dose_unit=?,spray_volume_l=?,area_stremma=?,applicator=?,weather=?,harvest_interval_days=?,cost=?,notes=?,inventory_quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""", (*values,self.selected_id))
            record_id=self.selected_id
        sync_consumption(self.db, source_type="plant_protection", source_id=int(record_id), movement_date=self.date.date().toString("yyyy-MM-dd"), item_id=inventory_item_id, quantity=inventory_quantity, field_id=self.field.currentData(), notes=f"Αυτόματη κατανάλωση από Φυτοπροστασία #{record_id}")
        self.clear_form(); self.refresh()

    def load_record(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0); record_id = item.data(Qt.ItemDataRole.UserRole) if item else None; record = self.db.query_one("SELECT * FROM plant_protection_records WHERE id=?", (record_id,)) if record_id else None
        if record is None: return
        self.selected_id = int(record["id"]); date = QDate.fromString(record["application_date"], "yyyy-MM-dd"); self.date.setDate(date); self._refresh_choices(record["field_id"], record["inventory_item_id"], record["product_name"]); self.purpose.setText(record["purpose"]); self.active_ingredient.setText(record["active_ingredient"]); self._authorization_number = record["authorization_number"] or ""; self.dose.setValue(record["dose"]); self.dose_unit.setCurrentText(record["dose_unit"]); self.inventory_quantity.setValue(record["inventory_quantity"]); self.spray_volume.setValue(record["spray_volume_l"]); self.area.setValue(record["area_stremma"]); self.applicator.setText(record["applicator"]); self.weather.setText(record["weather"]); self.harvest_interval.setValue(record["harvest_interval_days"]); self.cost.setValue(record["cost"]); self.notes.setPlainText(record["notes"])
        locked = is_year_locked(self.db, date.year()); self.form_box.setTitle(f"Προβολή επέμβασης — ΚΛΕΙΔΩΜΕΝΟ {date.year()}" if locked else "Επεξεργασία επέμβασης"); self.save_button.setText("Κλειδωμένο" if locked else "Αποθήκευση"); self.save_button.setEnabled(not locked); self.delete_button.setEnabled(not locked); self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_id = None; self.date.setDate(QDate.currentDate()); self._refresh_choices(); self.purpose.clear(); self.active_ingredient.clear(); self._authorization_number = ""; self.dose.setValue(0); self.dose_unit.setCurrentIndex(0); self.inventory_quantity.setValue(0); self.spray_volume.setValue(0); self.area.setValue(0); self.applicator.clear(); self.weather.clear(); self.harvest_interval.setValue(0); self.cost.setValue(0); self.notes.clear(); self.form_box.setTitle("Νέα επέμβαση"); self.save_button.setText("Προσθήκη"); self.save_button.setEnabled(True); self.cancel_button.setEnabled(False); self.delete_button.setEnabled(False); self.table.clearSelection()

    def delete_record(self) -> None:
        if self.selected_id is None: return
        year = self._record_year(self.selected_id)
        if year and is_year_locked(self.db, year): warn_locked_year(self, self.db, year); return
        if not self.confirm_delete(self, "Διαγραφή επέμβασης", "Να διαγραφεί η επιλεγμένη καταγραφή φυτοπροστασίας;"): return
        delete_consumption(self.db, source_type="plant_protection", source_id=self.selected_id); self.db.execute("DELETE FROM plant_protection_records WHERE id=?", (self.selected_id,)); self.clear_form(); self.refresh()

    def refresh(self) -> None:
        selected_year = self.year_filter.currentData() if self.year_filter.count() else "all"; self.year_filter.blockSignals(True); self.year_filter.clear(); self.year_filter.addItem("Όλα", "all")
        for row in self.db.query("SELECT DISTINCT substr(application_date,1,4) year FROM plant_protection_records ORDER BY year DESC"): self.year_filter.addItem(row["year"], row["year"])
        index = self.year_filter.findData(selected_year); self.year_filter.setCurrentIndex(index if index >= 0 else 0); self.year_filter.blockSignals(False)
        self._refresh_choices(self.field.currentData(), self.product.currentData(), combo_source_text(self.product))
        where=[]; params=[]
        if self.year_filter.currentData() != "all": where.append("substr(p.application_date,1,4)=?"); params.append(self.year_filter.currentData())
        search=self.search.text().strip()
        if search: where.append("(f.name LIKE ? OR p.purpose LIKE ? OR p.product_name LIKE ? OR p.applicator LIKE ?)"); params.extend([f"%{search}%"]*4)
        rows=self.db.query("""SELECT p.*,COALESCE(f.name,'') field_name FROM plant_protection_records p LEFT JOIN fields f ON f.id=p.field_id"""+(" WHERE "+" AND ".join(where) if where else "")+" ORDER BY p.application_date DESC,p.id DESC",params); self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            values=[row["application_date"],row["field_name"],row["purpose"],row["product_name"],f'{row["dose"]:g} {row["dose_unit"]}',f'{row["area_stremma"]:g} στρ.',f'{row["harvest_interval_days"]} ημ.',row["applicator"],f'{row["cost"]:.2f} €']
            for c,value in enumerate(values):
                item=QTableWidgetItem(str(value)); self.table.setItem(r,c,item)
                if c==0: item.setData(Qt.ItemDataRole.UserRole,row["id"])
