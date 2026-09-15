from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QGroupBox,
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

from .database import Database
from .language import tr
from .ui_helpers import table_widget


SEVERITY_ORDER = {
    "ERROR": 0,
    "WARNING": 1,
}

SEVERITY_LABELS = {
    "ERROR": "Σφάλμα",
    "WARNING": "Προειδοποίηση",
}

CATEGORY_LABELS = {
    "producer": "Παραγωγός",
    "fields": "Αγροτεμάχια",
    "production": "Παραγωγή",
    "activities": "Άρδευση & Λίπανση",
    "plant_protection": "Φυτοπροστασία",
    "labor": "Εργατικά & Προσωπικό",
    "plantings": "Φυτεύσεις & Δέντρα",
    "sales": "Πωλήσεις Παραγωγής",
    "inventory": "Αποθήκη & Εφόδια",
    "income": "Έσοδα",
    "expenses": "Έξοδα",
    "declaration": "Δήλωση Καλλιέργειας",
    "snapshots": "Snapshots",
}


class DataQualityPage(QWidget):
    """
    Read-only data quality center.

    It never changes user data. It only reports missing, suspicious or
    inconsistent records and gives a suggested correction.
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.all_issues: list[dict] = []

        layout = QVBoxLayout(self)

        title = QLabel("Έλεγχος Δεδομένων")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Εντοπισμός ελλιπών ή ασυνεπών στοιχείων πριν από δήλωση / εξαγωγή"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        summary_box = QGroupBox()
        summary_layout = QHBoxLayout(summary_box)

        self.error_card = self._metric_card("Σφάλματα", "0")
        self.warning_card = self._metric_card("Προειδοποιήσεις", "0")
        self.total_card = self._metric_card("Σύνολο θεμάτων", "0")
        self.status_card = self._metric_card("Κατάσταση", "Καθαρά")

        for card, _value_label in (
            self.error_card,
            self.warning_card,
            self.total_card,
            self.status_card,
        ):
            summary_layout.addWidget(card, 1)

        layout.addWidget(summary_box)

        filters_box = QGroupBox()
        filters_layout = QVBoxLayout(filters_box)

        filters_title = QLabel("Φίλτρα")
        filters_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        filters_layout.addWidget(filters_title)

        row = QHBoxLayout()

        row.addWidget(QLabel("Σοβαρότητα"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItem("Όλα", None)
        self.severity_filter.addItem("Σφάλματα", "ERROR")
        self.severity_filter.addItem("Προειδοποιήσεις", "WARNING")
        self.severity_filter.currentIndexChanged.connect(self._apply_filters)
        row.addWidget(self.severity_filter)

        row.addWidget(QLabel("Ενότητα"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Όλες", None)
        for key, label in CATEGORY_LABELS.items():
            self.category_filter.addItem(label, key)
        self.category_filter.currentIndexChanged.connect(self._apply_filters)
        row.addWidget(self.category_filter)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση σε πρόβλημα, εγγραφή ή προτεινόμενη διόρθωση..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filters)
        row.addWidget(self.search, 1)

        filters_layout.addLayout(row)
        layout.addWidget(filters_box)

        actions = QHBoxLayout()

        self.result_label = QLabel("0 θέματα")
        self.result_label.setStyleSheet(
            "font-weight: 700; color: #26382f;"
        )
        actions.addWidget(self.result_label)

        actions.addStretch()

        refresh_button = QPushButton("Νέος έλεγχος")
        refresh_button.clicked.connect(self.refresh)
        actions.addWidget(refresh_button)

        export_button = QPushButton("Εξαγωγή CSV")
        export_button.clicked.connect(self.export_csv)
        actions.addWidget(export_button)

        layout.addLayout(actions)

        self.table = table_widget(
            [
                "Σοβαρότητα",
                "Ενότητα",
                "Εγγραφή",
                "Πρόβλημα",
                "Προτεινόμενη διόρθωση",
            ]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setMinimumHeight(440)

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
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )

        layout.addWidget(self.table)

        note = QLabel(
            "Ο έλεγχος είναι μόνο για ανάγνωση και δεν αλλάζει τίποτα στη βάση."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #67746d;")
        layout.addWidget(note)

        self.refresh()

    def _metric_card(self, caption: str, value: str):
        box = QGroupBox()
        box.setObjectName("metricCard")

        card_layout = QVBoxLayout(box)

        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")
        card_layout.addWidget(caption_label)

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        card_layout.addWidget(value_label)

        return box, value_label

    def _table_exists(self, table_name: str) -> bool:
        row = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (table_name,),
        )
        return row is not None

    def _add_issue(
        self,
        severity: str,
        category: str,
        record: str,
        problem: str,
        fix: str,
    ) -> None:
        self.all_issues.append(
            {
                "severity": severity,
                "category": category,
                "record": record,
                "problem": problem,
                "fix": fix,
            }
        )

    def refresh(self) -> None:
        self.all_issues = []

        self._check_producer()
        self._check_fields()
        self._check_production()
        self._check_activities()
        self._check_plant_protection()
        self._check_labor()
        self._check_plantings()
        self._check_sales()
        self._check_sales_products()
        self._check_equipment_expenses()
        self._check_partner_links()
        self._check_inventory_receipt_expenses()
        self._check_inventory()
        self._check_income()
        self._check_expenses()
        self._check_declarations()
        self._check_snapshots()

        self.all_issues.sort(
            key=lambda issue: (
                SEVERITY_ORDER.get(issue["severity"], 99),
                CATEGORY_LABELS.get(
                    issue["category"],
                    issue["category"],
                ),
                issue["record"],
            )
        )

        errors = sum(
            1
            for issue in self.all_issues
            if issue["severity"] == "ERROR"
        )
        warnings = sum(
            1
            for issue in self.all_issues
            if issue["severity"] == "WARNING"
        )

        self.error_card[1].setText(str(errors))
        self.warning_card[1].setText(str(warnings))
        self.total_card[1].setText(str(len(self.all_issues)))

        if errors:
            self.status_card[1].setText("Χρειάζεται διόρθωση")
        elif warnings:
            self.status_card[1].setText("Με προειδοποιήσεις")
        else:
            self.status_card[1].setText("Καθαρά")

        self._apply_filters()

    def _check_producer(self) -> None:
        if not self._table_exists("producer"):
            self._add_issue(
                "ERROR",
                "producer",
                "—",
                "Λείπει ο πίνακας παραγωγού.",
                "Έλεγξε / επανάφερε τη βάση δεδομένων.",
            )
            return

        row = self.db.query_one(
            """
            SELECT *
            FROM producer
            WHERE id=1
            """
        )

        if row is None:
            self._add_issue(
                "ERROR",
                "producer",
                "ID 1",
                "Δεν υπάρχει καταχώρηση παραγωγού.",
                "Συμπλήρωσε τα Στοιχεία Παραγωγού.",
            )
            return

        name = str(row["name"] or "").strip()
        tax_id = str(row["tax_id"] or "").strip()

        if not name:
            self._add_issue(
                "ERROR",
                "producer",
                "Παραγωγός",
                "Δεν έχει συμπληρωθεί ονοματεπώνυμο / επωνυμία.",
                "Πήγαινε στα Στοιχεία Παραγωγού και συμπλήρωσε το όνομα.",
            )

        if not tax_id:
            self._add_issue(
                "ERROR",
                "producer",
                "Παραγωγός",
                "Δεν έχει συμπληρωθεί ΑΦΜ.",
                "Συμπλήρωσε το ΑΦΜ στα Στοιχεία Παραγωγού.",
            )
        elif not (tax_id.isdigit() and len(tax_id) == 9):
            self._add_issue(
                "WARNING",
                "producer",
                "Παραγωγός",
                "Το ΑΦΜ δεν έχει τη συνήθη ελληνική μορφή 9 ψηφίων.",
                "Έλεγξε ότι το ΑΦΜ έχει καταχωρηθεί σωστά.",
            )

    def _check_fields(self) -> None:
        if not self._table_exists("fields"):
            self._add_issue(
                "ERROR",
                "fields",
                "—",
                "Λείπει ο πίνακας αγροτεμαχίων.",
                "Έλεγξε / επανάφερε τη βάση δεδομένων.",
            )
            return

        rows = self.db.query(
            """
            SELECT *
            FROM fields
            ORDER BY id
            """
        )

        if not rows:
            self._add_issue(
                "WARNING",
                "fields",
                "—",
                "Δεν έχει καταχωρηθεί κανένα αγροτεμάχιο.",
                "Πρόσθεσε τα αγροτεμάχιά σου στην ενότητα Αγροτεμάχια.",
            )
            return

        kaek_to_ids: dict[str, list[int]] = {}

        for row in rows:
            field_id = int(row["id"])
            name = str(row["name"] or "").strip()
            kaek = str(row["kaek"] or "").strip()
            location = str(row["location"] or "").strip()
            area = float(row["area_stremma"] or 0)
            trees = int(row["productive_trees"] or 0)

            record = f"#{field_id} {name or '(χωρίς όνομα)'}"

            if not name:
                self._add_issue(
                    "ERROR",
                    "fields",
                    record,
                    "Το αγροτεμάχιο δεν έχει ονομασία.",
                    "Συμπλήρωσε Ονομασία στην ενότητα Αγροτεμάχια.",
                )

            if not kaek:
                self._add_issue(
                    "WARNING",
                    "fields",
                    record,
                    "Δεν έχει συμπληρωθεί ΚΑΕΚ.",
                    "Συμπλήρωσε το ΚΑΕΚ αν είναι διαθέσιμο.",
                )
            else:
                kaek_to_ids.setdefault(kaek, []).append(field_id)

            if not location:
                self._add_issue(
                    "WARNING",
                    "fields",
                    record,
                    "Δεν έχει συμπληρωθεί Τοποθεσία.",
                    "Συμπλήρωσε την Τοποθεσία του αγροτεμαχίου.",
                )

            if area <= 0:
                self._add_issue(
                    "WARNING",
                    "fields",
                    record,
                    "Η έκταση είναι 0 ή μικρότερη.",
                    "Έλεγξε την έκταση σε στρέμματα.",
                )

            if trees == 0:
                self._add_issue(
                    "WARNING",
                    "fields",
                    record,
                    "Τα παραγωγικά δέντρα είναι 0.",
                    "Αν υπάρχουν παραγωγικά δέντρα, ενημέρωσε τον αριθμό.",
                )

        for kaek, ids in kaek_to_ids.items():
            if len(ids) <= 1:
                continue

            self._add_issue(
                "ERROR",
                "fields",
                f"ΚΑΕΚ {kaek}",
                "Το ίδιο ΚΑΕΚ χρησιμοποιείται σε περισσότερα από ένα αγροτεμάχια.",
                "Έλεγξε τα αγροτεμάχια με ID: "
                + ", ".join(str(value) for value in ids),
            )

    def _check_production(self) -> None:
        if not self._table_exists("production"):
            return

        rows = self.db.query(
            """
            SELECT
                p.id,
                p.entry_date,
                p.field_id,
                p.quantity_kg,
                f.id AS existing_field_id,
                f.name AS field_name,
                f.productive_trees
            FROM production p
            LEFT JOIN fields f
                ON f.id=p.field_id
            ORDER BY p.id
            """
        )

        today = QDate.currentDate()

        for row in rows:
            production_id = int(row["id"])
            record = f"#{production_id}"

            entry_date = str(row["entry_date"] or "")
            parsed = QDate.fromString(entry_date, "yyyy-MM-dd")

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "production",
                    record,
                    f"Μη έγκυρη ημερομηνία: {entry_date or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία της καταχώρησης παραγωγής.",
                )
            elif parsed > today:
                self._add_issue(
                    "WARNING",
                    "production",
                    record,
                    f"Η ημερομηνία {entry_date} είναι στο μέλλον.",
                    "Έλεγξε αν η ημερομηνία καταχωρήθηκε σωστά.",
                )

            if row["existing_field_id"] is None:
                self._add_issue(
                    "ERROR",
                    "production",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Διόρθωσε ή διέγραψε την καταχώρηση παραγωγής.",
                )

            quantity = float(row["quantity_kg"] or 0)

            if quantity <= 0:
                self._add_issue(
                    "ERROR",
                    "production",
                    record,
                    "Η ποσότητα παραγωγής είναι 0 ή μικρότερη.",
                    "Καταχώρησε ποσότητα μεγαλύτερη από 0 kg.",
                )

            if (
                row["existing_field_id"] is not None
                and int(row["productive_trees"] or 0) == 0
                and quantity > 0
            ):
                field_name = row["field_name"] or f"ID {row['field_id']}"
                self._add_issue(
                    "WARNING",
                    "production",
                    record,
                    f"Υπάρχει παραγωγή στο «{field_name}», αλλά έχει 0 παραγωγικά δέντρα.",
                    "Έλεγξε τα παραγωγικά δέντρα του αγροτεμαχίου.",
                )


    def _check_activities(self) -> None:
        if not self._table_exists("farm_activities"):
            return

        rows = self.db.query(
            """
            SELECT
                a.*,
                f.id AS existing_field_id,
                f.name AS field_name
            FROM farm_activities a
            LEFT JOIN fields f ON f.id=a.field_id
            ORDER BY a.id
            """
        )

        valid_statuses = {
            "Προγραμματισμένη",
            "Ολοκληρώθηκε",
            "Ακυρώθηκε",
        }

        for row in rows:
            activity_id = int(row["id"])
            record = f"#{activity_id}"

            activity_date = str(row["activity_date"] or "")
            parsed = QDate.fromString(activity_date, "yyyy-MM-dd")
            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "activities",
                    record,
                    f"Μη έγκυρη ημερομηνία: {activity_date or '(κενή)' }.",
                    "Διόρθωσε την ημερομηνία στην ενότητα Εργασίες Αγρού.",
                )

            if not str(row["category"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "activities",
                    record,
                    "Η εργασία δεν έχει κατηγορία.",
                    "Συμπλήρωσε το είδος εργασίας.",
                )

            status = str(row["status"] or "").strip()
            if status not in valid_statuses:
                self._add_issue(
                    "WARNING",
                    "activities",
                    record,
                    f"Μη αναμενόμενη κατάσταση: {status or '(κενή)' }.",
                    "Επίλεξε Προγραμματισμένη, Ολοκληρώθηκε ή Ακυρώθηκε.",
                )

            if row["field_id"] is not None and row["existing_field_id"] is None:
                self._add_issue(
                    "ERROR",
                    "activities",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Διόρθωσε ή διέγραψε την εργασία.",
                )


    def _check_plant_protection(self) -> None:
        if not self._table_exists("plant_protection_records"):
            return

        rows = self.db.query(
            """
            SELECT
                p.*,
                f.id AS existing_field_id,
                f.name AS field_name,
                i.id AS existing_inventory_item_id
            FROM plant_protection_records p
            LEFT JOIN fields f
                ON f.id=p.field_id
            LEFT JOIN inventory_items i
                ON i.id=p.inventory_item_id
            ORDER BY p.id
            """
        )

        today = QDate.currentDate()

        for row in rows:
            record_id = int(row["id"])
            record = f"#{record_id}"

            application_date = str(row["application_date"] or "")
            parsed = QDate.fromString(application_date, "yyyy-MM-dd")

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "plant_protection",
                    record,
                    f"Μη έγκυρη ημερομηνία εφαρμογής: {application_date or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία στο Ημερολόγιο Φυτοπροστασίας.",
                )
            elif parsed > today:
                self._add_issue(
                    "WARNING",
                    "plant_protection",
                    record,
                    f"Η ημερομηνία εφαρμογής {application_date} είναι στο μέλλον.",
                    "Έλεγξε ότι η ημερομηνία έχει καταχωρηθεί σωστά.",
                )

            if row["existing_field_id"] is None:
                self._add_issue(
                    "ERROR",
                    "plant_protection",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Διόρθωσε ή διέγραψε την καταγραφή φυτοπροστασίας.",
                )

            if not str(row["purpose"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "plant_protection",
                    record,
                    "Δεν έχει συμπληρωθεί στόχος / αιτία επέμβασης.",
                    "Συμπλήρωσε τον στόχο της επέμβασης.",
                )

            if not str(row["product_name"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "plant_protection",
                    record,
                    "Δεν έχει συμπληρωθεί σκεύασμα / προϊόν.",
                    "Συμπλήρωσε το προϊόν της επέμβασης.",
                )

            if float(row["dose"] or 0) <= 0:
                self._add_issue(
                    "WARNING",
                    "plant_protection",
                    record,
                    "Η δόση είναι 0 ή μικρότερη.",
                    "Έλεγξε τη δόση και τη μονάδα εφαρμογής.",
                )

            if float(row["area_stremma"] or 0) <= 0:
                self._add_issue(
                    "WARNING",
                    "plant_protection",
                    record,
                    "Η έκταση εφαρμογής είναι 0 ή μικρότερη.",
                    "Συμπλήρωσε την έκταση στην οποία έγινε η επέμβαση.",
                )

            if (
                row["inventory_item_id"] is not None
                and row["existing_inventory_item_id"] is None
            ):
                self._add_issue(
                    "WARNING",
                    "plant_protection",
                    record,
                    f"Το συνδεδεμένο είδος αποθήκης ID {row['inventory_item_id']} δεν υπάρχει πλέον.",
                    "Επίλεξε ξανά το σωστό προϊόν ή άφησε το προϊόν ως ελεύθερο κείμενο.",
                )


    def _check_labor(self) -> None:
        if not self._table_exists("labor_entries"):
            return

        rows = self.db.query(
            """
            SELECT
                l.*,
                f.id AS existing_field_id,
                w.id AS existing_worker_id
            FROM labor_entries l
            LEFT JOIN fields f
                ON f.id=l.field_id
            LEFT JOIN workers w
                ON w.id=l.worker_id
            ORDER BY l.id
            """
        )

        today = QDate.currentDate()

        for row in rows:
            record = f"#{int(row['id'])}"

            parsed = QDate.fromString(
                row["work_date"] or "",
                "yyyy-MM-dd",
            )

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "labor",
                    record,
                    f"Μη έγκυρη ημερομηνία: {row['work_date'] or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία της καταχώρησης εργατικών.",
                )
            elif parsed > today:
                self._add_issue(
                    "WARNING",
                    "labor",
                    record,
                    f"Η ημερομηνία {row['work_date']} είναι στο μέλλον.",
                    "Έλεγξε αν η ημερομηνία καταχωρήθηκε σωστά.",
                )

            if row["existing_worker_id"] is None:
                self._add_issue(
                    "ERROR",
                    "labor",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο εργαζόμενο ID {row['worker_id']}.",
                    "Διόρθωσε την καταχώρηση εργατικών.",
                )

            if (
                row["field_id"] is not None
                and row["existing_field_id"] is None
            ):
                self._add_issue(
                    "WARNING",
                    "labor",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Επίλεξε ξανά αγροτεμάχιο ή άφησέ το ως γενική εργασία.",
                )

            hours = float(row["hours"] or 0)
            rate = float(row["hourly_rate"] or 0)
            cost = float(row["cost"] or 0)

            if hours <= 0:
                self._add_issue(
                    "ERROR",
                    "labor",
                    record,
                    "Οι ώρες είναι 0 ή μικρότερες.",
                    "Καταχώρησε ώρες μεγαλύτερες από 0.",
                )

            expected = hours * rate
            if abs(expected - cost) > 0.02:
                self._add_issue(
                    "WARNING",
                    "labor",
                    record,
                    "Το αποθηκευμένο κόστος δεν συμφωνεί με ώρες × αμοιβή/ώρα.",
                    "Άνοιξε και αποθήκευσε ξανά την καταχώρηση.",
                )


    def _check_plantings(self) -> None:
        if not self._table_exists("planting_batches"):
            return

        rows = self.db.query(
            """
            SELECT
                p.*,
                f.id AS existing_field_id
            FROM planting_batches p
            LEFT JOIN fields f
                ON f.id=p.field_id
            ORDER BY p.id
            """
        )

        today = QDate.currentDate()

        for row in rows:
            record = f"#{int(row['id'])}"

            parsed = QDate.fromString(
                row["planting_date"] or "",
                "yyyy-MM-dd",
            )

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "plantings",
                    record,
                    f"Μη έγκυρη ημερομηνία φύτευσης: {row['planting_date'] or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία της παρτίδας.",
                )
            elif parsed > today:
                self._add_issue(
                    "WARNING",
                    "plantings",
                    record,
                    f"Η ημερομηνία φύτευσης {row['planting_date']} είναι στο μέλλον.",
                    "Έλεγξε την ημερομηνία.",
                )

            if row["existing_field_id"] is None:
                self._add_issue(
                    "ERROR",
                    "plantings",
                    record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Διόρθωσε ή διέγραψε την παρτίδα φύτευσης.",
                )

            planted = int(row["trees_planted"] or 0)
            alive = int(row["trees_alive"] or 0)

            if planted <= 0:
                self._add_issue(
                    "ERROR",
                    "plantings",
                    record,
                    "Ο αριθμός φυτεμένων δέντρων είναι 0 ή μικρότερος.",
                    "Καταχώρησε σωστό αριθμό φυτεμένων δέντρων.",
                )

            if alive < 0 or alive > planted:
                self._add_issue(
                    "ERROR",
                    "plantings",
                    record,
                    "Ο αριθμός ζωντανών δέντρων είναι εκτός έγκυρου ορίου.",
                    "Τα ζωντανά πρέπει να είναι από 0 έως τα φυτεμένα.",
                )


    def _check_sales(self) -> None:
        if not self._table_exists("production_sales"):
            return

        rows = self.db.query(
            """
            SELECT
                s.*,
                b.id AS existing_buyer_id,
                i.id AS existing_income_id
            FROM production_sales s
            LEFT JOIN business_partners b
                ON b.id=s.buyer_id
            LEFT JOIN income i
                ON i.id=s.income_id
            ORDER BY s.id
            """
        )

        produced_row = self.db.query_one(
            """
            SELECT COALESCE(SUM(quantity_kg),0) AS total
            FROM production
            """
        )
        sold_row = self.db.query_one(
            """
            SELECT COALESCE(SUM(quantity_kg),0) AS total
            FROM production_sales
            """
        )

        produced = float(
            produced_row["total"] or 0
        ) if produced_row else 0.0
        sold = float(
            sold_row["total"] or 0
        ) if sold_row else 0.0

        if sold > produced + 0.000001:
            self._add_issue(
                "ERROR",
                "sales",
                "ΣΥΝΟΛΟ",
                (
                    f"Οι πωλήσεις ({sold:.3f} kg) είναι μεγαλύτερες από "
                    f"την καταγεγραμμένη παραγωγή ({produced:.3f} kg)."
                ),
                "Έλεγξε τις πωλήσεις ή τις καταχωρήσεις παραγωγής.",
            )

        for row in rows:
            record = f"#{int(row['id'])}"

            parsed = QDate.fromString(
                row["sale_date"] or "",
                "yyyy-MM-dd",
            )

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "sales",
                    record,
                    "Μη έγκυρη ημερομηνία πώλησης.",
                    "Διόρθωσε την ημερομηνία.",
                )

            if float(row["quantity_kg"] or 0) <= 0:
                self._add_issue(
                    "ERROR",
                    "sales",
                    record,
                    "Η ποσότητα πώλησης είναι 0 ή μικρότερη.",
                    "Καταχώρησε σωστή ποσότητα.",
                )

            expected = (
                float(row["quantity_kg"] or 0)
                * float(row["price_per_kg"] or 0)
            )

            if abs(
                expected
                - float(row["total_amount"] or 0)
            ) > 0.02:
                self._add_issue(
                    "WARNING",
                    "sales",
                    record,
                    "Η συνολική αξία δεν συμφωνεί με ποσότητα × τιμή/kg.",
                    "Άνοιξε και αποθήκευσε ξανά την πώληση.",
                )

            if (
                row["buyer_id"] is not None
                and row["existing_buyer_id"] is None
            ):
                self._add_issue(
                    "WARNING",
                    "sales",
                    record,
                    "Ο συνδεδεμένος αγοραστής δεν υπάρχει πλέον.",
                    "Επίλεξε ξανά αγοραστή.",
                )

            if row["existing_income_id"] is None:
                self._add_issue(
                    "WARNING",
                    "sales",
                    record,
                    "Δεν βρέθηκε το αυτόματα συνδεδεμένο έσοδο.",
                    "Άνοιξε και αποθήκευσε ξανά την πώληση.",
                )


    def _check_sales_products(self) -> None:
        if (
            not self._table_exists("production_sales")
            or not self._table_exists("production")
        ):
            return

        sale_columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(production_sales)"
            )
        }
        if "product" not in sale_columns:
            return

        products = {
            str(row["product"] or "").strip()
            for row in self.db.query(
                """
                SELECT DISTINCT TRIM(product) AS product
                FROM production
                WHERE TRIM(COALESCE(product,'')) <> ''
                """
            )
            if str(row["product"] or "").strip()
        }

        rows = self.db.query(
            """
            SELECT id,product
            FROM production_sales
            ORDER BY id
            """
        )

        for row in rows:
            product = str(row["product"] or "").strip()
            record = f"Πώληση #{int(row['id'])}"

            if not product:
                self._add_issue(
                    "WARNING",
                    "sales",
                    record,
                    "Η πώληση δεν έχει προϊόν.",
                    (
                        "Άνοιξε την πώληση και επίλεξε προϊόν. "
                        "Αυτό είναι απαραίτητο για σωστή αναφορά ανά προϊόν."
                    ),
                )
                continue

            if product not in products:
                self._add_issue(
                    "WARNING",
                    "sales",
                    record,
                    f"Το προϊόν «{product}» δεν υπάρχει πλέον στις καταχωρήσεις Παραγωγής.",
                    "Έλεγξε την πώληση και το προϊόν.",
                )


    def _check_equipment_expenses(self) -> None:
        if (
            not self._table_exists("equipment_maintenance")
            or not self._table_exists("expenses")
        ):
            return

        columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(equipment_maintenance)"
            )
        }
        if "expense_id" not in columns:
            return

        rows = self.db.query(
            """
            SELECT
                m.id,
                m.service_date,
                m.cost,
                m.expense_id,
                e.name AS equipment_name,
                x.id AS existing_expense_id,
                x.amount AS expense_amount
            FROM equipment_maintenance m
            LEFT JOIN equipment e
                ON e.id=m.equipment_id
            LEFT JOIN expenses x
                ON x.id=m.expense_id
            ORDER BY m.id
            """
        )

        for row in rows:
            cost = float(row["cost"] or 0)
            record = f"Service #{int(row['id'])}"

            if cost <= 0:
                continue

            if row["existing_expense_id"] is None:
                self._add_issue(
                    "WARNING",
                    "equipment",
                    record,
                    (
                        f"Η συντήρηση του {row['equipment_name'] or 'μηχανήματος'} "
                        "έχει κόστος αλλά δεν βρέθηκε το συνδεδεμένο αυτόματο έξοδο."
                    ),
                    "Άνοιξε και αποθήκευσε ξανά τη συντήρηση.",
                )
                continue

            if abs(
                float(row["expense_amount"] or 0) - cost
            ) > 0.02:
                self._add_issue(
                    "WARNING",
                    "equipment",
                    record,
                    "Το αυτόματο έξοδο δεν συμφωνεί με το κόστος συντήρησης.",
                    "Άνοιξε και αποθήκευσε ξανά τη συντήρηση.",
                )


    def _check_partner_links(self) -> None:
        if not self._table_exists("business_partners"):
            return

        for table_name, section, text_column in (
            ("income", "income", "partner"),
            ("expenses", "expenses", "supplier"),
            ("invoice_documents", "invoice_documents", "supplier"),
        ):
            if not self._table_exists(table_name):
                continue

            columns = {
                row["name"]
                for row in self.db.query(
                    f"PRAGMA table_info({table_name})"
                )
            }
            if "partner_id" not in columns:
                continue

            rows = self.db.query(
                f"""
                SELECT
                    t.id,
                    t.partner_id,
                    t.{text_column} AS partner_text,
                    p.id AS existing_partner_id,
                    p.name AS partner_name
                FROM {table_name} t
                LEFT JOIN business_partners p
                    ON p.id=t.partner_id
                WHERE t.partner_id IS NOT NULL
                ORDER BY t.id
                """
            )

            for row in rows:
                record = f"#{int(row['id'])}"

                if row["existing_partner_id"] is None:
                    self._add_issue(
                        "WARNING",
                        section,
                        record,
                        (
                            f"Η εγγραφή αναφέρεται σε ανύπαρκτο συνεργάτη "
                            f"ID {row['partner_id']}."
                        ),
                        "Άνοιξε την εγγραφή και επίλεξε ξανά συνεργάτη.",
                    )
                    continue

                text_value = str(row["partner_text"] or "").strip()
                canonical = str(row["partner_name"] or "").strip()

                if text_value and text_value != canonical:
                    self._add_issue(
                        "WARNING",
                        section,
                        record,
                        (
                            f"Το αποθηκευμένο όνομα συνεργάτη «{text_value}» "
                            f"δεν συμφωνεί με το μητρώο «{canonical}»."
                        ),
                        "Άνοιξε και αποθήκευσε ξανά την εγγραφή.",
                    )

    def _check_inventory_receipt_expenses(self) -> None:
        if (
            not self._table_exists("inventory_movements")
            or not self._table_exists("expenses")
        ):
            return

        columns = {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(inventory_movements)"
            )
        }

        required = {
            "total_cost",
            "expense_id",
            "partner_id",
        }
        if not required.issubset(columns):
            return

        rows = self.db.query(
            """
            SELECT
                m.id,
                m.movement_type,
                m.quantity,
                m.unit_price,
                m.total_cost,
                m.expense_id,
                m.partner_id,
                i.name AS item_name,
                x.id AS existing_expense_id,
                x.amount AS expense_amount,
                x.partner_id AS expense_partner_id
            FROM inventory_movements m
            LEFT JOIN inventory_items i
                ON i.id=m.item_id
            LEFT JOIN expenses x
                ON x.id=m.expense_id
            WHERE m.movement_type='Παραλαβή'
            ORDER BY m.id
            """
        )

        for row in rows:
            record = f"Παραλαβή #{int(row['id'])}"
            total_cost = float(row["total_cost"] or 0)
            expected = (
                float(row["quantity"] or 0)
                * float(row["unit_price"] or 0)
            )

            if abs(expected - total_cost) > 0.02:
                self._add_issue(
                    "WARNING",
                    "inventory",
                    record,
                    "Το συνολικό κόστος δεν συμφωνεί με ποσότητα × τιμή μονάδας.",
                    "Άνοιξε και αποθήκευσε ξανά την παραλαβή.",
                )

            if total_cost <= 0:
                continue

            if row["existing_expense_id"] is None:
                self._add_issue(
                    "WARNING",
                    "inventory",
                    record,
                    (
                        f"Η παραλαβή {row['item_name'] or ''} έχει κόστος "
                        "αλλά δεν βρέθηκε το συνδεδεμένο αυτόματο έξοδο."
                    ),
                    "Άνοιξε και αποθήκευσε ξανά την παραλαβή.",
                )
                continue

            if abs(
                float(row["expense_amount"] or 0)
                - total_cost
            ) > 0.02:
                self._add_issue(
                    "WARNING",
                    "inventory",
                    record,
                    "Το αυτόματο έξοδο δεν συμφωνεί με το κόστος παραλαβής.",
                    "Άνοιξε και αποθήκευσε ξανά την παραλαβή.",
                )

            if row["partner_id"] != row["expense_partner_id"]:
                self._add_issue(
                    "WARNING",
                    "inventory",
                    record,
                    "Ο προμηθευτής της παραλαβής δεν συμφωνεί με το αυτόματο έξοδο.",
                    "Άνοιξε και αποθήκευσε ξανά την παραλαβή.",
                )


    def _check_income(self) -> None:
        if not self._table_exists("income"):
            return

        rows = self.db.query(
            """
            SELECT
                i.*,
                f.id AS existing_field_id
            FROM income i
            LEFT JOIN fields f
                ON f.id=i.field_id
            ORDER BY i.id
            """
        )

        for row in rows:
            record = f"#{int(row['id'])}"

            if (
                row["field_id"] is not None
                and row["existing_field_id"] is None
            ):
                self._add_issue(
                    "WARNING",
                    "income",
                    record,
                    f"Το έσοδο αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Άνοιξε την καταχώρηση εσόδου και επίλεξε ξανά αγροτεμάχιο ή Γενικό.",
                )

            if not str(row["description"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "income",
                    record,
                    "Το έσοδο δεν έχει Περιγραφή.",
                    "Συμπλήρωσε Περιγραφή στην καταχώρηση εσόδου.",
                )

            if float(row["amount"] or 0) <= 0:
                self._add_issue(
                    "ERROR",
                    "income",
                    record,
                    "Το ποσό εσόδου είναι 0 ή μικρότερο.",
                    "Καταχώρησε ποσό μεγαλύτερο από 0 €.",
                )

            entry_date = str(row["entry_date"] or "")
            parsed = QDate.fromString(entry_date, "yyyy-MM-dd")

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "income",
                    record,
                    f"Μη έγκυρη ημερομηνία: {entry_date or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία του εσόδου.",
                )

    def _check_expenses(self) -> None:
        if not self._table_exists("expenses"):
            return

        rows = self.db.query(
            """
            SELECT
                e.*,
                f.id AS existing_field_id
            FROM expenses e
            LEFT JOIN fields f
                ON f.id=e.field_id
            ORDER BY e.id
            """
        )

        for row in rows:
            record = f"#{int(row['id'])}"

            if (
                row["field_id"] is not None
                and row["existing_field_id"] is None
            ):
                self._add_issue(
                    "WARNING",
                    "expenses",
                    record,
                    f"Το έξοδο αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Άνοιξε την καταχώρηση εξόδου και επίλεξε ξανά αγροτεμάχιο ή Γενικό.",
                )

            if not str(row["description"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "expenses",
                    record,
                    "Το έξοδο δεν έχει Περιγραφή.",
                    "Συμπλήρωσε Περιγραφή στην καταχώρηση εξόδου.",
                )

            if not str(row["category"] or "").strip():
                self._add_issue(
                    "WARNING",
                    "expenses",
                    record,
                    "Το έξοδο δεν έχει Κατηγορία.",
                    "Επίλεξε σωστή Κατηγορία εξόδου.",
                )

            if float(row["amount"] or 0) <= 0:
                self._add_issue(
                    "ERROR",
                    "expenses",
                    record,
                    "Το ποσό εξόδου είναι 0 ή μικρότερο.",
                    "Καταχώρησε ποσό μεγαλύτερο από 0 €.",
                )

            entry_date = str(row["entry_date"] or "")
            parsed = QDate.fromString(entry_date, "yyyy-MM-dd")

            if not parsed.isValid():
                self._add_issue(
                    "ERROR",
                    "expenses",
                    record,
                    f"Μη έγκυρη ημερομηνία: {entry_date or '(κενή)'}.",
                    "Διόρθωσε την ημερομηνία του εξόδου.",
                )

    def _check_inventory(self) -> None:
        if not self._table_exists("inventory_items"):
            return

        items = self.db.query(
            """
            SELECT
                i.*,
                COALESCE(SUM(
                    CASE
                        WHEN m.movement_type IN ('Παραλαβή','Διόρθωση +')
                            THEN m.quantity
                        WHEN m.movement_type IN ('Κατανάλωση','Διόρθωση -')
                            THEN -m.quantity
                        ELSE 0
                    END
                ),0) AS current_stock
            FROM inventory_items i
            LEFT JOIN inventory_movements m ON m.item_id=i.id
            GROUP BY i.id
            ORDER BY i.id
            """
        )

        names: dict[str, list[int]] = {}

        for row in items:
            item_id = int(row["id"])
            name = str(row["name"] or "").strip()
            unit = str(row["unit"] or "").strip()
            stock = float(row["current_stock"] or 0)
            minimum = float(row["minimum_stock"] or 0)
            record = f"#{item_id} {name or '(χωρίς όνομα)'}"

            if not name:
                self._add_issue(
                    "ERROR", "inventory", record,
                    "Το είδος αποθήκης δεν έχει ονομασία.",
                    "Συμπλήρωσε την ονομασία στην Αποθήκη & Εφόδια.",
                )
            else:
                names.setdefault(name.casefold(), []).append(item_id)

            if not unit:
                self._add_issue(
                    "ERROR", "inventory", record,
                    "Το είδος αποθήκης δεν έχει μονάδα μέτρησης.",
                    "Συμπλήρωσε μονάδα (kg, L, τεμ. κ.λπ.).",
                )

            if minimum < 0:
                self._add_issue(
                    "ERROR", "inventory", record,
                    "Το ελάχιστο απόθεμα είναι αρνητικό.",
                    "Διόρθωσε το ελάχιστο απόθεμα.",
                )

            if stock < -0.000001:
                self._add_issue(
                    "ERROR", "inventory", record,
                    f"Το υπολογισμένο απόθεμα είναι αρνητικό ({stock:.3f}).",
                    "Έλεγξε τις κινήσεις Παραλαβής / Κατανάλωσης.",
                )
            elif stock <= 0:
                self._add_issue(
                    "WARNING", "inventory", record,
                    "Το είδος είναι εξαντλημένο.",
                    "Καταχώρησε νέα παραλαβή αν υπάρχει διαθέσιμο απόθεμα.",
                )
            elif minimum > 0 and stock <= minimum:
                self._add_issue(
                    "WARNING", "inventory", record,
                    f"Χαμηλό απόθεμα ({stock:.3f}, όριο {minimum:.3f}).",
                    "Έλεγξε αν χρειάζεται αναπλήρωση.",
                )

        for _name, ids in names.items():
            if len(ids) > 1:
                self._add_issue(
                    "ERROR", "inventory",
                    "IDs " + ", ".join(str(value) for value in ids),
                    "Υπάρχουν δύο είδη αποθήκης με την ίδια ονομασία.",
                    "Συγχώνευσε ή μετονόμασε τις διπλές εγγραφές.",
                )

        if not self._table_exists("inventory_movements"):
            return

        movements = self.db.query(
            """
            SELECT
                m.*,
                i.id AS existing_item_id,
                f.id AS existing_field_id
            FROM inventory_movements m
            LEFT JOIN inventory_items i ON i.id=m.item_id
            LEFT JOIN fields f ON f.id=m.field_id
            ORDER BY m.id
            """
        )

        valid_types = {
            "Παραλαβή", "Κατανάλωση", "Διόρθωση +", "Διόρθωση -"
        }

        for row in movements:
            movement_id = int(row["id"])
            record = f"Κίνηση #{movement_id}"
            date_text = str(row["movement_date"] or "")
            parsed = QDate.fromString(date_text, "yyyy-MM-dd")

            if not parsed.isValid():
                self._add_issue(
                    "ERROR", "inventory", record,
                    f"Μη έγκυρη ημερομηνία: {date_text or '(κενή)' }.",
                    "Διόρθωσε την ημερομηνία της κίνησης.",
                )

            if row["existing_item_id"] is None:
                self._add_issue(
                    "ERROR", "inventory", record,
                    f"Αναφέρεται σε ανύπαρκτο είδος ID {row['item_id']}.",
                    "Διόρθωσε ή διέγραψε την κίνηση.",
                )

            if row["field_id"] is not None and row["existing_field_id"] is None:
                self._add_issue(
                    "WARNING", "inventory", record,
                    f"Αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {row['field_id']}.",
                    "Διόρθωσε το αγροτεμάχιο της κίνησης.",
                )

            if str(row["movement_type"] or "") not in valid_types:
                self._add_issue(
                    "ERROR", "inventory", record,
                    "Μη αναγνωρισμένος τύπος κίνησης.",
                    "Επίλεξε έναν από τους διαθέσιμους τύπους κίνησης.",
                )

            if float(row["quantity"] or 0) <= 0:
                self._add_issue(
                    "ERROR", "inventory", record,
                    "Η ποσότητα είναι 0 ή μικρότερη.",
                    "Καταχώρησε ποσότητα μεγαλύτερη από 0.",
                )

    def _check_declarations(self) -> None:
        if not self._table_exists("cultivation_declarations"):
            return

        declarations = self.db.query(
            """
            SELECT *
            FROM cultivation_declarations
            ORDER BY declaration_year
            """
        )

        fields_table_exists = self._table_exists(
            "cultivation_declaration_fields"
        )

        for row in declarations:
            declaration_id = int(row["id"])
            year = int(row["declaration_year"])
            record = f"{year}"

            if not str(row["producer_name"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "declaration",
                    record,
                    "Η αποθηκευμένη δήλωση δεν έχει όνομα παραγωγού.",
                    "Άνοιξε τη δήλωση, κάνε επεξεργασία και αποθήκευσέ την ξανά.",
                )

            if not str(row["producer_tax_id"] or "").strip():
                self._add_issue(
                    "ERROR",
                    "declaration",
                    record,
                    "Η αποθηκευμένη δήλωση δεν έχει ΑΦΜ παραγωγού.",
                    "Διόρθωσε πρώτα τα Στοιχεία Παραγωγού και αποθήκευσε ξανά τη δήλωση.",
                )

            if fields_table_exists:
                count_row = self.db.query_one(
                    """
                    SELECT COUNT(*) AS total
                    FROM cultivation_declaration_fields
                    WHERE declaration_id=?
                    """,
                    (declaration_id,),
                )

                selected_count = int(
                    count_row["total"] if count_row else 0
                )

                if selected_count == 0:
                    self._add_issue(
                        "ERROR",
                        "declaration",
                        record,
                        "Η δήλωση δεν περιλαμβάνει κανένα αγροτεμάχιο.",
                        "Επίλεξε τουλάχιστον ένα αγροτεμάχιο και αποθήκευσε ξανά.",
                    )

                orphan_rows = self.db.query(
                    """
                    SELECT cdf.field_id
                    FROM cultivation_declaration_fields cdf
                    LEFT JOIN fields f
                        ON f.id=cdf.field_id
                    WHERE
                        cdf.declaration_id=?
                        AND f.id IS NULL
                    """,
                    (declaration_id,),
                )

                for orphan in orphan_rows:
                    self._add_issue(
                        "ERROR",
                        "declaration",
                        record,
                        f"Η δήλωση αναφέρεται σε ανύπαρκτο αγροτεμάχιο ID {orphan['field_id']}.",
                        "Άνοιξε και αποθήκευσε ξανά τη δήλωση με τα σωστά αγροτεμάχια.",
                    )

    @staticmethod
    def _snapshot_hash(payload: dict) -> str:
        hash_payload = dict(payload)
        hash_payload.pop("generated_at", None)

        canonical = json.dumps(
            hash_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def _check_snapshots(self) -> None:
        if not self._table_exists("upload_packages"):
            return

        rows = self.db.query(
            """
            SELECT
                id,
                declaration_year,
                payload_json,
                payload_hash
            FROM upload_packages
            ORDER BY id
            """
        )

        for row in rows:
            snapshot_id = int(row["id"])
            record = f"Snapshot #{snapshot_id}"
            payload_text = str(row["payload_json"] or "")
            stored_hash = str(row["payload_hash"] or "")

            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                self._add_issue(
                    "ERROR",
                    "snapshots",
                    record,
                    "Το snapshot δεν περιέχει έγκυρο JSON.",
                    "Μην το χρησιμοποιήσεις. Δημιούργησε νέο snapshot από το Κέντρο Αποστολής.",
                )
                continue

            actual_hash = self._snapshot_hash(payload)

            if not stored_hash:
                self._add_issue(
                    "ERROR",
                    "snapshots",
                    record,
                    "Λείπει το SHA-256 fingerprint.",
                    "Δημιούργησε νέο snapshot από το Κέντρο Αποστολής.",
                )
            elif actual_hash != stored_hash:
                self._add_issue(
                    "ERROR",
                    "snapshots",
                    record,
                    "Το περιεχόμενο δεν συμφωνεί με το αποθηκευμένο SHA-256.",
                    "Μην το χρησιμοποιήσεις για αποστολή. Δημιούργησε νέο snapshot.",
                )

            payload_year = payload.get("year")

            try:
                payload_year_int = int(payload_year)
            except (TypeError, ValueError):
                payload_year_int = None

            if (
                payload_year_int is not None
                and payload_year_int != int(row["declaration_year"])
            ):
                self._add_issue(
                    "WARNING",
                    "snapshots",
                    record,
                    "Το έτος μέσα στο JSON διαφέρει από το έτος της εγγραφής snapshot.",
                    "Έλεγξε το snapshot πριν από οποιαδήποτε χρήση.",
                )

    def _filtered_issues(self) -> list[dict]:
        severity = self.severity_filter.currentData()
        category = self.category_filter.currentData()
        search = self.search.text().strip().casefold()

        result = []

        for issue in self.all_issues:
            if severity and issue["severity"] != severity:
                continue

            if category and issue["category"] != category:
                continue

            haystack = " ".join(
                [
                    SEVERITY_LABELS.get(
                        issue["severity"],
                        issue["severity"],
                    ),
                    CATEGORY_LABELS.get(
                        issue["category"],
                        issue["category"],
                    ),
                    issue["record"],
                    issue["problem"],
                    issue["fix"],
                ]
            ).casefold()

            if search and search not in haystack:
                continue

            result.append(issue)

        return result

    def _apply_filters(self, *_args) -> None:
        issues = self._filtered_issues()

        self.table.setRowCount(len(issues))

        for row_index, issue in enumerate(issues):
            values = [
                SEVERITY_LABELS.get(
                    issue["severity"],
                    issue["severity"],
                ),
                CATEGORY_LABELS.get(
                    issue["category"],
                    issue["category"],
                ),
                issue["record"],
                issue["problem"],
                issue["fix"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column_index in (3, 4):
                    item.setToolTip(str(value))

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.result_label.setText(
            f"{len(issues)} θέματα"
        )

    def export_csv(self) -> None:
        issues = self._filtered_issues()

        if not issues:
            QMessageBox.information(
                self,
                "Έλεγχος Δεδομένων",
                "Δεν υπάρχουν θέματα για εξαγωγή με τα τρέχοντα φίλτρα.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Εξαγωγή ελέγχου δεδομένων",
            "mastixa_data_quality.csv",
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
                writer = csv.writer(
                    handle,
                    delimiter=";",
                )

                writer.writerow(
                    [tr(value) for value in [
                        "Σοβαρότητα",
                        "Ενότητα",
                        "Εγγραφή",
                        "Πρόβλημα",
                        "Προτεινόμενη διόρθωση",
                    ]]
                )

                for issue in issues:
                    writer.writerow(
                        [
                            SEVERITY_LABELS.get(
                                issue["severity"],
                                issue["severity"],
                            ),
                            CATEGORY_LABELS.get(
                                issue["category"],
                                issue["category"],
                            ),
                            issue["record"],
                            issue["problem"],
                            issue["fix"],
                        ]
                    )
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Έλεγχος Δεδομένων",
                f"Η εξαγωγή απέτυχε.\n\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Έλεγχος Δεδομένων",
            f"Το CSV δημιουργήθηκε επιτυχώς:\n{path}",
        )
