from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from PySide6.QtCore import Qt
import csv
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
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

from .localized_messages import _text, _message
from .database import Database
from .report_quantities import quantities, quantity_text, coherent_quantity, unposted_activity_cost
from .ui_helpers import compact_decimal, table_widget


class FieldFinancePage(YearFilteredPage):
    """
    Direct cost / profitability analysis per field.

    Important accounting rule:
    - income / expenses count only when explicitly assigned to a field
    - only activity costs without a linked automatic expense are added separately
    - plant-protection, labor and planting costs remain direct operational costs
    - unassigned income / expenses stay visible separately and are NOT allocated
      proportionally, so the report does not invent accounting data
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("fieldFinanceContent")
        content.setStyleSheet(
            "QWidget#fieldFinanceContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 18, 16, 20)
        layout.setSpacing(14)
        scroll.setWidget(content)

        title = QLabel("Κόστη ανά Αγροτεμάχιο")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Άμεσα έσοδα, έξοδα και καλλιεργητικές δαπάνες ανά αγροτεμάχιο"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        filter_box = QGroupBox()
        filter_layout = QHBoxLayout(filter_box)

        filter_layout.addWidget(QLabel("Έτος"))
        self.year = QComboBox()
        self.year.currentIndexChanged.connect(self.refresh)
        filter_layout.addWidget(self.year)

        filter_layout.addStretch()

        self.export_button = QPushButton("Εξαγωγή CSV")
        self.export_button.clicked.connect(self.export_csv)
        filter_layout.addWidget(self.export_button)

        layout.addWidget(filter_box)

        metrics = QGridLayout()

        self.direct_cost_card = self._metric_card("Άμεσο κόστος", "0,00 €")
        self.assigned_income_card = self._metric_card(
            "Κατανεμημένα έσοδα",
            "0,00 €",
        )
        self.direct_result_card = self._metric_card(
            "Άμεσο αποτέλεσμα",
            "0,00 €",
        )
        self.unassigned_card = self._metric_card(
            "Μη κατανεμημένα",
            "0,00 € / 0,00 €",
        )

        metrics.addWidget(self.direct_cost_card[0], 0, 0)
        metrics.addWidget(self.assigned_income_card[0], 0, 1)
        metrics.addWidget(self.direct_result_card[0], 1, 0)
        metrics.addWidget(self.unassigned_card[0], 1, 1)

        layout.addLayout(metrics)

        note_box = QGroupBox()
        note_layout = QVBoxLayout(note_box)

        note_title = QLabel("Πώς υπολογίζεται")
        note_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        note_layout.addWidget(note_title)

        note = QLabel(
            "Τα γενικά / μη κατανεμημένα ποσά εμφανίζονται ξεχωριστά και δεν μοιράζονται αυτόματα. "
            "Τα αυτόματα έξοδα Άρδευσης & Λίπανσης μετριούνται μία φορά. "
            "Κόστη ημερολογίων χωρίς συνδεδεμένο έξοδο προστίθενται χωριστά. "
            "Χειροκίνητες διπλές καταχωρήσεις δεν αντιστοιχίζονται αυτόματα."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #67746d;")
        note_layout.addWidget(note)

        layout.addWidget(note_box)

        table_box = QGroupBox()
        table_layout = QVBoxLayout(table_box)

        table_title = QLabel("Ανάλυση ανά αγροτεμάχιο")
        table_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        table_layout.addWidget(table_title)

        self.table = table_widget(
            [
                "Αγροτεμάχιο",
                "Παραγωγή",
                "Έσοδα",
                "Έξοδα",
                "Άρδευση / Λίπανση",
                "Φυτοπροστασία",
                "Εργατικά",
                "Φυτεύσεις",
                "Σύνολο κόστους",
                "Άμεσο αποτέλεσμα",
                "Κόστος / μονάδα",
            ]
        )
        self.table.setMinimumHeight(340)

        header = self.table.horizontalHeader()
        for index in range(self.table.columnCount()):
            header.setSectionResizeMode(
                index,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        table_layout.addWidget(self.table)
        layout.addWidget(table_box)

        self._load_years()
        self.refresh()

    def _metric_card(self, caption: str, value: str):
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

    @staticmethod
    def _money(value: float) -> str:
        return (
            f"{value:,.2f} €"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

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

    def _has_column(self, table_name: str, column_name: str) -> bool:
        if not self._table_exists(table_name):
            return False

        rows = self.db.query(f"PRAGMA table_info({table_name})")
        return any(row["name"] == column_name for row in rows)

    def _load_years(self) -> None:
        populate_year_filter(self, self.year, strings=True)

    def _sum_for_field(
        self,
        *,
        table: str,
        amount_column: str,
        field_id: int,
        date_column: str,
        year: str | None,
    ) -> float:
        if not self._table_exists(table):
            return 0.0

        if not self._has_column(table, "field_id"):
            return 0.0

        if year is None:
            row = self.db.query_one(
                f"""
                SELECT COALESCE(SUM({amount_column}),0) AS total
                FROM {table}
                WHERE field_id=?
                """,
                (field_id,),
            )
        else:
            row = self.db.query_one(
                f"""
                SELECT COALESCE(SUM({amount_column}),0) AS total
                FROM {table}
                WHERE
                    field_id=?
                    AND SUBSTR({date_column},1,4)=?
                """,
                (field_id, year),
            )

        return float(row["total"] or 0) if row else 0.0

    def _unassigned_total(
        self,
        table: str,
        year: str | None,
    ) -> float:
        if not self._table_exists(table):
            return 0.0

        if not self._has_column(table, "field_id"):
            row = self.db.query_one(
                f"SELECT COALESCE(SUM(amount),0) AS total FROM {table}"
            )
            return float(row["total"] or 0) if row else 0.0

        if year is None:
            row = self.db.query_one(
                f"""
                SELECT COALESCE(SUM(amount),0) AS total
                FROM {table}
                WHERE field_id IS NULL
                """
            )
        else:
            row = self.db.query_one(
                f"""
                SELECT COALESCE(SUM(amount),0) AS total
                FROM {table}
                WHERE
                    field_id IS NULL
                    AND SUBSTR(entry_date,1,4)=?
                """,
                (year,),
            )

        return float(row["total"] or 0) if row else 0.0

    def refresh(self, *_args) -> None:
        self._load_years()
        year = self.year.currentData()

        fields = self.db.query(
            """
            SELECT id, name
            FROM fields
            ORDER BY name, id
            """
        )

        rows: list[list[str]] = []

        total_cost = 0.0
        total_assigned_income = 0.0
        total_direct_result = 0.0

        for field in fields:
            field_id = int(field["id"])

            production = quantities(self.db, year=year, field_id=field_id)

            assigned_income = self._sum_for_field(
                table="income",
                amount_column="amount",
                field_id=field_id,
                date_column="entry_date",
                year=year,
            )
            assigned_expenses = self._sum_for_field(
                table="expenses",
                amount_column="amount",
                field_id=field_id,
                date_column="entry_date",
                year=year,
            )
            activity_cost = unposted_activity_cost(self.db, field_id, year)
            protection_cost = self._sum_for_field(
                table="plant_protection_records",
                amount_column="cost",
                field_id=field_id,
                date_column="application_date",
                year=year,
            )
            labor_cost = self._sum_for_field(
                table="labor_entries",
                amount_column="cost",
                field_id=field_id,
                date_column="work_date",
                year=year,
            )
            planting_cost = self._sum_for_field(
                table="planting_batches",
                amount_column="cost",
                field_id=field_id,
                date_column="planting_date",
                year=year,
            )

            direct_cost = (
                assigned_expenses
                + activity_cost
                + protection_cost
                + labor_cost
                + planting_cost
            )
            direct_result = assigned_income - direct_cost
            coherent = coherent_quantity(production, single_product=True)
            cost_per_unit = (f"{self._money(direct_cost/coherent[0])}/{coherent[1]}"
                             if coherent and coherent[0] > 0 else "—")

            total_cost += direct_cost
            total_assigned_income += assigned_income
            total_direct_result += direct_result

            rows.append(
                [
                    field["name"] or f"ID {field_id}",
                    quantity_text(production),
                    self._money(assigned_income),
                    self._money(assigned_expenses),
                    self._money(activity_cost),
                    self._money(protection_cost),
                    self._money(labor_cost),
                    self._money(planting_cost),
                    self._money(direct_cost),
                    self._money(direct_result),
                    cost_per_unit,
                ]
            )

        self.table.setRowCount(len(rows))

        for row_index, values in enumerate(rows):
            for column_index, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(str(value)),
                )

        unassigned_income = self._unassigned_total("income", year)
        unassigned_expenses = self._unassigned_total("expenses", year)

        self.direct_cost_card[1].setText(
            self._money(total_cost)
        )
        self.assigned_income_card[1].setText(
            self._money(total_assigned_income)
        )
        self.direct_result_card[1].setText(
            self._money(total_direct_result)
        )
        self.unassigned_card[1].setText(
            f"{self._money(unassigned_income)} / "
            f"{self._money(unassigned_expenses)}"
        )

    def export_csv(self) -> None:
        if self.table.rowCount() == 0:
            QMessageBox.information(
                self,
                "Κόστη ανά Αγροτεμάχιο",
                "Δεν υπάρχουν δεδομένα για εξαγωγή.",
            )
            return

        year = self.year.currentData()
        suffix = year if year is not None else "ola_ta_eti"

        path, _ = QFileDialog.getSaveFileName(
            self,
            _text("Εξαγωγή κόστους ανά αγροτεμάχιο"),
            f"mastixa_field_costs_{suffix}.csv",
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

                writer.writerow(
                    [
                        self.table.horizontalHeaderItem(column).text()
                        for column in range(self.table.columnCount())
                    ]
                )

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
            _message(self, 'critical', 'Κόστη ανά Αγροτεμάχιο', 'Η εξαγωγή απέτυχε.\n\n{exc}', exc=exc)
            return

        _message(self, 'information', 'Κόστη ανά Αγροτεμάχιο', 'Το CSV δημιουργήθηκε:\n{path}', path=path)
