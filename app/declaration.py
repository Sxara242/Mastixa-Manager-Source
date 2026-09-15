from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .ui_helpers import compact_decimal, format_kg, table_widget
from .year_lock import is_year_locked, warn_locked_year


class AutoGrowingTextEdit(QTextEdit):
    """Text box that grows with its content, then scrolls after a safe limit."""

    MIN_HEIGHT = 82
    MAX_HEIGHT = 220

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(self.MIN_HEIGHT)
        self.setMaximumHeight(self.MAX_HEIGHT)
        self.document().contentsChanged.connect(self._update_height)
        self._update_height()

    def _update_height(self) -> None:
        document_height = self.document().size().height()

        frame = self.frameWidth() * 2
        margins = self.contentsMargins()
        extra = (
            frame
            + margins.top()
            + margins.bottom()
            + 18
        )

        target = int(document_height + extra)
        target = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, target))
        self.setFixedHeight(target)


class DeclarationPage(QWidget):
    """
    Local cultivation-declaration workspace.

    This sprint stores a draft declaration and the exact fields selected for it.
    It does NOT upload anything externally. The Upload Center can use these
    saved drafts in the next sprint.
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._loading = False
        self._editing = False
        self._has_saved_declaration = False

        self._ensure_schema()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.viewport().setStyleSheet("background: #f5f6f3;")

        content = QWidget()
        content.setObjectName("declarationContent")
        content.setStyleSheet(
            "QWidget#declarationContent { background: #f5f6f3; }"
        )

        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 10, 12, 16)
        layout.setSpacing(12)

        title = QLabel("Δήλωση Καλλιέργειας")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Προετοιμασία και αποθήκευση πρόχειρης δήλωσης ανά έτος"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        top_box = QGroupBox()
        top_layout = QVBoxLayout(top_box)

        top_title = QLabel("Στοιχεία δήλωσης")
        top_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        top_layout.addWidget(top_title)

        form = QFormLayout()
        self.year = QComboBox()
        self.year.currentIndexChanged.connect(self._year_changed)
        form.addRow("Έτος", self.year)

        self.status = QLineEdit()
        self.status.setReadOnly(True)
        self.status.setProperty("mastixaI18nStaticText", True)
        form.addRow("Κατάσταση", self.status)

        self.notes = AutoGrowingTextEdit()
        self.notes.setPlaceholderText(
            "Προαιρετικές σημειώσεις για τη συγκεκριμένη δήλωση..."
        )
        form.addRow("Σημειώσεις", self.notes)

        top_layout.addLayout(form)
        layout.addWidget(top_box)

        producer_box = QGroupBox()
        producer_layout = QFormLayout(producer_box)

        producer_title = QLabel("Στοιχεία παραγωγού")
        producer_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        producer_layout.addRow(producer_title)

        self.producer_name = QLabel("—")
        self.producer_tax_id = QLabel("—")
        producer_layout.addRow("Ονοματεπώνυμο / Επωνυμία", self.producer_name)
        producer_layout.addRow("ΑΦΜ", self.producer_tax_id)

        layout.addWidget(producer_box)

        selection_box = QGroupBox()
        selection_layout = QVBoxLayout(selection_box)

        selection_title = QLabel("Αγροτεμάχια που περιλαμβάνονται")
        selection_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        selection_layout.addWidget(selection_title)

        select_buttons = QHBoxLayout()

        self.select_all_button = QPushButton("Επιλογή όλων")
        self.select_all_button.clicked.connect(
            lambda: self._set_all_checked(True)
        )
        select_buttons.addWidget(self.select_all_button)

        self.clear_all_button = QPushButton("Καμία επιλογή")
        self.clear_all_button.clicked.connect(
            lambda: self._set_all_checked(False)
        )
        select_buttons.addWidget(self.clear_all_button)

        self.refresh_button = QPushButton("Ανανέωση δεδομένων")
        self.refresh_button.clicked.connect(self.refresh)
        select_buttons.addWidget(self.refresh_button)

        select_buttons.addStretch()
        selection_layout.addLayout(select_buttons)

        self.table = table_widget(
            [
                "Επιλογή",
                "Αγροτεμάχιο",
                "ΚΑΕΚ",
                "Τοποθεσία",
                "Έκταση στρ.",
                "Παραγωγικά δέντρα",
                "Παραγωγή kg",
            ]
        )
        self.table.itemChanged.connect(self._selection_changed)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.table.setMinimumHeight(125)

        selection_layout.addWidget(self.table)

        layout.addWidget(selection_box)

        summary_box = QGroupBox()
        summary_layout = QHBoxLayout(summary_box)

        self.selected_fields_label = QLabel("Αγροτεμάχια: 0")
        self.area_label = QLabel("Έκταση: 0 στρ.")
        self.trees_label = QLabel("Παραγωγικά δέντρα: 0")
        self.production_label = QLabel("Παραγωγή: 0 kg")

        for widget in (
            self.selected_fields_label,
            self.area_label,
            self.trees_label,
            self.production_label,
        ):
            widget.setStyleSheet(
                "font-weight: 700; color: #26382f; padding: 4px 8px;"
            )
            summary_layout.addWidget(widget)

        summary_layout.addStretch()
        layout.addWidget(summary_box)

        action_box = QGroupBox()
        action_layout = QHBoxLayout(action_box)

        local_only = QLabel(
            "Η δήλωση αποθηκεύεται τοπικά. Δεν αποστέλλεται αυτόματα."
        )
        local_only.setStyleSheet("color: #67746d;")
        action_layout.addWidget(local_only)
        action_layout.addStretch()

        self.edit_button = QPushButton("Επεξεργασία δήλωσης")
        self.edit_button.clicked.connect(self.start_edit)
        action_layout.addWidget(self.edit_button)

        self.cancel_button = QPushButton("Ακύρωση αλλαγών")
        self.cancel_button.clicked.connect(self.cancel_edit)
        action_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("Αποθήκευση πρόχειρης δήλωσης")
        self.save_button.clicked.connect(self.save_draft)
        action_layout.addWidget(self.save_button)

        # Explicit style so these buttons remain clearly visible even inside
        # scrollable/group-box content.
        action_button_style = """
            QPushButton {
                background: #52745f;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #3f604c;
            }
            QPushButton:pressed {
                background: #324f3f;
            }
            QPushButton:disabled {
                background: #D5DDD8;
                color: #58665F;
                border: 1px solid #C4CEC8;
            }
        """

        for button in (
            self.select_all_button,
            self.clear_all_button,
            self.refresh_button,
            self.edit_button,
            self.cancel_button,
            self.save_button,
        ):
            button.setStyleSheet(action_button_style)

        layout.addWidget(action_box)

        self.refresh()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _ensure_schema(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS cultivation_declarations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                declaration_year INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'draft',
                producer_name TEXT NOT NULL DEFAULT '',
                producer_tax_id TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS cultivation_declaration_fields (
                declaration_id INTEGER NOT NULL,
                field_id INTEGER NOT NULL,
                PRIMARY KEY (declaration_id, field_id),
                FOREIGN KEY (declaration_id)
                    REFERENCES cultivation_declarations(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (field_id)
                    REFERENCES fields(id)
                    ON DELETE CASCADE
            )
            """
        )

    def _load_years(self) -> None:
        current = self.year.currentData()
        current_year = QDate.currentDate().year()

        rows = self.db.query(
            """
            SELECT DISTINCT year
            FROM (
                SELECT CAST(SUBSTR(entry_date, 1, 4) AS INTEGER) AS year
                FROM production
                WHERE entry_date IS NOT NULL AND entry_date <> ''

                UNION

                SELECT declaration_year AS year
                FROM cultivation_declarations
            )
            WHERE year IS NOT NULL
            ORDER BY year DESC
            """
        )

        years = {current_year}
        for row in rows:
            try:
                years.add(int(row["year"]))
            except (TypeError, ValueError):
                continue

        self.year.blockSignals(True)
        self.year.clear()
        for value in sorted(years, reverse=True):
            self.year.addItem(str(value), value)

        index = self.year.findData(current)
        if index < 0:
            index = self.year.findData(current_year)
        if index >= 0:
            self.year.setCurrentIndex(index)
        self.year.blockSignals(False)

    def _refresh_producer(self) -> None:
        row = self.db.query_one("SELECT * FROM producer WHERE id=1")

        if row is None:
            self.producer_name.setText("—")
            self.producer_tax_id.setText("—")
            return

        self.producer_name.setText(row["name"] or "—")
        self.producer_tax_id.setText(row["tax_id"] or "—")

    def _year_changed(self, _index: int) -> None:
        if self._loading:
            return

        # Normally the year combo is disabled while editing, so changing year
        # always means "load that declaration".
        self._editing = False
        self._load_current_year()

    def refresh(self) -> None:
        # Restoring an older compatible backup can remove these newer tables.
        # Recreate them transparently when the page is refreshed.
        self._ensure_schema()

        self._editing = False
        self._loading = True
        try:
            self._load_years()
            self._refresh_producer()
            self._load_current_year()
        finally:
            self._loading = False

    def _load_current_year(self) -> None:
        year = self.year.currentData()
        if year is None:
            return

        declaration = self.db.query_one(
            """
            SELECT *
            FROM cultivation_declarations
            WHERE declaration_year=?
            """,
            (year,),
        )

        if declaration is None:
            self._has_saved_declaration = False
            selected_ids = {
                int(row["id"])
                for row in self.db.query("SELECT id FROM fields")
            }
            self.notes.clear()
            self.status.setText("Πρόχειρη — δεν έχει αποθηκευτεί")

            # A brand-new declaration starts directly in edit mode.
            self._editing = True
        else:
            self._has_saved_declaration = True
            declaration_id = int(declaration["id"])
            selected_ids = {
                int(row["field_id"])
                for row in self.db.query(
                    """
                    SELECT field_id
                    FROM cultivation_declaration_fields
                    WHERE declaration_id=?
                    """,
                    (declaration_id,),
                )
            }

            self.notes.setPlainText(declaration["notes"] or "")

            updated_at = declaration["updated_at"] or ""
            if updated_at:
                self.status.setText(
                    f"Πρόχειρη — αποθηκευμένη ({updated_at})"
                )
            else:
                self.status.setText("Πρόχειρη — αποθηκευμένη")

            # Draft declarations are meant to be adjusted repeatedly. Open an
            # unlocked saved draft directly in edit mode so field checkboxes
            # and Select all / Clear all respond immediately. _apply_edit_mode
            # still forces read-only mode for a locked year.
            self._editing = True

        self._populate_fields(int(year), selected_ids)
        self._apply_edit_mode()

    def _populate_fields(
        self,
        year: int,
        selected_ids: set[int],
    ) -> None:
        rows = self.db.query(
            """
            SELECT
                f.id,
                f.name,
                f.kaek,
                f.location,
                f.area_stremma,
                f.productive_trees,
                COALESCE(SUM(
                    CASE
                        WHEN SUBSTR(p.entry_date, 1, 4)=?
                        THEN p.quantity_kg
                        ELSE 0
                    END
                ), 0) AS production_total
            FROM fields f
            LEFT JOIN production p ON p.field_id = f.id
            GROUP BY
                f.id,
                f.name,
                f.kaek,
                f.location,
                f.area_stremma,
                f.productive_trees
            ORDER BY f.name, f.id
            """,
            (str(year),),
        )

        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            field_id = int(row["id"])

            check_item = QTableWidgetItem("")
            check_item.setData(Qt.ItemDataRole.UserRole, field_id)
            check_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            check_item.setCheckState(
                Qt.CheckState.Checked
                if field_id in selected_ids
                else Qt.CheckState.Unchecked
            )
            self.table.setItem(row_index, 0, check_item)

            values = [
                row["name"] or "",
                row["kaek"] or "",
                row["location"] or "",
                compact_decimal(row["area_stremma"], 3),
                str(int(row["productive_trees"] or 0)),
                compact_decimal(row["production_total"], 3),
            ]

            for column_index, value in enumerate(values, start=1):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

        self.table.blockSignals(False)
        self._update_summary()

    def _apply_edit_mode(self) -> None:
        year = self.year.currentData()
        locked = (
            year is not None
            and is_year_locked(self.db, int(year))
        )

        if locked:
            self._editing = False

        editing = self._editing

        self.notes.setReadOnly(not editing)
        self.select_all_button.setEnabled(editing)
        self.clear_all_button.setEnabled(editing)

        # Refresh is useful in view mode. While editing it would throw away the
        # unsaved changes, so keep it disabled until Save/Cancel.
        self.refresh_button.setEnabled(not editing)

        # Keep the year fixed during an edit session.
        self.year.setEnabled(not editing or not self._has_saved_declaration)

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue

            flags = (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            if editing:
                flags |= Qt.ItemFlag.ItemIsUserCheckable

            item.setFlags(flags)

        if locked:
            self.status.setText(
                f"{self.status.text()} — ΚΛΕΙΔΩΜΕΝΟ {int(year)}"
            )
            self.edit_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_button.setText("Κλειδωμένο")
            self.save_button.setEnabled(False)
        elif self._has_saved_declaration:
            self.edit_button.setVisible(not editing)
            self.save_button.setVisible(editing)
            self.cancel_button.setVisible(editing)
            self.save_button.setEnabled(True)

            if editing:
                self.save_button.setText("Αποθήκευση αλλαγών")
            else:
                self.save_button.setText("Αποθήκευση πρόχειρης δήλωσης")
        else:
            # New, unsaved declaration: there is nothing to "edit" or cancel
            # back to yet.
            self.edit_button.setVisible(False)
            self.cancel_button.setVisible(False)
            self.save_button.setVisible(True)
            self.save_button.setEnabled(True)
            self.save_button.setText("Αποθήκευση πρόχειρης δήλωσης")

    def start_edit(self) -> None:
        if not self._has_saved_declaration:
            return

        year = self.year.currentData()
        if (
            year is not None
            and is_year_locked(self.db, int(year))
        ):
            warn_locked_year(self, self.db, int(year))
            return

        self._editing = True
        self.status.setText("Πρόχειρη — επεξεργασία")
        self._apply_edit_mode()
        self.notes.setFocus()

    def cancel_edit(self) -> None:
        if not self._has_saved_declaration:
            return

        answer = QMessageBox.question(
            self,
            "Ακύρωση αλλαγών",
            "Να ακυρωθούν οι μη αποθηκευμένες αλλαγές;",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._editing = False
        self._load_current_year()

    def _checked_field_ids(self) -> list[int]:
        ids: list[int] = []

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            if item.checkState() != Qt.CheckState.Checked:
                continue

            field_id = item.data(Qt.ItemDataRole.UserRole)
            if field_id is not None:
                ids.append(int(field_id))

        return ids

    def _set_all_checked(self, checked: bool) -> None:
        state = (
            Qt.CheckState.Checked
            if checked
            else Qt.CheckState.Unchecked
        )

        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None:
                item.setCheckState(state)
        self.table.blockSignals(False)

        self._update_summary()

    def _selection_changed(self, item: QTableWidgetItem) -> None:
        if self._loading or not self._editing or item.column() != 0:
            return
        self._update_summary()

    def _update_summary(self) -> None:
        count = 0
        area = 0.0
        trees = 0
        production = 0.0

        for row in range(self.table.rowCount()):
            check_item = self.table.item(row, 0)
            if (
                check_item is None
                or check_item.checkState() != Qt.CheckState.Checked
            ):
                continue

            count += 1

            area_item = self.table.item(row, 4)
            trees_item = self.table.item(row, 5)
            production_item = self.table.item(row, 6)

            try:
                area += float(area_item.text()) if area_item else 0.0
            except ValueError:
                pass

            try:
                trees += int(trees_item.text()) if trees_item else 0
            except ValueError:
                pass

            try:
                production += (
                    float(production_item.text())
                    if production_item
                    else 0.0
                )
            except ValueError:
                pass

        self.selected_fields_label.setText(f"Αγροτεμάχια: {count}")
        self.area_label.setText(
            f"Έκταση: {compact_decimal(area, 3)} στρ."
        )
        self.trees_label.setText(f"Παραγωγικά δέντρα: {trees}")
        self.production_label.setText(
            f"Παραγωγή: {format_kg(production)}"
        )

    def save_draft(self) -> None:
        if self._has_saved_declaration and not self._editing:
            return

        year = self.year.currentData()
        if year is None:
            QMessageBox.warning(
                self,
                "Δήλωση Καλλιέργειας",
                "Δεν έχει επιλεγεί έτος.",
            )
            return

        if is_year_locked(self.db, int(year)):
            warn_locked_year(self, self.db, int(year))
            self._apply_edit_mode()
            return

        selected_ids = self._checked_field_ids()

        if not selected_ids:
            QMessageBox.warning(
                self,
                "Δήλωση Καλλιέργειας",
                "Επίλεξε τουλάχιστον ένα αγροτεμάχιο.",
            )
            return

        producer = self.db.query_one(
            "SELECT name, tax_id FROM producer WHERE id=1"
        )
        producer_name = (
            producer["name"] if producer is not None else ""
        ) or ""
        producer_tax_id = (
            producer["tax_id"] if producer is not None else ""
        ) or ""

        self.db.execute(
            """
            INSERT INTO cultivation_declarations (
                declaration_year,
                status,
                producer_name,
                producer_tax_id,
                notes,
                updated_at
            )
            VALUES (?, 'draft', ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(declaration_year)
            DO UPDATE SET
                status='draft',
                producer_name=excluded.producer_name,
                producer_tax_id=excluded.producer_tax_id,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                int(year),
                producer_name,
                producer_tax_id,
                self.notes.toPlainText().strip(),
            ),
        )

        declaration = self.db.query_one(
            """
            SELECT id
            FROM cultivation_declarations
            WHERE declaration_year=?
            """,
            (int(year),),
        )

        if declaration is None:
            QMessageBox.critical(
                self,
                "Δήλωση Καλλιέργειας",
                "Δεν ήταν δυνατή η αποθήκευση της δήλωσης.",
            )
            return

        declaration_id = int(declaration["id"])

        self.db.execute(
            """
            DELETE FROM cultivation_declaration_fields
            WHERE declaration_id=?
            """,
            (declaration_id,),
        )

        for field_id in selected_ids:
            self.db.execute(
                """
                INSERT INTO cultivation_declaration_fields (
                    declaration_id,
                    field_id
                )
                VALUES (?, ?)
                """,
                (declaration_id, field_id),
            )

        self._editing = False
        self._load_current_year()

        QMessageBox.information(
            self,
            "Δήλωση Καλλιέργειας",
            "Η πρόχειρη δήλωση αποθηκεύτηκε επιτυχώς.\n\n"
            "Δεν έχει γίνει καμία εξωτερική αποστολή.",
        )
