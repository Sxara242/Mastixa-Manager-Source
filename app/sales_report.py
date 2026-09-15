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
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .language import tr
from .ui_helpers import compact_decimal, format_kg, table_widget


class SalesReportPage(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("salesReportContent")
        content.setStyleSheet(
            "QWidget#salesReportContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Αναφορά Πωλήσεων & Stock")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Συγκεντρωτικά στοιχεία πωλήσεων, μέσης τιμής, εσόδων και διαθέσιμης παραγωγής"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.year_filter = QComboBox()
        self.year_filter.currentIndexChanged.connect(self.refresh)

        self.buyer_filter = QComboBox()
        self.buyer_filter.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Αναζήτηση αγοραστή ή σημειώσεων...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        self.export_button = QPushButton("Εξαγωγή CSV")
        self.export_button.clicked.connect(self.export_csv)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Αγοραστής"))
        filters.addWidget(self.buyer_filter)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.export_button)

        layout.addWidget(filters_box)

        metrics_box = QGroupBox()
        metrics = QGridLayout(metrics_box)

        self.production_metric = self._metric("Συνολική παραγωγή")
        self.sold_metric = self._metric("Πωλημένα")
        self.stock_metric = self._metric("Διαθέσιμο stock")
        self.revenue_metric = self._metric("Έσοδα πωλήσεων")
        self.avg_price_metric = self._metric("Μέση τιμή / kg")
        self.sales_count_metric = self._metric("Αριθμός πωλήσεων")

        cards = (
            self.production_metric,
            self.sold_metric,
            self.stock_metric,
            self.revenue_metric,
            self.avg_price_metric,
            self.sales_count_metric,
        )

        for i, (card, _value) in enumerate(cards):
            card.setMinimumHeight(105)
            metrics.addWidget(card, i // 3, i % 3)

        layout.addWidget(metrics_box)

        buyer_box = QGroupBox("Ανάλυση ανά αγοραστή")
        buyer_layout = QVBoxLayout(buyer_box)
        self.buyer_table = table_widget(
            ["Αγοραστής", "Πωλήσεις", "Ποσότητα kg", "Έσοδα", "Μέση τιμή / kg"]
        )
        self.buyer_table.setMinimumHeight(260)
        buyer_layout.addWidget(self.buyer_table)
        layout.addWidget(buyer_box)

        detail_box = QGroupBox("Αναλυτικές πωλήσεις")
        detail_layout = QVBoxLayout(detail_box)
        self.detail_table = table_widget(
            [
                "Ημερομηνία", "Αγοραστής", "Ποσότητα kg",
                "Τιμή / kg", "Σύνολο", "Πληρωμή", "Σημειώσεις",
            ]
        )
        self.detail_table.setMinimumHeight(320)
        detail_layout.addWidget(self.detail_table)
        layout.addWidget(detail_box)

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
        text = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{text} €"

    def _table_exists(self, name: str) -> bool:
        return self.db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ) is not None

    def _refresh_filters(self) -> None:
        year = self.year_filter.currentData()
        buyer = self.buyer_filter.currentData()

        self.year_filter.blockSignals(True)
        self.year_filter.clear()
        self.year_filter.addItem("Όλα τα έτη", None)

        if self._table_exists("production_sales"):
            for row in self.db.query(
                """
                SELECT DISTINCT SUBSTR(sale_date,1,4) AS year
                FROM production_sales
                WHERE sale_date IS NOT NULL AND sale_date<>''
                ORDER BY year DESC
                """
            ):
                if row["year"]:
                    self.year_filter.addItem(row["year"], row["year"])

        idx = self.year_filter.findData(year)
        self.year_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.year_filter.blockSignals(False)

        self.buyer_filter.blockSignals(True)
        self.buyer_filter.clear()
        self.buyer_filter.addItem("Όλοι οι αγοραστές", None)

        if self._table_exists("business_partners"):
            for row in self.db.query(
                """
                SELECT id,name
                FROM business_partners
                WHERE partner_type IN ('buyer','both')
                ORDER BY name,id
                """
            ):
                self.buyer_filter.addItem(row["name"], int(row["id"]))

        idx = self.buyer_filter.findData(buyer)
        self.buyer_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.buyer_filter.blockSignals(False)

    def _sales_rows(self):
        if not self._table_exists("production_sales"):
            return []

        where = ["1=1"]
        params = []

        year = self.year_filter.currentData()
        buyer_id = self.buyer_filter.currentData()
        search = self.search.text().strip()

        if year:
            where.append("SUBSTR(sale_date,1,4)=?")
            params.append(year)

        if buyer_id is not None:
            where.append("buyer_id=?")
            params.append(buyer_id)

        if search:
            token = f"%{search}%"
            where.append("(COALESCE(buyer_name,'') LIKE ? OR COALESCE(notes,'') LIKE ?)")
            params.extend([token, token])

        return self.db.query(
            f"""
            SELECT *
            FROM production_sales
            WHERE {' AND '.join(where)}
            ORDER BY sale_date DESC,id DESC
            """,
            params,
        )

    def refresh(self, *_args) -> None:
        self._refresh_filters()
        rows = self._sales_rows()

        qty = sum(float(r["quantity_kg"] or 0) for r in rows)
        revenue = sum(float(r["total_amount"] or 0) for r in rows)
        avg = revenue / qty if qty > 0 else 0.0

        production = 0.0
        production_all = 0.0
        if self._table_exists("production"):
            year = self.year_filter.currentData()
            if year:
                row = self.db.query_one(
                    """SELECT COALESCE(SUM(quantity_kg),0) AS total
                       FROM production
                       WHERE SUBSTR(entry_date,1,4)=?""",
                    (year,),
                )
            else:
                row = self.db.query_one(
                    "SELECT COALESCE(SUM(quantity_kg),0) AS total FROM production"
                )
            production = float(row["total"] or 0) if row else 0.0

            row = self.db.query_one(
                "SELECT COALESCE(SUM(quantity_kg),0) AS total FROM production"
            )
            production_all = float(row["total"] or 0) if row else 0.0

        sold_all = 0.0
        if self._table_exists("production_sales"):
            row = self.db.query_one(
                "SELECT COALESCE(SUM(quantity_kg),0) AS total FROM production_sales"
            )
            sold_all = float(row["total"] or 0) if row else 0.0

        stock = max(production_all - sold_all, 0.0)

        self.production_metric[1].setText(format_kg(production))
        self.sold_metric[1].setText(format_kg(qty))
        self.stock_metric[1].setText(format_kg(stock))
        self.revenue_metric[1].setText(self._money(revenue))
        self.avg_price_metric[1].setText(f"{compact_decimal(avg, 2)} €/kg")
        self.sales_count_metric[1].setText(str(len(rows)))

        grouped = {}
        for row in rows:
            buyer = row["buyer_name"] or "Χωρίς όνομα"
            bucket = grouped.setdefault(buyer, [0, 0.0, 0.0])
            bucket[0] += 1
            bucket[1] += float(row["quantity_kg"] or 0)
            bucket[2] += float(row["total_amount"] or 0)

        buyer_rows = sorted(
            grouped.items(),
            key=lambda x: (-x[1][2], x[0]),
        )

        self.buyer_table.setRowCount(len(buyer_rows))
        for r, (buyer, values) in enumerate(buyer_rows):
            count, bqty, brevenue = values
            bavg = brevenue / bqty if bqty > 0 else 0.0
            display = [
                buyer,
                count,
                compact_decimal(bqty, 3),
                self._money(brevenue),
                f"{compact_decimal(bavg, 2)} €/kg",
            ]
            for c, value in enumerate(display):
                self.buyer_table.setItem(r, c, QTableWidgetItem(str(value)))

        self.detail_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            display = [
                row["sale_date"] or "",
                row["buyer_name"] or "",
                compact_decimal(row["quantity_kg"], 3),
                f"{compact_decimal(row['price_per_kg'], 2)} €/kg",
                self._money(float(row["total_amount"] or 0)),
                row["payment_method"] or "",
                row["notes"] or "",
            ]
            for c, value in enumerate(display):
                item = QTableWidgetItem(str(value))
                if c == 6:
                    item.setToolTip(str(value))
                self.detail_table.setItem(r, c, item)

    def export_csv(self) -> None:
        rows = self._sales_rows()
        if not rows:
            QMessageBox.information(
                self,
                "Εξαγωγή CSV",
                "Δεν υπάρχουν πωλήσεις με τα τρέχοντα φίλτρα.",
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Αποθήκευση Αναφοράς Πωλήσεων",
            "sales_report.csv",
            "CSV (*.csv)",
        )
        if not filename:
            return

        path = Path(filename)
        if path.suffix.lower() != ".csv":
            path = path.with_suffix(".csv")

        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow(
                [tr(value) for value in [
                    "Ημερομηνία", "Αγοραστής", "Ποσότητα kg",
                    "Τιμή / kg", "Σύνολο", "Πληρωμή", "Σημειώσεις",
                ]]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["sale_date"] or "",
                        row["buyer_name"] or "",
                        compact_decimal(row["quantity_kg"], 3),
                        compact_decimal(row["price_per_kg"], 2),
                        compact_decimal(row["total_amount"], 2),
                        row["payment_method"] or "",
                        row["notes"] or "",
                    ]
                )

        QMessageBox.information(
            self,
            "Εξαγωγή CSV",
            f"Η αναφορά αποθηκεύτηκε:\n{path}",
        )