from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QMenu,
    QPushButton,
    QScrollArea,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .report_quantities import quantities, quantity_text, stock_quantities, average_price_text, product_rows
from .language import combo_source_text, tr
from .localized_messages import _language, _text, _message
from .ui_helpers import compact_decimal, table_widget
from .annual_report_exports import (
    AnnualProduct, AnnualSnapshot, export_annual_csv, export_annual_pdf,
    export_annual_xlsx, scope_note,
)


class AnnualFarmReportPage(YearFilteredPage):
    """
    Ετήσια αναφορά εκμετάλλευσης.

    Σε συγκεκριμένο προϊόν, μόνο Παραγωγή/Πωλήσεις/Stock/Έσοδα πωλήσεων
    θεωρούνται product-specific. Τα υπόλοιπα έσοδα και τα έξοδα εμφανίζονται
    ως μη κατανεμημένα και δεν επιμερίζονται αυθαίρετα.
    """

    def __init__(self, db: Database, *, staged=False, parent=None) -> None:
        super().__init__(parent)
        self._finance_ready = False
        self.db = db
        self._rows_cache: list[dict[str, object]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
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

        self.export_button = QToolButton()
        # Windows' split-button style derives a point-sized menu font. The
        # application uses pixels, whose QFont.pointSize() is -1; provide a
        # valid equivalent point size at this native control's font source.
        self.export_button.setStyleSheet(f"font-size: {14 * 72 / self.logicalDpiY():g}pt;")
        self.export_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        menu = QMenu(self.export_button)
        self.export_actions = {}
        for kind, callback in (("pdf", self.export_pdf), ("xlsx", self.export_xlsx), ("csv", self.export_csv)):
            action = QAction(self.export_button)
            action.triggered.connect(callback)
            menu.addAction(action)
            self.export_actions[kind] = action
        self.export_button.setMenu(menu)
        self.export_button.setDefaultAction(self.export_actions["pdf"])

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year_filter)
        filters.addWidget(QLabel("Προϊόν"))
        filters.addWidget(self.product_filter)
        filters.addStretch()
        filters.addWidget(self.export_button)

        layout.addWidget(filters_box)

        self.scope_note = QLabel()
        self.scope_note.setProperty("mastixaI18nSkipText", True)
        self.scope_note.setTextFormat(Qt.TextFormat.PlainText)
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
        self.avg_price_metric = self._metric("Μέση τιμή / μονάδα")
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

        self._finance_section = QWidget(content)
        self._finance_section.setMinimumHeight(620)
        self._finance_layout = QVBoxLayout(self._finance_section)
        self._finance_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._finance_section)
        if staged and parent is not None and parent.isVisible() and parent.window().height() < 800:
            from .staged_construction import AfterFirstPaint
            self._secondary_construction = AfterFirstPaint(self, self._finish_finance_section, viewport_limit=610)
            scroll.verticalScrollBar().valueChanged.connect(self._secondary_construction.finish)
        else:
            self._build_finance_section()

        layout.addStretch()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self.refresh)
        self.refresh()

    def _finish_finance_section(self):
        self._finance_section.hide()
        self._build_finance_section()
        # Reuse the same navigation invalidation token as the owning window.
        # Filter/language changes already refresh the snapshot synchronously;
        # an independent write or year/context change requires a fresh read.
        token = getattr(self.window(), "_presentation_token", None)
        if callable(token) and token() == self._snapshot_token:
            self._populate_product()
            self._populate_finance()
        else:
            self.refresh()
        from .staged_construction import prepare_subtree
        prepare_subtree(self, self._finance_section)
        self._finance_section.show()

    def _build_finance_section(self):
        layout = self._finance_layout
        breakdown_box = QGroupBox("Ανάλυση προϊόντων")
        breakdown_layout = QVBoxLayout(breakdown_box)

        self.product_table = table_widget(
            [
                "Προϊόν",
                "Παραγωγή",
                "Πωλημένα",
                "Έσοδα πωλήσεων",
                "Μέση τιμή / μονάδα",
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

        self._finance_ready = True
        self._finance_section.setMinimumHeight(0)

    @staticmethod
    def _metric(caption: str):
        box = QGroupBox()
        box.setObjectName("metricCard")
        inner = QVBoxLayout(box)

        label = QLabel(caption)
        label.setObjectName("metricCaption")
        label.setWordWrap(True)

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
        current_product = self.product_filter.currentData()
        populate_year_filter(self, self.year_filter, all_years=False)

        products = product_rows(self.db)

        self.product_filter.blockSignals(True)
        self.product_filter.clear()
        self.product_filter.addItem("Όλα τα προϊόντα", None)

        for product in products:
            self.product_filter.addItem(product["name"], int(product["id"]))

        idx = self.product_filter.findData(current_product)
        self.product_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.product_filter.blockSignals(False)

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

    def _product_breakdown(self, year):
        produced = quantities(self.db, year=year)
        sales = quantities(self.db, "production_sales", year)
        stock = stock_quantities(quantities(self.db, year=year, through=True),
                                 quantities(self.db, "production_sales", year, through=True))
        products = {g["key"]: g for g in produced + sales + stock}
        for product in product_rows(self.db):
            key = ("id", product["id"])
            products.setdefault(key, dict(key=key, product=product["name"], unit=product["unit"]))
        production_map = {g["key"]: g["quantity"] for g in produced}
        sales_map = {g["key"]: g for g in sales}
        stock_map = {g["key"]: g["quantity"] for g in stock}
        rows = []
        for key, group in products.items():
            sale = sales_map.get(key, {})
            sold, revenue = sale.get("quantity", 0.0), sale.get("revenue", 0.0)
            rows.append(dict(product=group["product"], product_id=key[1] if key[0] == "id" else None,
                unit=group["unit"], key=key, produced=production_map.get(key, 0.0), sold=sold,
                revenue=revenue, avg=revenue/sold if sold > 0 else 0.0, stock=stock_map.get(key,0.0)))
        return sorted(rows, key=lambda row: (row["product"], str(row["key"])))

    def refresh(self, *_args) -> None:
        for kind, action in self.export_actions.items():
            action.setText(_text("Εξαγωγή " + kind.upper()))
        self._refresh_filters()

        year = self.year_filter.currentData()
        if year is None:
            return

        year = int(year)
        product = self.product_filter.currentData()
        product_name = combo_source_text(self.product_filter)
        if product:
            product = int(product)

        breakdown = self._product_breakdown(year)
        if product is not None:
            breakdown = [r for r in breakdown if r["product_id"] == product]
        def groups(column):
            return [dict(key=r["key"], product=r["product"], unit=r["unit"],
                         quantity=r[column], revenue=r["revenue"]) for r in breakdown]
        sales_revenue = sum(r["revenue"] for r in breakdown)
        total_income, other_income, expenses = (
            self._finance_for_year(year)
        )
        self._export_snapshot = AnnualSnapshot(
            year, product, product_name, tuple(AnnualProduct(**row) for row in breakdown),
            total_income, other_income, expenses,
        )

        for metric, column in ((self.production_metric,"produced"), (self.sold_metric,"sold"), (self.stock_metric,"stock")):
            metric[1].setProperty("mastixaI18nSkipText", True)
            metric[1].setTextFormat(Qt.TextFormat.PlainText)
            metric[1].setWordWrap(True)
            metric[1].setText(quantity_text(groups(column)))
        self.sales_revenue_metric[1].setText(self._money(sales_revenue))
        self.avg_price_metric[1].setProperty("mastixaI18nSkipText", True)
        self.avg_price_metric[1].setTextFormat(Qt.TextFormat.PlainText)
        self.avg_price_metric[1].setText(average_price_text(groups("sold")))

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
        else:
            self.other_income_metric[1].setText(
                self._money(other_income)
            )
            self.expenses_metric[1].setText(
                self._money(expenses)
            )
            self.result_metric[1].setText("—")
        self.scope_note.setText(scope_note(self._export_snapshot))

        self._rows_cache = breakdown
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

        self._finance_rows = finance_rows
        if self._finance_ready:
            self._populate_product()
            self._populate_finance()
        token = getattr(self.window(), "_presentation_token", None)
        self._snapshot_token = token() if callable(token) else None

    def _populate_product(self):
        breakdown = self._rows_cache
        self.product_table.setRowCount(len(breakdown))

        for r, row in enumerate(breakdown):
            display = [
                row["product"],
                f"{compact_decimal(row['produced'], 3)} {row['unit'] or '[?]'}",
                f"{compact_decimal(row['sold'], 3)} {row['unit'] or '[?]'}",
                self._money(float(row["revenue"])),
                f"{compact_decimal(row['avg'], 2)} €/{row['unit']}" if row["unit"] and row['sold'] > 0 else "—",
                f"{compact_decimal(row['stock'], 3)} {row['unit'] or '[?]'}",
            ]

            for c, value in enumerate(display):
                self.product_table.setItem(
                    r,
                    c,
                    QTableWidgetItem(str(value)),
                )

    def _populate_finance(self):
        finance_rows = self._finance_rows
        self.finance_table.setRowCount(len(finance_rows))

        for r, (category, amount, handling) in enumerate(
            finance_rows
        ):
            values = [
                tr(category),
                self._money(amount),
                tr(handling),
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

    def _annual_report_snapshot(self) -> AnnualSnapshot:
        return self._export_snapshot

    def _export(self, kind: str) -> None:
        snapshot = self._annual_report_snapshot()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            _text("Αποθήκευση Ετήσιας Αναφοράς"),
            f"annual_report_{snapshot.year}.{kind}",
            f"{kind.upper()} (*.{kind})",
        )
        if not filename:
            return

        path = Path(filename)
        if path.suffix.lower() != "." + kind:
            path = path.with_suffix("." + kind)

        try:
            {"csv": export_annual_csv, "pdf": export_annual_pdf, "xlsx": export_annual_xlsx}[kind](path, snapshot)
            _message(
                self, "information", "Εξαγωγή " + kind.upper(),
                "Η αναφορά αποθηκεύτηκε:\n{path}", path=path,
            )
        except Exception as exc:
            _message(
                self, "critical", "Σφάλμα εξαγωγής",
                "{error}", error=str(exc),
            )

    def export_csv(self) -> None:
        AnnualFarmReportPage._export(self, "csv")

    def export_pdf(self) -> None:
        AnnualFarmReportPage._export(self, "pdf")

    def export_xlsx(self) -> None:
        AnnualFarmReportPage._export(self, "xlsx")
