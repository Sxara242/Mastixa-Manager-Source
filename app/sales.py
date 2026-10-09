from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from .date_preferences import format_iso_date, refresh_date_inputs

from .localized_messages import _message, _language, _text

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
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .numeric_inputs import NumericDoubleSpinBox
from .crud import CrudPage
from .database import Database
from .language import combo_source_text
from .ui_helpers import compact_decimal, table_widget
from .widgets import date_input, quantity_input
from .year_lock import warn_locked_year
from .year_context import is_year_write_blocked as is_year_locked, working_context_date
from .product_registry import add_product_choices, ensure_product_links, product_row
from .partner_links import ensure_partner_link_schema
from .report_quantities import sale_availability, sale_source_fields, source_rows, quantities
from .sale_source_schema import migrate_sale_sources, install_source_audit


class SalesPage(CrudPage):
    """Πωλήσεις προϊόντων με αυτόματη ενημέρωση εσόδων και διαθέσιμου stock."""

    def _composed_text(self, widget, template, **values):
        if not hasattr(self, "_composed_specs"):
            self._composed_specs = {}
            controller = _language()
            if controller is not None:
                controller.language_changed.connect(self._refresh_composed_text)
        if isinstance(widget, QGroupBox):
            widget.setProperty("mastixaI18nSkipTitle", True)
        else:
            widget.setProperty("mastixaI18nSkipText", True)
            widget.setTextFormat(widget.textFormat().PlainText)
        self._composed_specs[widget] = (template, values)
        self._refresh_composed_text()

    def _refresh_composed_text(self, *_args):
        for widget, (template, values) in self._composed_specs.items():
            text = _text(template, **{key: value() if callable(value) else value
                                     for key, value in values.items()})
            if isinstance(widget, QGroupBox):
                widget.setTitle(text)
            else:
                widget.setText(text)

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_sale_id: int | None = None

        self._ensure_schema()
        ensure_partner_link_schema(self.db)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("salesContent")
        content.setStyleSheet(
            "QWidget#salesContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Πωλήσεις Παραγωγής")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Καταγραφή πωλήσεων προϊόντων, διαθέσιμου αποθέματος και αυτόματης δημιουργίας εσόδου"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        product_selection = QHBoxLayout()
        self.product_filter = QComboBox()
        self.product_filter.currentIndexChanged.connect(self.refresh)
        product_selection.addWidget(QLabel("Προϊόν"))
        product_selection.addWidget(self.product_filter, 1)
        layout.addLayout(product_selection)

        metrics = QHBoxLayout()
        self.produced_metric = self._metric("Συνολική παραγωγή")
        self.sold_metric = self._metric("Πωλημένα")
        self.stock_metric = self._metric("Διαθέσιμο stock")
        self.revenue_metric = self._metric("Αξία πωλήσεων")

        for card, _value in (
            self.produced_metric,
            self.sold_metric,
            self.stock_metric,
            self.revenue_metric,
        ):
            metrics.addWidget(card, 1)

        layout.addLayout(metrics)

        self.form_box = QGroupBox("Νέα πώληση")
        form = QFormLayout(self.form_box)

        self.sale_date = date_input(self.db)

        self.buyer = QComboBox()
        self.buyer.setEditable(False)

        self.product = QComboBox()
        self.product.setEditable(False)
        self.product.currentIndexChanged.connect(self._product_changed)

        self.source = QComboBox()
        self.source.setProperty("mastixaI18nSkipItems", True)
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self._refresh_sources)

        self.quantity = quantity_input()

        self.price_per_kg = NumericDoubleSpinBox()
        self.price_per_kg.setRange(0, 999999999)
        self.price_per_kg.setDecimals(2)
        self.price_per_kg.setSuffix(" € / μονάδα")
        self.price_per_kg.valueChanged.connect(
            self._update_total_preview
        )

        self.quantity.valueChanged.connect(
            self._update_total_preview
        )

        self.total_preview = QLabel("0,00 €")
        self.total_preview.setStyleSheet(
            "font-weight: 700; color: #315F49;"
        )

        self.payment = QComboBox()
        self.payment.addItems(
            [
                "Μετρητά",
                "Τραπεζική μεταφορά",
                "Κάρτα",
                "Πίστωση",
                "Άλλο",
            ]
        )

        self.notes = QLineEdit()

        form.addRow("Ημερομηνία", self.sale_date)
        form.addRow("Αγοραστής", self.buyer)
        form.addRow("Προϊόν", self.product)
        form.addRow("Πηγή παραγωγής", self.source)
        form.addRow("Ποσότητα πώλησης", self.quantity)
        form.addRow("Τιμή / μονάδα", self.price_per_kg)
        form.addRow("Συνολική αξία", self.total_preview)
        form.addRow("Τρόπος πληρωμής", self.payment)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_sale)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_sale)
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

        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.buyer_filter = QComboBox()
        self.buyer_filter.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση αγοραστή ή σημειώσεων..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Αγοραστής"))
        filters.addWidget(self.buyer_filter)
        filters.addWidget(self.search, 1)

        layout.addWidget(filters_box)

        self.table = table_widget(
            [
                "Ημερομηνία",
                "Αγοραστής",
                "Προϊόν",
                "Ποσότητα",
                "Τιμή / μονάδα",
                "Σύνολο",
                "Πληρωμή",
                "Σημειώσεις",
                "Πηγή παραγωγής",
            ]
        )
        self.table.cellClicked.connect(self.load_sale)
        self.table.setMinimumHeight(340)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        for column in (3, 4, 5, 6):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.Stretch
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
        value.setTextFormat(Qt.TextFormat.PlainText)
        value.setProperty("mastixaI18nSkipText", True)

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
            CREATE TABLE IF NOT EXISTS production_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                buyer_id INTEGER,
                buyer_name TEXT NOT NULL DEFAULT '',
                quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
                price_per_kg REAL NOT NULL CHECK(price_per_kg >= 0),
                total_amount REAL NOT NULL CHECK(total_amount >= 0),
                payment_method TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                income_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(buyer_id) REFERENCES business_partners(id) ON DELETE SET NULL
            )
            """
        )

        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_production_sales_date
            ON production_sales(sale_date)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_production_sales_buyer
            ON production_sales(buyer_id)
            """
        )

        sale_columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(production_sales)"
            )
        }
        if "product" not in sale_columns:
            self.db.execute(
                "ALTER TABLE production_sales ADD COLUMN product TEXT NOT NULL DEFAULT ''"
            )
        ensure_product_links(self.db)

        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_production_sales_product
            ON production_sales(product)
            """
        )

        # Safe legacy backfill only when Production has exactly one distinct product.
        product_rows = self.db.query(
            """
            SELECT DISTINCT TRIM(product) AS product
            FROM production
            WHERE TRIM(COALESCE(product,'')) <> ''
            ORDER BY product
            """
        )
        if len(product_rows) == 1:
            self.db.execute(
                """
                UPDATE production_sales
                SET product=?
                WHERE TRIM(COALESCE(product,''))=''
                """,
                (product_rows[0]["product"],),
            )

        with self.db.connect() as con:
            migrate_sale_sources(con)
            install_source_audit(con)

    def _table_exists(self, table_name: str) -> bool:
        return self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (table_name,),
        ) is not None

    def _refresh_buyers(self) -> None:
        current = self.buyer.currentData()
        current_filter = self.buyer_filter.currentData()

        self.buyer.blockSignals(True)
        self.buyer.clear()
        self.buyer.addItem("Επίλεξε αγοραστή", None)

        self.buyer_filter.blockSignals(True)
        self.buyer_filter.clear()
        self.buyer_filter.addItem("Όλοι", None)

        if self._table_exists("business_partners"):
            rows = self.db.query(
                """
                SELECT id,name
                FROM business_partners
                WHERE partner_type IN ('buyer','both')
                ORDER BY name,id
                """
            )

            for row in rows:
                self.buyer.addItem(
                    row["name"],
                    int(row["id"]),
                )
                self.buyer_filter.addItem(
                    row["name"],
                    int(row["id"]),
                )

        index = self.buyer.findData(current)
        self.buyer.setCurrentIndex(index if index >= 0 else 0)

        index = self.buyer_filter.findData(current_filter)
        self.buyer_filter.setCurrentIndex(index if index >= 0 else 0)

        self.buyer.blockSignals(False)
        self.buyer_filter.blockSignals(False)

    def _refresh_products(self) -> None:
        ensure_product_links(self.db)
        current = self.product.currentData()
        current_filter = self.product_filter.currentData()

        self.product.blockSignals(True)
        add_product_choices(self.product, self.db, selected_id=current)
        self.product.blockSignals(False)
        self._product_changed()

        self.product_filter.blockSignals(True)
        self.product_filter.clear()
        self.product_filter.addItem("Όλα", None)
        for row in self.db.query(
            """SELECT DISTINCT pr.id,pr.name
               FROM products pr
               JOIN production p ON p.product_id=pr.id
               ORDER BY pr.name,pr.id"""
        ):
            self.product_filter.addItem(row["name"], int(row["id"]))

        idx = self.product_filter.findData(current_filter)
        self.product_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.product_filter.blockSignals(False)

    def _refresh_years(self) -> None:
        populate_year_filter(self, self.year_filter, strings=True)

    def _product_changed(self, *_args) -> None:
        row = product_row(self.db, self.product.currentData())
        unit = str(row["unit"]) if row is not None else "μονάδα"
        self.quantity.setSuffix(f" {unit}")
        self.price_per_kg.setSuffix(f" €/{unit}")
        self._refresh_sources()

    def _produced_total(
        self,
        product: int | None = None,
    ) -> float:
        return sum(g["quantity"] for g in quantities(self.db, product_id=product))

    def _sold_total(self, exclude_sale_id=None, product=None):
        return sum(g["quantity"] for g in quantities(self.db, "production_sales", product_id=product,
                                                    exclude_sale_id=exclude_sale_id))

    def _available_for_sale(self, exclude_sale_id=None, product=None):
        return sale_availability(self.db, product, exclude_sale_id=exclude_sale_id)

    def _refresh_sources(self, *_args, reset=False):
        selected = self.source.currentData()
        if reset:
            selected = "choose_field" if self.db.get_app_setting("default_sale_source", "pooled") == "field" else None
        product = product_row(self.db, self.product.currentData())
        unit = str(product["unit"] or "[?]") if product else "[?]"
        product_id = product["id"] if product else None
        total = sale_availability(self.db, product_id, exclude_sale_id=self.selected_sale_id)
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem(_text("Συνολικό απόθεμα — διαθέσιμο {quantity} {unit}", quantity=compact_decimal(total,3), unit=unit), None)
        self.source.addItem(_text("Ανά αγροτεμάχιο — επίλεξε αγροτεμάχιο"), "choose_field")
        production_fields = {r.get("field_id") for r in source_rows(self.db, "production", product_id=product_id)} if product else set()
        for field_id, name in sale_source_fields(self.db, product_id) if product else []:
            if field_id not in production_fields and field_id != selected:
                continue
            available = sale_availability(self.db, product_id, field_id, self.selected_sale_id)
            self.source.addItem(_text("{field} — διαθέσιμο {quantity} {unit}", field=name,
                                     quantity=compact_decimal(available,3), unit=unit), field_id)
        index = self.source.findData(selected)
        self.source.setCurrentIndex(index if index >= 0 else 1)
        self.source.blockSignals(False)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 8)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) is None:
                item.setText(_text("Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις"))

    def _record_year(self, sale_id: int) -> int | None:
        row = self.db.query_one(
            """
            SELECT sale_date
            FROM production_sales
            WHERE id=?
            """,
            (sale_id,),
        )
        if row is None:
            return None

        parsed = QDate.fromString(
            row["sale_date"] or "",
            "yyyy-MM-dd",
        )
        return parsed.year() if parsed.isValid() else None

    def _update_total_preview(self, *_args) -> None:
        total = (
            self.quantity.value()
            * self.price_per_kg.value()
        )
        self.total_preview.setText(self._money(total))

    def _sync_income(
        self,
        *,
        sale_id: int,
        income_id: int | None,
        sale_date: str,
        buyer_name: str,
        total_amount: float,
        payment_method: str,
        notes: str,
        db=None,
    ) -> int:
        db = self.db if db is None else db
        description = f"Πώληση προϊόντος — πώληση #{sale_id}"

        sale_row = db.query_one(
            "SELECT buyer_id,source_field_id FROM production_sales WHERE id=?",
            (sale_id,),
        )
        buyer_id = (
            int(sale_row["buyer_id"])
            if sale_row and sale_row["buyer_id"] is not None
            else None
        )

        values = (
            sale_date,
            sale_row["source_field_id"] if sale_row else None,
            description,
            buyer_name,
            buyer_id,
            payment_method,
            total_amount,
            notes,
        )

        if income_id is None:
            return int(
                db.execute(
                    """
                    INSERT INTO income(
                        entry_date,
                        field_id,
                        description,
                        partner,
                        partner_id,
                        payment_method,
                        amount,
                        notes
                    )
                    VALUES(?,?,?,?,?,?,?,?)
                    """,
                    values,
                )
            )

        db.execute(
            """
            UPDATE income
            SET
                entry_date=?,
                field_id=?,
                description=?,
                partner=?,
                partner_id=?,
                payment_method=?,
                amount=?,
                notes=?
            WHERE id=?
            """,
            (*values, income_id),
        )
        return int(income_id)

    def save_sale(self) -> None:
        target_year = self.sale_date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(
                self,
                self.db,
                target_year,
            )
            if self.selected_sale_id is None:
                self.clear_form()
            return

        if self.selected_sale_id is not None:
            original_year = self._record_year(
                self.selected_sale_id
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
                return

        buyer_id = self.buyer.currentData()
        if buyer_id is None:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Επίλεξε αγοραστή.",
            )
            return

        product_id = self.product.currentData()
        selected_product = product_row(self.db, product_id)
        if selected_product is None:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Επίλεξε προϊόν.",
            )
            return

        product = str(selected_product["name"]).strip()

        quantity = self.quantity.value()
        if quantity <= 0:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Η ποσότητα πώλησης πρέπει να είναι μεγαλύτερη από 0.",
            )
            return

        available = self._available_for_sale(
            self.selected_sale_id,
            int(selected_product["id"]),
        )

        if quantity > available + 0.000001:
            _message(self, 'warning', 'Ανεπαρκές διαθέσιμο stock', 'Δεν μπορεί να καταχωρηθεί μεγαλύτερη πώληση από τη διαθέσιμη παραγωγή του προϊόντος «{product}».\n\nΔιαθέσιμο: {value1}', product=product, value1=f"{compact_decimal(available, 3)} {selected_product['unit']}")
            return

        source_field = self.source.currentData()
        if source_field == "choose_field":
            _message(self, "warning", "Ελλιπή στοιχεία", "Επίλεξε αγροτεμάχιο προέλευσης ή Συνολικό απόθεμα.")
            return
        source_name = ""
        if source_field is not None:
            field = self.db.query_one("SELECT name FROM fields WHERE id=?", (source_field,))
            has_production = source_rows(self.db, "production", product_id=product_id, field_id=source_field)
            if field is None or not has_production:
                _message(self, "warning", "Ελλιπή στοιχεία", "Το αγροτεμάχιο δεν έχει παραγωγή για το επιλεγμένο προϊόν.")
                return
            source_name = field["name"]
            available = sale_availability(self.db, product_id, source_field, self.selected_sale_id)
            if quantity > available + 0.000001:
                _message(self, "warning", "Ανεπαρκές διαθέσιμο stock",
                         "Διαθέσιμο για πώληση από το αγροτεμάχιο «{field}»: {quantity} {unit}.",
                         field=source_name, quantity=compact_decimal(available,3), unit=selected_product["unit"])
                return

        buyer_name = combo_source_text(self.buyer).strip()
        price = self.price_per_kg.value()
        total = quantity * price
        sale_date = self.sale_date.date().toString(
            "yyyy-MM-dd"
        )
        payment_method = combo_source_text(self.payment)
        notes = self.notes.text().strip()

        with self.db.transaction() as tx:
            # Revalidate on the same SQLite snapshot used by both linked writes.
            if quantity > sale_availability(tx, product_id, source_field, self.selected_sale_id) + 0.000001:
                _message(self, "warning", "Ανεπαρκές διαθέσιμο stock", "Το διαθέσιμο απόθεμα άλλαξε. Ελέγξτε ξανά την ποσότητα.")
                return
            if self.selected_sale_id is None:
                sale_id = int(
                    tx.execute(
                        """
                        INSERT INTO production_sales(
                            sale_date,
                            buyer_id,
                            buyer_name,
                            product,
                            product_id,
                            quantity_kg,
                            price_per_kg,
                            total_amount,
                            payment_method,
                            notes,
                            source_field_id,
                            source_field_name
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            sale_date,
                            buyer_id,
                            buyer_name,
                            product,
                            int(selected_product["id"]),
                            quantity,
                            price,
                            total,
                            payment_method,
                            notes,
                            source_field,
                            source_name,
                        ),
                    )
                )
                income_id = None
            else:
                existing = tx.query_one(
                    """
                    SELECT income_id
                    FROM production_sales
                    WHERE id=?
                    """,
                    (self.selected_sale_id,),
                )
                income_id = (
                    int(existing["income_id"])
                    if existing
                    and existing["income_id"] is not None
                    else None
                )
                sale_id = self.selected_sale_id

                tx.execute(
                    """
                    UPDATE production_sales
                    SET
                        sale_date=?,
                        buyer_id=?,
                        buyer_name=?,
                        product=?,
                        product_id=?,
                        quantity_kg=?,
                        price_per_kg=?,
                        total_amount=?,
                        payment_method=?,
                        notes=?,
                        source_field_id=?,
                        source_field_name=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (
                        sale_date,
                        buyer_id,
                        buyer_name,
                        product,
                        int(selected_product["id"]),
                        quantity,
                        price,
                        total,
                        payment_method,
                        notes,
                        source_field,
                        source_name,
                        sale_id,
                    ),
                )

            income_id = self._sync_income(
                db=tx,
                sale_id=sale_id,
                income_id=income_id,
                sale_date=sale_date,
                buyer_name=buyer_name,
                total_amount=total,
                payment_method=payment_method,
                notes=notes,
            )

            tx.execute(
                """
                UPDATE production_sales
                SET income_id=?
                WHERE id=?
                """,
                (income_id, sale_id),
            )

        self.clear_form()
        self.refresh()

    def load_sale(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        sale_id = item.data(
            Qt.ItemDataRole.UserRole
        )
        if sale_id is None:
            return

        record = self.db.query_one(
            """
            SELECT *
            FROM production_sales
            WHERE id=?
            """,
            (sale_id,),
        )
        if record is None:
            return

        self.selected_sale_id = int(record["id"])

        parsed = QDate.fromString(
            record["sale_date"] or "",
            "yyyy-MM-dd",
        )
        if parsed.isValid():
            self.sale_date.setDate(parsed)

        self._refresh_buyers()
        self.product.blockSignals(True)
        add_product_choices(
            self.product,
            self.db,
            selected_id=record["product_id"],
            legacy_name=record["product"] or "",
        )
        self.product.blockSignals(False)
        self._product_changed()
        self.source.setCurrentIndex(self.source.findData(record["source_field_id"]))
        index = self.buyer.findData(record["buyer_id"])
        self.buyer.setCurrentIndex(index if index >= 0 else 0)

        self.quantity.setValue(
            float(record["quantity_kg"] or 0)
        )
        self.price_per_kg.setValue(
            float(record["price_per_kg"] or 0)
        )
        self.payment.setCurrentText(
            record["payment_method"] or ""
        )
        self.notes.setText(record["notes"] or "")
        self._update_total_preview()

        year = parsed.year() if parsed.isValid() else None
        locked = (
            year is not None
            and is_year_locked(self.db, year)
        )

        if locked:
            self._composed_text(self.form_box, 'Προβολή πώλησης — ΚΛΕΙΔΩΜΕΝΟ {year}', year=year)
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self._composed_text(self.form_box, 'Επεξεργασία πώλησης')
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_sale_id = None
        self.sale_date.setDate(working_context_date(self.db))
        self._refresh_buyers()
        self._refresh_products()
        self.buyer.setCurrentIndex(0)
        self.product.setCurrentIndex(0)
        self._refresh_sources(reset=True)
        self.quantity.setValue(0)
        self.price_per_kg.setValue(0)
        self.payment.setCurrentIndex(0)
        self.notes.clear()
        self._update_total_preview()

        self._composed_text(self.form_box, 'Νέα πώληση')
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()

    def delete_sale(self) -> None:
        if self.selected_sale_id is None:
            return

        year = self._record_year(
            self.selected_sale_id
        )

        if year is not None and is_year_locked(
            self.db,
            year,
        ):
            warn_locked_year(
                self,
                self.db,
                year,
            )
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή πώλησης",
            (
                "Να διαγραφεί η επιλεγμένη πώληση;\n\n"
                "Θα διαγραφεί και το αυτόματα συνδεδεμένο έσοδο."
            ),
        ):
            return

        with self.db.transaction() as tx:
            row = tx.query_one(
                """
                SELECT income_id
                FROM production_sales
                WHERE id=?
                """,
                (self.selected_sale_id,),
            )

            if row and row["income_id"] is not None:
                tx.execute(
                    "DELETE FROM income WHERE id=?",
                    (row["income_id"],),
                )

            tx.execute(
                """
                DELETE FROM production_sales
                WHERE id=?
                """,
                (self.selected_sale_id,),
            )

        self.clear_form()
        self.refresh()

    def refresh(self, *_args) -> None:
        refresh_date_inputs(self, self.db)
        self._ensure_schema()
        self._refresh_buyers()
        self._refresh_products()
        self._refresh_years()

        year = self.year_filter.currentData()
        buyer_id = self.buyer_filter.currentData()
        product_filter = self.product_filter.currentData()
        search = self.search.text().strip()

        where = ["1=1"]
        params: list[object] = []

        if year:
            where.append(
                "SUBSTR(s.sale_date,1,4)=?"
            )
            params.append(year)

        if buyer_id is not None:
            where.append("s.buyer_id=?")
            params.append(buyer_id)

        if product_filter:
            where.append("s.product_id=?")
            params.append(product_filter)

        if search:
            token = f"%{search}%"
            where.append(
                "("
                "s.buyer_name LIKE ? OR "
                "s.product LIKE ? OR "
                "s.notes LIKE ?"
                ")"
            )
            params.extend([token, token, token])

        rows = self.db.query(
            f"""
            SELECT s.*, pr.unit AS product_unit
            FROM production_sales s
            LEFT JOIN products pr ON pr.id=s.product_id
            WHERE {' AND '.join(where)}
            ORDER BY s.sale_date DESC,s.id DESC
            """,
            params,
        )

        self.table.setRowCount(len(rows))

        filtered_revenue = 0.0

        for row_index, row in enumerate(rows):
            unit = str(row["product_unit"]) if row["product_unit"] is not None else "—"
            filtered_revenue += float(
                row["total_amount"] or 0
            )

            values = [
                format_iso_date(row["sale_date"], self.db),
                row["buyer_name"] or "",
                row["product"] or "—",
                f"{compact_decimal(row['quantity_kg'], 3)} {unit}",
                self._money(
                    float(row["price_per_kg"] or 0)
                ) + f"/{unit}",
                self._money(
                    float(row["total_amount"] or 0)
                ),
                row["payment_method"] or "",
                row["notes"] or "",
                row["source_field_name"] if row["source_field_id"] is not None else _text("Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις"),
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                if column == 8:
                    item.setData(Qt.ItemDataRole.UserRole, row["source_field_id"])
                self.table.setItem(
                    row_index,
                    column,
                    item,
                )

        selected_product = product_row(self.db, product_filter)
        quantity_labels = ("—", "—", "—")
        if selected_product is not None:
            # Stock remains all-time/product-specific, independent of list filters.
            produced = sum(g['quantity'] for g in quantities(self.db, year=year, product_id=product_filter))
            sold = sum(g['quantity'] for g in quantities(self.db, 'production_sales', year, product_id=product_filter))
            available = self._available_for_sale(product=product_filter)
            unit = str(selected_product["unit"])
            quantity_labels = tuple(
                f"{compact_decimal(value, 3)} {unit}"
                for value in (produced, sold, available)
            )
        for metric, text in zip(
            (self.produced_metric, self.sold_metric, self.stock_metric), quantity_labels
        ):
            metric[1].setText(text)
        self.revenue_metric[1].setText(
            self._money(filtered_revenue)
        )
