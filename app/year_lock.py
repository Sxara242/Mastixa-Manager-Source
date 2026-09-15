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
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .language import tr
from .ui_helpers import table_widget


def ensure_year_lock_schema(db: Database) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS year_locks (
            year INTEGER PRIMARY KEY,
            is_locked INTEGER NOT NULL DEFAULT 0,
            locked_at TEXT,
            unlocked_at TEXT,
            reason TEXT NOT NULL DEFAULT ''
        )
        """
    )


def is_year_locked(db: Database, year: int) -> bool:
    ensure_year_lock_schema(db)

    row = db.query_one(
        """
        SELECT is_locked
        FROM year_locks
        WHERE year=?
        """,
        (int(year),),
    )

    return bool(row and int(row["is_locked"] or 0) == 1)


def locked_year_reason(db: Database, year: int) -> str:
    ensure_year_lock_schema(db)

    row = db.query_one(
        """
        SELECT reason
        FROM year_locks
        WHERE year=?
        """,
        (int(year),),
    )

    if row is None:
        return ""

    return row["reason"] or ""


def warn_locked_year(parent, db: Database, year: int) -> None:
    reason = locked_year_reason(db, year)

    message = (
        f"Το έτος {year} είναι κλειδωμένο.\n\n"
        "Δεν επιτρέπεται προσθήκη, αλλαγή ή διαγραφή "
        "ετήσιων δεδομένων όσο παραμένει κλειδωμένο."
    )

    if reason:
        message += f"\n\nΑιτιολογία:\n{reason}"

    QMessageBox.warning(
        parent,
        "Κλειδωμένο έτος",
        message,
    )


class YearLockPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_year: int | None = None

        self._ensure_schema_and_audit_triggers()

        layout = QVBoxLayout(self)

        title = QLabel("Κλείδωμα Έτους")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Προστασία ολοκληρωμένων ετών από κατά λάθος αλλαγές"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        info_box = QGroupBox()
        info_layout = QVBoxLayout(info_box)

        info_title = QLabel("Τι προστατεύει το κλείδωμα")
        info_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        info_layout.addWidget(info_title)

        info = QLabel(
            "Όταν ένα έτος είναι κλειδωμένο, δεν επιτρέπονται αλλαγές "
            "σε Παραγωγή, Πωλήσεις, Άρδευση & Λίπανση, Φυτοπροστασία, Εργατικά, Φυτεύσεις, Κινήσεις Αποθήκης, Έσοδα, Έξοδα και στη Δήλωση Καλλιέργειας "
            "του συγκεκριμένου έτους. Τα Αγροτεμάχια παραμένουν master "
            "δεδομένα και μπορούν να ενημερώνονται. Για ακριβές ιστορικό "
            "της δήλωσης χρησιμοποίησε τα snapshots του Κέντρου Αποστολής."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #67746d;")
        info_layout.addWidget(info)

        layout.addWidget(info_box)

        control_box = QGroupBox()
        control_layout = QVBoxLayout(control_box)

        control_title = QLabel("Διαχείριση")
        control_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        control_layout.addWidget(control_title)

        form = QFormLayout()

        self.year = QComboBox()
        self.year.currentIndexChanged.connect(self._year_changed)
        form.addRow("Έτος", self.year)

        self.reason = QLineEdit()
        self.reason.setPlaceholderText(
            "Π.χ. Ολοκληρώθηκε η χρήση / υποβλήθηκε η δήλωση"
        )
        form.addRow("Αιτιολογία", self.reason)

        control_layout.addLayout(form)

        buttons = QHBoxLayout()

        self.lock_button = QPushButton("Κλείδωμα έτους")
        self.lock_button.clicked.connect(self.lock_year)
        buttons.addWidget(self.lock_button)

        self.unlock_button = QPushButton("Ξεκλείδωμα έτους")
        self.unlock_button.clicked.connect(self.unlock_year)
        buttons.addWidget(self.unlock_button)

        buttons.addStretch()
        control_layout.addLayout(buttons)

        layout.addWidget(control_box)

        table_box = QGroupBox()
        table_layout = QVBoxLayout(table_box)

        table_title = QLabel("Κατάσταση ετών")
        table_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        table_layout.addWidget(table_title)

        self.table = table_widget(
            [
                "Έτος",
                "Κατάσταση",
                "Κλειδώθηκε",
                "Ξεκλειδώθηκε",
                "Αιτιολογία",
            ]
        )
        self.table.cellClicked.connect(self._load_selected)

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
            QHeaderView.ResizeMode.Stretch,
        )

        table_layout.addWidget(self.table)
        layout.addWidget(table_box)
        layout.addStretch()

        self.refresh()

    def _ensure_schema_and_audit_triggers(self) -> None:
        ensure_year_lock_schema(self.db)

        # AuditPage is constructed before this page in MainWindow, so
        # audit_events normally already exists. IF NOT EXISTS keeps this safe.
        audit_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='audit_events'
            """
        )

        if audit_exists is None:
            return

        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_year_lock_insert
            AFTER INSERT ON year_locks
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'year_locks',
                    'INSERT',
                    CAST(NEW.year AS TEXT),
                    CASE
                        WHEN NEW.is_locked=1
                        THEN 'Κλείδωμα έτους ' || CAST(NEW.year AS TEXT) ||
                             ' | ' || COALESCE(NEW.reason, '')
                        ELSE 'Δημιουργία κατάστασης έτους ' ||
                             CAST(NEW.year AS TEXT)
                    END
                );
            END
            """
        )

        self.db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS audit_year_lock_update
            AFTER UPDATE ON year_locks
            BEGIN
                INSERT INTO audit_events(
                    event_time, table_name, action, record_id, details
                )
                VALUES(
                    datetime('now','localtime'),
                    'year_locks',
                    'UPDATE',
                    CAST(NEW.year AS TEXT),
                    CASE
                        WHEN NEW.is_locked=1
                        THEN 'Κλείδωμα έτους ' || CAST(NEW.year AS TEXT) ||
                             ' | ' || COALESCE(NEW.reason, '')
                        ELSE 'Ξεκλείδωμα έτους ' || CAST(NEW.year AS TEXT)
                    END
                );
            END
            """
        )

    def _available_years(self) -> list[int]:
        current_year = QDate.currentDate().year()

        rows = self.db.query(
            """
            SELECT year
            FROM (
                SELECT CAST(SUBSTR(entry_date, 1, 4) AS INTEGER) AS year
                FROM production
                WHERE entry_date IS NOT NULL AND entry_date <> ''

                UNION

                SELECT CAST(SUBSTR(entry_date, 1, 4) AS INTEGER) AS year
                FROM income
                WHERE entry_date IS NOT NULL AND entry_date <> ''

                UNION

                SELECT CAST(SUBSTR(entry_date, 1, 4) AS INTEGER) AS year
                FROM expenses
                WHERE entry_date IS NOT NULL AND entry_date <> ''

                UNION

                SELECT declaration_year AS year
                FROM cultivation_declarations

                UNION

                SELECT CAST(SUBSTR(activity_date, 1, 4) AS INTEGER) AS year
                FROM farm_activities
                WHERE activity_date IS NOT NULL AND activity_date <> ''

                UNION

                SELECT CAST(SUBSTR(movement_date, 1, 4) AS INTEGER) AS year
                FROM inventory_movements
                WHERE movement_date IS NOT NULL AND movement_date <> ''

                UNION

                SELECT year
                FROM year_locks
            )
            WHERE year IS NOT NULL
            ORDER BY year DESC
            """
        )

        years = {current_year}

        plant_protection_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='plant_protection_records'
            """
        )

        if plant_protection_exists is not None:
            plant_year_rows = self.db.query(
                """
                SELECT DISTINCT
                    CAST(SUBSTR(application_date, 1, 4) AS INTEGER) AS year
                FROM plant_protection_records
                WHERE
                    application_date IS NOT NULL
                    AND application_date <> ''
                """
            )

            for row in plant_year_rows:
                try:
                    years.add(int(row["year"]))
                except (TypeError, ValueError):
                    continue

        labor_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='labor_entries'
            """
        )

        if labor_exists is not None:
            labor_year_rows = self.db.query(
                """
                SELECT DISTINCT
                    CAST(SUBSTR(work_date, 1, 4) AS INTEGER) AS year
                FROM labor_entries
                WHERE
                    work_date IS NOT NULL
                    AND work_date <> ''
                """
            )

            for labor_row in labor_year_rows:
                try:
                    years.add(int(labor_row["year"]))
                except (TypeError, ValueError):
                    continue

        plantings_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='planting_batches'
            """
        )

        if plantings_exists is not None:
            planting_year_rows = self.db.query(
                """
                SELECT DISTINCT
                    CAST(SUBSTR(planting_date, 1, 4) AS INTEGER) AS year
                FROM planting_batches
                WHERE planting_date IS NOT NULL AND planting_date <> ''
                """
            )

            for planting_row in planting_year_rows:
                try:
                    years.add(int(planting_row["year"]))
                except (TypeError, ValueError):
                    continue

        sales_exists = self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='production_sales'
            """
        )

        if sales_exists is not None:
            sales_year_rows = self.db.query(
                """
                SELECT DISTINCT
                    CAST(SUBSTR(sale_date,1,4) AS INTEGER) AS year
                FROM production_sales
                WHERE sale_date IS NOT NULL AND sale_date <> ''
                """
            )

            for sales_row in sales_year_rows:
                try:
                    years.add(int(sales_row["year"]))
                except (TypeError, ValueError):
                    continue

        for row in rows:
            try:
                years.add(int(row["year"]))
            except (TypeError, ValueError):
                continue

        return sorted(years, reverse=True)

    def refresh(self) -> None:
        self._ensure_schema_and_audit_triggers()

        current = self.year.currentData()
        years = self._available_years()

        self.year.blockSignals(True)
        self.year.clear()

        for value in years:
            self.year.addItem(str(value), value)

        index = self.year.findData(current)
        if index < 0 and years:
            index = 0
        if index >= 0:
            self.year.setCurrentIndex(index)

        self.year.blockSignals(False)

        self.table.setRowCount(len(years))

        for row_index, year in enumerate(years):
            lock_row = self.db.query_one(
                """
                SELECT *
                FROM year_locks
                WHERE year=?
                """,
                (year,),
            )

            locked = bool(
                lock_row
                and int(lock_row["is_locked"] or 0) == 1
            )

            values = [
                str(year),
                tr("Κλειδωμένο" if locked else "Ανοιχτό"),
                (
                    lock_row["locked_at"] or ""
                    if lock_row is not None
                    else ""
                ),
                (
                    lock_row["unlocked_at"] or ""
                    if lock_row is not None
                    else ""
                ),
                (
                    lock_row["reason"] or ""
                    if lock_row is not None
                    else ""
                ),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                if column_index == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        year,
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self._update_button_state()

    def _year_changed(self, _index: int) -> None:
        year = self.year.currentData()
        self.selected_year = (
            int(year)
            if year is not None
            else None
        )

        if self.selected_year is None:
            self.reason.clear()
            self._update_button_state()
            return

        row = self.db.query_one(
            """
            SELECT reason
            FROM year_locks
            WHERE year=?
            """,
            (self.selected_year,),
        )

        self.reason.setText(
            (row["reason"] or "")
            if row is not None
            else ""
        )

        self._update_button_state()

    def _load_selected(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        year = item.data(Qt.ItemDataRole.UserRole)
        if year is None:
            return

        index = self.year.findData(int(year))
        if index >= 0:
            self.year.setCurrentIndex(index)

    def _update_button_state(self) -> None:
        year = self.year.currentData()

        if year is None:
            self.lock_button.setEnabled(False)
            self.unlock_button.setEnabled(False)
            return

        locked = is_year_locked(self.db, int(year))

        self.lock_button.setEnabled(not locked)
        self.unlock_button.setEnabled(locked)

    def lock_year(self) -> None:
        year = self.year.currentData()
        if year is None:
            return

        year = int(year)

        if is_year_locked(self.db, year):
            return

        answer = QMessageBox.warning(
            self,
            "Κλείδωμα έτους",
            f"Να κλειδωθεί το έτος {year};\n\n"
            "Μετά το κλείδωμα δεν θα μπορείς να προσθέσεις, "
            "να αλλάξεις ή να διαγράψεις Παραγωγή, Εργασίες Αγρού, Έσοδα, Έξοδα "
            "και Δήλωση Καλλιέργειας για αυτό το έτος.\n\n"
            "Μπορείς να το ξεκλειδώσεις αργότερα από αυτή τη σελίδα.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        reason = self.reason.text().strip()

        self.db.execute(
            """
            INSERT INTO year_locks(
                year,
                is_locked,
                locked_at,
                unlocked_at,
                reason
            )
            VALUES(
                ?,
                1,
                CURRENT_TIMESTAMP,
                NULL,
                ?
            )
            ON CONFLICT(year)
            DO UPDATE SET
                is_locked=1,
                locked_at=CURRENT_TIMESTAMP,
                unlocked_at=NULL,
                reason=excluded.reason
            """,
            (year, reason),
        )

        self.refresh()

        QMessageBox.information(
            self,
            "Κλείδωμα έτους",
            f"Το έτος {year} κλειδώθηκε επιτυχώς.",
        )

    def unlock_year(self) -> None:
        year = self.year.currentData()
        if year is None:
            return

        year = int(year)

        if not is_year_locked(self.db, year):
            return

        answer = QMessageBox.warning(
            self,
            "Ξεκλείδωμα έτους",
            f"Να ξεκλειδωθεί το έτος {year};\n\n"
            "Μετά το ξεκλείδωμα θα επιτρέπονται ξανά αλλαγές "
            "στα ετήσια δεδομένα.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.execute(
            """
            UPDATE year_locks
            SET
                is_locked=0,
                unlocked_at=CURRENT_TIMESTAMP
            WHERE year=?
            """,
            (year,),
        )

        self.refresh()

        QMessageBox.information(
            self,
            "Ξεκλείδωμα έτους",
            f"Το έτος {year} ξεκλειδώθηκε.",
        )
