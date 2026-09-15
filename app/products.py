from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QFormLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from .crud import CrudPage
from .database import Database
from .language import combo_source_text, tr
from .ui_helpers import table_widget


class ProductsPage(CrudPage):
    """General product registry with non-destructive field associations."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_id: int | None = None
        self.selected_link: tuple[int, int] | None = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)
        content = QWidget()
        content.setObjectName("productsPageContent")
        content.setStyleSheet("QWidget#productsPageContent { background: #f5f6f3; }")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 18, 16, 20)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Προϊόντα")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)
        subtitle = QLabel("Γενικό μητρώο παραγόμενων προϊόντων και μονάδων μέτρησης")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.form_box = QGroupBox("Νέο προϊόν")
        form = QFormLayout(self.form_box)
        self.name = QLineEdit()
        self.name.setPlaceholderText("π.χ. Ντομάτες, Καρύδια")
        self.unit = QComboBox()
        self.unit.setEditable(True)
        self.unit.addItems(["kg", "τεμάχια", "λίτρα", "τόνοι", "κιβώτια"])
        form.addRow("Όνομα", self.name)
        form.addRow("Μονάδα μέτρησης", self.unit)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_product)
        buttons.addWidget(self.save_button)
        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.cancel_button)
        self.status_button = QPushButton("Απενεργοποίηση")
        self.status_button.clicked.connect(self.toggle_status)
        self.status_button.setEnabled(False)
        buttons.addWidget(self.status_button)
        buttons.addStretch()
        form.addRow("", buttons)
        layout.addWidget(self.form_box)

        filters = QHBoxLayout()
        self.status_filter = QComboBox()
        self.status_filter.addItem("Όλα", "all")
        self.status_filter.addItem("Ενεργά", 1)
        self.status_filter.addItem("Ανενεργά", 0)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση προϊόντος...")
        self.search.textChanged.connect(self.refresh)
        filters.addWidget(QLabel("Κατάσταση"))
        filters.addWidget(self.status_filter)
        filters.addWidget(self.search, 1)
        layout.addLayout(filters)
        self.table = table_widget(["Όνομα", "Μονάδα", "Κατάσταση"])
        self.table.cellClicked.connect(self.load_product)
        self.table.setMinimumHeight(190)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        links_box = QGroupBox("Συσχετίσεις προϊόντων με αγροτεμάχια")
        links_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        links_layout = QVBoxLayout(links_box)
        link_form = QHBoxLayout()
        self.link_product = QComboBox()
        self.link_product.setMinimumWidth(180)
        self.link_field = QComboBox()
        self.link_field.setMinimumWidth(180)
        self.add_link_button = QPushButton("Προσθήκη σύνδεσης")
        self.add_link_button.clicked.connect(self.add_link)
        link_form.addWidget(QLabel("Προϊόν"))
        link_form.addWidget(self.link_product, 1)
        link_form.addWidget(QLabel("Αγροτεμάχιο"))
        link_form.addWidget(self.link_field, 1)
        link_form.addWidget(self.add_link_button)
        links_layout.addLayout(link_form)
        self.links_table = table_widget([
            "Προϊόν", "Μονάδα", "Κατάσταση προϊόντος", "Αγροτεμάχιο",
            "Ποικιλία", "Φύτευση / έναρξη", "Κατάσταση καλλιέργειας",
        ])
        self.links_table.cellClicked.connect(self.select_link)
        self.links_table.setMinimumHeight(230)
        self.links_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.links_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.links_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        links_header = self.links_table.horizontalHeader()
        links_header.setStretchLastSection(False)
        links_header.setMinimumSectionSize(90)
        links_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column, width in enumerate([150, 100, 150, 180, 150, 150, 180]):
            self.links_table.setColumnWidth(column, width)
        links_layout.addWidget(self.links_table)

        profile_form = QFormLayout()
        self.link_variety = QLineEdit()
        self.link_variety.setPlaceholderText("Προαιρετική ποικιλία")
        date_row = QHBoxLayout()
        self.link_date_enabled = QCheckBox("Καθορισμένη")
        self.link_planting_date = QDateEdit(QDate.currentDate())
        self.link_planting_date.setCalendarPopup(True)
        self.link_planting_date.setDisplayFormat("dd/MM/yyyy")
        self.link_planting_date.setEnabled(False)
        self.link_date_enabled.toggled.connect(self.link_planting_date.setEnabled)
        date_row.addWidget(self.link_date_enabled)
        date_row.addWidget(self.link_planting_date)
        date_row.addStretch()
        self.link_cultivation_status = QComboBox()
        self.link_cultivation_status.addItem("Ενεργή", "active")
        self.link_cultivation_status.addItem("Ανενεργή", "inactive")
        profile_form.addRow("Ποικιλία", self.link_variety)
        profile_form.addRow("Φύτευση / έναρξη", date_row)
        profile_form.addRow("Κατάσταση καλλιέργειας", self.link_cultivation_status)
        links_layout.addLayout(profile_form)
        self.save_profile_button = QPushButton("Αποθήκευση στοιχείων καλλιέργειας")
        self.save_profile_button.setEnabled(False)
        self.save_profile_button.clicked.connect(self.save_link_profile)
        links_layout.addWidget(self.save_profile_button)
        self.remove_link_button = QPushButton("Αφαίρεση σύνδεσης")
        self.remove_link_button.setEnabled(False)
        self.remove_link_button.clicked.connect(self.remove_link)
        links_layout.addWidget(self.remove_link_button)
        layout.addWidget(links_box)
        self.refresh()

    def _duplicate(self, name: str, exclude_id: int | None = None):
        for row in self.db.query("SELECT id,name FROM products"):
            if exclude_id is not None and int(row["id"]) == exclude_id:
                continue
            if str(row["name"]).strip().casefold() == name.casefold():
                return row
        return None

    def save_product(self) -> None:
        name = self.name.text().strip()
        unit = combo_source_text(self.unit).strip()
        if not name or not unit:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Συμπλήρωσε όνομα και μονάδα μέτρησης.")
            return
        if self._duplicate(name, self.selected_id) is not None:
            QMessageBox.warning(self, "Διπλό προϊόν", "Υπάρχει ήδη προϊόν με αυτό το όνομα.")
            return
        if self.selected_id is None:
            self.db.execute("INSERT INTO products(name,unit,is_active) VALUES(?,?,1)", (name, unit))
        else:
            self.db.execute(
                "UPDATE products SET name=?,unit=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (name, unit, self.selected_id),
            )
        self.clear_form()
        self.refresh()

    def load_product(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        product_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        record = self.db.query_one("SELECT * FROM products WHERE id=?", (product_id,)) if product_id else None
        if record is None:
            return
        self.selected_id = int(record["id"])
        self.name.setText(record["name"])
        self.unit.setCurrentText(record["unit"])
        self.form_box.setTitle("Επεξεργασία προϊόντος")
        self.save_button.setText("Αποθήκευση")
        self.cancel_button.setEnabled(True)
        self.status_button.setText("Απενεργοποίηση" if record["is_active"] else "Ενεργοποίηση")
        self.status_button.setEnabled(True)

    def toggle_status(self) -> None:
        if self.selected_id is None:
            return
        row = self.db.query_one("SELECT is_active FROM products WHERE id=?", (self.selected_id,))
        if row is not None:
            self.db.execute(
                "UPDATE products SET is_active=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (0 if row["is_active"] else 1, self.selected_id),
            )
        self.clear_form()
        self.refresh()

    def clear_form(self) -> None:
        self.selected_id = None
        self.name.clear()
        self.unit.setCurrentText("kg")
        self.form_box.setTitle("Νέο προϊόν")
        self.save_button.setText("Προσθήκη")
        self.cancel_button.setEnabled(False)
        self.status_button.setEnabled(False)
        self.table.clearSelection()

    def _refresh_link_choices(self) -> None:
        product_id = self.link_product.currentData()
        field_id = self.link_field.currentData()
        self.link_product.clear()
        self.link_product.addItem("Επίλεξε ενεργό προϊόν", None)
        for row in self.db.query("SELECT id,name,unit FROM products WHERE is_active=1 ORDER BY name,id"):
            self.link_product.addItem(f"{row['name']} ({row['unit']})", int(row["id"]))
        index = self.link_product.findData(product_id)
        self.link_product.setCurrentIndex(index if index >= 0 else 0)
        self.link_field.clear()
        self.link_field.addItem("Επίλεξε αγροτεμάχιο", None)
        for row in self.db.query("SELECT id,name FROM fields ORDER BY name,id"):
            self.link_field.addItem(row["name"], int(row["id"]))
        index = self.link_field.findData(field_id)
        self.link_field.setCurrentIndex(index if index >= 0 else 0)

    def add_link(self) -> None:
        product_id = self.link_product.currentData()
        field_id = self.link_field.currentData()
        if product_id is None or field_id is None:
            QMessageBox.warning(self, "Ελλιπή στοιχεία", "Επίλεξε ενεργό προϊόν και αγροτεμάχιο.")
            return
        if self.db.query_one("SELECT 1 FROM product_fields WHERE product_id=? AND field_id=?", (product_id, field_id)):
            QMessageBox.information(self, "Υπάρχουσα σύνδεση", "Η σύνδεση υπάρχει ήδη.")
            return
        self.db.execute("INSERT INTO product_fields(product_id,field_id) VALUES(?,?)", (product_id, field_id))
        self.refresh()

    def select_link(self, row: int, _column: int) -> None:
        item = self.links_table.item(row, 0)
        pair = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.selected_link = tuple(pair) if pair else None
        self.remove_link_button.setEnabled(self.selected_link is not None)
        self.save_profile_button.setEnabled(self.selected_link is not None)
        if self.selected_link is None:
            return
        record = self.db.query_one(
            "SELECT variety,planting_date,cultivation_status FROM product_fields WHERE product_id=? AND field_id=?",
            self.selected_link,
        )
        if record is None:
            return
        self.link_variety.setText(record["variety"] or "")
        date = QDate.fromString(record["planting_date"] or "", "yyyy-MM-dd")
        self.link_date_enabled.setChecked(date.isValid())
        self.link_planting_date.setDate(date if date.isValid() else QDate.currentDate())
        index = self.link_cultivation_status.findData(record["cultivation_status"] or "active")
        self.link_cultivation_status.setCurrentIndex(index if index >= 0 else 0)

    @staticmethod
    def validate_profile(planting_date: str, status: str) -> None:
        if status not in {"active", "inactive"}:
            raise ValueError("invalid cultivation status")
        if planting_date and not QDate.fromString(planting_date, "yyyy-MM-dd").isValid():
            raise ValueError("invalid planting date")

    def save_link_profile(self) -> None:
        if self.selected_link is None:
            return
        planting_date = self.link_planting_date.date().toString("yyyy-MM-dd") if self.link_date_enabled.isChecked() else ""
        status = str(self.link_cultivation_status.currentData() or "")
        try:
            self.validate_profile(planting_date, status)
        except ValueError:
            QMessageBox.warning(self, "Μη έγκυρα στοιχεία", "Έλεγξε ημερομηνία και κατάσταση.")
            return
        self.db.execute(
            """UPDATE product_fields SET variety=?,planting_date=?,cultivation_status=?,
                      updated_at=CURRENT_TIMESTAMP WHERE product_id=? AND field_id=?""",
            (self.link_variety.text().strip(), planting_date, status, *self.selected_link),
        )
        self.refresh()

    def remove_link(self) -> None:
        if self.selected_link is None:
            return
        if not self.confirm_delete(
            self, "Αφαίρεση σύνδεσης",
            "Να αφαιρεθεί η σύνδεση προϊόντος–αγροτεμαχίου;\n\n"
            "Οι ιστορικές καταχωρήσεις Παραγωγής και Πωλήσεων δεν θα αλλάξουν.",
        ):
            return
        self.db.execute("DELETE FROM product_fields WHERE product_id=? AND field_id=?", self.selected_link)
        self.selected_link = None
        self.remove_link_button.setEnabled(False)
        self.save_profile_button.setEnabled(False)
        self.refresh()

    def _refresh_links(self) -> None:
        rows = self.db.query(
            """SELECT pf.product_id,pf.field_id,p.name product_name,p.unit,
                      p.is_active,f.name field_name,pf.variety,pf.planting_date,
                      pf.cultivation_status
               FROM product_fields pf JOIN products p ON p.id=pf.product_id
               JOIN fields f ON f.id=pf.field_id
               ORDER BY p.name,f.name,pf.product_id,pf.field_id"""
        )
        self.links_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["product_name"], row["unit"],
                tr("Ενεργό" if row["is_active"] else "Ανενεργό"), row["field_name"],
                row["variety"] or "—", row["planting_date"] or "—",
                tr("Ενεργή" if row["cultivation_status"] == "active" else "Ανενεργή"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.links_table.setItem(row_index, column, item)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, (int(row["product_id"]), int(row["field_id"])))

    def refresh(self, *_args) -> None:
        where: list[str] = []
        params: list[object] = []
        status = self.status_filter.currentData()
        if status != "all":
            where.append("is_active=?")
            params.append(status)
        search = self.search.text().strip()
        if search:
            where.append("name LIKE ?")
            params.append(f"%{search}%")
        sql = "SELECT * FROM products"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY is_active DESC,name COLLATE NOCASE,id"
        rows = self.db.query(sql, params)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["name"],
                row["unit"],
                tr("Ενεργό" if row["is_active"] else "Ανενεργό"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_index, column, item)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row["id"])
        self._refresh_link_choices()
        self._refresh_links()
