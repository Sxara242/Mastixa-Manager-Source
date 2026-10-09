from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from .localized_messages import _language, _message, _text

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidgetItem,
    QVBoxLayout,
)

from .crud import CrudPage
from .ui_helpers import batched_table_refresh, scrollable_entry_layout
from .date_preferences import format_iso_date, refresh_date_inputs, selected_date_format
from .database import Database
from .ui_helpers import compact_decimal, table_widget
from .widgets import date_input, quantity_input
from .year_lock import warn_locked_year
from .year_context import is_year_write_blocked as is_year_locked, working_context_date
from .product_registry import (
    ProductionStockError, add_product_choices, ensure_product_links,
    ensure_production_stock, product_row,
)


class ProductionPage(CrudPage):
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
        ensure_product_links(self.db)
        self.selected_production_id: int | None = None

        layout = scrollable_entry_layout(self)

        title = QLabel("Παραγωγή ανά αγροτεμάχιο")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.form_box = QGroupBox("Νέα καταχώρηση παραγωγής")
        form = QFormLayout(self.form_box)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.date = date_input(self.db)
        self.date.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.field = QComboBox()
        self.product = QComboBox()
        self.product.currentIndexChanged.connect(self._product_changed)
        self.quantity = quantity_input()
        self.notes = QLineEdit()

        form.addRow("Ημερομηνία", self.date)
        form.addRow("Αγροτεμάχιο", self.field)
        form.addRow("Προϊόν", self.product)
        form.addRow("Παραγωγή", self.quantity)
        form.addRow("Παρατηρήσεις", self.notes)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_production)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_production)
        self.delete_button.setEnabled(False)

        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.delete_button)
        form.addRow("", buttons)

        layout.addWidget(self.form_box)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Έτος"))
        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)
        filters.addWidget(self.year_filter)
        layout.addLayout(filters)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση παραγωγής...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(
            lambda text: self.filter_table(self.table, text)
        )
        layout.addWidget(self.search)

        self.table = table_widget(
            ["Ημερομηνία", "Αγροτεμάχιο", "Προϊόν", "Ποσότητα", "Παρατηρήσεις"]
        )
        self.table.cellClicked.connect(self.load_selected)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table)

        self.refresh()

    def refresh_fields(self, preferred_id=None) -> None:
        if preferred_id is None:
            preferred_id = self.field.currentData()

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Επίλεξε αγροτεμάχιο", None)

        for row in self.db.query("SELECT id, name FROM fields ORDER BY name, id"):
            self.field.addItem(row["name"], row["id"])

        index = self.field.findData(preferred_id)
        if index >= 0:
            self.field.setCurrentIndex(index)

        self.field.blockSignals(False)

    def _record_year(self, production_id: int) -> int | None:
        row = self.db.query_one(
            "SELECT entry_date FROM production WHERE id=?",
            (production_id,),
        )

        if row is None:
            return None

        parsed = QDate.fromString(
            row["entry_date"] or "",
            "yyyy-MM-dd",
        )

        return parsed.year() if parsed.isValid() else None

    def _product_changed(self, *_args) -> None:
        row = product_row(self.db, self.product.currentData())
        unit = str(row["unit"]) if row is not None else ""
        self.quantity.setSuffix(f" {unit}" if unit else "")

    def _locked_for_save(self) -> bool:
        target_year = self.date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True

        if self.selected_production_id is not None:
            original_year = self._record_year(
                self.selected_production_id
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

    def _stock_allows_change(self, *, product_id=None, quantity=0.0) -> bool:
        try:
            ensure_production_stock(
                self.db, self.selected_production_id,
                product_id=product_id, quantity=quantity,
                field_id=self.field.currentData() if product_id is not None else None,
            )
        except ProductionStockError as exc:
            if exc.field is not None:
                _message(self, "warning", "Η παραγωγή απαιτείται από πωλήσεις",
                         "Οι πωλήσεις του προϊόντος «{product}» από το αγροτεμάχιο «{field}» απαιτούν τουλάχιστον {sold} {unit}. Μετά την αλλαγή απομένουν {proposed} {unit}. Η αλλαγή δεν αποθηκεύτηκε.",
                         product=exc.product, field=exc.field, sold=f"{exc.sold:g}",
                         proposed=f"{exc.proposed:g}", unit=exc.unit)
                return False
            _message(
                self, "warning", "Η παραγωγή απαιτείται από πωλήσεις",
                "Οι υπάρχουσες πωλήσεις του προϊόντος «{product}» απαιτούν να παραμείνει "
                "επαρκής παραγωγή. Η αλλαγή δεν αποθηκεύτηκε.\n\n"
                "Πωλημένη ποσότητα / ελάχιστη συνολική παραγωγή: {sold}\n"
                "Συνολική παραγωγή μετά την αλλαγή: {proposed}",
                product=exc.product, sold=f"{exc.sold:g}", proposed=f"{exc.proposed:g}",
            )
            return False
        return True

    def save_production(self) -> None:
        if self._locked_for_save():
            if self.selected_production_id is None:
                self.clear_form()
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

        product_id = self.product.currentData()
        selected_product = product_row(self.db, product_id)
        if selected_product is None:
            QMessageBox.warning(
                self, "Ελλιπή στοιχεία", "Επίλεξε ενεργό προϊόν."
            )
            self.product.setFocus()
            return

        if self.quantity.value() <= 0:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Η ποσότητα παραγωγής πρέπει να είναι μεγαλύτερη από 0.",
            )
            self.quantity.setFocus()
            return

        values = (
            self.date.date().toString("yyyy-MM-dd"),
            field_id,
            selected_product["name"],
            int(selected_product["id"]),
            self.quantity.value(),
            self.notes.text().strip(),
        )

        if self.selected_production_id is None:
            self.db.execute(
                """
                INSERT INTO production
                    (entry_date, field_id, product, product_id, quantity_kg, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        else:
            if not self._stock_allows_change(
                product_id=int(selected_product["id"]), quantity=self.quantity.value(),
            ):
                return
            self.db.execute(
                """
                UPDATE production
                SET entry_date=?,
                    field_id=?,
                    product=?,
                    product_id=?,
                    quantity_kg=?,
                    notes=?
                WHERE id=?
                """,
                (*values, self.selected_production_id),
            )

        self.clear_form()
        self.refresh()

    def load_selected(self, row: int, _column: int) -> None:
        first_item = self.table.item(row, 0)
        if first_item is None:
            return

        production_id = first_item.data(Qt.ItemDataRole.UserRole)
        if production_id is None:
            return

        production = self.db.query_one(
            "SELECT * FROM production WHERE id=?",
            (production_id,),
        )
        if production is None:
            self.refresh()
            return

        self.selected_production_id = int(production["id"])

        parsed_date = QDate.fromString(
            production["entry_date"],
            "yyyy-MM-dd",
        )
        if parsed_date.isValid():
            self.date.setDate(parsed_date)

        self.refresh_fields(production["field_id"])
        self.product.blockSignals(True)
        add_product_choices(
            self.product,
            self.db,
            selected_id=production["product_id"],
            legacy_name=production["product"] or "",
        )
        self.product.blockSignals(False)
        self._product_changed()
        self.quantity.setValue(float(production["quantity_kg"] or 0))
        self.notes.setText(production["notes"] or "")

        record_year = parsed_date.year() if parsed_date.isValid() else None
        locked = (
            record_year is not None
            and is_year_locked(self.db, record_year)
        )

        if locked:
            self._composed_text(self.form_box, 'Προβολή παραγωγής — ΚΛΕΙΔΩΜΕΝΟ {record_year}', record_year=record_year)
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self._composed_text(self.form_box, 'Επεξεργασία παραγωγής')
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_production_id = None

        self.date.setDate(working_context_date(self.db))
        self.refresh_fields(None)
        self.field.setCurrentIndex(0)
        self.product.blockSignals(True)
        add_product_choices(self.product, self.db)
        self.product.blockSignals(False)
        self._product_changed()
        self.quantity.setValue(0)
        self.notes.clear()

        self._composed_text(self.form_box, 'Νέα καταχώρηση παραγωγής')
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()

    def delete_production(self) -> None:
        if self.selected_production_id is None:
            return

        record_year = self._record_year(
            self.selected_production_id
        )

        if (
            record_year is not None
            and is_year_locked(self.db, record_year)
        ):
            warn_locked_year(self, self.db, record_year)
            return

        if not self.confirm_delete(
            self,
            "Διαγραφή παραγωγής",
            "Να διαγραφεί η επιλεγμένη καταχώρηση παραγωγής;",
        ):
            return

        if not self._stock_allows_change():
            return

        self.db.execute(
            "DELETE FROM production WHERE id=?",
            (self.selected_production_id,),
        )

        self.clear_form()
        self.refresh()

    @batched_table_refresh
    def refresh(self, *_args) -> None:
        refresh_date_inputs(self, self.db)
        ensure_product_links(self.db)
        current_field_id = self.field.currentData()
        self.refresh_fields(current_field_id)
        current_product_id = self.product.currentData()
        self.product.blockSignals(True)
        add_product_choices(
            self.product, self.db, selected_id=current_product_id
        )
        self.product.blockSignals(False)
        self._product_changed()

        populate_year_filter(self, self.year_filter)
        year = self.year_filter.currentData()
        rows = self.db.query(
            f"""
            SELECT
                p.id,
                p.entry_date,
                COALESCE(f.name, '') AS field_name,
                COALESCE(pr.name,p.product,'') AS product_name,
                COALESCE(pr.unit,'kg') AS product_unit,
                p.quantity_kg,
                p.notes
            FROM production p
            LEFT JOIN fields f ON f.id = p.field_id
            LEFT JOIN products pr ON pr.id = p.product_id
            {"WHERE SUBSTR(p.entry_date,1,4)=?" if year is not None else ""}
            ORDER BY p.entry_date DESC, p.id DESC
            """,
            (str(year),) if year is not None else (),
        )

        self.table.setRowCount(len(rows))
        date_format = selected_date_format(self.db)

        for row_index, row in enumerate(rows):
            values = [
                format_iso_date(row["entry_date"], self.db, display_format=date_format),
                row["field_name"] or "",
                row["product_name"] or "",
                f"{compact_decimal(row['quantity_kg'], 3)} {row['product_unit']}",
                row["notes"] or "",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        int(row["id"]),
                    )
                self.table.setItem(row_index, column_index, item)

        self.filter_table(self.table, self.search.text())
