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
from .ui_helpers import compact_decimal, table_widget


class InventoryReportPage(QWidget):
    """Αναφορά αποθέματος και εκτιμώμενης αξίας με weighted-average purchase cost."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
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
        content.setObjectName("inventoryReportContent")
        content.setStyleSheet(
            "QWidget#inventoryReportContent { background: #f5f6f3; }"
        )

        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Αναφορά Αποθήκης & Αξίας Stock")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Τρέχον απόθεμα, αγορές, καταναλώσεις, μέση τιμή αγοράς και "
            "εκτιμώμενη αξία stock ανά είδος"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.category_filter = QComboBox()
        self.category_filter.currentIndexChanged.connect(self.refresh)

        self.stock_filter = QComboBox()
        self.stock_filter.addItem("Όλα", "all")
        self.stock_filter.addItem("Με απόθεμα", "positive")
        self.stock_filter.addItem("Χαμηλό / εξαντλημένο", "low")
        self.stock_filter.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση είδους, κατηγορίας ή μονάδας..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        self.export_button = QPushButton("Εξαγωγή CSV")
        self.export_button.clicked.connect(self.export_csv)

        filters.addWidget(QLabel("Κατηγορία"))
        filters.addWidget(self.category_filter)
        filters.addWidget(QLabel("Stock"))
        filters.addWidget(self.stock_filter)
        filters.addWidget(self.search, 1)
        filters.addWidget(self.export_button)

        layout.addWidget(filters_box)

        metrics_box = QGroupBox()
        metrics = QGridLayout(metrics_box)

        self.items_metric = self._metric("Είδη")
        self.stock_items_metric = self._metric("Είδη με stock")
        self.low_metric = self._metric("Χαμηλά / εξαντλημένα")
        self.purchase_metric = self._metric("Αξία παραλαβών")
        self.stock_value_metric = self._metric("Εκτιμώμενη αξία stock")
        self.consumed_metric = self._metric("Καταναλώσεις")

        cards = (
            self.items_metric,
            self.stock_items_metric,
            self.low_metric,
            self.purchase_metric,
            self.stock_value_metric,
            self.consumed_metric,
        )

        for i, (card, _value) in enumerate(cards):
            card.setMinimumHeight(105)
            metrics.addWidget(card, i // 3, i % 3)

        for c in range(3):
            metrics.setColumnStretch(c, 1)

        layout.addWidget(metrics_box)

        table_box = QGroupBox("Ανάλυση ανά είδος")
        table_layout = QVBoxLayout(table_box)

        self.table = table_widget(
            [
                "Είδος",
                "Κατηγορία",
                "Μονάδα",
                "Τρέχον stock",
                "Ελάχιστο",
                "Παραλαβές",
                "Καταναλώσεις",
                "Μέση τιμή αγοράς",
                "Αξία stock",
                "Κατάσταση",
            ]
        )
        self.table.setMinimumHeight(420)
        self.table.setWordWrap(True)
        table_layout.addWidget(self.table)

        layout.addWidget(table_box)

        note = QLabel(
            "Η «Μέση τιμή αγοράς» υπολογίζεται σταθμισμένα από τις Παραλαβές "
            "που έχουν καταχωρημένη τιμή μονάδας. Η «Αξία stock» είναι "
            "Τρέχον stock × Μέση τιμή αγοράς και αποτελεί εκτίμηση."
        )
        note.setWordWrap(True)
        note.setObjectName("pageSubtitle")
        layout.addWidget(note)

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

    def _movement_columns(self) -> set[str]:
        if not self._table_exists("inventory_movements"):
            return set()

        return {
            row["name"]
            for row in self.db.query(
                "PRAGMA table_info(inventory_movements)"
            )
        }

    def _refresh_categories(self) -> None:
        current = self.category_filter.currentData()

        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("Όλες", None)

        if self._table_exists("inventory_items"):
            rows = self.db.query(
                """
                SELECT DISTINCT category
                FROM inventory_items
                WHERE TRIM(COALESCE(category,'')) <> ''
                ORDER BY category
                """
            )
            for row in rows:
                self.category_filter.addItem(
                    row["category"],
                    row["category"],
                )

        idx = self.category_filter.findData(current)
        self.category_filter.setCurrentIndex(
            idx if idx >= 0 else 0
        )
        self.category_filter.blockSignals(False)

    def _load_rows(self) -> list[dict[str, object]]:
        if not (
            self._table_exists("inventory_items")
            and self._table_exists("inventory_movements")
        ):
            return []

        columns = self._movement_columns()
        has_cost = {
            "unit_price",
            "total_cost",
        }.issubset(columns)

        cost_sql = (
            """
            COALESCE(SUM(
                CASE
                    WHEN m.movement_type='Παραλαβή'
                    THEN COALESCE(m.total_cost,0)
                    ELSE 0
                END
            ),0) AS purchase_value,
            COALESCE(SUM(
                CASE
                    WHEN m.movement_type='Παραλαβή'
                         AND COALESCE(m.unit_price,0) > 0
                    THEN m.quantity
                    ELSE 0
                END
            ),0) AS priced_receipt_qty
            """
            if has_cost
            else
            """
            0 AS purchase_value,
            0 AS priced_receipt_qty
            """
        )

        rows = self.db.query(
            f"""
            SELECT
                i.id,
                i.name,
                i.category,
                i.unit,
                i.minimum_stock,
                COALESCE(SUM(
                    CASE
                        WHEN m.movement_type IN ('Παραλαβή','Διόρθωση +')
                        THEN m.quantity
                        WHEN m.movement_type IN ('Κατανάλωση','Διόρθωση -')
                        THEN -m.quantity
                        ELSE 0
                    END
                ),0) AS current_stock,
                COALESCE(SUM(
                    CASE
                        WHEN m.movement_type='Παραλαβή'
                        THEN m.quantity
                        ELSE 0
                    END
                ),0) AS receipt_qty,
                COALESCE(SUM(
                    CASE
                        WHEN m.movement_type='Κατανάλωση'
                        THEN m.quantity
                        ELSE 0
                    END
                ),0) AS consumed_qty,
                {cost_sql}
            FROM inventory_items i
            LEFT JOIN inventory_movements m
                ON m.item_id=i.id
            GROUP BY i.id
            ORDER BY i.name,i.id
            """
        )

        result: list[dict[str, object]] = []

        for row in rows:
            stock = float(row["current_stock"] or 0)
            minimum = float(row["minimum_stock"] or 0)
            receipt_qty = float(row["receipt_qty"] or 0)
            consumed = float(row["consumed_qty"] or 0)
            purchase_value = float(row["purchase_value"] or 0)
            priced_qty = float(row["priced_receipt_qty"] or 0)

            avg_price = (
                purchase_value / priced_qty
                if priced_qty > 0
                else 0.0
            )
            stock_value = max(stock, 0.0) * avg_price

            if stock <= 0:
                status = "Εξαντλημένο"
            elif minimum > 0 and stock <= minimum:
                status = "Χαμηλό"
            else:
                status = "OK"

            result.append(
                {
                    "id": int(row["id"]),
                    "name": row["name"] or "",
                    "category": row["category"] or "",
                    "unit": row["unit"] or "",
                    "minimum": minimum,
                    "stock": stock,
                    "receipt_qty": receipt_qty,
                    "consumed_qty": consumed,
                    "purchase_value": purchase_value,
                    "avg_price": avg_price,
                    "stock_value": stock_value,
                    "status": status,
                }
            )

        return result

    def refresh(self, *_args) -> None:
        self._refresh_categories()

        category = self.category_filter.currentData()
        stock_mode = self.stock_filter.currentData()
        search = self.search.text().strip().casefold()

        rows = self._load_rows()
        visible = []

        for row in rows:
            haystack = (
                f"{row['name']} {row['category']} {row['unit']}"
            ).casefold()

            if search and search not in haystack:
                continue

            if category and row["category"] != category:
                continue

            if stock_mode == "positive" and float(row["stock"]) <= 0:
                continue

            if (
                stock_mode == "low"
                and row["status"] == "OK"
            ):
                continue

            visible.append(row)

        self._rows_cache = visible

        self.items_metric[1].setText(str(len(rows)))
        self.stock_items_metric[1].setText(
            str(
                sum(
                    1
                    for row in rows
                    if float(row["stock"]) > 0
                )
            )
        )
        self.low_metric[1].setText(
            str(
                sum(
                    1
                    for row in rows
                    if row["status"] != "OK"
                )
            )
        )
        self.purchase_metric[1].setText(
            self._money(
                sum(
                    float(row["purchase_value"])
                    for row in rows
                )
            )
        )
        self.stock_value_metric[1].setText(
            self._money(
                sum(
                    float(row["stock_value"])
                    for row in rows
                )
            )
        )

        consumed_total = sum(
            float(row["consumed_qty"])
            for row in rows
        )
        self.consumed_metric[1].setText(
            compact_decimal(consumed_total, 3)
        )

        self.table.setRowCount(len(visible))

        for r, row in enumerate(visible):
            display = [
                row["name"],
                row["category"],
                row["unit"],
                compact_decimal(row["stock"], 3),
                compact_decimal(row["minimum"], 3),
                compact_decimal(row["receipt_qty"], 3),
                compact_decimal(row["consumed_qty"], 3),
                (
                    f"{compact_decimal(row['avg_price'], 2)} €/{row['unit']}"
                    if float(row["avg_price"]) > 0
                    else "—"
                ),
                self._money(float(row["stock_value"])),
                row["status"],
            ]

            for c, value in enumerate(display):
                item = QTableWidgetItem(str(value))
                self.table.setItem(r, c, item)

    def export_csv(self) -> None:
        if not self._rows_cache:
            QMessageBox.information(
                self,
                "Εξαγωγή CSV",
                "Δεν υπάρχουν εγγραφές με τα τρέχοντα φίλτρα.",
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Αποθήκευση Αναφοράς Αποθήκης",
            "inventory_stock_report.csv",
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
                    [tr(value) for value in [
                        "Είδος",
                        "Κατηγορία",
                        "Μονάδα",
                        "Τρέχον stock",
                        "Ελάχιστο",
                        "Παραλαβές",
                        "Καταναλώσεις",
                        "Μέση τιμή αγοράς",
                        "Αξία stock",
                        "Κατάσταση",
                    ]]
                )

                for row in self._rows_cache:
                    writer.writerow(
                        [
                            row["name"],
                            row["category"],
                            row["unit"],
                            compact_decimal(row["stock"], 3),
                            compact_decimal(row["minimum"], 3),
                            compact_decimal(row["receipt_qty"], 3),
                            compact_decimal(row["consumed_qty"], 3),
                            compact_decimal(row["avg_price"], 2),
                            compact_decimal(row["stock_value"], 2),
                            row["status"],
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
