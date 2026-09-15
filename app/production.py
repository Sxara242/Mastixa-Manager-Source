from __future__ import annotations

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
    QTableWidgetItem,
    QVBoxLayout,
)

from .crud import CrudPage
from .database import Database
from .ui_helpers import compact_decimal, table_widget
from .widgets import date_input, quantity_input
from .year_lock import is_year_locked, warn_locked_year
from .product_registry import add_product_choices, ensure_product_links, product_row


class ProductionPage(CrudPage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        ensure_product_links(self.db)
        self.selected_production_id: int | None = None

        layout = QVBoxLayout(self)

        title = QLabel("Παραγωγή ανά αγροτεμάχιο")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.form_box = QGroupBox("Νέα καταχώρηση παραγωγής")
        form = QFormLayout(self.form_box)

        self.date = date_input()
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

    def save_production(self) -> None:
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
            self.form_box.setTitle(
                f"Προβολή παραγωγής — ΚΛΕΙΔΩΜΕΝΟ {record_year}"
            )
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.form_box.setTitle("Επεξεργασία παραγωγής")
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_production_id = None

        self.date.setDate(QDate.currentDate())
        self.refresh_fields(None)
        self.field.setCurrentIndex(0)
        self.product.blockSignals(True)
        add_product_choices(self.product, self.db)
        self.product.blockSignals(False)
        self._product_changed()
        self.quantity.setValue(0)
        self.notes.clear()

        self.form_box.setTitle("Νέα καταχώρηση παραγωγής")
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

        self.db.execute(
            "DELETE FROM production WHERE id=?",
            (self.selected_production_id,),
        )

        self.clear_form()
        self.refresh()

    def refresh(self) -> None:
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

        rows = self.db.query(
            """
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
            ORDER BY p.entry_date DESC, p.id DESC
            """
        )

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row["entry_date"] or "",
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
