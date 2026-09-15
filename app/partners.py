from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
from .partner_links import ensure_partner_link_schema, sync_partner_names


PARTNER_TYPES = [
    ("Προμηθευτής", "supplier"),
    ("Αγοραστής", "buyer"),
    ("Προμηθευτής & Αγοραστής", "both"),
]


class PartnersPage(CrudPage):
    """Ενιαίο μητρώο προμηθευτών και αγοραστών."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_partner_id: int | None = None
        self._ensure_schema()
        ensure_partner_link_schema(self.db)

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
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 18, 12, 12)
        layout.setSpacing(10)
        scroll.setWidget(content)

        title = QLabel("Προμηθευτές & Αγοραστές")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Στοιχεία συνεργατών και συγκεντρωτική εικόνα αγορών / πωλήσεων"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        metrics = QHBoxLayout()
        self.total_metric = self._metric("Συνεργάτες")
        self.suppliers_metric = self._metric("Προμηθευτές")
        self.buyers_metric = self._metric("Αγοραστές")
        for card, _value in (
            self.total_metric,
            self.suppliers_metric,
            self.buyers_metric,
        ):
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        self.form_box = QGroupBox("Νέος συνεργάτης")
        form = QFormLayout(self.form_box)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Επωνυμία ή ονοματεπώνυμο")
        self.partner_type = QComboBox()
        for label, value in PARTNER_TYPES:
            self.partner_type.addItem(label, value)
        self.tax_id = QLineEdit()
        self.tax_id.setPlaceholderText("ΑΦΜ")
        self.contact_person = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()
        self.products = QLineEdit()
        self.products.setPlaceholderText(
            "Π.χ. λιπάσματα, καύσιμα ή αγροτικά προϊόντα"
        )
        self.payment_terms = QLineEdit()
        self.payment_terms.setPlaceholderText("Π.χ. 30 ημέρες, μετρητά")
        self.notes = QLineEdit()
        form.addRow("Επωνυμία / όνομα", self.name)
        form.addRow("Τύπος συνεργάτη", self.partner_type)
        form.addRow("ΑΦΜ", self.tax_id)
        form.addRow("Υπεύθυνος επικοινωνίας", self.contact_person)
        form.addRow("Τηλέφωνο", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Διεύθυνση", self.address)
        form.addRow("Προϊόντα / υπηρεσίες", self.products)
        form.addRow("Όροι πληρωμής", self.payment_terms)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Προσθήκη συνεργάτη")
        self.save_button.clicked.connect(self.save_partner)
        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)
        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_partner)
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

        list_box = QGroupBox("Μητρώο συνεργατών")
        list_layout = QVBoxLayout(list_box)
        filters = QHBoxLayout()
        self.type_filter = QComboBox()
        self.type_filter.addItem("Όλοι οι συνεργάτες", None)
        for label, value in PARTNER_TYPES:
            self.type_filter.addItem(label, value)
        self.type_filter.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση ονόματος, ΑΦΜ, τηλεφώνου ή προϊόντος..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(self.type_filter)
        filters.addWidget(self.search, 1)
        list_layout.addLayout(filters)

        self.table = table_widget(
            [
                "Επωνυμία / όνομα",
                "Τύπος",
                "ΑΦΜ",
                "Τηλέφωνο",
                "Email",
                "Αγορές",
                "Πωλήσεις",
            ]
        )
        self.table.cellClicked.connect(self.load_partner)
        self.table.setMinimumHeight(260)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3, 5, 6):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        list_layout.addWidget(self.table)
        layout.addWidget(list_box)

        history_box = QGroupBox("Κινήσεις επιλεγμένου συνεργάτη")
        history_layout = QVBoxLayout(history_box)
        self.history_summary = QLabel(
            "Επίλεξε συνεργάτη για προβολή σχετικών εσόδων και εξόδων."
        )
        self.history_summary.setStyleSheet(
            "font-weight: 700; color: #315F49; background: transparent;"
        )
        history_layout.addWidget(self.history_summary)
        self.history_table = table_widget(
            ["Ημερομηνία", "Κίνηση", "Περιγραφή", "Ποσό", "Πληρωμή"]
        )
        self.history_table.setMinimumHeight(220)
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_box)
        layout.addStretch()
        self.refresh()

    @staticmethod
    def _metric(caption: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        layout = QVBoxLayout(box)
        label = QLabel(caption)
        label.setObjectName("metricCaption")
        value = QLabel("0")
        value.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return box, value

    def _ensure_schema(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS business_partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                partner_type TEXT NOT NULL DEFAULT 'supplier',
                tax_id TEXT NOT NULL DEFAULT '',
                contact_person TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                products TEXT NOT NULL DEFAULT '',
                payment_terms TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_business_partners_name
            ON business_partners(LOWER(TRIM(name)))
            """
        )
        if self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_events'"
        ) is None:
            return
        for sql in (
            """CREATE TRIGGER IF NOT EXISTS audit_business_partners_insert
            AFTER INSERT ON business_partners BEGIN
            INSERT INTO audit_events(event_time,table_name,action,record_id,details)
            VALUES(datetime('now','localtime'),'business_partners','INSERT',CAST(NEW.id AS TEXT),'Συνεργάτης: '||NEW.name); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_business_partners_update
            AFTER UPDATE ON business_partners BEGIN
            INSERT INTO audit_events(event_time,table_name,action,record_id,details)
            VALUES(datetime('now','localtime'),'business_partners','UPDATE',CAST(NEW.id AS TEXT),'Συνεργάτης: '||NEW.name); END""",
            """CREATE TRIGGER IF NOT EXISTS audit_business_partners_delete
            AFTER DELETE ON business_partners BEGIN
            INSERT INTO audit_events(event_time,table_name,action,record_id,details)
            VALUES(datetime('now','localtime'),'business_partners','DELETE',CAST(OLD.id AS TEXT),'Συνεργάτης: '||OLD.name); END""",
        ):
            self.db.execute(sql)

    def save_partner(self) -> None:
        name = self.name.text().strip()
        if not name:
            QMessageBox.warning(
                self, "Ελλιπή στοιχεία", "Συμπλήρωσε την επωνυμία ή το όνομα."
            )
            self.name.setFocus()
            return
        duplicate = self.db.query_one(
            """
            SELECT id FROM business_partners
            WHERE LOWER(TRIM(name))=LOWER(TRIM(?))
              AND id<>COALESCE(?, -1)
            """,
            (name, self.selected_partner_id),
        )
        if duplicate is not None:
            QMessageBox.warning(
                self, "Διπλός συνεργάτης", "Υπάρχει ήδη συνεργάτης με αυτό το όνομα."
            )
            return
        values = (
            name,
            self.partner_type.currentData(),
            self.tax_id.text().strip(),
            self.contact_person.text().strip(),
            self.phone.text().strip(),
            self.email.text().strip(),
            self.address.text().strip(),
            self.products.text().strip(),
            self.payment_terms.text().strip(),
            self.notes.text().strip(),
        )
        if self.selected_partner_id is None:
            partner_id = int(
                self.db.execute(
                    """
                    INSERT INTO business_partners(
                        name,partner_type,tax_id,contact_person,phone,email,
                        address,products,payment_terms,notes
                    ) VALUES(?,?,?,?,?,?,?,?,?,?)
                    """,
                    values,
                )
            )
        else:
            partner_id = self.selected_partner_id
            self.db.execute(
                """
                UPDATE business_partners SET
                    name=?,partner_type=?,tax_id=?,contact_person=?,phone=?,
                    email=?,address=?,products=?,payment_terms=?,notes=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (*values, partner_id),
            )

        sync_partner_names(
            self.db,
            int(partner_id),
            name,
        )

        self.clear_form()
        self.refresh()

    def load_partner(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        partner_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        record = self.db.query_one(
            "SELECT * FROM business_partners WHERE id=?", (partner_id,)
        ) if partner_id else None
        if record is None:
            return
        self.selected_partner_id = int(record["id"])
        self.name.setText(record["name"] or "")
        index = self.partner_type.findData(record["partner_type"])
        self.partner_type.setCurrentIndex(index if index >= 0 else 0)
        self.tax_id.setText(record["tax_id"] or "")
        self.contact_person.setText(record["contact_person"] or "")
        self.phone.setText(record["phone"] or "")
        self.email.setText(record["email"] or "")
        self.address.setText(record["address"] or "")
        self.products.setText(record["products"] or "")
        self.payment_terms.setText(record["payment_terms"] or "")
        self.notes.setText(record["notes"] or "")
        self.form_box.setTitle("Επεξεργασία συνεργάτη")
        self.save_button.setText("Αποθήκευση")
        self.cancel_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self._refresh_history(int(record["id"]), record["name"] or "")

    def clear_form(self) -> None:
        self.selected_partner_id = None
        for widget in (
            self.name, self.tax_id, self.contact_person, self.phone,
            self.email, self.address, self.products, self.payment_terms,
            self.notes,
        ):
            widget.clear()
        self.partner_type.setCurrentIndex(0)
        self.form_box.setTitle("Νέος συνεργάτης")
        self.save_button.setText("Προσθήκη συνεργάτη")
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()
        self.history_table.setRowCount(0)
        self.history_summary.setText(
            "Επίλεξε συνεργάτη για προβολή σχετικών εσόδων και εξόδων."
        )

    def delete_partner(self) -> None:
        if self.selected_partner_id is None:
            return
        if not self.confirm_delete(
            self, "Διαγραφή συνεργάτη", "Να διαγραφεί ο επιλεγμένος συνεργάτης;"
        ):
            return
        if self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_movements'"
        ) is not None:
            movement_columns = {
                row["name"]
                for row in self.db.query(
                    "PRAGMA table_info(inventory_movements)"
                )
            }
            if "partner_id" in movement_columns:
                self.db.execute(
                    "UPDATE inventory_movements SET partner_id=NULL WHERE partner_id=?",
                    (self.selected_partner_id,),
                )

        self.db.execute(
            "DELETE FROM business_partners WHERE id=?",
            (self.selected_partner_id,),
        )
        self.clear_form()
        self.refresh()

    @staticmethod
    def _type_label(value: str) -> str:
        return dict((value, label) for label, value in PARTNER_TYPES).get(
            value, value
        )

    def _refresh_history(
        self,
        partner_id: int,
        name: str,
    ) -> None:
        ensure_partner_link_schema(self.db)

        rows = self.db.query(
            """
            SELECT
                entry_date,
                'Έσοδο' AS movement,
                description,
                amount,
                payment_method
            FROM income
            WHERE
                partner_id=?
                OR (
                    partner_id IS NULL
                    AND LOWER(TRIM(partner))=LOWER(TRIM(?))
                )

            UNION ALL

            SELECT
                entry_date,
                'Έξοδο' AS movement,
                description,
                amount,
                payment_method
            FROM expenses
            WHERE
                partner_id=?
                OR (
                    partner_id IS NULL
                    AND LOWER(TRIM(supplier))=LOWER(TRIM(?))
                )

            ORDER BY entry_date DESC
            """,
            (partner_id, name, partner_id, name),
        )

        self.history_table.setRowCount(len(rows))
        income_total = 0.0
        expense_total = 0.0

        for row_index, row in enumerate(rows):
            amount = float(row["amount"] or 0)

            if row["movement"] == "Έσοδο":
                income_total += amount
            else:
                expense_total += amount

            values = [
                row["entry_date"] or "",
                row["movement"],
                row["description"] or "",
                f"{amount:.2f} €",
                row["payment_method"] or "",
            ]

            for column, value in enumerate(values):
                self.history_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(str(value)),
                )

        self.history_summary.setText(
            f"{name} — Πωλήσεις: {income_total:.2f} € | "
            f"Αγορές: {expense_total:.2f} €"
        )

    def refresh(self, *_args) -> None:
        self._ensure_schema()
        partner_type = self.type_filter.currentData()
        search = self.search.text().strip()
        where = ["1=1"]
        params: list[object] = []
        if partner_type == "supplier":
            where.append("p.partner_type IN ('supplier','both')")
        elif partner_type == "buyer":
            where.append("p.partner_type IN ('buyer','both')")
        elif partner_type == "both":
            where.append("p.partner_type='both'")
        if search:
            token = f"%{search}%"
            where.append(
                "(p.name LIKE ? OR p.tax_id LIKE ? OR p.phone LIKE ? OR p.products LIKE ?)"
            )
            params.extend([token, token, token, token])
        rows = self.db.query(
            f"""
            SELECT p.*,
              COALESCE((
                SELECT SUM(amount)
                FROM expenses
                WHERE
                    partner_id=p.id
                    OR (
                        partner_id IS NULL
                        AND LOWER(TRIM(supplier))=LOWER(TRIM(p.name))
                    )
              ),0) purchases,
              COALESCE((
                SELECT SUM(amount)
                FROM income
                WHERE
                    partner_id=p.id
                    OR (
                        partner_id IS NULL
                        AND LOWER(TRIM(partner))=LOWER(TRIM(p.name))
                    )
              ),0) sales
            FROM business_partners p
            WHERE {' AND '.join(where)}
            ORDER BY p.name,p.id
            """,
            params,
        )
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["name"], self._type_label(row["partner_type"]),
                row["tax_id"], row["phone"], row["email"],
                f"{float(row['purchases'] or 0):.2f} €",
                f"{float(row['sales'] or 0):.2f} €",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value or ""))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
                self.table.setItem(row_index, column, item)
        all_rows = self.db.query(
            "SELECT partner_type,COUNT(*) total FROM business_partners GROUP BY partner_type"
        )
        counts = {row["partner_type"]: int(row["total"]) for row in all_rows}
        self.total_metric[1].setText(str(sum(counts.values())))
        self.suppliers_metric[1].setText(
            str(counts.get("supplier", 0) + counts.get("both", 0))
        )
        self.buyers_metric[1].setText(
            str(counts.get("buyer", 0) + counts.get("both", 0))
        )
