from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .language import combo_source_text, tr
from .product_registry import ensure_product_links
from .ui_helpers import compact_decimal, format_kg, table_widget


class AnnualFarmReportPage(QWidget):
    """
    Ετήσια αναφορά εκμετάλλευσης.

    Σε συγκεκριμένο προϊόν, μόνο Παραγωγή/Πωλήσεις/Stock/Έσοδα πωλήσεων
    θεωρούνται product-specific. Τα υπόλοιπα έσοδα και τα έξοδα εμφανίζονται
    ως μη κατανεμημένα και δεν επιμερίζονται αυθαίρετα.
    """

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        ensure_product_links(self.db)
        self._rows_cache: list[dict[str, object]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("annualFarmReportContent")
        content.setStyleSheet(
            "QWidget#annualFarmReportContent { background: #f5f6f3; }"
        )

        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Ετήσια Αναφορά Εκμετάλλευσης")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Παραγωγή, πωλήσεις, έσοδα, έξοδα και αποτέλεσμα ανά έτος — "
            "με δυνατότητα προβολής ανά προϊόν"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        filters_box = QGroupBox("Επιλογές αναφοράς")
        filters = QHBoxLayout(filters_box)

        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.product_filter = QComboBox()
        self.product_filter.currentIndexChanged.connect(self.refresh)

        self.export_button = QPushButton("Εξαγωγή CSV")
        self.export_button.clicked.connect(self.export_csv)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Προϊόν"))
        filters.addWidget(self.product_filter)
        filters.addStretch()
        filters.addWidget(self.export_button)

        layout.addWidget(filters_box)

        self.scope_note = QLabel()
        self.scope_note.setWordWrap(True)
        self.scope_note.setObjectName("pageSubtitle")
        layout.addWidget(self.scope_note)

        metrics_box = QGroupBox()
        metrics = QGridLayout(metrics_box)
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)

        self.production_metric = self._metric("Παραγωγή")
        self.sold_metric = self._metric("Πωλημένα")
        self.stock_metric = self._metric("Υπόλοιπο stock τέλους έτους")
        self.sales_revenue_metric = self._metric("Έσοδα πωλήσεων")
        self.avg_price_metric = self._metric("Μέση τιμή / kg")
        self.other_income_metric = self._metric("Λοιπά έσοδα")
        self.expenses_metric = self._metric("Έξοδα")
        self.result_metric = self._metric("Καθαρό αποτέλεσμα")

        cards = (
            self.production_metric,
            self.sold_metric,
            self.stock_metric,
            self.sales_revenue_metric,
            self.avg_price_metric,
            self.other_income_metric,
            self.expenses_metric,
            self.result_metric,
        )

        for i, (card, _value) in enumerate(cards):
            card.setMinimumHeight(108)
            metrics.addWidget(card, i // 4, i % 4)

        for col in range(4):
            metrics.setColumnStretch(col, 1)

        layout.addWidget(metrics_box)

        breakdown_box = QGroupBox("Ανάλυση προϊόντων")
        breakdown_layout = QVBoxLayout(breakdown_box)

        self.product_table = table_widget(
            [
                "Προϊόν",
                "Παραγωγή kg",
                "Πωλημένα kg",
                "Έσοδα πωλήσεων",
                "Μέση τιμή / kg",
                "Stock τέλους έτους",
            ]
        )
        self.product_table.setMinimumHeight(260)
        breakdown_layout.addWidget(self.product_table)

        layout.addWidget(breakdown_box)

        finance_box = QGroupBox("Οικονομική εικόνα έτους")
        finance_layout = QVBoxLayout(finance_box)

        self.finance_table = table_widget(
            [
                "Κατηγορία",
                "Ποσό",
                "Χειρισμός στην αναφορά προϊόντος",
            ]
        )
        self.finance_table.setMinimumHeight(220)
        self.finance_table.setWordWrap(True)
        finance_layout.addWidget(self.finance_table)

        layout.addWidget(finance_box)

        layout.addStretch()
        self.refresh()

    @staticmethod
    def _metric(caption: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        inner = QVBoxLayout(box)

        label = QLabel(caption)
        label.setObjectName("metricCaption")

        value = QLabel("0")
        value.setObjectName("metricValue")
        value.setWordWrap(True)

        inner.addWidget(label)
        inner.addWidget(value)
        return box, value

    @staticmethod
    def _money(value: float) -> str:
        text = (
            f"{float(value):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        return f"{text} €"

    def _table_exists(self, name: str) -> bool:
        return self.db.query_one(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (name,),
        ) is not None

    def _refresh_filters(self) -> None:
        current_year = self.year_filter.currentData()
        current_product = self.product_filter.currentData()

        years: set[int] = set()

        if self._table_exists("production"):
            for row in self.db.query(
                """
                SELECT DISTINCT CAST(SUBSTR(entry_date,1,4) AS INTEGER) AS year
                FROM production
                WHERE entry_date IS NOT NULL AND entry_date<>''
                """
            ):
                try:
                    years.add(int(row["year"]))
                except (TypeError, ValueError):
                    pass

        if self._table_exists("production_sales"):
            for row in self.db.query(
                """
                SELECT DISTINCT CAST(SUBSTR(sale_date,1,4) AS INTEGER) AS year
                FROM production_sales
                WHERE sale_date IS NOT NULL AND sale_date<>''
                """
            ):
                try:
                    years.add(int(row["year"]))
                except (TypeError, ValueError):
                    pass

        if self._table_exists("income"):
            for row in self.db.query(
                """
                SELECT DISTINCT CAST(SUBSTR(entry_date,1,4) AS INTEGER) AS year
                FROM income
                WHERE entry_date IS NOT NULL AND entry_date<>''
                """
            ):
                try:
                    years.add(int(row["year"]))
                except (TypeError, ValueError):
                    pass

        if self._table_exists("expenses"):
            for row in self.db.query(
                """
                SELECT DISTINCT CAST(SUBSTR(entry_date,1,4) AS INTEGER) AS year
                FROM expenses
                WHERE entry_date IS NOT NULL AND entry_date<>''
                """
            ):
                try:
                    years.add(int(row["year"]))
                except (TypeError, ValueError):
                    pass

        self.year_filter.blockSignals(True)
        self.year_filter.clear()

        for year in sorted(years, reverse=True):
            self.year_filter.addItem(str(year), year)

        if not years:
            from PySide6.QtCore import QDate
            current = QDate.currentDate().year()
            self.year_filter.addItem(str(current), current)

        idx = self.year_filter.findData(current_year)
        self.year_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.year_filter.blockSignals(False)

        products = self.db.query(
            """SELECT DISTINCT pr.id,pr.name
               FROM products pr JOIN production p ON p.product_id=pr.id
               ORDER BY pr.name,pr.id"""
        ) if self._table_exists("production") else []

        self.product_filter.blockSignals(True)
        self.product_filter.clear()
        self.product_filter.addItem("Όλα τα προϊόντα", None)

        for product in products:
            self.product_filter.addItem(product["name"], int(product["id"]))

        idx = self.product_filter.findData(current_product)
        self.product_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.product_filter.blockSignals(False)

    def _production_for(
        self,
        year: int,
        product: int | None,
        through_year_end: bool = False,
    ) -> float:
        if not self._table_exists("production"):
            return 0.0

        if through_year_end:
            where = ["SUBSTR(entry_date,1,4)<=?"]
        else:
            where = ["SUBSTR(entry_date,1,4)=?"]

        params: list[object] = [str(year)]

        if product:
            where.append("product_id=?")
            params.append(product)

        row = self.db.query_one(
            f"""
            SELECT COALESCE(SUM(quantity_kg),0) AS total
            FROM production
            WHERE {' AND '.join(where)}
            """,
            params,
        )
        return float(row["total"] or 0) if row else 0.0

    def _sales_for(
        self,
        year: int,
        product: int | None,
        through_year_end: bool = False,
    ) -> tuple[float, float]:
        if not self._table_exists("production_sales"):
            return 0.0, 0.0

        if through_year_end:
            where = ["SUBSTR(sale_date,1,4)<=?"]
        else:
            where = ["SUBSTR(sale_date,1,4)=?"]

        params: list[object] = [str(year)]

        if product:
            where.append("product_id=?")
            params.append(product)

        row = self.db.query_one(
            f"""
            SELECT
                COALESCE(SUM(quantity_kg),0) AS qty,
                COALESCE(SUM(total_amount),0) AS revenue
            FROM production_sales
            WHERE {' AND '.join(where)}
            """,
            params,
        )

        if row is None:
            return 0.0, 0.0

        return (
            float(row["qty"] or 0),
            float(row["revenue"] or 0),
        )

    def _finance_for_year(
        self,
        year: int,
    ) -> tuple[float, float, float]:
        total_income = 0.0
        sales_income = 0.0
        expenses = 0.0

        if self._table_exists("income"):
            row = self.db.query_one(
                """
                SELECT COALESCE(SUM(amount),0) AS total
                FROM income
                WHERE SUBSTR(entry_date,1,4)=?
                """,
                (str(year),),
            )
            total_income = (
                float(row["total"] or 0)
                if row
                else 0.0
            )

            if self._table_exists("production_sales"):
                row = self.db.query_one(
                    """
                    SELECT COALESCE(SUM(i.amount),0) AS total
                    FROM production_sales s
                    JOIN income i
                        ON i.id=s.income_id
                    WHERE SUBSTR(s.sale_date,1,4)=?
                    """,
                    (str(year),),
                )
                sales_income = (
                    float(row["total"] or 0)
                    if row
                    else 0.0
                )

        if self._table_exists("expenses"):
            row = self.db.query_one(
                """
                SELECT COALESCE(SUM(amount),0) AS total
                FROM expenses
                WHERE SUBSTR(entry_date,1,4)=?
                """,
                (str(year),),
            )
            expenses = (
                float(row["total"] or 0)
                if row
                else 0.0
            )

        other_income = max(
            total_income - sales_income,
            0.0,
        )
        return total_income, other_income, expenses

    def _product_breakdown(
        self,
        year: int,
    ) -> list[dict[str, object]]:
        if not self._table_exists("production"):
            return []

        products = self.db.query(
            """SELECT DISTINCT pr.id,pr.name
               FROM products pr JOIN production p ON p.product_id=pr.id
               ORDER BY pr.name,pr.id"""
        )

        rows: list[dict[str, object]] = []

        for product_row in products:
            product = int(product_row["id"])
            produced = self._production_for(
                year,
                product,
            )
            sold, revenue = self._sales_for(
                year,
                product,
            )
            produced_to_date = self._production_for(
                year,
                product,
                through_year_end=True,
            )
            sold_to_date, _ = self._sales_for(
                year,
                product,
                through_year_end=True,
            )

            avg = revenue / sold if sold > 0 else 0.0
            stock = max(
                produced_to_date - sold_to_date,
                0.0,
            )

            rows.append(
                {
                    "product": product_row["name"],
                    "product_id": product,
                    "produced": produced,
                    "sold": sold,
                    "revenue": revenue,
                    "avg": avg,
                    "stock": stock,
                }
            )

        return rows

    def refresh(self, *_args) -> None:
        ensure_product_links(self.db)
        self._refresh_filters()

        year = self.year_filter.currentData()
        if year is None:
            return

        year = int(year)
        product = self.product_filter.currentData()
        product_name = combo_source_text(self.product_filter)
        if product:
            product = int(product)

        produced = self._production_for(
            year,
            product,
        )
        sold, sales_revenue = self._sales_for(
            year,
            product,
        )

        produced_to_date = self._production_for(
            year,
            product,
            through_year_end=True,
        )
        sold_to_date, _ = self._sales_for(
            year,
            product,
            through_year_end=True,
        )
        stock = max(
            produced_to_date - sold_to_date,
            0.0,
        )
        avg_price = (
            sales_revenue / sold
            if sold > 0
            else 0.0
        )

        total_income, other_income, expenses = (
            self._finance_for_year(year)
        )

        self.production_metric[1].setText(
            format_kg(produced)
        )
        self.sold_metric[1].setText(
            format_kg(sold)
        )
        self.stock_metric[1].setText(
            format_kg(stock)
        )
        self.sales_revenue_metric[1].setText(
            self._money(sales_revenue)
        )
        self.avg_price_metric[1].setText(
            f"{compact_decimal(avg_price, 2)} €/kg"
        )

        if product is None:
            self.other_income_metric[0].setTitle("")
            self.other_income_metric[1].setText(
                self._money(other_income)
            )
            self.expenses_metric[1].setText(
                self._money(expenses)
            )
            self.result_metric[1].setText(
                self._money(total_income - expenses)
            )
            self.scope_note.setText(
                "Προβολή όλων των προϊόντων: το Καθαρό αποτέλεσμα είναι "
                "Σύνολο εσόδων − Σύνολο εξόδων για ολόκληρη την εκμετάλλευση."
            )
        else:
            self.other_income_metric[1].setText(
                self._money(other_income)
            )
            self.expenses_metric[1].setText(
                self._money(expenses)
            )
            self.result_metric[1].setText("—")
            self.scope_note.setText(
                f"Προβολή προϊόντος «{product_name}»: Παραγωγή, Πωλήσεις, Stock και "
                "Έσοδα πωλήσεων αφορούν μόνο το προϊόν. Τα Λοιπά έσοδα και "
                "Έξοδα εμφανίζονται ως γενικά / μη κατανεμημένα και ΔΕΝ "
                "επιμερίζονται αυθαίρετα στο προϊόν. Για αυτό δεν υπολογίζεται "
                "ψευδές «καθαρό αποτέλεσμα προϊόντος»."
            )

        breakdown = self._product_breakdown(year)

        if product:
            breakdown = [
                row
                for row in breakdown
                if row["product_id"] == product
            ]

        self._rows_cache = breakdown
        self.product_table.setRowCount(len(breakdown))

        for r, row in enumerate(breakdown):
            display = [
                row["product"],
                compact_decimal(row["produced"], 3),
                compact_decimal(row["sold"], 3),
                self._money(float(row["revenue"])),
                f"{compact_decimal(row['avg'], 2)} €/kg",
                compact_decimal(row["stock"], 3),
            ]

            for c, value in enumerate(display):
                self.product_table.setItem(
                    r,
                    c,
                    QTableWidgetItem(str(value)),
                )

        finance_rows = [
            (
                "Έσοδα πωλήσεων",
                sales_revenue,
                (
                    "Περιλαμβάνονται στο προϊόν"
                    if product
                    else "Περιλαμβάνονται στο αποτέλεσμα"
                ),
            ),
            (
                "Λοιπά έσοδα",
                other_income,
                (
                    "Μη κατανεμημένα — δεν αποδίδονται στο προϊόν"
                    if product
                    else "Περιλαμβάνονται στο αποτέλεσμα"
                ),
            ),
            (
                "Έξοδα",
                expenses,
                (
                    "Μη κατανεμημένα — δεν αφαιρούνται από προϊόν"
                    if product
                    else "Περιλαμβάνονται στο αποτέλεσμα"
                ),
            ),
        ]

        self.finance_table.setRowCount(len(finance_rows))

        for r, (category, amount, handling) in enumerate(
            finance_rows
        ):
            values = [
                category,
                self._money(amount),
                handling,
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if c == 2:
                    item.setToolTip(str(value))
                self.finance_table.setItem(
                    r,
                    c,
                    item,
                )

    def export_csv(self) -> None:
        year = self.year_filter.currentData()
        if year is None:
            return

        product = self.product_filter.currentData()
        product_label = (
            combo_source_text(self.product_filter)
            if product
            else "Όλα τα προϊόντα"
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Αποθήκευση Ετήσιας Αναφοράς",
            f"annual_report_{year}.csv",
            "CSV (*.csv)",
        )
        if not filename:
            return

        path = Path(filename)
        if path.suffix.lower() != ".csv":
            path = path.with_suffix(".csv")

        try:
            with path.open(
                "w",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                writer = csv.writer(
                    handle,
                    delimiter=";",
                )
                writer.writerow(
                    [tr("Ετήσια Αναφορά Εκμετάλλευσης")]
                )
                writer.writerow([tr("Έτος"), year])
                writer.writerow(
                    [tr("Προϊόν"), product_label]
                )
                writer.writerow([])
                writer.writerow(
                    [tr(value) for value in [
                        "Προϊόν",
                        "Παραγωγή kg",
                        "Πωλημένα kg",
                        "Έσοδα πωλήσεων",
                        "Μέση τιμή / kg",
                        "Stock τέλους έτους",
                    ]]
                )

                for row in self._rows_cache:
                    writer.writerow(
                        [
                            row["product"],
                            compact_decimal(
                                row["produced"],
                                3,
                            ),
                            compact_decimal(
                                row["sold"],
                                3,
                            ),
                            compact_decimal(
                                row["revenue"],
                                2,
                            ),
                            compact_decimal(
                                row["avg"],
                                2,
                            ),
                            compact_decimal(
                                row["stock"],
                                3,
                            ),
                        ]
                    )

            QMessageBox.information(
                self,
                "Εξαγωγή CSV",
                f"Η αναφορά αποθηκεύτηκε:\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Σφάλμα εξαγωγής",
                str(exc),
            )
