from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from .crud import CrudPage
from .database import Database
from .ui_helpers import compact_decimal, table_widget
from .widgets import area_input, required_text


class FieldsPage(CrudPage):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_field_id: int | None = None

        self._ensure_money_cleanup_trigger()

        layout = QVBoxLayout(self)

        title = QLabel("Αγροτεμάχια")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.form_box = QGroupBox("Νέο αγροτεμάχιο")
        form = QFormLayout(self.form_box)

        self.name = QLineEdit()
        self.kaek = QLineEdit()
        self.location = QLineEdit()
        self.area = area_input()
        self.trees = QSpinBox()
        self.trees.setRange(0, 1_000_000)
        self.notes = QLineEdit()

        form.addRow("Ονομασία", self.name)
        form.addRow("ΚΑΕΚ", self.kaek)
        form.addRow("Τοποθεσία", self.location)
        form.addRow("Έκταση", self.area)
        form.addRow("Παραγωγικά δέντρα", self.trees)
        form.addRow("Σημειώσεις", self.notes)

        buttons = QHBoxLayout()

        self.save_button = QPushButton("Προσθήκη")
        self.save_button.clicked.connect(self.save_field)

        self.cancel_button = QPushButton("Ακύρωση")
        self.cancel_button.clicked.connect(self.clear_form)
        self.cancel_button.setEnabled(False)

        self.delete_button = QPushButton("Διαγραφή")
        self.delete_button.clicked.connect(self.delete_field)
        self.delete_button.setEnabled(False)

        buttons.addWidget(self.save_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.delete_button)
        form.addRow("", buttons)

        layout.addWidget(self.form_box)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση αγροτεμαχίου...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda text: self.filter_table(self.table, text))
        layout.addWidget(self.search)

        self.table = table_widget(
            ["Ονομασία", "ΚΑΕΚ", "Τοποθεσία", "Έκταση", "Δέντρα", "Σημειώσεις"]
        )
        self.table.cellClicked.connect(self.load_selected)
        layout.addWidget(self.table)

        self.map_button = QPushButton("Χάρτης αγροτεμαχίου")
        self.map_button.clicked.connect(self.open_map)
        layout.addWidget(self.map_button)
        self.coordinates_button = QPushButton("Εξαγωγή κορυφών / συντεταγμένων")
        self.coordinates_button.clicked.connect(self.export_coordinates)
        layout.addWidget(self.coordinates_button)

        self.refresh()

    def open_map(self) -> None:
        if self.selected_field_id is None:
            QMessageBox.information(self, "Αγροτεμάχια", "Επίλεξε πρώτα αγροτεμάχιο.")
            return
        from .gis.dialog import ParcelMapDialog
        ParcelMapDialog(self.db, self.selected_field_id, self).exec()

    def export_coordinates(self) -> None:
        from .gis.export_dialog import CoordinateExportDialog
        CoordinateExportDialog(self.db,self.selected_field_id,self).exec()

    def _ensure_money_cleanup_trigger(self) -> None:
        income_columns = {
            row["name"]
            for row in self.db.query("PRAGMA table_info(income)")
        }
        expense_columns = {
            row["name"]
            for row in self.db.query("PRAGMA table_info(expenses)")
        }

        if "field_id" not in income_columns or "field_id" not in expense_columns:
            return

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

    def save_field(self) -> None:
        name = required_text(self.name, "Ονομασία")
        if name is None:
            return

        values = (
            name,
            self.kaek.text().strip(),
            self.location.text().strip(),
            self.area.value(),
            self.trees.value(),
            self.notes.text().strip(),
        )

        if self.selected_field_id is None:
            self.db.execute(
                """
                INSERT INTO fields
                    (name, kaek, location, area_stremma, productive_trees, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        else:
            self.db.execute(
                """
                UPDATE fields
                SET name=?,
                    kaek=?,
                    location=?,
                    area_stremma=?,
                    productive_trees=?,
                    notes=?
                WHERE id=?
                """,
                (*values, self.selected_field_id),
            )

        self.clear_form()
        self.refresh()

    def load_selected(self, row: int, _column: int) -> None:
        first_item = self.table.item(row, 0)
        if first_item is None:
            return

        field_id = first_item.data(Qt.ItemDataRole.UserRole)
        if field_id is None:
            return

        field = self.db.query_one("SELECT * FROM fields WHERE id=?", (field_id,))
        if field is None:
            self.refresh()
            return

        self.selected_field_id = int(field["id"])
        self.name.setText(field["name"] or "")
        self.kaek.setText(field["kaek"] or "")
        self.location.setText(field["location"] or "")
        self.area.setValue(float(field["area_stremma"] or 0))
        self.trees.setValue(int(field["productive_trees"] or 0))
        self.notes.setText(field["notes"] or "")

        self.form_box.setTitle("Επεξεργασία αγροτεμαχίου")
        self.save_button.setText("Αποθήκευση")
        self.cancel_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def clear_form(self) -> None:
        self.selected_field_id = None

        self.name.clear()
        self.kaek.clear()
        self.location.clear()
        self.area.setValue(0)
        self.trees.setValue(0)
        self.notes.clear()

        self.form_box.setTitle("Νέο αγροτεμάχιο")
        self.save_button.setText("Προσθήκη")
        self.cancel_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.table.clearSelection()
        self.name.setFocus()

    def delete_field(self) -> None:
        if self.selected_field_id is None:
            return

        field_name = self.name.text().strip() or "το επιλεγμένο αγροτεμάχιο"
        if not self.confirm_delete(
            self,
            "Διαγραφή αγροτεμαχίου",
            f'Να διαγραφεί το αγροτεμάχιο «{field_name}»;',
        ):
            return

        try:
            self.db.execute(
                "DELETE FROM fields WHERE id=?",
                (self.selected_field_id,),
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Αδυναμία διαγραφής",
                "Το αγροτεμάχιο δεν διαγράφηκε. "
                "Ενδέχεται να χρησιμοποιείται σε άλλες καταχωρήσεις.\n\n"
                f"Λεπτομέρειες: {exc}",
            )
            return

        self.clear_form()
        self.refresh()

    def refresh(self) -> None:
        rows = self.db.query("SELECT * FROM fields ORDER BY name, id")
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            values = [
                row["name"] or "",
                row["kaek"] or "",
                row["location"] or "",
                compact_decimal(row["area_stremma"], 3),
                str(int(row["productive_trees"] or 0)),
                row["notes"] or "",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, int(row["id"]))
                self.table.setItem(row_index, column_index, item)

        self.filter_table(self.table, self.search.text())
