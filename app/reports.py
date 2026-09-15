from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .charts import BarChartWidget
from .database import Database
from .exporters import export_report_pdf, export_report_xlsx
from .ui_helpers import compact_decimal, format_kg, table_widget


class ReportsPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("reportsContent")
        content.setStyleSheet("QWidget#reportsContent { background: #f5f6f3; }")
        scroll.viewport().setStyleSheet("background: #f5f6f3;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 20)
        layout.setSpacing(14)

        title = QLabel("Αναφορές & Στατιστικά")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Συνοπτική εικόνα ανά έτος και ανάλυση παραγωγής ανά αγροτεμάχιο"
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        filters = QGroupBox()
        filters_outer = QVBoxLayout(filters)

        filters_title = QLabel("Φίλτρα")
        filters_title.setStyleSheet(
            "font-weight: 700; font-size: 15px; color: #26382f;"
        )
        filters_outer.addWidget(filters_title)

        filters_layout = QHBoxLayout()
        filters_outer.addLayout(filters_layout)

        filters_layout.addWidget(QLabel("Έτος"))
        self.year = QComboBox()
        self.year.currentIndexChanged.connect(self.refresh)
        filters_layout.addWidget(self.year)
        filters_layout.addStretch()

        export_button_style = """
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
        """

        self.export_pdf_button = QPushButton("Εξαγωγή PDF")
        self.export_pdf_button.setEnabled(True)
        self.export_pdf_button.setMinimumWidth(130)
        self.export_pdf_button.setStyleSheet(export_button_style)
        self.export_pdf_button.clicked.connect(self.export_pdf)
        filters_layout.addWidget(self.export_pdf_button)

        self.export_excel_button = QPushButton("Εξαγωγή Excel")
        self.export_excel_button.setEnabled(True)
        self.export_excel_button.setMinimumWidth(130)
        self.export_excel_button.setStyleSheet(export_button_style)
        self.export_excel_button.clicked.connect(self.export_excel)
        filters_layout.addWidget(self.export_excel_button)

        layout.addWidget(filters)

        metrics = QGridLayout()

        self.production_card = self._metric_card("Παραγωγή", "0 kg")
        self.income_card = self._metric_card("Έσοδα", "0,00 €")
        self.expenses_card = self._metric_card("Έξοδα", "0,00 €")
        self.balance_card = self._metric_card("Καθαρό αποτέλεσμα", "0,00 €")

        metrics.addWidget(self.production_card[0], 0, 0)
        metrics.addWidget(self.income_card[0], 0, 1)
        metrics.addWidget(self.expenses_card[0], 1, 0)
        metrics.addWidget(self.balance_card[0], 1, 1)

        layout.addLayout(metrics)

        charts_box = QGroupBox()
        charts_outer = QVBoxLayout(charts_box)
        charts_title = QLabel("Γραφήματα ανά έτος")
        charts_title.setStyleSheet("font-weight: 700; font-size: 15px; color: #26382f;")
        charts_outer.addWidget(charts_title)
        charts_layout = QHBoxLayout()
        charts_outer.addLayout(charts_layout)

        self.production_chart = BarChartWidget(
            "Παραγωγή ανά έτος",
            "kg",
        )
        self.balance_chart = BarChartWidget(
            "Καθαρό αποτέλεσμα ανά έτος",
            "€",
        )

        charts_layout.addWidget(self.production_chart, 1)
        charts_layout.addWidget(self.balance_chart, 1)
        layout.addWidget(charts_box)

        yearly_box = QGroupBox()
        yearly_layout = QVBoxLayout(yearly_box)
        yearly_title = QLabel("Σύνοψη ανά έτος")
        yearly_title.setStyleSheet("font-weight: 700; font-size: 15px; color: #26382f;")
        yearly_layout.addWidget(yearly_title)
        self.yearly_table = table_widget(
            ["Έτος", "Παραγωγή kg", "Έσοδα", "Έξοδα", "Καθαρό αποτέλεσμα"]
        )
        yearly_layout.addWidget(self.yearly_table)
        layout.addWidget(yearly_box)

        fields_box = QGroupBox()
        fields_layout = QVBoxLayout(fields_box)
        fields_title = QLabel("Παραγωγή ανά αγροτεμάχιο")
        fields_title.setStyleSheet("font-weight: 700; font-size: 15px; color: #26382f;")
        fields_layout.addWidget(fields_title)
        self.fields_table = table_widget(
            [
                "Αγροτεμάχιο",
                "Έκταση στρ.",
                "Παραγωγικά δέντρα",
                "Παραγωγή kg",
                "g / δέντρο",
            ]
        )
        fields_layout.addWidget(self.fields_table)
        layout.addWidget(fields_box)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self._load_years()
        self.refresh()

    def _metric_card(self, caption: str, value: str):
        box = QGroupBox()
        box.setObjectName("metricCard")

        card_layout = QVBoxLayout(box)

        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        card_layout.addWidget(caption_label)
        card_layout.addWidget(value_label)

        return box, value_label

    def _load_years(self) -> None:
        current = self.year.currentData()

        rows = self.db.query(
            """
            SELECT year
            FROM (
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM production
                UNION
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM income
                UNION
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM expenses
            )
            WHERE year IS NOT NULL AND year <> ''
            ORDER BY year DESC
            """
        )

        self.year.blockSignals(True)
        self.year.clear()
        self.year.addItem("Όλα τα έτη", None)

        for row in rows:
            year = str(row["year"])
            self.year.addItem(year, year)

        index = self.year.findData(current)
        if index >= 0:
            self.year.setCurrentIndex(index)

        self.year.blockSignals(False)

    def _total_for(self, table: str, column: str, year: str | None) -> float:
        if year is None:
            row = self.db.query_one(
                f"SELECT COALESCE(SUM({column}), 0) AS total FROM {table}"
            )
        else:
            row = self.db.query_one(
                f"""
                SELECT COALESCE(SUM({column}), 0) AS total
                FROM {table}
                WHERE SUBSTR(entry_date, 1, 4)=?
                """,
                (year,),
            )

        return float(row["total"] or 0)

    def refresh(self) -> None:
        self._load_years()
        selected_year = self.year.currentData()

        production = self._total_for(
            "production", "quantity_kg", selected_year
        )
        income = self._total_for("income", "amount", selected_year)
        expenses = self._total_for("expenses", "amount", selected_year)

        self.production_card[1].setText(format_kg(production))
        self.income_card[1].setText(self._money(income))
        self.expenses_card[1].setText(self._money(expenses))
        self.balance_card[1].setText(self._money(income - expenses))

        yearly_rows = self._yearly_rows()
        self._refresh_charts(yearly_rows)
        self._refresh_yearly_table(yearly_rows)
        self._refresh_fields_table(selected_year)

    @staticmethod
    def _money(value: float) -> str:
        return (
            f"{value:,.2f} €"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )


    @staticmethod
    def _fit_table_height(table, row_count: int, max_visible_rows: int = 8) -> None:
        """Keep table headers and rows fully visible without making the page huge."""
        visible_rows = max(1, min(row_count, max_visible_rows))
        header_height = max(32, table.horizontalHeader().height())
        row_height = max(30, table.verticalHeader().defaultSectionSize())
        table.setMinimumHeight(header_height + visible_rows * row_height + 18)
        table.setMaximumHeight(header_height + visible_rows * row_height + 18)

    def _yearly_rows(self):
        return self.db.query(
            """
            WITH years AS (
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM production
                UNION
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM income
                UNION
                SELECT SUBSTR(entry_date, 1, 4) AS year FROM expenses
            )
            SELECT
                y.year,
                COALESCE((
                    SELECT SUM(p.quantity_kg)
                    FROM production p
                    WHERE SUBSTR(p.entry_date, 1, 4)=y.year
                ), 0) AS production_total,
                COALESCE((
                    SELECT SUM(i.amount)
                    FROM income i
                    WHERE SUBSTR(i.entry_date, 1, 4)=y.year
                ), 0) AS income_total,
                COALESCE((
                    SELECT SUM(e.amount)
                    FROM expenses e
                    WHERE SUBSTR(e.entry_date, 1, 4)=y.year
                ), 0) AS expense_total
            FROM years y
            WHERE y.year IS NOT NULL AND y.year <> ''
            ORDER BY y.year ASC
            """
        )

    def _refresh_charts(self, rows) -> None:
        labels: list[str] = []
        production_values: list[float] = []
        balance_values: list[float] = []

        for row in rows:
            production = float(row["production_total"] or 0)
            income = float(row["income_total"] or 0)
            expenses = float(row["expense_total"] or 0)

            labels.append(str(row["year"]))
            production_values.append(production)
            balance_values.append(income - expenses)

        self.production_chart.set_data(labels, production_values)
        self.balance_chart.set_data(labels, balance_values)

    def _refresh_yearly_table(self, rows) -> None:
        display_rows = list(reversed(rows))
        self.yearly_table.setRowCount(len(display_rows))

        for row_index, row in enumerate(display_rows):
            production = float(row["production_total"] or 0)
            income = float(row["income_total"] or 0)
            expenses = float(row["expense_total"] or 0)

            values = [
                str(row["year"]),
                compact_decimal(production, 3),
                self._money(income),
                self._money(expenses),
                self._money(income - expenses),
            ]

            for column_index, value in enumerate(values):
                self.yearly_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

        self._fit_table_height(self.yearly_table, len(display_rows), 8)


    def _table_rows_as_text(self, table) -> list[list[str]]:
        rows: list[list[str]] = []
        for row_index in range(table.rowCount()):
            values = []
            for column_index in range(table.columnCount()):
                item = table.item(row_index, column_index)
                values.append(item.text() if item is not None else "")
            rows.append(values)
        return rows

    @staticmethod
    def _parse_float(text: str) -> float:
        cleaned = text.replace("€", "").replace("kg", "").replace(" ", "").strip()
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _report_snapshot(self) -> dict:
        selected_year = self.year.currentData()
        year_label = (
            f"Έτος: {selected_year}"
            if selected_year is not None
            else "Όλα τα έτη"
        )

        yearly_rows = []
        for values in self._table_rows_as_text(self.yearly_table):
            yearly_rows.append(
                {
                    "year": values[0] if len(values) > 0 else "",
                    "production": self._parse_float(values[1]) if len(values) > 1 else 0.0,
                    "income": self._parse_float(values[2]) if len(values) > 2 else 0.0,
                    "expenses": self._parse_float(values[3]) if len(values) > 3 else 0.0,
                    "balance": self._parse_float(values[4]) if len(values) > 4 else 0.0,
                }
            )

        field_rows = []
        for values in self._table_rows_as_text(self.fields_table):
            field_rows.append(
                {
                    "name": values[0] if len(values) > 0 else "",
                    "area": self._parse_float(values[1]) if len(values) > 1 else 0.0,
                    "trees": int(self._parse_float(values[2])) if len(values) > 2 else 0,
                    "production": self._parse_float(values[3]) if len(values) > 3 else 0.0,
                    "grams_per_tree": self._parse_float(values[4]) if len(values) > 4 else 0.0,
                }
            )

        return {
            "year_label": year_label,
            "production": self._parse_float(self.production_card[1].text()),
            "income": self._parse_float(self.income_card[1].text()),
            "expenses": self._parse_float(self.expenses_card[1].text()),
            "balance": self._parse_float(self.balance_card[1].text()),
            "yearly_rows": yearly_rows,
            "field_rows": field_rows,
            "font": self.font(),
        }

    def export_pdf(self) -> None:
        year = self.year.currentData()
        suffix = str(year) if year is not None else "ola_ta_eti"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Εξαγωγή αναφοράς σε PDF",
            f"mastixa_report_{suffix}.pdf",
            "PDF (*.pdf)",
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"

        try:
            export_report_pdf(path, self._report_snapshot())
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Αποτυχία εξαγωγής PDF",
                f"Η εξαγωγή απέτυχε.\n\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Εξαγωγή PDF",
            f"Το PDF δημιουργήθηκε:\n{path}",
        )

    def export_excel(self) -> None:
        year = self.year.currentData()
        suffix = str(year) if year is not None else "ola_ta_eti"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Εξαγωγή αναφοράς σε Excel",
            f"mastixa_report_{suffix}.xlsx",
            "Excel (*.xlsx)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"

        try:
            export_report_xlsx(path, self._report_snapshot())
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Αποτυχία εξαγωγής Excel",
                f"Η εξαγωγή απέτυχε.\n\n{exc}",
            )
            return

        QMessageBox.information(
            self,
            "Εξαγωγή Excel",
            f"Το Excel δημιουργήθηκε:\n{path}",
        )

    def _refresh_fields_table(self, year: str | None) -> None:
        if year is None:
            rows = self.db.query(
                """
                SELECT
                    f.id,
                    f.name,
                    f.area_stremma,
                    f.productive_trees,
                    COALESCE(SUM(p.quantity_kg), 0) AS production_total
                FROM fields f
                LEFT JOIN production p ON p.field_id = f.id
                GROUP BY
                    f.id,
                    f.name,
                    f.area_stremma,
                    f.productive_trees
                ORDER BY f.name, f.id
                """
            )
        else:
            rows = self.db.query(
                """
                SELECT
                    f.id,
                    f.name,
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
                    f.area_stremma,
                    f.productive_trees
                ORDER BY f.name, f.id
                """,
                (year,),
            )

        self.fields_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            area = float(row["area_stremma"] or 0)
            trees = int(row["productive_trees"] or 0)
            production = float(row["production_total"] or 0)

            grams_per_tree = (
                production * 1000.0 / trees
                if trees > 0
                else 0.0
            )

            values = [
                row["name"] or "",
                compact_decimal(area, 3),
                str(trees),
                compact_decimal(production, 3),
                f"{grams_per_tree:.1f}",
            ]

            for column_index, value in enumerate(values):
                self.fields_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(value),
                )

        self._fit_table_height(self.fields_table, len(rows), 10)
