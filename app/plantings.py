from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .crud import CrudPage
from .database import Database
from .language import combo_source_text
from .ui_helpers import compact_decimal, table_widget
from .widgets import date_input
from .year_lock import is_year_locked, warn_locked_year


class PlantingsPage(CrudPage):
    """Καταγραφή παρτίδων φύτευσης και επιβίωσης δέντρων ανά αγροτεμάχιο."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_id: int | None = None

        self._ensure_schema()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("plantingsContent")
        content.setStyleSheet(
            "QWidget#plantingsContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Φυτεύσεις & Δέντρα")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Παρακολούθηση παρτίδων φύτευσης, απωλειών και επιβίωσης ανά αγροτεμάχιο"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        metrics = QHBoxLayout()
        self.planted_metric = self._metric("Φυτεμένα")
        self.alive_metric = self._metric("Ζωντανά")
        self.losses_metric = self._metric("Απώλειες")
        self.survival_metric = self._metric("Επιβίωση")
        for card, _value in (
            self.planted_metric,
            self.alive_metric,
            self.losses_metric,
            self.survival_metric,
        ):
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        # Entry form
        self.form_box = QGroupBox("Νέα φύτευση")
        form = QFormLayout(self.form_box)

        self.planting_date = date_input()
        self.field = QComboBox()

        self.trees_planted = QSpinBox()
        self.trees_planted.setRange(1, 1_000_000)
        self.trees_planted.setValue(1)
        self.trees_planted.valueChanged.connect(self._sync_alive_limit)

        self.trees_alive = QSpinBox()
        self.trees_alive.setRange(0, 1_000_000)

        self.material_type = QComboBox()
        self.material_type.addItems(
            [
                "Καταβολάδες",
                "Παραφυάδες",
                "Δενδρύλλια",
                "Μοσχεύματα",
                "Άλλο",
            ]
        )
        self.source = QLineEdit()
        self.source.setPlaceholderText("Προέλευση φυτικού υλικού")

        self.variety = QLineEdit()
        self.variety.setPlaceholderText("Ποικιλία / κλώνος, αν είναι γνωστό")

        self.spacing = QLineEdit()
        self.spacing.setPlaceholderText("Π.χ. 2 x 6 m")

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 999_999_999)
        self.cost.setDecimals(2)
        self.cost.setSuffix(" €")

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Σημειώσεις...")
        self.notes.setFixedHeight(78)

        form.addRow("Ημερομηνία", self.planting_date)
        form.addRow("Αγροτεμάχιο", self.field)
        form.addRow("Φυτεμένα δέντρα", self.trees_planted)
        form.addRow("Ζωντανά σήμερα", self.trees_alive)
        form.addRow("Τύπος φυτικού υλικού", self.material_type)
        form.addRow("Προέλευση", self.source)
        form.addRow("Ποικιλία / κλώνος", self.variety)
        form.addRow("Αποστάσεις", self.spacing)
        form.addRow("Κόστος παρτίδας", self.cost)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_record)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_record)
        self.delete_button.setEnabled(False)

        for button in (
            self.save_button,
            self.cancel_button,
            self.delete_button,
        ):
            buttons.addWidget(button)

        buttons.addStretch()
        form.addRow("", buttons)
        layout.addWidget(self.form_box)

        # Filters
        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.field_filter = QComboBox()
        self.field_filter.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση προέλευσης, τύπου, ποικιλίας ή σημειώσεων..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Αγροτεμάχιο"))
        filters.addWidget(self.field_filter)
        filters.addWidget(self.search, 1)

        layout.addWidget(filters_box)

        self.table = table_widget(
            [
                "Ημερομηνία",
                "Αγροτεμάχιο",
                "Φυτεμένα",
                "Ζωντανά",
                "Απώλειες",
                "Επιβίωση",
                "Υλικό",
                "Προέλευση",
                "Αποστάσεις",
                "Κόστος",
            ]
        )
        self.table.cellClicked.connect(self.load_record)
        self.table.setMinimumHeight(340)

        header = self.table.horizontalHeader()
        for column in range(self.table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.Stretch,
        )

        layout.addWidget(self.table)
        layout.addStretch()

        self.refresh()
        self.clear_form()

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
            CREATE TABLE IF NOT EXISTS planting_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                planting_date TEXT NOT NULL,
                field_id INTEGER NOT NULL,
                trees_planted INTEGER NOT NULL DEFAULT 0,
                trees_alive INTEGER NOT NULL DEFAULT 0,
                material_type TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                variety TEXT NOT NULL DEFAULT '',
                spacing TEXT NOT NULL DEFAULT '',
                cost REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE RESTRICT
            )
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_planting_batches_date
            ON planting_batches(planting_date)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_planting_batches_field
            ON planting_batches(field_id)
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

        for sql in (
            """
            CREATE TRIGGER IF NOT EXISTS audit_planting_insert
            AFTER INSERT ON planting_batches
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'planting_batches','INSERT',CAST(NEW.id AS TEXT),
                    'Φύτευση: '||NEW.planting_date||' | '||
                    NEW.trees_planted||' δέντρα'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_planting_update
            AFTER UPDATE ON planting_batches
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'planting_batches','UPDATE',CAST(NEW.id AS TEXT),
                    'Φύτευση: '||NEW.planting_date||' | '||
                    NEW.trees_planted||' δέντρα | ζωντανά '||NEW.trees_alive
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_planting_delete
            AFTER DELETE ON planting_batches
            BEGIN
                INSERT INTO audit_events(
                    event_time,table_name,action,record_id,details
                )
                VALUES(
                    datetime('now','localtime'),
                    'planting_batches','DELETE',CAST(OLD.id AS TEXT),
                    'Φύτευση: '||OLD.planting_date||' | '||
                    OLD.trees_planted||' δέντρα'
                );
            END
            """,
        ):
            self.db.execute(sql)

    def _sync_alive_limit(self, value: int) -> None:
        self.trees_alive.setMaximum(value)
        if self.trees_alive.value() > value:
            self.trees_alive.setValue(value)

    def _refresh_fields(self) -> None:
        selected = self.field.currentData()
        selected_filter = self.field_filter.currentData()

        rows = self.db.query(
            "SELECT id,name FROM fields ORDER BY name,id"
        )

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Επίλεξε αγροτεμάχιο", None)
        for row in rows:
            self.field.addItem(row["name"], int(row["id"]))
        index = self.field.findData(selected)
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)

        self.field_filter.blockSignals(True)
        self.field_filter.clear()
        self.field_filter.addItem("Όλα", None)
        for row in rows:
            self.field_filter.addItem(row["name"], int(row["id"]))
        index = self.field_filter.findData(selected_filter)
        self.field_filter.setCurrentIndex(index if index >= 0 else 0)
        self.field_filter.blockSignals(False)

    def _refresh_years(self) -> None:
        selected = self.year_filter.currentData()
        rows = self.db.query(
            """
            SELECT DISTINCT SUBSTR(planting_date,1,4) AS year
            FROM planting_batches
            WHERE planting_date IS NOT NULL AND planting_date <> ''
            ORDER BY year DESC
            """
        )

        self.year_filter.blockSignals(True)
        self.year_filter.clear()
        self.year_filter.addItem("Όλα τα έτη", None)
        for row in rows:
            if row["year"]:
                self.year_filter.addItem(row["year"], row["year"])
        index = self.year_filter.findData(selected)
        self.year_filter.setCurrentIndex(index if index >= 0 else 0)
        self.year_filter.blockSignals(False)

    def _record_year(self, record_id: int) -> int | None:
        row = self.db.query_one(
            """
            SELECT planting_date
            FROM planting_batches
            WHERE id=?
            """,
            (record_id,),
        )
        if row is None:
            return None

        parsed = QDate.fromString(
            row["planting_date"] or "",
            "yyyy-MM-dd",
        )
        return parsed.year() if parsed.isValid() else None

    def _locked_for_save(self) -> bool:
        target_year = self.planting_date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True

        if self.selected_id is not None:
            original_year = self._record_year(self.selected_id)
            if (
                original_year is not None
                and original_year != target_year
                and is_year_locked(self.db, original_year)
            ):
                warn_locked_year(self, self.db, original_year)
                return True

        return False

    def save_record(self) -> None:
        if self._locked_for_save():
            return

        field_id = self.field.currentData()

        if field_id is None:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Επίλεξε αγροτεμάχιο.",
            )
            self.field.setFocus()
            return

        planted = self.trees_planted.value()
        alive = self.trees_alive.value()

        if alive > planted:
            QMessageBox.warning(
                self,
                "Μη έγκυρα στοιχεία",
                "Τα ζωντανά δέντρα δεν μπορούν να είναι περισσότερα από τα φυτεμένα.",
            )
            return

        values = (
            self.planting_date.date().toString("yyyy-MM-dd"),
            field_id,
            planted,
            alive,
            combo_source_text(self.material_type).strip(),
            self.source.text().strip(),
            self.variety.text().strip(),
            self.spacing.text().strip(),
            self.cost.value(),
            self.notes.toPlainText().strip(),
        )

        if self.selected_id is None:
            self.db.execute(
                """
                INSERT INTO planting_batches(
                    planting_date,
                    field_id,
                    trees_planted,
                    trees_alive,
                    material_type,
                    source,
                    variety,
                    spacing,
                    cost,
                    notes
                )
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
        else:
            self.db.execute(
                """
                UPDATE planting_batches
                SET
                    planting_date=?,
                    field_id=?,
                    trees_planted=?,
                    trees_alive=?,
                    material_type=?,
                    source=?,
                    variety=?,
                    spacing=?,
                    cost=?,
                    notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, self.selected_id),
            )

        self.clear_form()
        self.refresh()

    def load_record(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        record_id = (
            item.data(Qt.ItemDataRole.UserRole)
            if item is not None
            else None
        )

        if record_id is None:
            return

        record = self.db.query_one(
            "SELECT * FROM planting_batches WHERE id=?",
            (record_id,),
        )
        if record is None:
            return

        self.selected_id = int(record["id"])

        parsed = QDate.fromString(
            record["planting_date"] or "",
            "yyyy-MM-dd",
        )
        if parsed.isValid():
            self.planting_date.setDate(parsed)

        self._refresh_fields()
        index = self.field.findData(record["field_id"])
        self.field.setCurrentIndex(index if index >= 0 else 0)

        self.trees_planted.setValue(int(record["trees_planted"] or 0))
        self.trees_alive.setValue(int(record["trees_alive"] or 0))

        index = self.material_type.findText(
            record["material_type"] or ""
        )
        if index >= 0:
            self.material_type.setCurrentIndex(index)

        self.source.setText(record["source"] or "")
        self.variety.setText(record["variety"] or "")
        self.spacing.setText(record["spacing"] or "")
        self.cost.setValue(float(record["cost"] or 0))
        self.notes.setPlainText(record["notes"] or "")

        year = parsed.year() if parsed.isValid() else None
        locked = (
            year is not None
            and is_year_locked(self.db, year)
        )

        if locked:
            self.form_box.setTitle(
                f"Προβολή φύτευσης — ΚΛΕΙΔΩΜΕΝΟ {year}"
            )
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.form_box.setTitle("Επεξεργασία φύτευσης")
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_id = None
        self.planting_date.setDate(QDate.currentDate())
        self._refresh_fields()
        self.field.setCurrentIndex(0)
        self.trees_planted.setValue(1)
        self.trees_alive.setValue(1)
        self.material_type.setCurrentIndex(0)
        self.source.clear()
        self.variety.clear()
        self.spacing.clear()
        self.cost.setValue(0)
        self.notes.clear()

        self.form_box.setTitle("Νέα φύτευση")
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()

    def delete_record(self) -> None:
        if self.selected_id is None:
            return

        year = self._record_year(self.selected_id)
        if year is not None and is_year_locked(self.db, year):
            warn_locked_year(self, self.db, year)
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή φύτευσης",
            "Να διαγραφεί η επιλεγμένη παρτίδα φύτευσης;",
        ):
            return

        self.db.execute(
            "DELETE FROM planting_batches WHERE id=?",
            (self.selected_id,),
        )
        self.clear_form()
        self.refresh()

    def refresh(self, *_args) -> None:
        self._ensure_schema()
        self._refresh_fields()
        self._refresh_years()

        year = self.year_filter.currentData()
        field_id = self.field_filter.currentData()
        search = self.search.text().strip()

        where = ["1=1"]
        params: list[object] = []

        if year:
            where.append("SUBSTR(p.planting_date,1,4)=?")
            params.append(year)

        if field_id is not None:
            where.append("p.field_id=?")
            params.append(field_id)

        if search:
            token = f"%{search}%"
            where.append(
                "("
                "p.material_type LIKE ? OR "
                "p.source LIKE ? OR "
                "p.variety LIKE ? OR "
                "p.spacing LIKE ? OR "
                "p.notes LIKE ? OR "
                "f.name LIKE ?"
                ")"
            )
            params.extend(
                [token, token, token, token, token, token]
            )

        rows = self.db.query(
            f"""
            SELECT
                p.*,
                f.name AS field_name
            FROM planting_batches p
            LEFT JOIN fields f
                ON f.id=p.field_id
            WHERE {' AND '.join(where)}
            ORDER BY p.planting_date DESC,p.id DESC
            """,
            params,
        )

        self.table.setRowCount(len(rows))

        total_planted = 0
        total_alive = 0

        for row_index, row in enumerate(rows):
            planted = int(row["trees_planted"] or 0)
            alive = int(row["trees_alive"] or 0)
            losses = max(planted - alive, 0)
            survival = (
                (alive / planted) * 100.0
                if planted > 0
                else 0.0
            )

            total_planted += planted
            total_alive += alive

            values = [
                row["planting_date"] or "",
                row["field_name"] or "",
                str(planted),
                str(alive),
                str(losses),
                f"{compact_decimal(survival, 1)}%",
                row["material_type"] or "",
                row["source"] or "",
                row["spacing"] or "",
                self._money(float(row["cost"] or 0)),
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                self.table.setItem(
                    row_index,
                    column,
                    item,
                )

        total_losses = max(total_planted - total_alive, 0)
        overall_survival = (
            (total_alive / total_planted) * 100.0
            if total_planted > 0
            else 0.0
        )

        self.planted_metric[1].setText(str(total_planted))
        self.alive_metric[1].setText(str(total_alive))
        self.losses_metric[1].setText(str(total_losses))
        self.survival_metric[1].setText(
            f"{compact_decimal(overall_survival, 1)}%"
        )
