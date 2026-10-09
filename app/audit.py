from __future__ import annotations

import csv
import re
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .localized_messages import _text, _language, _message
from .database import Database
from .ui_helpers import table_widget, scrollable_entry_layout


TABLE_LABELS = {
    "producer": "Παραγωγός",
    "fields": "Αγροτεμάχια",
    "production": "Παραγωγή",
    "income": "Έσοδα",
    "expenses": "Έξοδα",
    "cultivation_declarations": "Δήλωση Καλλιέργειας",
    "upload_packages": "Κέντρο Αποστολής",
    "year_locks": "Κλείδωμα Έτους",
    "farm_activities": "Άρδευση & Λίπανση",
    "inventory_items": "Αποθήκη — Είδη",
    "inventory_movements": "Αποθήκη — Κινήσεις",
    "equipment": "Μηχανήματα",
    "equipment_maintenance": "Συντηρήσεις μηχανημάτων",
    "business_partners": "Προμηθευτές & Αγοραστές",
    "invoice_documents": "Έγγραφα Τιμολογίων",
    "plant_protection_records": "Φυτοπροστασία",
    "workers": "Εργαζόμενοι",
    "labor_entries": "Εργατικά",
    "planting_batches": "Φυτεύσεις & Δέντρα",
    "production_sales": "Πωλήσεις Παραγωγής",
}

ACTION_LABELS = {
    "INSERT": "Προσθήκη",
    "UPDATE": "Επεξεργασία",
    "DELETE": "Διαγραφή",
}


