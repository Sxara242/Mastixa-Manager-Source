from __future__ import annotations

from PySide6.QtCore import QDate, QEvent, QTimer, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFormLayout,
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
from .inventory_sync import ensure_inventory_source_schema
from .expense_sync import delete_expense, ensure_expense_source_schema, sync_expense
from .partner_links import PartnerComboBox, canonical_partner_name, ensure_partner_link_schema


ITEM_CATEGORIES = [
    "Λίπασμα",
    "Φυτοπροστασία",
    "Καύσιμα",
    "Υλικά συσκευασίας",
    "Εργαλεία / Αναλώσιμα",
    "Άλλο",
]

UNITS = [
    "kg",
    "L",
    "τεμ.",
    "m",
    "m²",
    "συσκ.",
    "Άλλο",
]

MOVEMENT_TYPES = [
    "Παραλαβή",
    "Κατανάλωση",
    "Διόρθωση +",
    "Διόρθωση -",
]


class ClickOpenComboBox(QComboBox):
    """Opens the popup when the user clicks anywhere on the control."""

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
            QTimer.singleShot(0, self.showPopup)
        return super().eventFilter(watched, event)


class ClickOpenDateEdit(QDateEdit):
    """Opens the standard Qt calendar popup from a click anywhere."""

    def __init__(self) -> None:
        super().__init__()
        self.setCalendarPopup(True)
        editor = self.lineEdit()
        if editor is not None:
            editor.installEventFilter(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # QDateEdit normally opens the calendar only from the arrow.
            # Simulate the arrow click through the protected popup behavior.
            self.setFocus()
            self.findChild(QWidget, "qt_calendar_calendarview")
            QTimer.singleShot(0, self._open_calendar_popup)
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
            QTimer.singleShot(0, self._open_calendar_popup)
            return False
        return super().eventFilter(watched, event)

    def _open_calendar_popup(self) -> None:
        # Qt has no public showCalendar() method. Sending Alt+Down is not
        # portable, so use the built-in calendarPopup by focusing the control
        # and invoking its menu through a synthetic mouse press at the arrow.
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        point = QPoint(max(1, self.width() - 8), self.height() // 2)
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            point,
            self.mapToGlobal(point),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        super().mousePressEvent(event)


class InventoryPage(CrudPage):
    """Αποθήκη εφοδίων και κινήσεις αποθέματος."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_item_id: int | None = None
        self.selected_movement_id: int | None = None

        self._ensure_schema_and_audit_triggers()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("inventoryScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setStyleSheet(
            """
            QScrollArea#inventoryScroll {
                border: none;
                background: #f5f6f3;
            }
            QScrollArea#inventoryScroll QWidget#qt_scrollarea_viewport {
                background: #f5f6f3;
            }
            QWidget#inventoryContent {
                background: #f5f6f3;
            }
            """
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("inventoryContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)

        title = QLabel("Αποθήκη & Εφόδια")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Παρακολούθηση λιπασμάτων, υλικών, αναλωσίμων και κινήσεων αποθέματος"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        summary = QHBoxLayout()
        self.items_metric = self._metric_card("Είδη", "0")
        self.low_metric = self._metric_card("Χαμηλό απόθεμα", "0")
        self.zero_metric = self._metric_card("Εξαντλημένα", "0")
        for card, _label in (
            self.items_metric,
            self.low_metric,
            self.zero_metric,
        ):
            summary.addWidget(card, 1)
        layout.addLayout(summary)

        # ---------------------------------------------------------
        # Master item form
        # ---------------------------------------------------------
        self.item_box = QGroupBox("Νέο είδος αποθήκης")
        item_form = QFormLayout(self.item_box)

        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("Π.χ. Λίπασμα 20-10-10")

        self.item_category = ClickOpenComboBox()
        self.item_category.setEditable(True)
        self.item_category.setProperty("mastixaI18nStaticItems", True)
        self.item_category.addItems(ITEM_CATEGORIES)

        self.item_unit = ClickOpenComboBox()
        self.item_unit.setEditable(True)
        self.item_unit.setProperty("mastixaI18nStaticItems", True)
        self.item_unit.addItems(UNITS)

        self.minimum_stock = QLineEdit("0")
        self.minimum_stock.setValidator(
            QDoubleValidator(0.0, 999999999.0, 3, self.minimum_stock)
        )
        self.minimum_stock.setPlaceholderText("0")

        self.initial_stock = QLineEdit("0")
        self.initial_stock.setValidator(
            QDoubleValidator(0.0, 999999999.0, 3, self.initial_stock)
        )
        self.initial_stock.setPlaceholderText("0")
        self.initial_stock_label = QLabel("Αρχικό απόθεμα")

        self.item_notes = QLineEdit()
        self.item_notes.setPlaceholderText("Προαιρετικές σημειώσεις")

        item_form.addRow("Είδος", self.item_name)
        item_form.addRow("Κατηγορία", self.item_category)
        item_form.addRow("Μονάδα", self.item_unit)
        item_form.addRow("Ελάχιστο απόθεμα", self.minimum_stock)
        item_form.addRow(self.initial_stock_label, self.initial_stock)
        item_form.addRow("Σημειώσεις", self.item_notes)

        initial_stock_help = QLabel(
            "Το αρχικό απόθεμα χρησιμοποιείται μόνο όταν δημιουργείς νέο είδος. "
            "Μετά, το απόθεμα αλλάζει από τις Κινήσεις Αποθήκης."
        )
        initial_stock_help.setWordWrap(True)
        initial_stock_help.setStyleSheet(
            "color: #66766E; font-size: 12px; background: transparent;"
        )
        item_form.addRow("", initial_stock_help)

        item_buttons = QHBoxLayout()
        self.item_save_button = QPushButton("Προσθήκη είδους")
        self.item_save_button.clicked.connect(self.save_item)
        item_buttons.addWidget(self.item_save_button)

        self.item_cancel_button = QPushButton("Ακύρωση")
        self.item_cancel_button.clicked.connect(self.clear_item_form)
        self.item_cancel_button.setEnabled(False)
        item_buttons.addWidget(self.item_cancel_button)

        self.item_delete_button = QPushButton("Διαγραφή")
        self.item_delete_button.clicked.connect(self.delete_item)
        self.item_delete_button.setEnabled(False)
        item_buttons.addWidget(self.item_delete_button)
        item_buttons.addStretch()
        item_form.addRow("", item_buttons)

        inventory_button_style = """
            QPushButton {
                background: #3F765B;
                color: #FFFFFF;
                border: 1px solid #35664F;
                border-radius: 7px;
                padding: 9px 17px;
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
            self.item_save_button,
            self.item_cancel_button,
            self.item_delete_button,
        ):
            button.setStyleSheet(inventory_button_style)

        layout.addWidget(self.item_box)

        stock_box = QGroupBox()
        stock_layout = QVBoxLayout(stock_box)
        stock_title = QLabel("Τρέχον απόθεμα")
        stock_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        stock_layout.addWidget(stock_title)

        stock_filter_row = QHBoxLayout()
        self.stock_search = QLineEdit()
        self.stock_search.setPlaceholderText("Αναζήτηση είδους / κατηγορίας...")
        self.stock_search.setClearButtonEnabled(True)
        self.stock_search.textChanged.connect(self.refresh)
        stock_filter_row.addWidget(self.stock_search, 1)

        self.low_only = QComboBox()
        self.low_only.addItem("Όλα τα είδη", None)
        self.low_only.addItem("Μόνο χαμηλό / εξαντλημένο", "low")
        self.low_only.currentIndexChanged.connect(self.refresh)
        stock_filter_row.addWidget(self.low_only)
        stock_layout.addLayout(stock_filter_row)

        self.stock_table = table_widget(
            [
                "Είδος",
                "Κατηγορία",
                "Μονάδα",
                "Απόθεμα",
                "Ελάχιστο",
                "Κατάσταση",
            ]
        )
        self.stock_table.cellClicked.connect(self.load_item)
        self.stock_table.setMinimumHeight(220)
        stock_header = self.stock_table.horizontalHeader()
        stock_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        stock_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in (2, 3, 4, 5):
            stock_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        stock_layout.addWidget(self.stock_table)
        layout.addWidget(stock_box)

        # ---------------------------------------------------------
        # Movement form
        # ---------------------------------------------------------
        self.movement_box = QGroupBox("Νέα κίνηση αποθήκης")
        movement_form = QFormLayout(self.movement_box)

        self.movement_date = QDateEdit(QDate.currentDate())
        self.movement_date.setCalendarPopup(True)
        self.movement_date.setDisplayFormat("dd/MM/yyyy")

        self.movement_item = ClickOpenComboBox()
        self.movement_type = ClickOpenComboBox()
        self.movement_type.addItems(MOVEMENT_TYPES)

        self.movement_quantity = QLineEdit()
        self.movement_quantity.setValidator(
            QDoubleValidator(0.001, 999999999.0, 3, self.movement_quantity)
        )
        self.movement_quantity.setPlaceholderText("Ποσότητα")

        self.movement_field = ClickOpenComboBox()

        self.movement_supplier = PartnerComboBox(
            self.db,
            role="supplier",
        )
        self.movement_supplier.setPlaceholderText(
            "Προαιρετικός προμηθευτής"
        )

        self.movement_unit_price = QLineEdit()
        self.movement_unit_price.setValidator(
            QDoubleValidator(
                0.0,
                999999999.0,
                2,
                self.movement_unit_price,
            )
        )
        self.movement_unit_price.setPlaceholderText(
            "Τιμή ανά μονάδα"
        )
        self.movement_unit_price.textChanged.connect(
            self._update_receipt_total
        )
        self.movement_quantity.textChanged.connect(
            self._update_receipt_total
        )

        self.movement_total_cost = QLabel("0 €")
        self.movement_total_cost.setStyleSheet(
            "font-weight: 700; color: #315F49;"
        )

        self.movement_notes = QLineEdit()
        self.movement_notes.setPlaceholderText("Προαιρετικές σημειώσεις")

        movement_form.addRow("Ημερομηνία", self.movement_date)
        movement_form.addRow("Είδος", self.movement_item)
        movement_form.addRow("Κίνηση", self.movement_type)
        movement_form.addRow("Ποσότητα", self.movement_quantity)
        movement_form.addRow("Αγροτεμάχιο", self.movement_field)
        movement_form.addRow("Προμηθευτής", self.movement_supplier)
        movement_form.addRow("Τιμή μονάδας", self.movement_unit_price)
        movement_form.addRow("Συνολικό κόστος αγοράς", self.movement_total_cost)
        movement_form.addRow("Σημειώσεις", self.movement_notes)

        self.movement_type.currentTextChanged.connect(
            self._update_receipt_fields_visibility
        )

        movement_buttons = QHBoxLayout()
        self.movement_save_button = QPushButton("Προσθήκη κίνησης")
        self.movement_save_button.clicked.connect(self.save_movement)
        movement_buttons.addWidget(self.movement_save_button)

        self.movement_cancel_button = QPushButton("Ακύρωση")
        self.movement_cancel_button.clicked.connect(self.clear_movement_form)
        self.movement_cancel_button.setEnabled(False)
        movement_buttons.addWidget(self.movement_cancel_button)

        self.movement_delete_button = QPushButton("Διαγραφή")
        self.movement_delete_button.clicked.connect(self.delete_movement)
        self.movement_delete_button.setEnabled(False)
        movement_buttons.addWidget(self.movement_delete_button)
        movement_buttons.addStretch()
        movement_form.addRow("", movement_buttons)

        for button in (
            self.movement_save_button,
            self.movement_cancel_button,
            self.movement_delete_button,
        ):
            button.setStyleSheet(inventory_button_style)

        layout.addWidget(self.movement_box)

        movement_list_box = QGroupBox()
        movement_list_layout = QVBoxLayout(movement_list_box)
        movement_title = QLabel("Ιστορικό κινήσεων")
        movement_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        movement_list_layout.addWidget(movement_title)

        filters = QGridLayout()
        filters.setColumnStretch(1, 1)
        filters.setColumnStretch(3, 1)

        self.year_filter = ClickOpenComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Έτος"), 0, 0)
        filters.addWidget(self.year_filter, 0, 1)

        self.item_filter = ClickOpenComboBox()
        self.item_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Είδος"), 0, 2)
        filters.addWidget(self.item_filter, 0, 3)

        self.type_filter = ClickOpenComboBox()
        self.type_filter.addItem("Όλες", None)
        for movement_type in MOVEMENT_TYPES:
            self.type_filter.addItem(movement_type, movement_type)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Κίνηση"), 1, 0)
        filters.addWidget(self.type_filter, 1, 1)

        self.movement_search = QLineEdit()
        self.movement_search.setPlaceholderText("Αναζήτηση...")
        self.movement_search.setClearButtonEnabled(True)
        self.movement_search.textChanged.connect(self.refresh)
        filters.addWidget(QLabel("Αναζήτηση"), 1, 2)
        filters.addWidget(self.movement_search, 1, 3)

        movement_list_layout.addLayout(filters)

        self.movement_table = table_widget(
            [
                "Ημερομηνία",
                "Είδος",
                "Κίνηση",
                "Ποσότητα",
                "Μονάδα",
                "Αγροτεμάχιο",
                "Σημειώσεις",
            ]
        )
        self.movement_table.cellClicked.connect(self.load_movement)
        self.movement_table.setMinimumHeight(260)
        movement_header = self.movement_table.horizontalHeader()
        for column in (0, 2, 3, 4):
            movement_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        for column in (1, 5, 6):
            movement_header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.Stretch
            )
        movement_list_layout.addWidget(self.movement_table)

        layout.addWidget(movement_list_box)
        layout.addStretch()

        self.refresh()

    def _metric_card(self, caption: str, value: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        card_layout = QVBoxLayout(box)
        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")
        card_layout.addWidget(caption_label)
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        card_layout.addWidget(value_label)
        return box, value_label

    @staticmethod
    def _to_float(text: str) -> float | None:
        value = text.strip().replace(",", ".")
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _fmt(value: float) -> str:
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text or "0"

    def _ensure_schema_and_audit_triggers(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT '',
                minimum_stock REAL NOT NULL DEFAULT 0,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_date TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                field_id INTEGER,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_inventory_movements_date
            ON inventory_movements(movement_date)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_inventory_movements_item
            ON inventory_movements(item_id)
            """
        )
        ensure_inventory_source_schema(self.db)
        ensure_expense_source_schema(self.db)
        ensure_partner_link_schema(self.db)

        movement_columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(inventory_movements)"
            )
        }

        additions = {
            "partner_id": "INTEGER",
            "supplier_name": "TEXT NOT NULL DEFAULT ''",
            "unit_price": "REAL NOT NULL DEFAULT 0",
            "total_cost": "REAL NOT NULL DEFAULT 0",
            "expense_id": "INTEGER",
        }

        for name, definition in additions.items():
            if name not in movement_columns:
                self.db.execute(
                    f"ALTER TABLE inventory_movements ADD COLUMN {name} {definition}"
                )

        self.db.execute(
            '''
            CREATE INDEX IF NOT EXISTS idx_inventory_movements_partner
            ON inventory_movements(partner_id)
            '''
        )

        audit_exists = self.db.query_one(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='audit_events'
            """
        )
        if audit_exists is None:
            return

        triggers = [
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_items_insert
            AFTER INSERT ON inventory_items
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_items', 'INSERT', CAST(NEW.id AS TEXT),
                    'Είδος: ' || COALESCE(NEW.name,'') ||
                    ' | Μονάδα: ' || COALESCE(NEW.unit,'')
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_items_update
            AFTER UPDATE ON inventory_items
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_items', 'UPDATE', CAST(NEW.id AS TEXT),
                    'Είδος: ' || COALESCE(NEW.name,'') ||
                    ' | Μονάδα: ' || COALESCE(NEW.unit,'')
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_items_delete
            AFTER DELETE ON inventory_items
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_items', 'DELETE', CAST(OLD.id AS TEXT),
                    'Είδος: ' || COALESCE(OLD.name,'')
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_movements_insert
            AFTER INSERT ON inventory_movements
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_movements', 'INSERT', CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.movement_date,'') ||
                    ' | Είδος ID: ' || CAST(NEW.item_id AS TEXT) ||
                    ' | ' || COALESCE(NEW.movement_type,'') ||
                    ' | Ποσότητα: ' || CAST(ROUND(NEW.quantity,3) AS TEXT)
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_movements_update
            AFTER UPDATE ON inventory_movements
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_movements', 'UPDATE', CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.movement_date,'') ||
                    ' | Είδος ID: ' || CAST(NEW.item_id AS TEXT) ||
                    ' | ' || COALESCE(NEW.movement_type,'') ||
                    ' | Ποσότητα: ' || CAST(ROUND(NEW.quantity,3) AS TEXT)
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_inventory_movements_delete
            AFTER DELETE ON inventory_movements
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                ) VALUES(
                    datetime('now','localtime'),
                    'inventory_movements', 'DELETE', CAST(OLD.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(OLD.movement_date,'') ||
                    ' | Είδος ID: ' || CAST(OLD.item_id AS TEXT) ||
                    ' | ' || COALESCE(OLD.movement_type,'')
                );
            END
            """,
        ]
        for sql in triggers:
            self.db.execute(sql)

    def _stock_rows(self):
        return self.db.query(
            """
            SELECT
                i.*,
                COALESCE(SUM(
                    CASE
                        WHEN m.movement_type IN ('Παραλαβή','Διόρθωση +')
                            THEN m.quantity
                        WHEN m.movement_type IN ('Κατανάλωση','Διόρθωση -')
                            THEN -m.quantity
                        ELSE 0
                    END
                ),0) AS current_stock
            FROM inventory_items i
            LEFT JOIN inventory_movements m ON m.item_id=i.id
            GROUP BY i.id
            ORDER BY i.name, i.id
            """
        )

    def _current_stock(self, item_id: int, exclude_movement_id: int | None = None) -> float:
        where = ["item_id=?"]
        params: list[object] = [item_id]
        if exclude_movement_id is not None:
            where.append("id<>?")
            params.append(exclude_movement_id)
        row = self.db.query_one(
            f"""
            SELECT COALESCE(SUM(
                CASE
                    WHEN movement_type IN ('Παραλαβή','Διόρθωση +') THEN quantity
                    WHEN movement_type IN ('Κατανάλωση','Διόρθωση -') THEN -quantity
                    ELSE 0
                END
            ),0) AS stock
            FROM inventory_movements
            WHERE {' AND '.join(where)}
            """,
            tuple(params),
        )
        return float(row["stock"] if row else 0)

    def _refresh_combos(self) -> None:
        items = self.db.query(
            "SELECT id, name, unit FROM inventory_items ORDER BY name, id"
        )
        fields = self.db.query("SELECT id, name FROM fields ORDER BY name, id")

        current_item = self.movement_item.currentData()
        current_filter = self.item_filter.currentData()

        self.movement_item.blockSignals(True)
        self.movement_item.clear()
        self.movement_item.addItem("— επίλεξε είδος —", None)
        for row in items:
            label = row["name"] or f"ID {row['id']}"
            unit = row["unit"] or ""
            if unit:
                label += f" ({unit})"
            self.movement_item.addItem(label, row["id"])
        idx = self.movement_item.findData(current_item)
        self.movement_item.setCurrentIndex(idx if idx >= 0 else 0)
        self.movement_item.blockSignals(False)

        self.item_filter.blockSignals(True)
        self.item_filter.clear()
        self.item_filter.addItem("Όλα", None)
        for row in items:
            self.item_filter.addItem(row["name"] or f"ID {row['id']}", row["id"])
        idx = self.item_filter.findData(current_filter)
        self.item_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.item_filter.blockSignals(False)

        current_field = self.movement_field.currentData()
        self.movement_field.blockSignals(True)
        self.movement_field.clear()
        self.movement_field.addItem("Γενική / χωρίς αγροτεμάχιο", None)
        for row in fields:
            self.movement_field.addItem(row["name"] or f"ID {row['id']}", row["id"])
        idx = self.movement_field.findData(current_field)
        self.movement_field.setCurrentIndex(idx if idx >= 0 else 0)
        self.movement_field.blockSignals(False)

    def _refresh_years(self) -> None:
        current = self.year_filter.currentData()
        rows = self.db.query(
            """
            SELECT DISTINCT SUBSTR(movement_date,1,4) AS year
            FROM inventory_movements
            WHERE movement_date IS NOT NULL AND movement_date<>''
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
        idx = self.year_filter.findData(current)
        self.year_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.year_filter.blockSignals(False)

    def save_item(self) -> None:
        name = self.item_name.text().strip()
        category = combo_source_text(self.item_category).strip()
        unit = combo_source_text(self.item_unit).strip()
        minimum = self._to_float(self.minimum_stock.text())
        initial_stock = self._to_float(self.initial_stock.text())

        if not name:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Συμπλήρωσε το είδος.")
            self.item_name.setFocus()
            return
        if not unit:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Συμπλήρωσε τη μονάδα.")
            self.item_unit.setFocus()
            return
        if minimum is None or minimum < 0:
            QMessageBox.warning(
                self, "Ελλιπή στοιχεία", "Το ελάχιστο απόθεμα πρέπει να είναι 0 ή μεγαλύτερο."
            )
            self.minimum_stock.setFocus()
            return

        if initial_stock is None or initial_stock < 0:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Το αρχικό απόθεμα πρέπει να είναι 0 ή μεγαλύτερο.",
            )
            self.initial_stock.setFocus()
            return

        if (
            self.selected_item_id is None
            and initial_stock > 0
            and is_year_locked(self.db, QDate.currentDate().year())
        ):
            warn_locked_year(
                self,
                self.db,
                QDate.currentDate().year(),
            )
            return

        duplicate = self.db.query_one(
            """
            SELECT id FROM inventory_items
            WHERE LOWER(TRIM(name))=LOWER(TRIM(?)) AND id<>COALESCE(?, -1)
            """,
            (name, self.selected_item_id),
        )
        if duplicate is not None:
            QMessageBox.warning(
                self, "Διπλό είδος", "Υπάρχει ήδη είδος με την ίδια ονομασία."
            )
            return

        values = (name, category, unit, minimum, self.item_notes.text().strip())

        if self.selected_item_id is None:
            self.db.execute(
                """
                INSERT INTO inventory_items(name, category, unit, minimum_stock, notes)
                VALUES(?,?,?,?,?)
                """,
                values,
            )

            inserted = self.db.query_one(
                """
                SELECT id
                FROM inventory_items
                WHERE LOWER(TRIM(name))=LOWER(TRIM(?))
                ORDER BY id DESC
                LIMIT 1
                """,
                (name,),
            )

            if inserted is not None and initial_stock > 0:
                self.db.execute(
                    """
                    INSERT INTO inventory_movements(
                        movement_date,
                        item_id,
                        movement_type,
                        quantity,
                        field_id,
                        notes
                    )
                    VALUES(?, ?, 'Διόρθωση +', ?, NULL, ?)
                    """,
                    (
                        QDate.currentDate().toString("yyyy-MM-dd"),
                        int(inserted["id"]),
                        initial_stock,
                        "Αρχικό απόθεμα κατά τη δημιουργία είδους",
                    ),
                )
        else:
            self.db.execute(
                """
                UPDATE inventory_items
                SET name=?, category=?, unit=?, minimum_stock=?, notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, self.selected_item_id),
            )

        self.clear_item_form()
        self.refresh()

    def load_item(self, row: int, _column: int) -> None:
        item = self.stock_table.item(row, 0)
        if item is None:
            return
        item_id = item.data(Qt.ItemDataRole.UserRole)
        if item_id is None:
            return
        record = self.db.query_one("SELECT * FROM inventory_items WHERE id=?", (item_id,))
        if record is None:
            self.refresh()
            return

        self.selected_item_id = int(record["id"])
        self.item_name.setText(record["name"] or "")
        self.item_category.setEditText(record["category"] or "")
        self.item_unit.setEditText(record["unit"] or "")
        self.minimum_stock.setText(self._fmt(float(record["minimum_stock"] or 0)))

        current_stock = self._current_stock(self.selected_item_id)
        self.initial_stock.setText(self._fmt(current_stock))
        self.initial_stock.setReadOnly(True)
        self.initial_stock.setToolTip(
            "Το τρέχον απόθεμα αλλάζει μόνο από τις Κινήσεις Αποθήκης."
        )
        self.initial_stock_label.setText("Τρέχον απόθεμα")

        self.item_notes.setText(record["notes"] or "")
        self.item_box.setTitle("Επεξεργασία είδους")
        self.item_save_button.setText("Αποθήκευση")
        self.item_cancel_button.setEnabled(True)
        self.item_delete_button.setEnabled(True)

    def clear_item_form(self) -> None:
        self.selected_item_id = None
        self.item_name.clear()
        self.item_category.setCurrentIndex(0)
        self.item_unit.setCurrentIndex(0)
        self.minimum_stock.setText("0")
        self.initial_stock.setReadOnly(False)
        self.initial_stock.setText("0")
        self.initial_stock.setToolTip("")
        self.initial_stock_label.setText("Αρχικό απόθεμα")
        self.item_notes.clear()
        self.item_box.setTitle("Νέο είδος αποθήκης")
        self.item_save_button.setText("Προσθήκη είδους")
        self.item_cancel_button.setEnabled(False)
        self.item_delete_button.setEnabled(False)
        self.stock_table.clearSelection()

    def delete_item(self) -> None:
        if self.selected_item_id is None:
            return
        count = self.db.query_one(
            "SELECT COUNT(*) AS total FROM inventory_movements WHERE item_id=?",
            (self.selected_item_id,),
        )
        if count is not None and int(count["total"] or 0) > 0:
            QMessageBox.warning(
                self,
                "Δεν επιτρέπεται διαγραφή",
                "Το είδος έχει ιστορικό κινήσεων. Δεν διαγράφεται για να μη χαθεί το ιστορικό.",
            )
            return
        if not self.confirm_delete(
            self, "Διαγραφή είδους", "Να διαγραφεί το επιλεγμένο είδος αποθήκης;"
        ):
            return
        self.db.execute("DELETE FROM inventory_items WHERE id=?", (self.selected_item_id,))
        self.clear_item_form()
        self.refresh()

    def _movement_record_year(self, movement_id: int) -> int | None:
        row = self.db.query_one(
            "SELECT movement_date FROM inventory_movements WHERE id=?", (movement_id,)
        )
        if row is None:
            return None
        parsed = QDate.fromString(row["movement_date"] or "", "yyyy-MM-dd")
        return parsed.year() if parsed.isValid() else None

    def _movement_locked_for_save(self) -> bool:
        target_year = self.movement_date.date().year()
        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True
        if self.selected_movement_id is not None:
            original_year = self._movement_record_year(self.selected_movement_id)
            if (
                original_year is not None
                and original_year != target_year
                and is_year_locked(self.db, original_year)
            ):
                warn_locked_year(self, self.db, original_year)
                return True
        return False

    @staticmethod
    def _signed_quantity(movement_type: str, quantity: float) -> float:
        if movement_type in ("Παραλαβή", "Διόρθωση +"):
            return quantity
        if movement_type in ("Κατανάλωση", "Διόρθωση -"):
            return -quantity
        return 0.0

    @staticmethod
    def _money(value: float) -> str:
        text = (
            f"{float(value):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        return f"{text} €"

    def _update_receipt_fields_visibility(self, *_args) -> None:
        receipt = combo_source_text(self.movement_type).strip() == "Παραλαβή"

        self.movement_supplier.setEnabled(receipt)
        self.movement_unit_price.setEnabled(receipt)

        form = self.movement_box.layout()
        if isinstance(form, QFormLayout):
            form.setRowVisible(
                self.movement_supplier,
                receipt,
            )
            form.setRowVisible(
                self.movement_unit_price,
                receipt,
            )
            form.setRowVisible(
                self.movement_total_cost,
                receipt,
            )

        if not receipt:
            self.movement_supplier.setText("")
            self.movement_unit_price.clear()
            self.movement_total_cost.setText("0 €")

    def _update_receipt_total(self, *_args) -> None:
        quantity = self._to_float(
            self.movement_quantity.text()
        ) or 0.0
        unit_price = self._to_float(
            self.movement_unit_price.text()
        ) or 0.0

        self.movement_total_cost.setText(
            self._money(quantity * unit_price)
        )

    def save_movement(self) -> None:
        if self._movement_locked_for_save():
            return

        item_id = self.movement_item.currentData()
        movement_type = combo_source_text(self.movement_type).strip()
        quantity = self._to_float(self.movement_quantity.text())

        if item_id is None:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Επίλεξε είδος αποθήκης.")
            self.movement_item.setFocus()
            return
        if movement_type not in MOVEMENT_TYPES:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Επίλεξε έγκυρο τύπο κίνησης.")
            return
        if quantity is None or quantity <= 0:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Η ποσότητα πρέπει να είναι μεγαλύτερη από 0.")
            self.movement_quantity.setFocus()
            return

        stock_without_current = self._current_stock(
            int(item_id), self.selected_movement_id
        )
        projected = stock_without_current + self._signed_quantity(movement_type, quantity)
        if projected < -0.000001:
            QMessageBox.warning(
                self,
                "Ανεπαρκές απόθεμα",
                "Η κίνηση θα έκανε το απόθεμα αρνητικό.\n\n"
                f"Διαθέσιμο πριν την κίνηση: {self._fmt(stock_without_current)}",
            )
            return

        receipt = movement_type == "Παραλαβή"
        partner_id = (
            self.movement_supplier.selected_partner_id()
            if receipt
            else None
        )
        supplier_name = (
            canonical_partner_name(
                self.db,
                partner_id,
                self.movement_supplier.text(),
            )
            if receipt
            else ""
        )
        unit_price = (
            self._to_float(
                self.movement_unit_price.text()
            ) or 0.0
        ) if receipt else 0.0
        total_cost = quantity * unit_price if receipt else 0.0

        values = (
            self.movement_date.date().toString("yyyy-MM-dd"),
            int(item_id),
            movement_type,
            quantity,
            self.movement_field.currentData(),
            self.movement_notes.text().strip(),
            partner_id,
            supplier_name,
            unit_price,
            total_cost,
        )

        if self.selected_movement_id is None:
            movement_id = int(
                self.db.execute(
                    """
                    INSERT INTO inventory_movements(
                        movement_date,
                        item_id,
                        movement_type,
                        quantity,
                        field_id,
                        notes,
                        partner_id,
                        supplier_name,
                        unit_price,
                        total_cost
                    )
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    """,
                    values,
                )
            )
        else:
            movement_id = self.selected_movement_id
            self.db.execute(
                """
                UPDATE inventory_movements
                SET
                    movement_date=?,
                    item_id=?,
                    movement_type=?,
                    quantity=?,
                    field_id=?,
                    notes=?,
                    partner_id=?,
                    supplier_name=?,
                    unit_price=?,
                    total_cost=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, movement_id),
            )

        item_row = self.db.query_one(
            "SELECT name FROM inventory_items WHERE id=?",
            (int(item_id),),
        )
        item_name = (
            item_row["name"]
            if item_row
            else f"Είδος #{item_id}"
        )

        expense_id = sync_expense(
            self.db,
            source_type="inventory_receipt",
            source_id=int(movement_id),
            entry_date=self.movement_date.date().toString(
                "yyyy-MM-dd"
            ),
            category="Αποθήκη & Εφόδια",
            description=f"Παραλαβή αποθήκης — {item_name}",
            supplier=supplier_name,
            payment_method="",
            amount=total_cost,
            notes=(
                f"Αυτόματο έξοδο από παραλαβή αποθήκης #{movement_id}"
                + (
                    f" | {self.movement_notes.text().strip()}"
                    if self.movement_notes.text().strip()
                    else ""
                )
            ),
            partner_id=partner_id,
        )

        self.db.execute(
            """
            UPDATE inventory_movements
            SET expense_id=?
            WHERE id=?
            """,
            (expense_id, movement_id),
        )

        self.clear_movement_form()
        self.refresh()

    def load_movement(self, row: int, _column: int) -> None:
        item = self.movement_table.item(row, 0)
        if item is None:
            return
        movement_id = item.data(Qt.ItemDataRole.UserRole)
        if movement_id is None:
            return
        record = self.db.query_one(
            "SELECT * FROM inventory_movements WHERE id=?", (movement_id,)
        )
        if record is None:
            self.refresh()
            return

        self.selected_movement_id = int(record["id"])
        automatic_source = (
            "source_type" in record.keys()
            and bool(record["source_type"])
        )

        parsed = QDate.fromString(record["movement_date"] or "", "yyyy-MM-dd")
        if parsed.isValid():
            self.movement_date.setDate(parsed)
        idx = self.movement_item.findData(record["item_id"])
        self.movement_item.setCurrentIndex(idx if idx >= 0 else 0)
        idx = self.movement_type.findText(record["movement_type"] or "")
        self.movement_type.setCurrentIndex(idx if idx >= 0 else 0)
        self.movement_quantity.setText(self._fmt(float(record["quantity"] or 0)))
        idx = self.movement_field.findData(record["field_id"])
        self.movement_field.setCurrentIndex(idx if idx >= 0 else 0)

        self.movement_supplier.setText(
            record["supplier_name"] or "",
            record["partner_id"],
        )
        self.movement_unit_price.setText(
            self._fmt(float(record["unit_price"] or 0))
            if float(record["unit_price"] or 0) > 0
            else ""
        )
        self._update_receipt_total()
        self._update_receipt_fields_visibility()

        self.movement_notes.setText(record["notes"] or "")

        record_year = parsed.year() if parsed.isValid() else None
        locked = record_year is not None and is_year_locked(self.db, record_year)
        if automatic_source:
            source_label = {
                "farm_activity": "Άρδευση & Λίπανση",
                "plant_protection": "Φυτοπροστασία",
            }.get(
                record["source_type"],
                "άλλη ενότητα",
            )
            self.movement_box.setTitle(
                f"Αυτόματη κίνηση — διαχειρίζεται από {source_label}"
            )
            self.movement_save_button.setText("Αυτόματη")
            self.movement_save_button.setEnabled(False)
            self.movement_delete_button.setEnabled(False)
        elif locked:
            self.movement_box.setTitle(
                f"Προβολή κίνησης — ΚΛΕΙΔΩΜΕΝΟ {record_year}"
            )
            self.movement_save_button.setText("Κλειδωμένο")
            self.movement_save_button.setEnabled(False)
            self.movement_delete_button.setEnabled(False)
        else:
            self.movement_box.setTitle("Επεξεργασία κίνησης")
            self.movement_save_button.setText("Αποθήκευση")
            self.movement_save_button.setEnabled(True)
            self.movement_delete_button.setEnabled(True)
        self.movement_cancel_button.setEnabled(True)

    def clear_movement_form(self) -> None:
        self.selected_movement_id = None
        self.movement_date.setDate(QDate.currentDate())
        self.movement_item.setCurrentIndex(0)
        self.movement_type.setCurrentIndex(0)
        self.movement_quantity.clear()
        self.movement_field.setCurrentIndex(0)
        self.movement_supplier.setText("")
        self.movement_unit_price.clear()
        self.movement_total_cost.setText("0 €")
        self.movement_notes.clear()
        self._update_receipt_fields_visibility()
        self.movement_box.setTitle("Νέα κίνηση αποθήκης")
        self.movement_save_button.setText("Προσθήκη κίνησης")
        self.movement_save_button.setEnabled(True)
        self.movement_cancel_button.setEnabled(False)
        self.movement_delete_button.setEnabled(False)
        self.movement_table.clearSelection()

    def delete_movement(self) -> None:
        if self.selected_movement_id is None:
            return

        source_row = self.db.query_one(
            """
            SELECT source_type
            FROM inventory_movements
            WHERE id=?
            """,
            (self.selected_movement_id,),
        )
        if (
            source_row is not None
            and "source_type" in source_row.keys()
            and source_row["source_type"]
        ):
            QMessageBox.information(
                self,
                "Αυτόματη κίνηση",
                (
                    "Αυτή η κίνηση δημιουργήθηκε αυτόματα από άλλη ενότητα.\n\n"
                    "Διόρθωσε ή διέγραψε την αρχική καταχώρηση."
                ),
            )
            return

        record_year = self._movement_record_year(self.selected_movement_id)
        if record_year is not None and is_year_locked(self.db, record_year):
            warn_locked_year(self, self.db, record_year)
            return
        if not self.confirm_delete(
            self, "Διαγραφή κίνησης", "Να διαγραφεί η επιλεγμένη κίνηση αποθήκης;"
        ):
            return
        delete_expense(
            self.db,
            source_type="inventory_receipt",
            source_id=self.selected_movement_id,
        )
        self.db.execute(
            "DELETE FROM inventory_movements WHERE id=?",
            (self.selected_movement_id,),
        )
        self.clear_movement_form()
        self.refresh()

    def refresh(self, *_args) -> None:
        self._ensure_schema_and_audit_triggers()
        self._refresh_combos()
        self.movement_supplier.refresh_options()
        self._refresh_years()

        # Stock table and alert metrics.
        rows = self._stock_rows()
        search = self.stock_search.text().strip().casefold()
        low_only = self.low_only.currentData() == "low"
        visible = []
        low_count = 0
        zero_count = 0

        for row in rows:
            stock = float(row["current_stock"] or 0)
            minimum = float(row["minimum_stock"] or 0)
            if stock <= 0:
                status = "Εξαντλήθηκε"
                zero_count += 1
                low_count += 1
            elif minimum > 0 and stock <= minimum:
                status = "Χαμηλό"
                low_count += 1
            else:
                status = "OK"

            haystack = f"{row['name'] or ''} {row['category'] or ''} {row['unit'] or ''}".casefold()
            if search and search not in haystack:
                continue
            if low_only and status == "OK":
                continue
            visible.append((row, stock, minimum, status))

        self.items_metric[1].setText(str(len(rows)))
        self.low_metric[1].setText(str(low_count))
        self.zero_metric[1].setText(str(zero_count))

        self.stock_table.setRowCount(len(visible))
        for row_index, (row, stock, minimum, status) in enumerate(visible):
            values = [
                row["name"] or "",
                row["category"] or "",
                row["unit"] or "",
                self._fmt(stock),
                self._fmt(minimum),
                status,
            ]
            for column_index, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if column_index == 0:
                    table_item.setData(Qt.ItemDataRole.UserRole, row["id"])
                self.stock_table.setItem(row_index, column_index, table_item)

        # Movement history.
        where = ["1=1"]
        params: list[object] = []
        year = self.year_filter.currentData()
        if year is not None:
            where.append("SUBSTR(m.movement_date,1,4)=?")
            params.append(str(year))
        item_filter = self.item_filter.currentData()
        if item_filter is not None:
            where.append("m.item_id=?")
            params.append(item_filter)
        movement_type = self.type_filter.currentData()
        if movement_type:
            where.append("m.movement_type=?")
            params.append(movement_type)
        search_text = self.movement_search.text().strip()
        if search_text:
            where.append(
                """
                (
                    i.name LIKE ? OR i.category LIKE ? OR
                    m.notes LIKE ? OR COALESCE(f.name,'') LIKE ?
                )
                """
            )
            token = f"%{search_text}%"
            params.extend([token, token, token, token])

        movements = self.db.query(
            f"""
            SELECT
                m.*,
                i.name AS item_name,
                i.unit AS item_unit,
                COALESCE(f.name,'') AS field_name
            FROM inventory_movements m
            LEFT JOIN inventory_items i ON i.id=m.item_id
            LEFT JOIN fields f ON f.id=m.field_id
            WHERE {' AND '.join(where)}
            ORDER BY m.movement_date DESC, m.id DESC
            """,
            tuple(params),
        )
        self.movement_table.setRowCount(len(movements))
        for row_index, row in enumerate(movements):
            field_name = row["field_name"] or "Γενική"
            values = [
                row["movement_date"] or "",
                row["item_name"] or f"ID {row['item_id']}",
                row["movement_type"] or "",
                self._fmt(float(row["quantity"] or 0)),
                row["item_unit"] or "",
                field_name,
                (("[Αυτόματη] " if ("source_type" in row.keys() and row["source_type"]) else "") + (row["notes"] or "")),
            ]
            for column_index, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if column_index == 0:
                    table_item.setData(Qt.ItemDataRole.UserRole, row["id"])
                self.movement_table.setItem(row_index, column_index, table_item)
