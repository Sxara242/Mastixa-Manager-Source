from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from .date_preferences import format_iso_date

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
from .report_quantities import quantities, quantity_text, stock_quantities, average_price_text, identify_rows, group_quantities, product_rows
from .localized_messages import _message, _text, _language
from .report_quantities import sale_source_quantities, sale_source_fields, matches_sale_source
from .language import tr
from .ui_helpers import compact_decimal, table_widget


class SalesReportPage(YearFilteredPage):
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

        self.product_filter = QComboBox()
        self.product_filter.currentIndexChanged.connect(self.refresh)

        self.source_filter = QComboBox()
        self.source_filter.setProperty("mastixaI18nSkipItems", True)
        self.source_filter.currentIndexChanged.connect(self.refresh)

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
        filters.addWidget(QLabel("Προϊόν"))
        filters.addWidget(self.product_filter)
        filters.addWidget(QLabel("Πηγή παραγωγής"))
        filters.addWidget(self.source_filter)
        filters.addWidget(QLabel("Αγοραστής"))
        filters.addWidget(self.buyer_filter)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.export_button)

        layout.addWidget(filters_box)
        self.source_note = QLabel()
        self.source_note.setWordWrap(True)
        self.source_note.setProperty("mastixaI18nSkipText", True)
        self.source_note.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.source_note)

        metrics_box = QGroupBox()
        metrics = QGridLayout(metrics_box)

        self.production_metric = self._metric("Συνολική παραγωγή")
        self.sold_metric = self._metric("Πωλημένα")
        self.stock_metric = self._metric("Διαθέσιμο stock")
        self.revenue_metric = self._metric("Έσοδα πωλήσεων")
        self.avg_price_metric = self._metric("Μέση τιμή / μονάδα")
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
            ["Αγοραστής", "Πωλήσεις", "Ποσότητα", "Έσοδα", "Μέση τιμή / μονάδα"]
        )
        self.buyer_table.setMinimumHeight(260)
        buyer_layout.addWidget(self.buyer_table)
        layout.addWidget(buyer_box)

        detail_box = QGroupBox("Αναλυτικές πωλήσεις")
        detail_layout = QVBoxLayout(detail_box)
        self.detail_table = table_widget(
            [
                "Ημερομηνία", "Αγοραστής", "Ποσότητα",
                "Τιμή / μονάδα", "Σύνολο", "Πληρωμή", "Σημειώσεις", "Προϊόν", "Μονάδα", "Πηγή παραγωγής",
            ]
        )
        self.detail_table.setMinimumHeight(320)
        detail_layout.addWidget(self.detail_table)
        layout.addWidget(detail_box)

        layout.addStretch()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self.refresh)
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
        product = self.product_filter.currentData()
        self.product_filter.blockSignals(True)
        self.product_filter.clear()
        self.product_filter.addItem("Όλα τα προϊόντα", None)
        for row in product_rows(self.db):
            self.product_filter.addItem(row["name"], int(row["id"]))
        idx = self.product_filter.findData(product)
        self.product_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.product_filter.blockSignals(False)
        source = self.source_filter.currentData()
        self.source_filter.blockSignals(True)
        self.source_filter.clear()
        self.source_filter.addItem(_text("Όλες οι πηγές"), "all")
        self.source_filter.addItem(_text("Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις"), "pooled")
        for field, name in sale_source_fields(self.db, self.product_filter.currentData()):
            self.source_filter.addItem(name, field)
        self.source_filter.setCurrentIndex(max(0,self.source_filter.findData(source)))
        self.source_filter.blockSignals(False)
        buyer = self.buyer_filter.currentData()
        populate_year_filter(self, self.year_filter, strings=True)

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

        rows = self.db.query(
            f"""
            SELECT *
            FROM production_sales
            WHERE {' AND '.join(where)}
            ORDER BY sale_date DESC,id DESC
            """,
            params,
        )

        rows = identify_rows(self.db, rows)
        product = self.product_filter.currentData()
        return [r for r in rows if (product is None or r["product_key"] == ("id", product))
                and matches_sale_source(r, self.source_filter.currentData())]

    def refresh(self, *_args) -> None:
        self._refresh_filters()
        rows = self._sales_rows()

        product = self.product_filter.currentData()
        year = self.year_filter.currentData()
        sold = group_quantities(rows)
        source = self.source_filter.currentData()
        production, _, _ = sale_source_quantities(self.db, product, source=source, year=year)
        _, _, stock = sale_source_quantities(self.db, product, source=source)
        if source == "pooled":
            production, stock = [], []
            note = "Οι πωλήσεις συνολικού αποθέματος δεν έχουν κατανομή σε αγροτεμάχια. Παραγωγή και υπόλοιπο εμφανίζονται στις Όλες τις πηγές."
        elif isinstance(source, int):
            note = "Το υπόλοιπο αγροτεμαχίου αφαιρεί μόνο πωλήσεις από αυτό το αγροτεμάχιο. Οι μη κατανεμημένες πωλήσεις μειώνουν το συνολικό απόθεμα. Το όριο νέας πώλησης είναι το μικρότερο από τα δύο υπόλοιπα."
        else:
            note = "Το συνολικό απόθεμα περιλαμβάνει όλες τις πωλήσεις, κατανεμημένες και μη. Το υπόλοιπο είναι διαχρονικό· το έτος φιλτράρει παραγωγή και πωλήσεις."
        self.source_note.setText(_text(note))
        revenue = sum(float(r["total_amount"] or 0) for r in rows)
        for metric, groups in ((self.production_metric, production), (self.sold_metric, sold), (self.stock_metric, stock)):
            metric[1].setProperty("mastixaI18nSkipText", True)
            metric[1].setTextFormat(Qt.TextFormat.PlainText)
            metric[1].setText(quantity_text(groups))
        self.revenue_metric[1].setText(self._money(revenue))
        self.avg_price_metric[1].setProperty("mastixaI18nSkipText", True)
        self.avg_price_metric[1].setTextFormat(Qt.TextFormat.PlainText)
        self.avg_price_metric[1].setText(average_price_text(sold))
        self.sales_count_metric[1].setText(str(len(rows)))

        grouped = {}
        for row in rows:
            grouped.setdefault(row["buyer_name"] or "—", []).append(row)
        buyer_rows = sorted(grouped.items())
        self.buyer_table.setRowCount(len(buyer_rows))
        for index, (buyer, sales) in enumerate(buyer_rows):
            groups = group_quantities(sales)
            display = [buyer, len(sales), quantity_text(groups),
                       self._money(sum(float(r["total_amount"] or 0) for r in sales)), average_price_text(groups)]
            for column, value in enumerate(display):
                self.buyer_table.setItem(index, column, QTableWidgetItem(str(value)))

        self.detail_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            display = [
                format_iso_date(row["sale_date"], self.db),
                row["buyer_name"] or "",
                compact_decimal(row["quantity_kg"], 3),
                f"{compact_decimal(row['price_per_kg'], 2)} €/{row['unit']}" if row["unit"] else "—",
                self._money(float(row["total_amount"] or 0)),
                row["payment_method"] or "",
                row["notes"] or "",
                row["product_name"], row["unit"] or "[?]",
                row.get("source_field_name", "") if row.get("source_field_id") is not None else _text("Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις"),
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
            _text("Αποθήκευση Αναφοράς Πωλήσεων"),
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
                    "Ημερομηνία", "Αγοραστής", "Ποσότητα",
                    "Τιμή / μονάδα", "Σύνολο", "Πληρωμή", "Σημειώσεις", "Προϊόν", "Μονάδα", "Πηγή παραγωγής",
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
                        row["product_name"], row["unit"] or "[?]",
                        row.get("source_field_name", "") if row.get("source_field_id") is not None else _text("Συνολικό απόθεμα / μη κατανεμημένες πωλήσεις"),
                    ]
                )

        _message(
            self, "information", "Εξαγωγή CSV",
            "Η αναφορά αποθηκεύτηκε:\n{path}", path=path,
        )
