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
from .language import combo_source_text
from .widgets import date_input, money_input, required_text
from .year_lock import is_year_locked, warn_locked_year
from .expense_sync import ensure_expense_source_schema
from .partner_links import PartnerComboBox, ensure_partner_link_schema

def _table(headers: list[str]):
    from PySide6.QtWidgets import QTableWidget, QAbstractItemView

    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(True)
    table.horizontalHeader().setStretchLastSection(True)
    table.setAlternatingRowColors(True)
    return table


class MoneyPage(CrudPage):
    def __init__(self, db: Database, kind: str) -> None:
        super().__init__()
        self.db = db
        self.kind = kind
        self.is_income = kind == "income"
        self.selected_money_id: int | None = None

        self._ensure_field_link_schema()
        ensure_expense_source_schema(self.db)
        ensure_partner_link_schema(self.db)

        layout = QVBoxLayout(self)

        title = QLabel("Έσοδα" if self.is_income else "Έξοδα")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.form_box = QGroupBox(
            "Νέα καταχώρηση εσόδου" if self.is_income else "Νέα καταχώρηση εξόδου"
        )
        form = QFormLayout(self.form_box)

        self.date = date_input()
        self.category = QComboBox()
        if not self.is_income:
            self.category.addItems(
                ["Εργασία", "Λίπανση", "Άρδευση", "Εξοπλισμός", "Μεταφορές", "Άλλο"]
            )

        self.field = QComboBox()
        self.description = QLineEdit()
        self.partner = PartnerComboBox(
            self.db,
            role="buyer" if self.is_income else "supplier",
        )
        self.payment = QComboBox()
        self.payment.addItems(
            ["Μετρητά", "Τραπεζική μεταφορά", "Κάρτα", "Πίστωση", "Άλλο"]
        )
        self.amount = money_input()
        self.notes = QLineEdit()

        form.addRow("Ημερομηνία", self.date)
        form.addRow("Αγροτεμάχιο", self.field)
        if not self.is_income:
            form.addRow("Κατηγορία", self.category)
        form.addRow("Περιγραφή", self.description)
        form.addRow(
            "Πελάτης / Συνεργάτης" if self.is_income else "Προμηθευτής / Συνεργάτης",
            self.partner,
        )
        form.addRow("Τρόπος πληρωμής", self.payment)
        form.addRow("Ποσό", self.amount)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_money)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_money)
        self.delete_button.setEnabled(False)

        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.delete_button)
        form.addRow("", buttons)

        layout.addWidget(self.form_box)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση εσόδων..." if self.is_income else "Αναζήτηση εξόδων..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(
            lambda value: self.filter_table(self.table, value)
        )
        layout.addWidget(self.search)

        headers = [
            "Ημερομηνία",
            "Αγροτεμάχιο",
            "Περιγραφή",
            "Συνεργάτης",
            "Πληρωμή",
            "Ποσό",
            "Σημειώσεις",
        ]
        if not self.is_income:
            headers.insert(2, "Κατηγορία")

        self.table = _table(headers)
        self.table.cellClicked.connect(self.load_selected)
        layout.addWidget(self.table)

        self.refresh()

    def _ensure_field_link_schema(self) -> None:
        for table_name in ("income", "expenses"):
            columns = {
                row["name"]
                for row in self.db.query(
                    f"PRAGMA table_info({table_name})"
                )
            }

            if "field_id" not in columns:
                self.db.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN field_id INTEGER"
                )

            self.db.execute(
                f"""
                CREATE INDEX IF NOT EXISTS
                    idx_{table_name}_field_id
                ON {table_name}(field_id)
                """
            )

        # Existing databases cannot gain an FK through ALTER TABLE.
        # This trigger gives the same practical ON DELETE SET NULL behavior.
        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS money_field_delete_cleanup
            BEFORE DELETE ON fields
            BEGIN
                UPDATE income
                SET field_id=NULL
                WHERE field_id=OLD.id;

                UPDATE expenses
                SET field_id=NULL
                WHERE field_id=OLD.id;
            END
            """
        )

    def _refresh_field_choices(
        self,
        selected_field_id: int | None = None,
    ) -> None:
        current = (
            selected_field_id
            if selected_field_id is not None
            else self.field.currentData()
        )

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Γενικό / μη κατανεμημένο", None)

        for row in self.db.query(
            "SELECT id, name FROM fields ORDER BY name, id"
        ):
            self.field.addItem(
                row["name"],
                int(row["id"]),
            )

        index = self.field.findData(current)
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)

    def _money_table_name(self) -> str:
        return "income" if self.is_income else "expenses"

    def _record_year(self, record_id: int) -> int | None:
        row = self.db.query_one(
            f"""
            SELECT entry_date
            FROM {self._money_table_name()}
            WHERE id=?
            """,
            (record_id,),
        )

        if row is None:
            return None

        parsed = QDate.fromString(
            row["entry_date"] or "",
            "yyyy-MM-dd",
        )

        return parsed.year() if parsed.isValid() else None

    def _locked_for_save(self) -> bool:
        target_year = self.date.date().year()

        if is_year_locked(self.db, target_year):
            warn_locked_year(self, self.db, target_year)
            return True

        if self.selected_money_id is not None:
            original_year = self._record_year(
                self.selected_money_id
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

    def save_money(self) -> None:
        if self._locked_for_save():
            return

        description = required_text(self.description, "Περιγραφή")
        if description is None:
            return

        if self.amount.value() <= 0:
            QMessageBox.warning(
                self,
                "Ελλιπή στοιχεία",
                "Το ποσό πρέπει να είναι μεγαλύτερο από 0 €.",
            )
            self.amount.setFocus()
            return

        entry_date = self.date.date().toString("yyyy-MM-dd")
        field_id = self.field.currentData()
        partner = self.partner.text().strip()
        partner_id = self.partner.selected_partner_id()
        payment_method = combo_source_text(self.payment)
        amount = self.amount.value()
        notes = self.notes.text().strip()

        if self.is_income:
            if self.selected_money_id is None:
                self.db.execute(
                    """
                    INSERT INTO income
                        (
                            entry_date,
                            field_id,
                            description,
                            partner,
                            partner_id,
                            payment_method,
                            amount,
                            notes
                        )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_date,
                        field_id,
                        description,
                        partner,
                        partner_id,
                        payment_method,
                        amount,
                        notes,
                    ),
                )
            else:
                self.db.execute(
                    """
                    UPDATE income
                    SET entry_date=?,
                        field_id=?,
                        description=?,
                        partner=?,
                        partner_id=?,
                        payment_method=?,
                        amount=?,
                        notes=?
                    WHERE id=?
                    """,
                    (
                        entry_date,
                        field_id,
                        description,
                        partner,
                        partner_id,
                        payment_method,
                        amount,
                        notes,
                        self.selected_money_id,
                    ),
                )
        else:
            category = combo_source_text(self.category)

            if self.selected_money_id is None:
                self.db.execute(
                    """
                    INSERT INTO expenses
                        (
                            entry_date,
                            field_id,
                            category,
                            description,
                            supplier,
                            partner_id,
                            payment_method,
                            amount,
                            notes
                        )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_date,
                        field_id,
                        category,
                        description,
                        partner,
                        partner_id,
                        payment_method,
                        amount,
                        notes,
                    ),
                )
            else:
                self.db.execute(
                    """
                    UPDATE expenses
                    SET entry_date=?,
                        field_id=?,
                        category=?,
                        description=?,
                        supplier=?,
                        partner_id=?,
                        payment_method=?,
                        amount=?,
                        notes=?
                    WHERE id=?
                    """,
                    (
                        entry_date,
                        field_id,
                        category,
                        description,
                        partner,
                        partner_id,
                        payment_method,
                        amount,
                        notes,
                        self.selected_money_id,
                    ),
                )

        self.clear_form()
        self.refresh()

    def load_selected(self, row: int, _column: int) -> None:
        first_item = self.table.item(row, 0)
        if first_item is None:
            return

        record_id = first_item.data(Qt.ItemDataRole.UserRole)
        if record_id is None:
            return

        table_name = "income" if self.is_income else "expenses"
        record = self.db.query_one(
            f"SELECT * FROM {table_name} WHERE id=?",
            (record_id,),
        )
        if record is None:
            self.refresh()
            return

        self.selected_money_id = int(record["id"])

        auto_source = (
            not self.is_income
            and "source_type" in record.keys()
            and bool(record["source_type"])
        )

        parsed_date = QDate.fromString(record["entry_date"], "yyyy-MM-dd")
        if parsed_date.isValid():
            self.date.setDate(parsed_date)

        self._refresh_field_choices(record["field_id"])

        if not self.is_income:
            category_index = self.category.findText(record["category"] or "")
            if category_index >= 0:
                self.category.setCurrentIndex(category_index)

        self.description.setText(record["description"] or "")
        self.partner.setText(
            (record["partner"] if self.is_income else record["supplier"]) or "",
            record["partner_id"] if "partner_id" in record.keys() else None,
        )

        payment_index = self.payment.findText(record["payment_method"] or "")
        if payment_index >= 0:
            self.payment.setCurrentIndex(payment_index)

        self.amount.setValue(float(record["amount"] or 0))
        self.notes.setText(record["notes"] or "")

        record_year = parsed_date.year() if parsed_date.isValid() else None
        locked = (
            record_year is not None
            and is_year_locked(self.db, record_year)
        )

        if auto_source:
            self.form_box.setTitle(
                "Προβολή αυτόματου εξόδου — διαχειρίζεται από την αρχική ενότητα"
            )
            self.save_button.setText("Αυτόματο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif locked:
            label = "εσόδου" if self.is_income else "εξόδου"
            self.form_box.setTitle(
                f"Προβολή {label} — ΚΛΕΙΔΩΜΕΝΟ {record_year}"
            )
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.form_box.setTitle(
                "Επεξεργασία εσόδου"
                if self.is_income
                else "Επεξεργασία εξόδου"
            )
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_money_id = None

        self.date.setDate(QDate.currentDate())
        self._refresh_field_choices(None)
        self.field.setCurrentIndex(0)

        if not self.is_income and self.category.count() > 0:
            self.category.setCurrentIndex(0)

        self.description.clear()
        self.partner.setText("")
        if self.payment.count() > 0:
            self.payment.setCurrentIndex(0)
        self.amount.setValue(0)
        self.notes.clear()

        self.form_box.setTitle(
            "Νέα καταχώρηση εσόδου" if self.is_income else "Νέα καταχώρηση εξόδου"
        )
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()
        self.description.setFocus()

    def delete_money(self) -> None:
        if self.selected_money_id is None:
            return

        if not self.is_income:
            auto = self.db.query_one(
                """
                SELECT source_type
                FROM expenses
                WHERE id=?
                """,
                (self.selected_money_id,),
            )
            if auto is not None and auto["source_type"]:
                QMessageBox.information(
                    self,
                    "Αυτόματο έξοδο",
                    (
                        "Αυτό το έξοδο δημιουργήθηκε αυτόματα από άλλη ενότητα.\n\n"
                        "Διόρθωσε ή διέγραψε την αρχική καταχώρηση."
                    ),
                )
                return

        record_year = self._record_year(
            self.selected_money_id
        )

        if (
            record_year is not None
            and is_year_locked(self.db, record_year)
        ):
            warn_locked_year(self, self.db, record_year)
            return

        label = "έσοδο" if self.is_income else "έξοδο"

        if not self.confirm_delete(
            self,
            f"Διαγραφή {label}υ",
            f"Να διαγραφεί η επιλεγμένη καταχώρηση {label}υ;",
        ):
            return

        table_name = "income" if self.is_income else "expenses"
        self.db.execute(
            f"DELETE FROM {table_name} WHERE id=?",
            (self.selected_money_id,),
        )

        self.clear_form()
        self.refresh()

    def refresh(self) -> None:
        self._ensure_field_link_schema()
        self._refresh_field_choices()
        self.partner.refresh_options()

        if self.is_income:
            rows = self.db.query(
                """
                SELECT
                    i.*,
                    f.name AS field_name
                FROM income i
                LEFT JOIN fields f
                    ON f.id=i.field_id
                ORDER BY i.entry_date DESC, i.id DESC
                """
            )
        else:
            rows = self.db.query(
                """
                SELECT
                    e.*,
                    f.name AS field_name
                FROM expenses e
                LEFT JOIN fields f
                    ON f.id=e.field_id
                ORDER BY e.entry_date DESC, e.id DESC
                """
            )

        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            if self.is_income:
                values = [
                    row["entry_date"] or "",
                    row["field_name"] or "Γενικό",
                    row["description"] or "",
                    row["partner"] or "",
                    row["payment_method"] or "",
                    f'{float(row["amount"] or 0):.2f} €',
                    row["notes"] or "",
                ]
            else:
                values = [
                    row["entry_date"] or "",
                    row["field_name"] or "Γενικό",
                    row["category"] or "",
                    (
                        ("[Αυτόματο] " if ("source_type" in row.keys() and row["source_type"]) else "")
                        + (row["description"] or "")
                    ),
                    row["supplier"] or "",
                    row["payment_method"] or "",
                    f'{float(row["amount"] or 0):.2f} €',
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
