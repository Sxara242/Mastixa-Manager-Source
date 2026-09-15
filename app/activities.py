from __future__ import annotations

from PySide6.QtCore import QDate, QEvent, QPoint, QTimer, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
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
from .language import combo_source_text
from .ui_helpers import table_widget
from .year_lock import is_year_locked, warn_locked_year
from .inventory_sync import InventoryStockError, delete_consumption, ensure_can_consume, ensure_inventory_source_schema, sync_consumption


ACTIVITY_CATEGORIES = ["Πότισμα", "Λίπανση"]

ACTIVITY_STATUSES = [
    "Προγραμματισμένη",
    "Ολοκληρώθηκε",
    "Ακυρώθηκε",
]


class ClickOpenComboBox(QComboBox):
    """Editable combo that opens its list when any part is clicked."""

    def setEditable(self, editable: bool) -> None:
        super().setEditable(editable)

        editor = self.lineEdit()
        if editable and editor is not None:
            editor.installEventFilter(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.showPopup()
            event.accept()
            return

        super().mousePressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        editor = self.lineEdit()

        if (
            editor is not None
            and watched is editor
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            # Let the editor receive focus/cursor normally, but open the list
            # immediately after Qt finishes handling the click.
            QTimer.singleShot(0, self.showPopup)

        return super().eventFilter(watched, event)


class ClickOpenDateEdit(QDateEdit):
    """Date edit whose calendar opens from a click anywhere in the field."""

    def __init__(self) -> None:
        super().__init__()
        self.setCalendarPopup(True)
        self._popup_frame: QFrame | None = None
        self._popup_calendar: QCalendarWidget | None = None

        editor = self.lineEdit()
        if editor is not None:
            editor.installEventFilter(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_calendar()
            event.accept()
            return

        super().mousePressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        editor = self.lineEdit()

        if (
            editor is not None
            and watched is editor
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._show_calendar()
            return True

        return super().eventFilter(watched, event)

    def _ensure_popup(self) -> None:
        if self._popup_frame is not None:
            return

        self._popup_frame = QFrame(
            None,
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
        )
        self._popup_frame.setObjectName("activityDatePopup")

        popup_layout = QVBoxLayout(self._popup_frame)
        popup_layout.setContentsMargins(1, 1, 1, 1)

        self._popup_calendar = QCalendarWidget(self._popup_frame)
        self._popup_calendar.setGridVisible(True)
        self._popup_calendar.clicked.connect(self._calendar_date_clicked)
        popup_layout.addWidget(self._popup_calendar)

    def _show_calendar(self) -> None:
        self._ensure_popup()

        if self._popup_frame is None or self._popup_calendar is None:
            return

        self._popup_calendar.setSelectedDate(self.date())
        self._popup_frame.adjustSize()

        position = self.mapToGlobal(QPoint(0, self.height() + 2))
        screen = self.screen()

        if screen is not None:
            available = screen.availableGeometry()

            if position.x() + self._popup_frame.width() > available.right():
                position.setX(
                    max(
                        available.left(),
                        available.right() - self._popup_frame.width(),
                    )
                )

            if position.y() + self._popup_frame.height() > available.bottom():
                position = self.mapToGlobal(
                    QPoint(0, -self._popup_frame.height() - 2)
                )

        self._popup_frame.move(position)
        self._popup_frame.show()
        self._popup_frame.raise_()
        self._popup_calendar.setFocus()

    def _calendar_date_clicked(self, date: QDate) -> None:
        self.setDate(date)

        if self._popup_frame is not None:
            self._popup_frame.hide()


class ActivitiesPage(CrudPage):
    """Ενιαίο ημερολόγιο άρδευσης και λίπανσης ανά αγροτεμάχιο."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_activity_id: int | None = None

        self._ensure_schema_and_audit_triggers()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("activitiesScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()
        content.setObjectName("activitiesContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(10)

        self.scroll_area.setWidget(content)
        outer_layout.addWidget(self.scroll_area)

        title = QLabel("Άρδευση & Λίπανση")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(38)
        layout.addWidget(title)

        subtitle = QLabel(
            "Ενιαίο ημερολόγιο καταγραφών άρδευσης και λίπανσης"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setMinimumHeight(24)
        layout.addWidget(subtitle)

        self.form_box = QGroupBox("Νέα καταγραφή")
        form = QFormLayout(self.form_box)

        self.date = ClickOpenDateEdit()
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.date.setDate(QDate.currentDate())

        self.field = ClickOpenComboBox()

        self.category = QComboBox()
        self.category.addItem("Πότισμα", "irrigation")
        self.category.addItem("Λίπανση", "fertilization")
        self.category.currentIndexChanged.connect(self._update_action_fields)

        self.status = ClickOpenComboBox()
        self.status.addItems(ACTIVITY_STATUSES)
        self.status.setCurrentText("Ολοκληρώθηκε")


        self.duration = QDoubleSpinBox()
        self.duration.setRange(0, 999999)
        self.duration.setDecimals(1)
        self.duration.setSuffix(" λεπτά")

        self.water_quantity = QDoubleSpinBox()
        self.water_quantity.setRange(0, 999999999)
        self.water_quantity.setDecimals(3)
        self.water_quantity.setSuffix(" m³")

        # These controls deliberately use the native QComboBox behavior.
        # ClickOpenComboBox consumes mouse presses to open its popup, which is
        # useful for filters but prevents reliable cursor placement in an
        # editable combo's line editor.
        self.product = QComboBox()
        self.product.setEditable(True)
        self.product.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        if self.product.lineEdit() is not None:
            self.product.lineEdit().setReadOnly(False)
            self.product.lineEdit().setClearButtonEnabled(True)

        self.dose = QDoubleSpinBox()
        self.dose.setRange(0, 999999999)
        self.dose.setDecimals(3)

        self.dose_unit = QComboBox()
        self.dose_unit.addItem("Κιλά (kg)", "kg")
        self.dose_unit.addItem("Λίτρα (L)", "L")
        self.dose_unit.addItem("Γραμμάρια (g)", "g")
        self.dose_unit.addItem("Χιλιοστόλιτρα (ml)", "ml")
        self.dose_unit.addItem("Κιλά / στρέμμα", "kg/στρ.")
        self.dose_unit.addItem("Λίτρα / στρέμμα", "L/στρ.")
        self.dose_unit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.inventory_item = QComboBox()
        self.inventory_quantity = QDoubleSpinBox()
        self.inventory_quantity.setRange(0, 999999999)
        self.inventory_quantity.setDecimals(3)

        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 999999999)
        self.cost.setDecimals(2)
        self.cost.setSuffix(" €")

        for spinbox in (
            self.duration,
            self.water_quantity,
            self.dose,
            self.inventory_quantity,
            self.cost,
        ):
            spinbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            spinbox.setKeyboardTracking(True)
            spinbox.setAccelerated(True)
            spinbox.setButtonSymbols(
                QDoubleSpinBox.ButtonSymbols.UpDownArrows
            )
            spinbox.setMinimumWidth(180)
            spinbox.lineEdit().setReadOnly(False)

        self.responsible = QLineEdit()
        self.responsible.setPlaceholderText("Όνομα υπευθύνου")

        self.notes = QLineEdit()
        self.notes.setPlaceholderText("Προαιρετικές σημειώσεις")

        for widget in (
            self.date,
            self.field,
            self.category,
            self.status,
            self.duration,
            self.water_quantity,
            self.product,
            self.dose,
            self.dose_unit,
            self.inventory_item,
            self.inventory_quantity,
            self.cost,
            self.responsible,
            self.notes,
        ):
            widget.setMinimumHeight(36)

        form.addRow("Ημερομηνία", self.date)
        form.addRow("Αγροτεμάχιο", self.field)
        form.addRow("Τύπος ενέργειας", self.category)
        form.addRow("Κατάσταση", self.status)
        form.addRow("Διάρκεια άρδευσης", self.duration)
        form.addRow("Ποσότητα νερού", self.water_quantity)
        form.addRow("Προϊόν λίπανσης", self.product)
        self.dose_row = QHBoxLayout()
        self.dose_row.addWidget(self.dose, 2)
        self.dose_row.addWidget(self.dose_unit, 1)
        form.addRow("Δόση λίπανσης", self.dose_row)
        form.addRow("Είδος αποθήκης", self.inventory_item)
        form.addRow("Κατανάλωση αποθήκης", self.inventory_quantity)
        self.action_hint = QLabel()
        self.action_hint.setStyleSheet(
            "color: #315F49; font-weight: 600; background: transparent;"
        )
        form.addRow("", self.action_hint)
        form.addRow("Κόστος", self.cost)
        form.addRow("Υπεύθυνος", self.responsible)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_activity)
        buttons.addWidget(self.save_button)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.cancel_button)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_activity)
        self.delete_button.setEnabled(False)
        buttons.addWidget(self.delete_button)

        buttons.addStretch()
        form.addRow("", buttons)

        layout.addWidget(self.form_box)

        filters_box = QGroupBox()
        filters_layout = QVBoxLayout(filters_box)

        filters_title = QLabel("Φίλτρα")
        filters_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        filters_layout.addWidget(filters_title)

        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(3, 1)

        self.year_filter = ClickOpenComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)
        filter_grid.addWidget(QLabel("Έτος"), 0, 0)
        filter_grid.addWidget(self.year_filter, 0, 1)

        self.field_filter = ClickOpenComboBox()
        self.field_filter.currentIndexChanged.connect(self.refresh)
        filter_grid.addWidget(QLabel("Αγροτεμάχιο"), 0, 2)
        filter_grid.addWidget(self.field_filter, 0, 3)

        self.category_filter = ClickOpenComboBox()
        self.category_filter.addItem("Όλες", None)
        for category in ACTIVITY_CATEGORIES:
            self.category_filter.addItem(category, category)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        filter_grid.addWidget(QLabel("Τύπος"), 1, 0)
        filter_grid.addWidget(self.category_filter, 1, 1)

        self.status_filter = ClickOpenComboBox()
        self.status_filter.addItem("Όλες", None)
        for status in ACTIVITY_STATUSES:
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        filter_grid.addWidget(QLabel("Κατάσταση"), 1, 2)
        filter_grid.addWidget(self.status_filter, 1, 3)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        filter_grid.addWidget(QLabel("Αναζήτηση"), 2, 0)
        filter_grid.addWidget(self.search, 2, 1, 1, 3)

        for widget in (
            self.year_filter,
            self.field_filter,
            self.category_filter,
            self.status_filter,
            self.search,
        ):
            widget.setMinimumHeight(36)

        filters_layout.addLayout(filter_grid)
        layout.addWidget(filters_box)

        self.summary = QLabel("")
        self.summary.setStyleSheet(
            "font-weight: 700; color: #26382f; padding: 3px 0;"
        )
        layout.addWidget(self.summary)

        self.table = table_widget(
            [
                "Ημερομηνία",
                "Αγροτεμάχιο",
                "Τύπος",
                "Κατάσταση",
                "Στοιχεία",
                "Κόστος",
                "Υπεύθυνος",
                "Σημειώσεις",
            ]
        )
        self.table.cellClicked.connect(self.load_selected)
        self.table.setMinimumHeight(290)

        header = self.table.horizontalHeader()
        for column in (0, 2, 3, 5):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        for column in (1, 4, 6, 7):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.Stretch,
            )

        layout.addWidget(self.table)
        layout.addStretch()

        self._update_action_fields()
        self.refresh()

    def _ensure_schema_and_audit_triggers(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS farm_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_date TEXT NOT NULL,
                field_id INTEGER,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Ολοκληρώθηκε',
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Additive migration for databases created by earlier releases.
        columns = {
            row["name"] for row in self.db.query("PRAGMA table_info(farm_activities)")
        }
        additions = {
            "duration_minutes": "REAL NOT NULL DEFAULT 0",
            "water_quantity_m3": "REAL NOT NULL DEFAULT 0",
            "product": "TEXT NOT NULL DEFAULT ''",
            "dose": "REAL NOT NULL DEFAULT 0",
            "dose_unit": "TEXT NOT NULL DEFAULT ''",
            "cost": "REAL NOT NULL DEFAULT 0",
            "responsible": "TEXT NOT NULL DEFAULT ''",
            "inventory_item_id": "INTEGER",
            "inventory_quantity": "REAL NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.db.execute(
                    f"ALTER TABLE farm_activities ADD COLUMN {name} {definition}"
                )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_farm_activities_date
            ON farm_activities(activity_date)
            """
        )

        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_farm_activities_field
            ON farm_activities(field_id)
            """
        )
        ensure_inventory_source_schema(self.db)

    def _update_action_fields(self, *_args) -> None:
        action_type = self.category.currentData()
        irrigation = action_type == "irrigation"
        fertilization = action_type == "fertilization"
        self.duration.setEnabled(irrigation)
        self.water_quantity.setEnabled(irrigation)
        self.product.setEnabled(fertilization)
        self.dose.setEnabled(fertilization)
        self.dose_unit.setEnabled(fertilization)
        self.inventory_item.setEnabled(fertilization)
        self.inventory_quantity.setEnabled(fertilization)
        form = self.form_box.layout()
        if isinstance(form, QFormLayout):
            form.setRowVisible(self.duration, irrigation)
            form.setRowVisible(self.water_quantity, irrigation)
            form.setRowVisible(self.product, fertilization)
            form.setRowVisible(self.dose_row, fertilization)
            form.setRowVisible(self.inventory_item, fertilization)
            form.setRowVisible(self.inventory_quantity, fertilization)
        if fertilization:
            self.action_hint.setText(
                "Ενεργά πεδία λίπανσης: προϊόν, δόση και μονάδα."
            )
        else:
            self.action_hint.setText(
                "Ενεργά πεδία άρδευσης: διάρκεια και ποσότητα νερού."
            )

    def _refresh_inventory_combo(self) -> None:
        current = self.inventory_item.currentData()
        self.inventory_item.blockSignals(True)
        self.inventory_item.clear()
        self.inventory_item.addItem("— χωρίς αυτόματη κατανάλωση —", None)
        if self.db.query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_items'") is not None:
            for row in self.db.query("SELECT id,name,unit FROM inventory_items ORDER BY name,id"):
                label = row["name"] or f"ID {row['id']}"
                if row["unit"]:
                    label += f" ({row['unit']})"
                self.inventory_item.addItem(label, int(row["id"]))
        index = self.inventory_item.findData(current)
        self.inventory_item.setCurrentIndex(index if index >= 0 else 0)
        self.inventory_item.blockSignals(False)

    def _refresh_product_combo(self) -> None:
        current_text = combo_source_text(self.product).strip()
        self.product.blockSignals(True)
        self.product.clear()
        self.product.addItem("")
        table = self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_items'"
        )
        if table is not None:
            for row in self.db.query(
                """
                SELECT name FROM inventory_items
                WHERE category='Λίπασμα' OR category LIKE '%Λίπαν%'
                ORDER BY name, id
                """
            ):
                self.product.addItem(row["name"] or "")
        if current_text:
            index = self.product.findText(current_text)
            if index >= 0:
                self.product.setCurrentIndex(index)
            else:
                self.product.setEditText(current_text)
        self.product.blockSignals(False)

        audit_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='audit_events'
            """
        )

        if audit_exists is None:
            return

        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_farm_activities_insert
            AFTER INSERT ON farm_activities
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'farm_activities',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.activity_date, '') ||
                    ' | ' || COALESCE(NEW.category, '') ||
                    ' | Κατάσταση: ' || COALESCE(NEW.status, '')
                );
            END
            """
        )
        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_farm_activities_update
            AFTER UPDATE ON farm_activities
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'farm_activities',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.activity_date, '') ||
                    ' | ' || COALESCE(NEW.category, '') ||
                    ' | Κατάσταση: ' || COALESCE(NEW.status, '')
                );
            END
            """
        )
        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_farm_activities_delete
            AFTER DELETE ON farm_activities
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'farm_activities',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(OLD.activity_date, '') ||
                    ' | ' || COALESCE(OLD.category, '')
                );
            END
            """
        )

    def _refresh_field_combos(self) -> None:
        current_form = self.field.currentData()
        current_filter = self.field_filter.currentData()

        fields = self.db.query(
            "SELECT id, name FROM fields ORDER BY name, id"
        )

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Γενική / όλα τα αγροτεμάχια", None)
        for row in fields:
            self.field.addItem(row["name"] or f"ID {row['id']}", row["id"])
        index = self.field.findData(current_form)
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)

        self.field_filter.blockSignals(True)
        self.field_filter.clear()
        self.field_filter.addItem("Όλα", None)
        for row in fields:
            self.field_filter.addItem(
                row["name"] or f"ID {row['id']}",
                row["id"],
            )
        index = self.field_filter.findData(current_filter)
        self.field_filter.setCurrentIndex(index if index >= 0 else 0)
        self.field_filter.blockSignals(False)

    def _refresh_year_filter(self) -> None:
        current = self.year_filter.currentData()
        rows = self.db.query(
            """
            SELECT DISTINCT SUBSTR(activity_date,1,4) AS year
            FROM farm_activities
            WHERE activity_date IS NOT NULL AND activity_date <> ''
            ORDER BY year DESC
            """
        )

        years = {QDate.currentDate().year()}
        for row in rows:
            try:
                years.add(int(row["year"]))
            except (TypeError, ValueError):
                pass

        self.year_filter.blockSignals(True)
        self.year_filter.clear()
        self.year_filter.addItem("Όλα", None)
        for year in sorted(years, reverse=True):
            self.year_filter.addItem(str(year), year)

        index = self.year_filter.findData(current)
        self.year_filter.setCurrentIndex(index if index >= 0 else 0)
        self.year_filter.blockSignals(False)

    def _record_year(self, activity_id: int) -> int | None:
        row = self.db.query_one(
            "SELECT activity_date FROM farm_activities WHERE id=?",
            (activity_id,),
        )
        if row is None:
            return None

        parsed = QDate.fromString(
            row["activity_date"] or "",
            "yyyy-MM-dd",
        )
        return parsed.year() if parsed.isValid() else None

    def _locked_for_save(self) -> bool:
        target_year = self.date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True

        if self.selected_activity_id is not None:
            original_year = self._record_year(
                self.selected_activity_id
            )
            if (
                original_year is not None
                and original_year != target_year
                and is_year_locked(self.db, original_year)
            ):
                warn_locked_year(self, self.db, original_year)
                return True

        return False

    def save_activity(self) -> None:
        if self._locked_for_save():
            return

        category = combo_source_text(self.category).strip()
        status = combo_source_text(self.status).strip()

        if not category:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Συμπλήρωσε το είδος της εργασίας.",
            )
            self.category.setFocus()
            return

        if status not in ACTIVITY_STATUSES:
            status = "Ολοκληρώθηκε"

        irrigation = category == "Πότισμα"
        product = combo_source_text(self.product).strip() if not irrigation else ""
        dose = self.dose.value() if not irrigation else 0
        if not irrigation and (not product or dose <= 0):
            QMessageBox.warning(
                self, "Ελλιπή στοιχεία",
                "Για τη λίπανση συμπλήρωσε προϊόν και δόση μεγαλύτερη από 0.",
            )
            return
        if irrigation and self.duration.value() <= 0 and self.water_quantity.value() <= 0:
            QMessageBox.warning(
                self, "Ελλιπή στοιχεία",
                "Για την άρδευση συμπλήρωσε διάρκεια ή ποσότητα νερού.",
            )
            return

        inventory_item_id = self.inventory_item.currentData() if not irrigation else None
        inventory_quantity = self.inventory_quantity.value() if (not irrigation and status == "Ολοκληρώθηκε") else 0
        if inventory_quantity > 0 and inventory_item_id is None:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Για αυτόματη κατανάλωση επίλεξε είδος αποθήκης.")
            return
        try:
            ensure_can_consume(self.db, item_id=inventory_item_id, quantity=inventory_quantity, source_type="farm_activity", source_id=self.selected_activity_id)
        except InventoryStockError as exc:
            QMessageBox.warning(self, "Ανεπαρκές απόθεμα", f"Δεν υπάρχει αρκετό απόθεμα. Διαθέσιμο: {exc.available:g}")
            return

        values = (
            self.date.date().toString("yyyy-MM-dd"),
            self.field.currentData(),
            category,
            status,
            self.duration.value() if irrigation else 0,
            self.water_quantity.value() if irrigation else 0,
            product,
            dose,
            str(self.dose_unit.currentData() or "") if not irrigation else "",
            self.cost.value(),
            self.responsible.text().strip(),
            self.notes.text().strip(),
            inventory_item_id,
            inventory_quantity,
        )

        if self.selected_activity_id is None:
            record_id = self.db.execute(
                """
                INSERT INTO farm_activities(
                    activity_date,
                    field_id,
                    category,
                    status,
                    duration_minutes,
                    water_quantity_m3,
                    product,
                    dose,
                    dose_unit,
                    cost,
                    responsible,
                    notes,
                    inventory_item_id,
                    inventory_quantity
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
        else:
            self.db.execute(
                """
                UPDATE farm_activities
                SET
                    activity_date=?,
                    field_id=?,
                    category=?,
                    status=?,
                    duration_minutes=?,
                    water_quantity_m3=?,
                    product=?,
                    dose=?,
                    dose_unit=?,
                    cost=?,
                    responsible=?,
                    notes=?,
                    inventory_item_id=?,
                    inventory_quantity=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, self.selected_activity_id),
            )
            record_id = self.selected_activity_id

        sync_consumption(self.db, source_type="farm_activity", source_id=int(record_id), movement_date=self.date.date().toString("yyyy-MM-dd"), item_id=inventory_item_id, quantity=inventory_quantity, field_id=self.field.currentData(), notes=f"Αυτόματη κατανάλωση από Άρδευση & Λίπανση #{record_id}")

        self.clear_form()
        self.refresh()

    def load_selected(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        activity_id = item.data(Qt.ItemDataRole.UserRole)
        if activity_id is None:
            return

        activity = self.db.query_one(
            "SELECT * FROM farm_activities WHERE id=?",
            (activity_id,),
        )
        if activity is None:
            self.refresh()
            return

        self.selected_activity_id = int(activity["id"])

        parsed = QDate.fromString(
            activity["activity_date"] or "",
            "yyyy-MM-dd",
        )
        if parsed.isValid():
            self.date.setDate(parsed)

        field_index = self.field.findData(activity["field_id"])
        self.field.setCurrentIndex(field_index if field_index >= 0 else 0)

        category = activity["category"] or "Πότισμα"
        category_index = self.category.findText(category)
        if category_index >= 0:
            self.category.setCurrentIndex(category_index)
        else:
            self.category.setCurrentIndex(0)

        status = activity["status"] or "Ολοκληρώθηκε"
        status_index = self.status.findText(status)
        self.status.setCurrentIndex(status_index if status_index >= 0 else 1)


        self._update_action_fields()
        self.duration.setValue(float(activity["duration_minutes"] or 0))
        self.water_quantity.setValue(float(activity["water_quantity_m3"] or 0))
        product = activity["product"] or ""
        product_index = self.product.findText(product)
        if product_index >= 0:
            self.product.setCurrentIndex(product_index)
        else:
            self.product.setEditText(product)
        self.dose.setValue(float(activity["dose"] or 0))
        dose_unit = activity["dose_unit"] or "kg"
        unit_index = self.dose_unit.findData(dose_unit)
        if unit_index >= 0:
            self.dose_unit.setCurrentIndex(unit_index)
        self._refresh_inventory_combo()
        inventory_index = self.inventory_item.findData(activity["inventory_item_id"])
        self.inventory_item.setCurrentIndex(inventory_index if inventory_index >= 0 else 0)
        self.inventory_quantity.setValue(float(activity["inventory_quantity"] or 0))
        self.cost.setValue(float(activity["cost"] or 0))
        self.responsible.setText(activity["responsible"] or "")
        self.notes.setText(activity["notes"] or "")

        record_year = parsed.year() if parsed.isValid() else None
        locked = (
            record_year is not None
            and is_year_locked(self.db, record_year)
        )

        if locked:
            self.form_box.setTitle(
                f"Προβολή καταγραφής — ΚΛΕΙΔΩΜΕΝΟ {record_year}"
            )
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.form_box.setTitle("Επεξεργασία καταγραφής")
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_activity_id = None
        self.date.setDate(QDate.currentDate())
        self.field.setCurrentIndex(0)
        self.category.setCurrentIndex(0)
        self.status.setCurrentText("Ολοκληρώθηκε")
        self.duration.setValue(0)
        self.water_quantity.setValue(0)
        self.product.setCurrentIndex(0)
        self.dose.setValue(0)
        self.dose_unit.setCurrentIndex(0)
        self._refresh_inventory_combo()
        self.inventory_item.setCurrentIndex(0)
        self.inventory_quantity.setValue(0)
        self.cost.setValue(0)
        self.responsible.clear()
        self.notes.clear()
        self._update_action_fields()

        self.form_box.setTitle("Νέα καταγραφή")
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()

    def delete_activity(self) -> None:
        if self.selected_activity_id is None:
            return

        record_year = self._record_year(self.selected_activity_id)
        if (
            record_year is not None
            and is_year_locked(self.db, record_year)
        ):
            warn_locked_year(self, self.db, record_year)
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή καταγραφής",
            "Να διαγραφεί η επιλεγμένη καταγραφή άρδευσης ή λίπανσης;",
        ):
            return

        delete_consumption(self.db, source_type="farm_activity", source_id=self.selected_activity_id)
        self.db.execute(
            "DELETE FROM farm_activities WHERE id=?",
            (self.selected_activity_id,),
        )
        self.clear_form()
        self.refresh()

    def refresh(self, *_args) -> None:
        self._ensure_schema_and_audit_triggers()
        self._refresh_field_combos()
        self._refresh_product_combo()
        self._refresh_inventory_combo()
        self._refresh_year_filter()

        where = ["1=1"]
        params: list[object] = []

        year = self.year_filter.currentData()
        if year is not None:
            where.append("SUBSTR(a.activity_date,1,4)=?")
            params.append(str(year))

        field_id = self.field_filter.currentData()
        if field_id is not None:
            where.append("a.field_id=?")
            params.append(field_id)

        category = self.category_filter.currentData()
        if category:
            where.append("a.category=?")
            params.append(category)

        status = self.status_filter.currentData()
        if status:
            where.append("a.status=?")
            params.append(status)

        search = self.search.text().strip()
        if search:
            where.append(
                """
                (
                    a.category LIKE ?
                    OR a.product LIKE ?
                    OR a.responsible LIKE ?
                    OR a.notes LIKE ?
                    OR COALESCE(f.name,'') LIKE ?
                )
                """
            )
            token = f"%{search}%"
            params.extend([token, token, token, token, token])

        rows = self.db.query(
            f"""
            SELECT
                a.*,
                COALESCE(f.name, '') AS field_name
            FROM farm_activities a
            LEFT JOIN fields f ON f.id=a.field_id
            WHERE {' AND '.join(where)}
            ORDER BY a.activity_date DESC, a.id DESC
            """,
            tuple(params),
        )

        self.table.setRowCount(len(rows))

        planned = 0
        completed = 0

        for row_index, row in enumerate(rows):
            status_value = row["status"] or ""
            if status_value == "Προγραμματισμένη":
                planned += 1
            elif status_value == "Ολοκληρώθηκε":
                completed += 1

            field_name = row["field_name"] or "Γενική / όλα"

            if row["category"] == "Πότισμα":
                details = (
                    f"{float(row['duration_minutes'] or 0):g} λεπτά | "
                    f"{float(row['water_quantity_m3'] or 0):g} m³"
                )
            elif row["category"] == "Λίπανση":
                details = (
                    f"{row['product'] or '—'} | "
                    f"{float(row['dose'] or 0):g} {row['dose_unit'] or ''}"
                ).strip()
            else:
                details = row["description"] or ""

            values = [
                row["activity_date"] or "",
                field_name,
                row["category"] or "",
                status_value,
                details,
                f"{float(row['cost'] or 0):.2f} €",
                row["responsible"] or "",
                row["notes"] or "",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column_index == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                if column_index in (4, 6, 7):
                    item.setToolTip(str(value))
                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.summary.setText(
            f"Εγγραφές: {len(rows)}   |   "
            f"Προγραμματισμένες: {planned}   |   "
            f"Ολοκληρωμένες: {completed}"
        )