class AuditPage(QWidget):
    """
    Read-only activity history.

    SQLite triggers record future INSERT / UPDATE / DELETE operations from
    v0.11 onward. Existing historical edits from before this sprint cannot be
    reconstructed retroactively.
    """


    @staticmethod
    def _body_render(spec):
        template, values, labels = spec
        return _text(template, **dict(values, **{k: _text(v) for k, v in labels.items()}))

    def _set_body(self, item, template, *, _labels=None, **values):
        spec = (template, values, _labels or {})
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
        for name in ('count_label', 'empty_label'):
            label = getattr(self, name, None)
            spec = label.property("mastixaBodyTemplate") if label is not None else None
            if spec is not None:
                label.setText(self._body_render(spec))

    def __init__(self, db: Database) -> None:
        super().__init__()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self._refresh_body_language)
        self.db = db

        self._ensure_schema_and_triggers()

        layout = scrollable_entry_layout(self)

        title = QLabel("Ιστορικό Ενεργειών")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Καταγραφή αλλαγών στη βάση δεδομένων από αυτή την έκδοση και μετά"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        filters_box = QGroupBox()
        filters_layout = QVBoxLayout(filters_box)

        filters_title = QLabel("Φίλτρα")
        filters_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        filters_layout.addWidget(filters_title)

        row = QGridLayout()

        row.addWidget(QLabel("Από"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        self.date_from.setDate(QDate.currentDate().addYears(-10))
        self.date_from.dateChanged.connect(self.refresh)
        row.addWidget(self.date_from, 0, 1)

        row.addWidget(QLabel("Έως"), 0, 2)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.refresh)
        row.addWidget(self.date_to, 0, 3)

        row.addWidget(QLabel("Ενότητα"), 1, 0)
        self.section = QComboBox()
        self.section.addItem("Όλες", None)
        for table_name, label in TABLE_LABELS.items():
            self.section.addItem(label, table_name)
        self.section.currentIndexChanged.connect(self.refresh)
        row.addWidget(self.section, 1, 1)

        row.addWidget(QLabel("Ενέργεια"), 1, 2)
        self.action = QComboBox()
        self.action.addItem("Όλες", None)
        self.action.addItem("Προσθήκη", "INSERT")
        self.action.addItem("Επεξεργασία", "UPDATE")
        self.action.addItem("Διαγραφή", "DELETE")
        self.action.currentIndexChanged.connect(self.refresh)
        row.addWidget(self.action, 1, 3)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση σε λεπτομέρειες, ενότητα ή ID..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)
        row.addWidget(self.search, 2, 0, 1, 4)
        row.setColumnStretch(1, 1)
        row.setColumnStretch(3, 1)

        filters_layout.addLayout(row)
        layout.addWidget(filters_box)

        actions = QHBoxLayout()

        self.count_label = QLabel("0 εγγραφές")
        self.count_label.setStyleSheet(
            "font-weight: 700; color: #26382f;"
        )
        actions.addWidget(self.count_label)

        actions.addStretch()

        refresh_button = QPushButton("Ανανέωση")
        refresh_button.clicked.connect(self.refresh)
        actions.addWidget(refresh_button)

        export_button = QPushButton("Εξαγωγή CSV")
        export_button.clicked.connect(self.export_csv)
        actions.addWidget(export_button)

        layout.addLayout(actions)

        self.table = table_widget(
            [
                "Ημερομηνία",
                "Ενότητα",
                "Ενέργεια",
                "ID",
                "Λεπτομέρειες",
            ]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setMinimumHeight(420)

        self.empty_label = QLabel()
        self.empty_label.setWordWrap(True)
        layout.addWidget(self.empty_label)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        layout.addWidget(self.table)

        info = QLabel(
            "Το ιστορικό είναι μόνο για ανάγνωση. "
            "Δεν υπάρχει κουμπί διαγραφής, ώστε να παραμένει χρήσιμο ως audit trail."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #67746d;")
        layout.addWidget(info)

        self.refresh()

    def _ensure_schema_and_triggers(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                table_name TEXT NOT NULL,
                action TEXT NOT NULL,
                record_id TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT ''
            )
            """
        )

        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_time
            ON audit_events(event_time)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_table
            ON audit_events(table_name)
            """
        )
        self.db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_events_action
            ON audit_events(action)
            """
        )

        triggers = [
            # Producer
            """
            CREATE TRIGGER IF NOT EXISTS audit_producer_update
            AFTER UPDATE ON producer
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'producer',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Παραγωγός: ' || COALESCE(NEW.name, '') ||
                    ' | ΑΦΜ: ' || COALESCE(NEW.tax_id, '')
                );
            END
            """,

            # Fields
            """
            CREATE TRIGGER IF NOT EXISTS audit_fields_insert
            AFTER INSERT ON fields
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'fields',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Αγροτεμάχιο: ' || COALESCE(NEW.name, '') ||
                    ' | ΚΑΕΚ: ' || COALESCE(NEW.kaek, '') ||
                    ' | Έκταση: ' ||
                    CAST(ROUND(COALESCE(NEW.area_stremma, 0), 3) AS TEXT) ||
                    ' στρ. | Δέντρα: ' ||
                    CAST(COALESCE(NEW.productive_trees, 0) AS TEXT)
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_fields_update
            AFTER UPDATE ON fields
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'fields',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Αγροτεμάχιο: ' || COALESCE(NEW.name, '') ||
                    ' | ΚΑΕΚ: ' || COALESCE(NEW.kaek, '') ||
                    ' | Έκταση: ' ||
                    CAST(ROUND(COALESCE(NEW.area_stremma, 0), 3) AS TEXT) ||
                    ' στρ. | Δέντρα: ' ||
                    CAST(COALESCE(NEW.productive_trees, 0) AS TEXT)
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_fields_delete
            AFTER DELETE ON fields
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'fields',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Αγροτεμάχιο: ' || COALESCE(OLD.name, '') ||
                    ' | ΚΑΕΚ: ' || COALESCE(OLD.kaek, '')
                );
            END
            """,

            # Production
            """
            CREATE TRIGGER IF NOT EXISTS audit_production_insert
            AFTER INSERT ON production
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'production',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | Αγροτεμάχιο ID: ' ||
                    CAST(COALESCE(NEW.field_id, 0) AS TEXT) ||
                    ' | Παραγωγή: ' ||
                    CAST(ROUND(COALESCE(NEW.quantity_kg, 0), 3) AS TEXT) ||
                    ' kg'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_production_update
            AFTER UPDATE ON production
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'production',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | Αγροτεμάχιο ID: ' ||
                    CAST(COALESCE(NEW.field_id, 0) AS TEXT) ||
                    ' | Παραγωγή: ' ||
                    CAST(ROUND(COALESCE(NEW.quantity_kg, 0), 3) AS TEXT) ||
                    ' kg'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_production_delete
            AFTER DELETE ON production
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'production',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(OLD.entry_date, '') ||
                    ' | Παραγωγή: ' ||
                    CAST(ROUND(COALESCE(OLD.quantity_kg, 0), 3) AS TEXT) ||
                    ' kg'
                );
            END
            """,

            # Income
            """
            CREATE TRIGGER IF NOT EXISTS audit_income_insert
            AFTER INSERT ON income
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'income',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | ' || COALESCE(NEW.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(NEW.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_income_update
            AFTER UPDATE ON income
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'income',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | ' || COALESCE(NEW.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(NEW.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_income_delete
            AFTER DELETE ON income
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'income',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(OLD.entry_date, '') ||
                    ' | ' || COALESCE(OLD.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(OLD.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,

            # Expenses
            """
            CREATE TRIGGER IF NOT EXISTS audit_expenses_insert
            AFTER INSERT ON expenses
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'expenses',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | ' || COALESCE(NEW.category, '') ||
                    ' | ' || COALESCE(NEW.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(NEW.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_expenses_update
            AFTER UPDATE ON expenses
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'expenses',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(NEW.entry_date, '') ||
                    ' | ' || COALESCE(NEW.category, '') ||
                    ' | ' || COALESCE(NEW.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(NEW.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_expenses_delete
            AFTER DELETE ON expenses
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'expenses',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Ημερομηνία: ' || COALESCE(OLD.entry_date, '') ||
                    ' | ' || COALESCE(OLD.category, '') ||
                    ' | ' || COALESCE(OLD.description, '') ||
                    ' | Ποσό: ' ||
                    CAST(ROUND(COALESCE(OLD.amount, 0), 2) AS TEXT) ||
                    ' €'
                );
            END
            """,

            # Cultivation declarations
            """
            CREATE TRIGGER IF NOT EXISTS audit_declaration_insert
            AFTER INSERT ON cultivation_declarations
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'cultivation_declarations',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Έτος: ' ||
                    CAST(COALESCE(NEW.declaration_year, 0) AS TEXT) ||
                    ' | Κατάσταση: ' || COALESCE(NEW.status, '')
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_declaration_update
            AFTER UPDATE ON cultivation_declarations
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'cultivation_declarations',
                    'UPDATE',
                    CAST(NEW.id AS TEXT),
                    'Έτος: ' ||
                    CAST(COALESCE(NEW.declaration_year, 0) AS TEXT) ||
                    ' | Κατάσταση: ' || COALESCE(NEW.status, '')
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_declaration_delete
            AFTER DELETE ON cultivation_declarations
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'cultivation_declarations',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Έτος: ' ||
                    CAST(COALESCE(OLD.declaration_year, 0) AS TEXT)
                );
            END
            """,

            # Prepared upload packages / snapshots
            """
            CREATE TRIGGER IF NOT EXISTS audit_upload_package_insert
            AFTER INSERT ON upload_packages
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'upload_packages',
                    'INSERT',
                    CAST(NEW.id AS TEXT),
                    'Έτος: ' ||
                    CAST(COALESCE(NEW.declaration_year, 0) AS TEXT) ||
                    ' | Κατάσταση: ' || COALESCE(NEW.status, '') ||
                    ' | SHA-256: ' ||
                    SUBSTR(COALESCE(NEW.payload_hash, ''), 1, 16) || '…'
                );
            END
            """,
            """
            CREATE TRIGGER IF NOT EXISTS audit_upload_package_delete
            AFTER DELETE ON upload_packages
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'upload_packages',
                    'DELETE',
                    CAST(OLD.id AS TEXT),
                    'Έτος: ' ||
                    CAST(COALESCE(OLD.declaration_year, 0) AS TEXT) ||
                    ' | SHA-256: ' ||
                    SUBSTR(COALESCE(OLD.payload_hash, ''), 1, 16) || '…'
                );
            END
            """,
        ]

        for sql in triggers:
            # Lazy pages/older backups may not have created their tables yet.
            # Install their audit triggers on a later refresh, once they exist.
            target = re.search(r"\bON\s+(\w+)", sql, re.IGNORECASE).group(1)
            if self.db.query_one("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (target,)):
                self.db.execute(sql)

    def refresh(self, *_args) -> None:
        # A restore from an older backup can remove the audit table/triggers.
        # Recreate them transparently when this page is opened.
        self._ensure_schema_and_triggers()

        where = [
            "date(event_time) >= ?",
            "date(event_time) <= ?",
        ]
        params: list[object] = [
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd"),
        ]

        table_name = self.section.currentData()
        if table_name:
            where.append("table_name = ?")
            params.append(table_name)

        action = self.action.currentData()
        if action:
            where.append("action = ?")
            params.append(action)

        search = self.search.text().strip()
        if search:
            where.append(
                """
                (
                    details LIKE ?
                    OR table_name LIKE ?
                    OR record_id LIKE ?
                )
                """
            )
            token = f"%{search}%"
            params.extend([token, token, token])

        rows = self.db.query(
            f"""
            SELECT
                id,
                event_time,
                table_name,
                action,
                record_id,
                details
            FROM audit_events
            WHERE {' AND '.join(where)}
            ORDER BY event_time DESC, id DESC
            LIMIT 5000
            """,
            tuple(params),
        )

        self.table.setRowCount(len(rows))
        self._body_label(self.empty_label, "Δεν υπάρχουν εγγραφές ιστορικού με τα τρέχοντα φίλτρα.")
        self.empty_label.setVisible(not rows)

        for row_index, row in enumerate(rows):
            values = [
                row["event_time"] or "",
                TABLE_LABELS.get(
                    row["table_name"],
                    row["table_name"] or "",
                ),
                ACTION_LABELS.get(
                    row["action"],
                    row["action"] or "",
                ),
                row["record_id"] or "",
                row["details"] or "",
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column_index == 1 and row["table_name"] in TABLE_LABELS:
                    self._set_body(item, TABLE_LABELS[row["table_name"]])
                elif column_index == 2 and row["action"] in ACTION_LABELS:
                    self._set_body(item, ACTION_LABELS[row["action"]])

                if column_index == 4:
                    item.setToolTip(item.text())

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        if len(rows) >= 5000:
            self._body_label(self.count_label, "5.000+ εγγραφές (εμφανίζονται οι νεότερες 5.000)")
        else:
            self._body_label(self.count_label, "{count} εγγραφές", count=len(rows))

    def export_csv(self) -> None:
        if self.table.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Ιστορικό Ενεργειών",
                "Δεν υπάρχουν εγγραφές για εξαγωγή με τα τρέχοντα φίλτρα.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            _text("Εξαγωγή ιστορικού CSV"),
            "mastixa_audit_history.csv",
            "CSV (*.csv)",
        )

        if not path:
            return

        if not path.lower().endswith(".csv"):
            path += ".csv"

        try:
            with Path(path).open(
                "w",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                writer = csv.writer(handle, delimiter=";")

                headers = [
                    self.table.horizontalHeaderItem(column).text()
                    for column in range(self.table.columnCount())
                ]
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    writer.writerow(
                        [
                            (
                                self.table.item(row, column).text()
                                if self.table.item(row, column)
                                else ""
                            )
                            for column in range(self.table.columnCount())
                        ]
                    )
        except OSError as exc:
            _message(self, 'critical', 'Ιστορικό Ενεργειών', 'Η εξαγωγή απέτυχε.\n\n{exc}', exc=exc)
            return

        _message(self, 'information', 'Ιστορικό Ενεργειών', 'Το CSV δημιουργήθηκε επιτυχώς:\n{path}', path=path)
