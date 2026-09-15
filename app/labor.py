from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .crud import CrudPage
from .database import Database
from .ui_helpers import table_widget
from .widgets import date_input
from .year_lock import is_year_locked, warn_locked_year


class LaborPage(CrudPage):
    """Μητρώο εργαζομένων και ημερολόγιο εργατικών ανά αγροτεμάχιο."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_worker_id: int | None = None
        self.selected_entry_id: int | None = None

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
        content.setObjectName("laborContent")
        content.setStyleSheet(
            "QWidget#laborContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Εργατικά & Προσωπικό")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Εργαζόμενοι, ώρες εργασίας και άμεσο κόστος ανά αγροτεμάχιο"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        metrics = QHBoxLayout()
        self.active_workers_metric = self._metric("Ενεργοί εργαζόμενοι")
        self.hours_metric = self._metric("Ώρες")
        self.cost_metric = self._metric("Κόστος")
        for card, _value in (
            self.active_workers_metric,
            self.hours_metric,
            self.cost_metric,
        ):
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        # ---------------- Worker registry ----------------
        worker_box = QGroupBox("Μητρώο εργαζομένων")
        worker_layout = QHBoxLayout(worker_box)

        worker_form_box = QGroupBox("Νέος εργαζόμενος")
        self.worker_form_box = worker_form_box
        worker_form = QFormLayout(worker_form_box)

        self.worker_name = QLineEdit()
        self.worker_name.setPlaceholderText("Ονοματεπώνυμο")
        self.worker_role = QLineEdit()
        self.worker_role.setPlaceholderText("Π.χ. εργάτης, χειριστής")
        self.worker_phone = QLineEdit()
        self.worker_rate = self._money_spin()
        self.worker_active = QCheckBox("Ενεργός")
        self.worker_active.setChecked(True)
        self.worker_notes = QLineEdit()

        worker_form.addRow("Ονοματεπώνυμο", self.worker_name)
        worker_form.addRow("Ρόλος", self.worker_role)
        worker_form.addRow("Τηλέφωνο", self.worker_phone)
        worker_form.addRow("Προεπιλογή €/ώρα", self.worker_rate)
        worker_form.addRow("", self.worker_active)
        worker_form.addRow("Σημειώσεις", self.worker_notes)

        worker_buttons = QHBoxLayout()
        self.worker_save_button = QPushButton("Προσθήκη εργαζομένου")
        self.worker_save_button.clicked.connect(self.save_worker)
        self.worker_cancel_button = QPushButton("Ακύρωση")
        self.worker_cancel_button.clicked.connect(self.clear_worker_form)
        self.worker_cancel_button.setEnabled(False)
        self.worker_delete_button = QPushButton("Διαγραφή")
        self.worker_delete_button.clicked.connect(self.delete_worker)
        self.worker_delete_button.setEnabled(False)

        for button in (
            self.worker_save_button,
            self.worker_cancel_button,
            self.worker_delete_button,
        ):
            worker_buttons.addWidget(button)
        worker_buttons.addStretch()
        worker_form.addRow("", worker_buttons)

        worker_layout.addWidget(worker_form_box, 1)

        self.worker_table = table_widget(
            ["Εργαζόμενος", "Ρόλος", "Τηλέφωνο", "€/ώρα", "Κατάσταση"]
        )
        self.worker_table.cellClicked.connect(self.load_worker)
        self.worker_table.setMinimumHeight(210)
        header = self.worker_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3, 4):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        worker_layout.addWidget(self.worker_table, 2)

        layout.addWidget(worker_box)

        # ---------------- Labor entry ----------------
        self.entry_box = QGroupBox("Νέα καταχώρηση εργατικών")
        entry_form = QFormLayout(self.entry_box)

        self.work_date = date_input()
        self.field = QComboBox()
        self.worker = QComboBox()
        self.worker.currentIndexChanged.connect(
            self._worker_selection_changed
        )
        self.work_type = QLineEdit()
        self.work_type.setPlaceholderText(
            "Π.χ. κλάδεμα, καθαρισμός, συγκομιδή"
        )
        self.hours = self._hours_spin()
        self.hourly_rate = self._money_spin()
        self.hours.valueChanged.connect(self._update_calculated_cost)
        self.hourly_rate.valueChanged.connect(self._update_calculated_cost)

        self.calculated_cost = QLabel("0,00 €")
        self.calculated_cost.setStyleSheet(
            "font-weight: 700; color: #315F49; background: transparent;"
        )
        self.entry_notes = QLineEdit()

        entry_form.addRow("Ημερομηνία", self.work_date)
        entry_form.addRow("Αγροτεμάχιο", self.field)
        entry_form.addRow("Εργαζόμενος", self.worker)
        entry_form.addRow("Εργασία", self.work_type)
        entry_form.addRow("Ώρες", self.hours)
        entry_form.addRow("Αμοιβή / ώρα", self.hourly_rate)
        entry_form.addRow("Υπολογιζόμενο κόστος", self.calculated_cost)
        entry_form.addRow("Σημειώσεις", self.entry_notes)

        entry_buttons = QHBoxLayout()
        self.entry_save_button = QPushButton("Προσθήκη")
        self.entry_save_button.clicked.connect(self.save_entry)
        self.entry_cancel_button = QPushButton("Ακύρωση")
        self.entry_cancel_button.clicked.connect(self.clear_entry_form)
        self.entry_cancel_button.setEnabled(False)
        self.entry_delete_button = QPushButton("Διαγραφή")
        self.entry_delete_button.clicked.connect(self.delete_entry)
        self.entry_delete_button.setEnabled(False)

        for button in (
            self.entry_save_button,
            self.entry_cancel_button,
            self.entry_delete_button,
        ):
            entry_buttons.addWidget(button)
        entry_buttons.addStretch()
        entry_form.addRow("", entry_buttons)

        layout.addWidget(self.entry_box)

        # ---------------- Filters ----------------
        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.year_filter = QComboBox()
        self.year_filter.addItem("Όλα τα έτη", None)
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.field_filter = QComboBox()
        self.field_filter.currentIndexChanged.connect(self.refresh)

        self.worker_filter = QComboBox()
        self.worker_filter.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση εργασίας ή σημειώσεων...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Αγροτεμάχιο"))
        filters.addWidget(self.field_filter)
        filters.addWidget(QLabel("Εργαζόμενος"))
        filters.addWidget(self.worker_filter)
        filters.addWidget(self.search, 1)

        layout.addWidget(filters_box)

        self.entry_table = table_widget(
            [
                "Ημερομηνία",
                "Αγροτεμάχιο",
                "Εργαζόμενος",
                "Εργασία",
                "Ώρες",
                "€/ώρα",
                "Κόστος",
                "Σημειώσεις",
            ]
        )
        self.entry_table.cellClicked.connect(self.load_entry)
        self.entry_table.setMinimumHeight(300)
        entry_header = self.entry_table.horizontalHeader()
        entry_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        entry_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        entry_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        entry_header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        for column in (4, 5, 6):
            entry_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        entry_header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(self.entry_table)
        layout.addStretch()

        self.refresh()

    @staticmethod
    def _metric(caption: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        inner = QVBoxLayout(box)

        label = QLabel(caption)
        label.setObjectName("metricCaption")
        value = QLabel("0")
        value.setObjectName("metricValue")

        inner.addWidget(label)
        inner.addWidget(value)
        return box, value

    @staticmethod
    def _hours_spin() -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(0, 99999)
        widget.setDecimals(2)
        widget.setSingleStep(0.5)
        widget.setSuffix(" ώρες")
        return widget

    @staticmethod
    def _money_spin() -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(0, 999999)
        widget.setDecimals(2)
        widget.setSingleStep(0.50)
        widget.setSuffix(" €")
        return widget

    @staticmethod
    def _money(value: float) -> str:
        return (
            f"{value:,.2f} €"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    def _ensure_schema(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                default_hourly_rate REAL NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_workers_name
            ON workers(LOWER(TRIM(name)))
            """
        )

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS labor_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                field_id INTEGER,
                worker_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,
                hours REAL NOT NULL DEFAULT 0,
                hourly_rate REAL NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE SET NULL,
                FOREIGN KEY(worker_id) REFERENCES workers(id) ON DELETE RESTRICT
            )
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_labor_entries_date
            ON labor_entries(work_date)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_labor_entries_field
            ON labor_entries(field_id)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_labor_entries_worker
            ON labor_entries(worker_id)
            """
        )

        audit_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='audit_events'
            """
        )

        if audit_exists is None:
            return

        triggers = (
            """
            CREATE TRIGGER IF NOT EXISTS audit_workers_insert
            AFTER INSERT ON workers
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'workers','INSERT',CAST(NEW.id AS TEXT),
                    'Εργαζόμενος: '||NEW.name
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_workers_update
            AFTER UPDATE ON workers
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'workers','UPDATE',CAST(NEW.id AS TEXT),
                    'Εργαζόμενος: '||NEW.name
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_workers_delete
            AFTER DELETE ON workers
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'workers','DELETE',CAST(OLD.id AS TEXT),
                    'Εργαζόμενος: '||OLD.name
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_labor_insert
            AFTER INSERT ON labor_entries
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'labor_entries','INSERT',CAST(NEW.id AS TEXT),
                    'Εργατικά: '||NEW.work_type||' | '||NEW.work_date||
                    ' | '||ROUND(NEW.hours,2)||' ώρες'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_labor_update
            AFTER UPDATE ON labor_entries
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'labor_entries','UPDATE',CAST(NEW.id AS TEXT),
                    'Εργατικά: '||NEW.work_type||' | '||NEW.work_date||
                    ' | '||ROUND(NEW.hours,2)||' ώρες'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_labor_delete
            AFTER DELETE ON labor_entries
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'labor_entries','DELETE',CAST(OLD.id AS TEXT),
                    'Εργατικά: '||OLD.work_type||' | '||OLD.work_date
                );
            END
            """,
        )

        for sql in triggers:
            self.db.execute(sql)

    def _refresh_fields(self) -> None:
        current = self.field.currentData()
        current_filter = self.field_filter.currentData()

        rows = self.db.query(
            "SELECT id,name FROM fields ORDER BY name,id"
        )

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Γενική εργασία / χωρίς αγροτεμάχιο", None)
        for row in rows:
            self.field.addItem(row["name"], int(row["id"]))
        index = self.field.findData(current)
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)

        self.field_filter.blockSignals(True)
        self.field_filter.clear()
        self.field_filter.addItem("Όλα", None)
        for row in rows:
            self.field_filter.addItem(row["name"], int(row["id"]))
        index = self.field_filter.findData(current_filter)
        self.field_filter.setCurrentIndex(index if index >= 0 else 0)
        self.field_filter.blockSignals(False)

    def _refresh_workers(self) -> None:
        current = self.worker.currentData()
        current_filter = self.worker_filter.currentData()

        rows = self.db.query(
            """
            SELECT id,name,active,default_hourly_rate
            FROM workers
            ORDER BY active DESC,name,id
            """
        )

        self.worker.blockSignals(True)
        self.worker.clear()
        self.worker.addItem("Επίλεξε εργαζόμενο", None)
        for row in rows:
            label = row["name"]
            if not int(row["active"] or 0):
                label += " — ανενεργός"
            self.worker.addItem(label, int(row["id"]))
            self.worker.setItemData(
                self.worker.count() - 1,
                float(row["default_hourly_rate"] or 0),
                Qt.ItemDataRole.UserRole + 1,
            )
        index = self.worker.findData(current)
        self.worker.setCurrentIndex(index if index >= 0 else 0)
        self.worker.blockSignals(False)

        self.worker_filter.blockSignals(True)
        self.worker_filter.clear()
        self.worker_filter.addItem("Όλοι", None)
        for row in rows:
            self.worker_filter.addItem(
                row["name"],
                int(row["id"]),
            )
        index = self.worker_filter.findData(current_filter)
        self.worker_filter.setCurrentIndex(index if index >= 0 else 0)
        self.worker_filter.blockSignals(False)

    def _refresh_years(self) -> None:
        current = self.year_filter.currentData()
        rows = self.db.query(
            """
            SELECT DISTINCT SUBSTR(work_date,1,4) AS year
            FROM labor_entries
            WHERE work_date IS NOT NULL AND work_date <> ''
            ORDER BY year DESC
            """
        )

        self.year_filter.blockSignals(True)
        self.year_filter.clear()
        self.year_filter.addItem("Όλα τα έτη", None)
        for row in rows:
            if row["year"]:
                self.year_filter.addItem(row["year"], row["year"])
        index = self.year_filter.findData(current)
        self.year_filter.setCurrentIndex(index if index >= 0 else 0)
        self.year_filter.blockSignals(False)

    def _worker_selection_changed(self, _index: int) -> None:
        if self.selected_entry_id is not None:
            return

        rate = self.worker.currentData(
            Qt.ItemDataRole.UserRole + 1
        )
        if rate is not None:
            self.hourly_rate.setValue(float(rate))
        self._update_calculated_cost()

    def _update_calculated_cost(self, *_args) -> None:
        cost = self.hours.value() * self.hourly_rate.value()
        self.calculated_cost.setText(self._money(cost))

    # ---------------- Worker CRUD ----------------
    def save_worker(self) -> None:
        name = self.worker_name.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Συμπλήρωσε το ονοματεπώνυμο.",
            )
            self.worker_name.setFocus()
            return

        duplicate = self.db.query_one(
            """
            SELECT id
            FROM workers
            WHERE
                LOWER(TRIM(name))=LOWER(TRIM(?))
                AND id<>COALESCE(?, -1)
            """,
            (name, self.selected_worker_id),
        )

        if duplicate is not None:
            QMessageBox.warning(
                self,
                "Διπλή εγγραφή",
                "Υπάρχει ήδη εργαζόμενος με αυτό το όνομα.",
            )
            return

        values = (
            name,
            self.worker_role.text().strip(),
            self.worker_phone.text().strip(),
            self.worker_rate.value(),
            1 if self.worker_active.isChecked() else 0,
            self.worker_notes.text().strip(),
        )

        if self.selected_worker_id is None:
            self.db.execute(
                """
                INSERT INTO workers(
                    name,role,phone,default_hourly_rate,active,notes
                )
                VALUES(?,?,?,?,?,?)
                """,
                values,
            )
        else:
            self.db.execute(
                """
                UPDATE workers
                SET
                    name=?,
                    role=?,
                    phone=?,
                    default_hourly_rate=?,
                    active=?,
                    notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, self.selected_worker_id),
            )

        self.clear_worker_form()
        self.refresh()

    def load_worker(self, row: int, _column: int) -> None:
        item = self.worker_table.item(row, 0)
        worker_id = (
            item.data(Qt.ItemDataRole.UserRole)
            if item is not None
            else None
        )

        if worker_id is None:
            return

        record = self.db.query_one(
            "SELECT * FROM workers WHERE id=?",
            (worker_id,),
        )

        if record is None:
            return

        self.selected_worker_id = int(record["id"])
        self.worker_name.setText(record["name"] or "")
        self.worker_role.setText(record["role"] or "")
        self.worker_phone.setText(record["phone"] or "")
        self.worker_rate.setValue(
            float(record["default_hourly_rate"] or 0)
        )
        self.worker_active.setChecked(
            bool(int(record["active"] or 0))
        )
        self.worker_notes.setText(record["notes"] or "")

        self.worker_form_box.setTitle("Επεξεργασία εργαζομένου")
        self.worker_save_button.setText("Αποθήκευση")
        self.worker_cancel_button.setEnabled(True)
        self.worker_delete_button.setEnabled(True)

    def clear_worker_form(self) -> None:
        self.selected_worker_id = None
        self.worker_name.clear()
        self.worker_role.clear()
        self.worker_phone.clear()
        self.worker_rate.setValue(0)
        self.worker_active.setChecked(True)
        self.worker_notes.clear()
        self.worker_form_box.setTitle("Νέος εργαζόμενος")
        self.worker_save_button.setText("Προσθήκη εργαζομένου")
        self.worker_cancel_button.setEnabled(False)
        self.worker_delete_button.setEnabled(False)
        self.worker_table.clearSelection()

    def delete_worker(self) -> None:
        if self.selected_worker_id is None:
            return

        usage = self.db.query_one(
            """
            SELECT COUNT(*) AS total
            FROM labor_entries
            WHERE worker_id=?
            """,
            (self.selected_worker_id,),
        )

        if usage and int(usage["total"] or 0) > 0:
            QMessageBox.warning(
                self,
                "Δεν μπορεί να διαγραφεί",
                "Ο εργαζόμενος έχει ιστορικό εργατικών.\n\n"
                "Αποεπίλεξε το «Ενεργός» αντί να τον διαγράψεις, "
                "ώστε να διατηρηθεί το ιστορικό.",
            )
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή εργαζομένου",
            "Να διαγραφεί ο επιλεγμένος εργαζόμενος;",
        ):
            return

        self.db.execute(
            "DELETE FROM workers WHERE id=?",
            (self.selected_worker_id,),
        )
        self.clear_worker_form()
        self.refresh()

    # ---------------- Labor entry CRUD ----------------
    def _entry_year(self, entry_id: int) -> int | None:
        row = self.db.query_one(
            """
            SELECT work_date
            FROM labor_entries
            WHERE id=?
            """,
            (entry_id,),
        )

        if row is None:
            return None

        parsed = QDate.fromString(
            row["work_date"] or "",
            "yyyy-MM-dd",
        )
        return parsed.year() if parsed.isValid() else None

    def _locked_for_save(self) -> bool:
        target_year = self.work_date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True

        if self.selected_entry_id is not None:
            original_year = self._entry_year(
                self.selected_entry_id
            )
            if (
                original_year is not None
                and original_year != target_year
                and is_year_locked(self.db, original_year)
            ):
                warn_locked_year(
                    self,
                    self.db,
                    original_year,
                )
                return True

        return False

    def save_entry(self) -> None:
        if self._locked_for_save():
            return

        worker_id = self.worker.currentData()

        if worker_id is None:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Επίλεξε εργαζόμενο.",
            )
            self.worker.setFocus()
            return

        work_type = self.work_type.text().strip()
        if not work_type:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Συμπλήρωσε την εργασία.",
            )
            self.work_type.setFocus()
            return

        hours = self.hours.value()
        if hours <= 0:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Οι ώρες πρέπει να είναι μεγαλύτερες από 0.",
            )
            self.hours.setFocus()
            return

        hourly_rate = self.hourly_rate.value()
        cost = hours * hourly_rate

        values = (
            self.work_date.date().toString("yyyy-MM-dd"),
            self.field.currentData(),
            worker_id,
            work_type,
            hours,
            hourly_rate,
            cost,
            self.entry_notes.text().strip(),
        )

        if self.selected_entry_id is None:
            self.db.execute(
                """
                INSERT INTO labor_entries(
                    work_date,
                    field_id,
                    worker_id,
                    work_type,
                    hours,
                    hourly_rate,
                    cost,
                    notes
                )
                VALUES(?,?,?,?,?,?,?,?)
                """,
                values,
            )
        else:
            self.db.execute(
                """
                UPDATE labor_entries
                SET
                    work_date=?,
                    field_id=?,
                    worker_id=?,
                    work_type=?,
                    hours=?,
                    hourly_rate=?,
                    cost=?,
                    notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, self.selected_entry_id),
            )

        self.clear_entry_form()
        self.refresh()

    def load_entry(self, row: int, _column: int) -> None:
        item = self.entry_table.item(row, 0)
        entry_id = (
            item.data(Qt.ItemDataRole.UserRole)
            if item is not None
            else None
        )

        if entry_id is None:
            return

        record = self.db.query_one(
            "SELECT * FROM labor_entries WHERE id=?",
            (entry_id,),
        )
        if record is None:
            return

        self.selected_entry_id = int(record["id"])

        parsed = QDate.fromString(
            record["work_date"] or "",
            "yyyy-MM-dd",
        )
        if parsed.isValid():
            self.work_date.setDate(parsed)

        self._refresh_fields()
        index = self.field.findData(record["field_id"])
        self.field.setCurrentIndex(index if index >= 0 else 0)

        self._refresh_workers()
        index = self.worker.findData(record["worker_id"])
        self.worker.setCurrentIndex(index if index >= 0 else 0)

        self.work_type.setText(record["work_type"] or "")
        self.hours.setValue(float(record["hours"] or 0))
        self.hourly_rate.setValue(
            float(record["hourly_rate"] or 0)
        )
        self.entry_notes.setText(record["notes"] or "")
        self._update_calculated_cost()

        year = parsed.year() if parsed.isValid() else None
        locked = (
            year is not None
            and is_year_locked(self.db, year)
        )

        if locked:
            self.entry_box.setTitle(
                f"Προβολή εργατικών — ΚΛΕΙΔΩΜΕΝΟ {year}"
            )
            self.entry_save_button.setText("Κλειδωμένο")
            self.entry_save_button.setEnabled(False)
            self.entry_delete_button.setEnabled(False)
        else:
            self.entry_box.setTitle("Επεξεργασία εργατικών")
            self.entry_save_button.setText("Αποθήκευση")
            self.entry_save_button.setEnabled(True)
            self.entry_delete_button.setEnabled(True)

        self.entry_cancel_button.setEnabled(True)

    def clear_entry_form(self) -> None:
        self.selected_entry_id = None
        self.work_date.setDate(QDate.currentDate())
        self._refresh_fields()
        self.field.setCurrentIndex(0)
        self._refresh_workers()
        self.worker.setCurrentIndex(0)
        self.work_type.clear()
        self.hours.setValue(0)
        self.hourly_rate.setValue(0)
        self.entry_notes.clear()
        self._update_calculated_cost()

        self.entry_box.setTitle("Νέα καταχώρηση εργατικών")
        self.entry_save_button.setText("Προσθήκη")
        self.entry_save_button.setEnabled(True)
        self.entry_cancel_button.setEnabled(False)
        self.entry_delete_button.setEnabled(False)
        self.entry_table.clearSelection()

    def delete_entry(self) -> None:
        if self.selected_entry_id is None:
            return

        year = self._entry_year(self.selected_entry_id)
        if year is not None and is_year_locked(self.db, year):
            warn_locked_year(self, self.db, year)
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή εργατικών",
            "Να διαγραφεί η επιλεγμένη καταχώρηση εργατικών;",
        ):
            return

        self.db.execute(
            "DELETE FROM labor_entries WHERE id=?",
            (self.selected_entry_id,),
        )
        self.clear_entry_form()
        self.refresh()

    def refresh(self, *_args) -> None:
        self._ensure_schema()
        self._refresh_fields()
        self._refresh_workers()
        self._refresh_years()

        year = self.year_filter.currentData()
        field_id = self.field_filter.currentData()
        worker_id = self.worker_filter.currentData()
        search = self.search.text().strip()

        where = ["1=1"]
        params: list[object] = []

        if year:
            where.append("SUBSTR(l.work_date,1,4)=?")
            params.append(year)

        if field_id is not None:
            where.append("l.field_id=?")
            params.append(field_id)

        if worker_id is not None:
            where.append("l.worker_id=?")
            params.append(worker_id)

        if search:
            token = f"%{search}%"
            where.append(
                "(l.work_type LIKE ? OR l.notes LIKE ? OR w.name LIKE ?)"
            )
            params.extend([token, token, token])

        rows = self.db.query(
            f"""
            SELECT
                l.*,
                f.name AS field_name,
                w.name AS worker_name
            FROM labor_entries l
            LEFT JOIN fields f
                ON f.id=l.field_id
            LEFT JOIN workers w
                ON w.id=l.worker_id
            WHERE {' AND '.join(where)}
            ORDER BY l.work_date DESC,l.id DESC
            """,
            params,
        )

        self.entry_table.setRowCount(len(rows))

        total_hours = 0.0
        total_cost = 0.0

        for row_index, row in enumerate(rows):
            total_hours += float(row["hours"] or 0)
            total_cost += float(row["cost"] or 0)

            values = [
                row["work_date"] or "",
                row["field_name"] or "Γενική",
                row["worker_name"] or "",
                row["work_type"] or "",
                f"{float(row['hours'] or 0):.2f}",
                self._money(float(row["hourly_rate"] or 0)),
                self._money(float(row["cost"] or 0)),
                row["notes"] or "",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                self.entry_table.setItem(
                    row_index,
                    column,
                    item,
                )

        worker_rows = self.db.query(
            "SELECT * FROM workers ORDER BY active DESC,name,id"
        )
        self.worker_table.setRowCount(len(worker_rows))

        active_count = 0

        for row_index, row in enumerate(worker_rows):
            active = bool(int(row["active"] or 0))
            if active:
                active_count += 1

            values = [
                row["name"] or "",
                row["role"] or "",
                row["phone"] or "",
                self._money(
                    float(row["default_hourly_rate"] or 0)
                ),
                "Ενεργός" if active else "Ανενεργός",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                self.worker_table.setItem(
                    row_index,
                    column,
                    item,
                )

        self.active_workers_metric[1].setText(str(active_count))
        self.hours_metric[1].setText(f"{total_hours:.2f}")
        self.cost_metric[1].setText(self._money(total_cost))
