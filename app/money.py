from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
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
from .localized_messages import _language, _text
from .database import Database
from .language import combo_source_text
from .widgets import date_input, money_input, required_text
from .year_lock import warn_locked_year
from .year_context import is_year_write_blocked as is_year_locked, working_context_date
from .expense_sync import ensure_expense_source_schema
from .partner_links import PartnerComboBox, ensure_partner_link_schema
from .date_preferences import format_iso_date, refresh_date_inputs, selected_date_format
from .ui_helpers import batched_table_refresh, scrollable_entry_layout

def _table(headers: list[str]):
    from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QHeaderView

    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(True)
    header = table.horizontalHeader()
    header.setMinimumSectionSize(100)
    header.setResizeContentsPrecision(100)
    header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
    table.setAlternatingRowColors(True)
    return table


class MoneyPage(CrudPage):

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

    @staticmethod
    def _body_render(spec):
        template, values, labels = spec
        return _text(template, **dict(values, **{k: _text(v) for k, v in labels.items()}))

    def _set_body(self, item, template, *, _labels=None, **values):
        spec = (template, values, _labels or {})
        item.setData(2368, item.text())
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
        for name in ('table',):
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
        for name in ("year_filter", "category_filter"):
            combo = getattr(self, name, None)
            if combo is None:
                continue
            blocked = combo.blockSignals(True)
            for index in range(combo.count()):
                value = combo.itemData(index)
                if value is None:
                    label = "Όλα τα έτη" if name == "year_filter" else "Όλες οι κατηγορίες"
                    combo.setItemText(index, _text(label))
                elif name == "category_filter":
                    combo.setItemText(index, _text(value) if value in ("Εργασία", "Λίπανση", "Άρδευση", "Εξοπλισμός", "Μεταφορές", "Άλλο") else value)
            combo.blockSignals(blocked)

    def __init__(self, db: Database, kind: str) -> None:
        super().__init__()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self._refresh_body_language)
        self.db = db
        self.kind = kind
        self.is_income = kind == "income"
        self.selected_money_id: int | None = None

        self._ensure_field_link_schema()
        ensure_expense_source_schema(self.db)
        ensure_partner_link_schema(self.db)

        layout = scrollable_entry_layout(self)

        title = QLabel("Έσοδα" if self.is_income else "Έξοδα")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.form_box = QGroupBox(
            "Νέα καταχώρηση εσόδου" if self.is_income else "Νέα καταχώρηση εξόδου"
        )
        form = QFormLayout(self.form_box)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.date = date_input(self.db)
        self.date.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
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
        filters = QGridLayout()
        self.year_filter = QComboBox()
        self.year_filter.setProperty("mastixaI18nSkipItems", True)
        self.year_filter.addItem("Όλα τα έτη", None)
        self.year_filter.currentIndexChanged.connect(self.refresh)
        self.sort_order = QComboBox()
        for label, key in (("Ημερομηνία: νεότερα πρώτα", "date_desc"),
                           ("Ημερομηνία: παλαιότερα πρώτα", "date_asc"),
                           ("Ποσό: μικρότερο πρώτα", "amount_asc"),
                           ("Ποσό: μεγαλύτερο πρώτα", "amount_desc")):
            self.sort_order.addItem(label, key)
        self.sort_order.setProperty("mastixaI18nStaticItems", True)
        self.sort_order.currentIndexChanged.connect(self.refresh)
        filters.addWidget(QLabel("Έτος"), 0, 0)
        filters.addWidget(self.year_filter, 0, 1)
        filters.addWidget(QLabel("Ταξινόμηση"), 0, 2)
        filters.addWidget(self.sort_order, 0, 3)
        filters.setColumnStretch(1, 1)
        filters.setColumnStretch(3, 2)
        self.category_filter = QComboBox()
        self.category_filter.setProperty("mastixaI18nSkipItems", True)
        self.category_filter.addItem(_text("Όλες οι κατηγορίες"), None)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        if not self.is_income:
            filters.addWidget(QLabel("Κατηγορία"), 1, 0)
            filters.addWidget(self.category_filter, 1, 1, 1, 3)
        layout.addLayout(filters)
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
        self.table.setMinimumHeight(180)
        self.table.cellClicked.connect(self.load_selected)
        layout.addWidget(self.table)

        self.refresh()
        self._pristine_form = self._form_values()
        for signal in (self.date.dateChanged, self.field.currentIndexChanged,
                       self.category.currentIndexChanged, self.description.textChanged,
                       self.partner.currentTextChanged, self.payment.currentIndexChanged,
                       self.amount.valueChanged, self.notes.textChanged):
            signal.connect(self._update_cancel)
        # Numeric keyboard input may not be committed until focus leaves.
        self.amount.lineEdit().textEdited.connect(self._update_cancel)

    def _form_values(self):
        return (self.date.date().toString("yyyy-MM-dd"), self.field.currentData(),
                combo_source_text(self.category), self.description.text(),
                self.partner.text(), self.partner.selected_partner_id(),
                combo_source_text(self.payment), self.amount.value(), self.amount.lineEdit().text(), self.notes.text())

    def _update_cancel(self, *_args):
        self.cancel_button.setEnabled(self.selected_money_id is not None or
                                      self._form_values() != self._pristine_form)

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
            if self.selected_money_id is None:
                self.clear_form()
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            self._composed_text(self.form_box, 'Προβολή αυτόματου εξόδου — διαχειρίζεται από την αρχική ενότητα')
            self.save_button.setText("Αυτόματο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        elif locked:
            self._composed_text(self.form_box, 'Προβολή εσόδου — ΚΛΕΙΔΩΜΕΝΟ {record_year}' if self.is_income else 'Προβολή εξόδου — ΚΛΕΙΔΩΜΕΝΟ {record_year}', record_year=record_year)
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self._composed_text(self.form_box, 'Επεξεργασία εσόδου' if self.is_income else 'Επεξεργασία εξόδου')
            self.save_button.setText("Αποθήκευση")
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)

        self.cancel_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_money_id = None

        self.date.setDate(working_context_date(self.db))
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

        self._composed_text(self.form_box, 'Νέα καταχώρηση εσόδου' if self.is_income else 'Νέα καταχώρηση εξόδου')
        self.save_button.setText("Προσθήκη")
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self._pristine_form = self._form_values()
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

    @staticmethod
    def filter_table(table, text):
        blocked = table.blockSignals(True)
        displayed = []
        try:
            for row in range(table.rowCount()):
                for column in range(table.columnCount()):
                    item = table.item(row, column)
                    source = item.data(2368) if item is not None else None
                    if source is not None:
                        displayed.append((item, item.text()))
                        item.setText(source)
            CrudPage.filter_table(table, text)
        finally:
            for item, value in displayed:
                item.setText(value)
            table.blockSignals(blocked)

    @batched_table_refresh
    def refresh(self, *_args) -> None:
        refresh_date_inputs(self, self.db)
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

        populate_year_filter(self, self.year_filter, strings=True)
        category = self.category_filter.currentData()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem(_text("Όλες οι κατηγορίες"), None)
        if not self.is_income:
            for value in sorted({r['category'] or '' for r in rows}):
                self.category_filter.addItem(_text(value) if value in ('Εργασία','Λίπανση','Άρδευση','Εξοπλισμός','Μεταφορές','Άλλο') else value, value)
        self.category_filter.setCurrentIndex(max(0, self.category_filter.findData(category)))
        self.category_filter.blockSignals(False)
        year = self.year_filter.currentData()
        category = self.category_filter.currentData()
        rows = [r for r in rows if (year is None or str(r['entry_date'] or '').startswith(year + '-'))
                and (self.is_income or category is None or (r['category'] or '') == category)]
        order = self.sort_order.currentData()
        rows = sorted(rows, key=lambda r: int(r['id']))
        rows.sort(key=lambda r: float(r['amount'] or 0) if order.startswith('amount') else str(r['entry_date'] or ''),
                  reverse=order.endswith('desc'))
        self.table.setRowCount(len(rows))
        date_format = selected_date_format(self.db)

        for row_index, row in enumerate(rows):
            if self.is_income:
                values = [
                    format_iso_date(row["entry_date"], self.db, display_format=date_format),
                    row["field_name"] or "Γενικό",
                    row["description"] or "",
                    row["partner"] or "",
                    row["payment_method"] or "",
                    f'{float(row["amount"] or 0):.2f} €',
                    row["notes"] or "",
                ]
            else:
                values = [
                    format_iso_date(row["entry_date"], self.db, display_format=date_format),
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
                if column_index == 1 and not row["field_name"]:
                    self._set_body(item, "Γενικό")
                elif not self.is_income and column_index == 3 and "source_type" in row.keys() and row["source_type"]:
                    self._set_body(item, "[Αυτόματο] {description}", description=row["description"] or "")
                self.table.setItem(row_index, column_index, item)

        self.filter_table(self.table, self.search.text())
