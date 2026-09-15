from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .ui_helpers import compact_decimal, table_widget
from .year_lock import is_year_locked, warn_locked_year


class AlertsPage(QWidget):
    """
    Derived notifications / pending actions center.

    No extra alert table is required. Alerts are calculated live from:
    - planned farm activities
    - current inventory stock vs minimum stock
    - equipment service reminders
    - plant-protection pre-harvest waiting periods
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._alerts: list[dict] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("alertsContent")
        content.setStyleSheet(
            "QWidget#alertsContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Ειδοποιήσεις & Εκκρεμότητες")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Εργασίες, αποθέματα, service μηχανημάτων και αναμονές φυτοπροστασίας"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setMinimumHeight(28)
        layout.addWidget(subtitle)

        metrics_box = QGroupBox()
        metrics_layout = QGridLayout(metrics_box)
        metrics_layout.setHorizontalSpacing(12)
        metrics_layout.setVerticalSpacing(12)
        metrics_box.setMinimumHeight(285)

        self.overdue_card = self._metric("Εκπρόθεσμες εργασίες", "0")
        self.today_card = self._metric("Σήμερα", "0")
        self.upcoming_card = self._metric("Επόμενες 7 ημέρες", "0")
        self.low_stock_card = self._metric("Χαμηλό απόθεμα", "0")
        self.out_stock_card = self._metric("Εξαντλημένα", "0")
        self.service_card = self._metric("Service", "0")
        self.harvest_wait_card = self._metric("Αναμονή συγκομιδής", "0")

        cards = (
            self.overdue_card,
            self.today_card,
            self.upcoming_card,
            self.low_stock_card,
            self.out_stock_card,
            self.service_card,
            self.harvest_wait_card,
        )

        for index, (card, _label) in enumerate(cards):
            card.setMinimumHeight(118)
            metrics_layout.addWidget(
                card,
                index // 4,
                index % 4,
            )

        for column in range(4):
            metrics_layout.setColumnStretch(column, 1)

        layout.addWidget(metrics_box)

        filters_box = QGroupBox()
        filters_layout = QHBoxLayout(filters_box)

        filters_layout.addWidget(QLabel("Κατηγορία"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Όλα", None)
        self.category_filter.addItem("Άρδευση & Λίπανση", "activity")
        self.category_filter.addItem("Αποθήκη & Εφόδια", "inventory")
        self.category_filter.addItem("Μηχανήματα & Service", "equipment")
        self.category_filter.addItem("Φυτοπροστασία", "harvest_wait")
        self.category_filter.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.category_filter)

        filters_layout.addWidget(QLabel("Σοβαρότητα"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItem("Όλες", None)
        self.severity_filter.addItem("Άμεση", "critical")
        self.severity_filter.addItem("Προσοχή", "warning")
        self.severity_filter.addItem("Ενημέρωση", "info")
        self.severity_filter.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.severity_filter)

        filters_layout.addStretch()

        refresh_button = QPushButton("Ανανέωση")
        refresh_button.clicked.connect(self.refresh)
        filters_layout.addWidget(refresh_button)

        layout.addWidget(filters_box)

        self.table = table_widget(
            [
                "Σοβαρότητα",
                "Κατηγορία",
                "Ημερομηνία",
                "Αφορά",
                "Μήνυμα",
            ]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.itemSelectionChanged.connect(
            self._selection_changed
        )
        self.table.setMinimumHeight(330)
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

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

        layout.addWidget(self.table)

        actions_box = QGroupBox()
        actions = QHBoxLayout(actions_box)

        self.result_label = QLabel("0 ειδοποιήσεις")
        self.result_label.setStyleSheet(
            "font-weight: 700; color: #26382f;"
        )
        actions.addWidget(self.result_label)

        actions.addStretch()

        self.open_button = QPushButton("Άνοιγμα σχετικής ενότητας")
        self.open_button.clicked.connect(self.open_related_page)
        self.open_button.setEnabled(False)
        actions.addWidget(self.open_button)

        self.defer_button = QPushButton("Αναβολή +1 ημέρα")
        self.defer_button.clicked.connect(self.defer_activity)
        self.defer_button.setEnabled(False)
        actions.addWidget(self.defer_button)

        self.complete_button = QPushButton("Ολοκλήρωση εργασίας")
        self.complete_button.clicked.connect(self.complete_activity)
        self.complete_button.setEnabled(False)
        actions.addWidget(self.complete_button)

        layout.addWidget(actions_box)

        note = QLabel(
            "Οι ειδοποιήσεις υπολογίζονται αυτόματα από τα υπάρχοντα δεδομένα: "
            "εργασίες, απόθεμα, service και χρονικά διαστήματα αναμονής πριν τη συγκομιδή."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #67746d;")
        layout.addWidget(note)

        self.refresh()

    def _metric(self, caption: str, value: str):
        box = QGroupBox()
        box.setObjectName("metricCard")

        inner = QVBoxLayout(box)

        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")
        inner.addWidget(caption_label)

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        inner.addWidget(value_label)

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

    @staticmethod
    def _stock_expression() -> str:
        return """
            COALESCE(SUM(
                CASE
                    WHEN m.movement_type IN ('Παραλαβή','Διόρθωση +')
                        THEN m.quantity
                    WHEN m.movement_type IN ('Κατανάλωση','Διόρθωση -')
                        THEN -m.quantity
                    ELSE 0
                END
            ),0)
        """

    def refresh(self, *_args) -> None:
        alerts: list[dict] = []

        today = QDate.currentDate()
        today_iso = today.toString("yyyy-MM-dd")
        next_7_iso = today.addDays(7).toString("yyyy-MM-dd")

        overdue_count = 0
        today_count = 0
        upcoming_count = 0
        low_stock_count = 0
        out_stock_count = 0
        service_count = 0
        harvest_wait_count = 0

        if self._table_exists("farm_activities"):
            rows = self.db.query(
                """
                SELECT
                    a.id,
                    a.activity_date,
                    a.category,
                    a.description,
                    a.status,
                    f.name AS field_name
                FROM farm_activities a
                LEFT JOIN fields f
                    ON f.id=a.field_id
                WHERE a.status='Προγραμματισμένη'
                ORDER BY a.activity_date, a.id
                """
            )

            for row in rows:
                date_text = row["activity_date"] or ""
                parsed = QDate.fromString(
                    date_text,
                    "yyyy-MM-dd",
                )

                if not parsed.isValid():
                    continue

                field_name = (
                    row["field_name"]
                    or "Γενική / όλα τα αγροτεμάχια"
                )
                activity_type = row["category"] or "Εργασία"
                description = row["description"] or ""

                if parsed < today:
                    overdue_count += 1
                    severity = "critical"
                    severity_label = "Άμεση"
                    message = (
                        f"Εκπρόθεσμη προγραμματισμένη εργασία: {activity_type}"
                    )
                elif date_text == today_iso:
                    today_count += 1
                    severity = "warning"
                    severity_label = "Προσοχή"
                    message = (
                        f"Προγραμματισμένη για σήμερα: {activity_type}"
                    )
                elif date_text <= next_7_iso:
                    upcoming_count += 1
                    severity = "info"
                    severity_label = "Ενημέρωση"
                    message = (
                        f"Επερχόμενη εργασία: {activity_type}"
                    )
                else:
                    continue

                if description:
                    message += f" — {description}"

                alerts.append(
                    {
                        "kind": "activity",
                        "record_id": int(row["id"]),
                        "severity": severity,
                        "severity_label": severity_label,
                        "category_label": "Άρδευση & Λίπανση",
                        "date": date_text,
                        "subject": field_name,
                        "message": message,
                    }
                )

        if (
            self._table_exists("inventory_items")
            and self._table_exists("inventory_movements")
        ):
            rows = self.db.query(
                f"""
                SELECT
                    i.id,
                    i.name,
                    i.unit,
                    i.minimum_stock,
                    {self._stock_expression()} AS current_stock
                FROM inventory_items i
                LEFT JOIN inventory_movements m
                    ON m.item_id=i.id
                GROUP BY
                    i.id,
                    i.name,
                    i.unit,
                    i.minimum_stock
                ORDER BY i.name, i.id
                """
            )

            for row in rows:
                stock = float(row["current_stock"] or 0)
                minimum = float(row["minimum_stock"] or 0)

                if stock <= 0:
                    out_stock_count += 1
                    severity = "critical"
                    severity_label = "Άμεση"
                    message = (
                        f"Εξαντλημένο απόθεμα: {compact_decimal(stock, 3)} "
                        f"{row['unit'] or ''}"
                    )
                elif minimum > 0 and stock <= minimum:
                    low_stock_count += 1
                    severity = "warning"
                    severity_label = "Προσοχή"
                    message = (
                        f"Χαμηλό απόθεμα: {compact_decimal(stock, 3)} {row['unit'] or ''} "
                        f"(ελάχιστο {compact_decimal(minimum, 3)})"
                    )
                else:
                    continue

                alerts.append(
                    {
                        "kind": "inventory",
                        "record_id": int(row["id"]),
                        "severity": severity,
                        "severity_label": severity_label,
                        "category_label": "Αποθήκη & Εφόδια",
                        "date": "",
                        "subject": row["name"] or f"ID {row['id']}",
                        "message": message,
                    }
                )


        # --------------------------------------------------------------
        # Equipment service reminders
        # --------------------------------------------------------------
        if (
            self._table_exists("equipment")
            and self._table_exists("equipment_maintenance")
        ):
            equipment_rows = self.db.query(
                """
                SELECT
                    e.id,
                    e.name,
                    e.current_meter,
                    e.meter_type,
                    e.status,
                    (
                        SELECT m.next_service_date
                        FROM equipment_maintenance m
                        WHERE
                            m.equipment_id=e.id
                            AND (
                                m.next_service_date IS NOT NULL
                                OR m.next_service_meter IS NOT NULL
                            )
                        ORDER BY m.service_date DESC,m.id DESC
                        LIMIT 1
                    ) AS next_service_date,
                    (
                        SELECT m.next_service_meter
                        FROM equipment_maintenance m
                        WHERE
                            m.equipment_id=e.id
                            AND (
                                m.next_service_date IS NOT NULL
                                OR m.next_service_meter IS NOT NULL
                            )
                        ORDER BY m.service_date DESC,m.id DESC
                        LIMIT 1
                    ) AS next_service_meter
                FROM equipment e
                WHERE e.status NOT IN ('Πωλήθηκε','Εκτός λειτουργίας')
                ORDER BY e.name,e.id
                """
            )

            for row in equipment_rows:
                due_date = QDate.fromString(
                    row["next_service_date"] or "",
                    "yyyy-MM-dd",
                )
                due_meter = row["next_service_meter"]
                current_meter = float(row["current_meter"] or 0)

                date_overdue = (
                    due_date.isValid()
                    and due_date < today
                )
                date_upcoming = (
                    due_date.isValid()
                    and 0 <= today.daysTo(due_date) <= 30
                )
                meter_overdue = (
                    due_meter is not None
                    and current_meter >= float(due_meter)
                )
                meter_upcoming = (
                    due_meter is not None
                    and 0 < float(due_meter) - current_meter <= 50
                )

                if not (
                    date_overdue
                    or date_upcoming
                    or meter_overdue
                    or meter_upcoming
                ):
                    continue

                service_count += 1

                overdue = date_overdue or meter_overdue
                severity = "critical" if overdue else "warning"
                severity_label = "Άμεση" if overdue else "Προσοχή"

                details: list[str] = []

                if due_date.isValid():
                    details.append(
                        f"ημερομηνία {due_date.toString('dd/MM/yyyy')}"
                    )

                if due_meter is not None:
                    meter_label = (
                        "km"
                        if row["meter_type"] == "km"
                        else "ώρες"
                        if row["meter_type"] == "hours"
                        else ""
                    )
                    details.append(
                        f"μετρητής {compact_decimal(due_meter, 1)} {meter_label}".strip()
                    )

                message = (
                    "Εκπρόθεσμο service"
                    if overdue
                    else "Πλησιάζει service"
                )

                if details:
                    message += ": " + " / ".join(details)

                alerts.append(
                    {
                        "kind": "equipment",
                        "record_id": int(row["id"]),
                        "severity": severity,
                        "severity_label": severity_label,
                        "category_label": "Μηχανήματα & Service",
                        "date": (
                            row["next_service_date"]
                            if due_date.isValid()
                            else ""
                        ),
                        "subject": row["name"] or f"ID {row['id']}",
                        "message": message,
                    }
                )

        # --------------------------------------------------------------
        # Plant protection waiting period before harvest
        # --------------------------------------------------------------
        if self._table_exists("plant_protection_records"):
            protection_rows = self.db.query(
                """
                SELECT
                    p.id,
                    p.application_date,
                    p.product_name,
                    p.purpose,
                    p.harvest_interval_days,
                    f.name AS field_name
                FROM plant_protection_records p
                LEFT JOIN fields f
                    ON f.id=p.field_id
                WHERE p.harvest_interval_days > 0
                ORDER BY p.application_date DESC,p.id DESC
                """
            )

            for row in protection_rows:
                application_date = QDate.fromString(
                    row["application_date"] or "",
                    "yyyy-MM-dd",
                )

                if not application_date.isValid():
                    continue

                safe_date = application_date.addDays(
                    int(row["harvest_interval_days"] or 0)
                )
                days_left = today.daysTo(safe_date)

                # Only active waiting periods are alerts.
                if days_left <= 0:
                    continue

                harvest_wait_count += 1

                severity = (
                    "critical"
                    if days_left >= 3
                    else "warning"
                )
                severity_label = (
                    "Άμεση"
                    if severity == "critical"
                    else "Προσοχή"
                )

                product = row["product_name"] or "Φυτοπροστασία"
                field_name = row["field_name"] or "Αγροτεμάχιο"

                message = (
                    f"Μην γίνει συγκομιδή για ακόμη {days_left} "
                    f"{'ημέρα' if days_left == 1 else 'ημέρες'}. "
                    f"Ασφαλής ημερομηνία: {safe_date.toString('dd/MM/yyyy')} "
                    f"— {product}"
                )

                alerts.append(
                    {
                        "kind": "harvest_wait",
                        "record_id": int(row["id"]),
                        "severity": severity,
                        "severity_label": severity_label,
                        "category_label": "Φυτοπροστασία",
                        "date": row["application_date"] or "",
                        "subject": field_name,
                        "message": message,
                    }
                )

        severity_order = {
            "critical": 0,
            "warning": 1,
            "info": 2,
        }

        alerts.sort(
            key=lambda item: (
                severity_order.get(item["severity"], 99),
                item["date"] or "9999-12-31",
                item["subject"],
            )
        )

        self._alerts = alerts

        self.overdue_card[1].setText(str(overdue_count))
        self.today_card[1].setText(str(today_count))
        self.upcoming_card[1].setText(str(upcoming_count))
        self.low_stock_card[1].setText(str(low_stock_count))
        self.out_stock_card[1].setText(str(out_stock_count))
        self.service_card[1].setText(str(service_count))
        self.harvest_wait_card[1].setText(str(harvest_wait_count))

        self._apply_filters()

    def _filtered_alerts(self) -> list[dict]:
        kind = self.category_filter.currentData()
        severity = self.severity_filter.currentData()

        result = []

        for item in self._alerts:
            if kind and item["kind"] != kind:
                continue

            if severity and item["severity"] != severity:
                continue

            result.append(item)

        return result

    def _apply_filters(self, *_args) -> None:
        alerts = self._filtered_alerts()

        self.table.setRowCount(len(alerts))

        for row_index, alert in enumerate(alerts):
            values = [
                alert["severity_label"],
                alert["category_label"],
                alert["date"],
                alert["subject"],
                alert["message"],
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    alert,
                )
                item.setTextAlignment(
                    int(
                        Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter
                    )
                )

                if column_index == 4:
                    item.setToolTip(str(value))

                self.table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self.result_label.setText(
            f"{len(alerts)} ειδοποιήσεις"
        )
        self._selection_changed()

    def _selected_alert(self) -> dict | None:
        selected = self.table.selectedItems()

        if not selected:
            return None

        row = selected[0].row()
        item = self.table.item(row, 0)

        if item is None:
            return None

        value = item.data(Qt.ItemDataRole.UserRole)

        return value if isinstance(value, dict) else None

    def _selection_changed(self) -> None:
        alert = self._selected_alert()

        has_alert = alert is not None
        activity_selected = bool(
            alert and alert.get("kind") == "activity"
        )

        self.open_button.setEnabled(has_alert)
        self.defer_button.setEnabled(activity_selected)
        self.complete_button.setEnabled(activity_selected)

    def open_related_page(self) -> None:
        alert = self._selected_alert()

        if alert is None:
            return

        window = self.window()
        change_page = getattr(window, "change_page", None)

        if not callable(change_page):
            return

        if alert["kind"] == "activity":
            change_page(12)
        elif alert["kind"] == "inventory":
            change_page(13)
        elif alert["kind"] == "equipment":
            change_page(16)
        elif alert["kind"] == "harvest_wait":
            change_page(19)

    def _activity_year(self, activity_id: int) -> int | None:
        row = self.db.query_one(
            """
            SELECT activity_date
            FROM farm_activities
            WHERE id=?
            """,
            (activity_id,),
        )

        if row is None:
            return None

        parsed = QDate.fromString(
            row["activity_date"] or "",
            "yyyy-MM-dd",
        )

        return parsed.year() if parsed.isValid() else None

    def complete_activity(self) -> None:
        alert = self._selected_alert()

        if not alert or alert["kind"] != "activity":
            return

        activity_id = int(alert["record_id"])
        year = self._activity_year(activity_id)

        if (
            year is not None
            and is_year_locked(self.db, year)
        ):
            warn_locked_year(self, self.db, year)
            return

        answer = QMessageBox.question(
            self,
            "Ολοκλήρωση εργασίας",
            "Να σημειωθεί η επιλεγμένη εργασία ως ολοκληρωμένη;",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.db.execute(
            """
            UPDATE farm_activities
            SET
                status='Ολοκληρώθηκε',
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (activity_id,),
        )

        self.refresh()

    def defer_activity(self) -> None:
        alert = self._selected_alert()

        if not alert or alert["kind"] != "activity":
            return

        activity_id = int(alert["record_id"])

        row = self.db.query_one(
            """
            SELECT activity_date
            FROM farm_activities
            WHERE id=?
            """,
            (activity_id,),
        )

        if row is None:
            return

        parsed = QDate.fromString(
            row["activity_date"] or "",
            "yyyy-MM-dd",
        )

        if not parsed.isValid():
            QMessageBox.warning(
                self,
                "Αναβολή εργασίας",
                "Η εργασία δεν έχει έγκυρη ημερομηνία.",
            )
            return

        original_year = parsed.year()

        if is_year_locked(self.db, original_year):
            warn_locked_year(
                self,
                self.db,
                original_year,
            )
            return

        new_date = parsed.addDays(1)

        if (
            new_date.year() != original_year
            and is_year_locked(self.db, new_date.year())
        ):
            warn_locked_year(
                self,
                self.db,
                new_date.year(),
            )
            return

        self.db.execute(
            """
            UPDATE farm_activities
            SET
                activity_date=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                new_date.toString("yyyy-MM-dd"),
                activity_id,
            ),
        )

        self.refresh()
