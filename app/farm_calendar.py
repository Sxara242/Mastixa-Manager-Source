from __future__ import annotations

from .year_filters import populate_year_filter, YearFilteredPage

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .localized_messages import _language, _text
from .database import Database
from .ui_helpers import compact_decimal, format_kg, table_widget, scrollable_entry_layout


class FarmCalendarPage(YearFilteredPage):
    """Ενιαία, read-only χρονολογική προβολή των βασικών καλλιεργητικών γεγονότων."""


    @staticmethod
    def _body_render(spec):
        template, values, labels = spec
        return _text(template, **dict(values, **{k: _text(v) for k, v in labels.items()}))

    def _set_body(self, item, template, *, _labels=None, **values):
        spec = (template, values, _labels or {})
        item.setData(2367, spec)
        item.setText(self._body_render(spec))

    def _body_label(self, label, template, **values):
        label.setProperty("mastixaI18nSkipText", True)
        label.setTextFormat(label.textFormat().PlainText)
        spec = (template, values, {})
        label.setProperty("mastixaBodyTemplate", spec)
        label.setText(self._body_render(spec))

    def _refresh_body_language(self, *_args):
        # Only explicitly owned cells are projected; canonical rows remain opaque.
        for name in ('table',):
            table = getattr(self, name, None)
            if table is None:
                continue
            blocked = table.blockSignals(True)
            try:
                for row in range(table.rowCount()):
                    for column in range(table.columnCount()):
                        item = table.item(row, column)
                        spec = item.data(2367) if item is not None else None
                        if spec is not None:
                            text = self._body_render(spec)
                            if item.toolTip():
                                item.setToolTip(text)
                            item.setText(text)
            finally:
                table.blockSignals(blocked)
        for name in ('count_label',):
            label = getattr(self, name, None)
            spec = label.property("mastixaBodyTemplate") if label is not None else None
            if spec is not None:
                label.setText(self._body_render(spec))

    def __init__(self, db: Database) -> None:
        super().__init__()
        controller = _language()
        if controller is not None:
            controller.language_changed.connect(self._refresh_body_language)
        self.db = db
        self._rows: list[dict] = []

        layout = scrollable_entry_layout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(12)

        title = QLabel("Ενιαίο Ημερολόγιο")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Όλες οι βασικές καταχωρήσεις καλλιέργειας σε μία χρονολογική προβολή"
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        filters_box = QGroupBox("Φίλτρα")
        filters = QHBoxLayout(filters_box)

        self.year = QComboBox()
        self.year.currentIndexChanged.connect(self.refresh)

        self.month = QComboBox()
        self.month.addItem("Όλοι οι μήνες", None)
        for month in range(1, 13):
            self.month.addItem(
                QDate(2000, month, 1).toString("MMMM"),
                month,
            )
        self.month.currentIndexChanged.connect(self.refresh)

        self.field = QComboBox()
        self.field.currentIndexChanged.connect(self.refresh)

        self.section = QComboBox()
        self.section.addItem("Όλες οι ενότητες", None)
        for value in (
            "Παραγωγή",
            "Άρδευση & Λίπανση",
            "Φυτοπροστασία",
            "Εργατικά",
            "Φυτεύσεις & Δέντρα",
        ):
            self.section.addItem(value, value)
        self.section.currentIndexChanged.connect(self.refresh)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Αναζήτηση σε εργασία, προϊόν, εργαζόμενο, σημειώσεις..."
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh)

        filters.addWidget(QLabel("Έτος"))
        filters.addWidget(self.year)
        filters.addWidget(QLabel("Μήνας"))
        filters.addWidget(self.month)
        filters.addWidget(QLabel("Αγροτεμάχιο"))
        filters.addWidget(self.field)
        filters.addWidget(QLabel("Ενότητα"))
        filters.addWidget(self.section)
        filters.addWidget(self.search, 1)

        layout.addWidget(filters_box)

        summary = QHBoxLayout()

        self.count_label = QLabel("0 καταχωρήσεις")
        self.count_label.setStyleSheet(
            "font-weight: 700; color: #26382f;"
        )
        summary.addWidget(self.count_label)

        self.range_label = QLabel("")
        self.range_label.setStyleSheet("color: #67746d;")
        summary.addWidget(self.range_label)

        summary.addStretch()

        self.open_button = QPushButton("Άνοιγμα σχετικής ενότητας")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_selected)
        summary.addWidget(self.open_button)

        layout.addLayout(summary)

        self.table = table_widget(
            [
                "Ημερομηνία",
                "Ενότητα",
                "Αγροτεμάχιο",
                "Περιγραφή",
                "Ποσότητα / Κόστος",
            ]
        )
        self.table.itemSelectionChanged.connect(
            self._selection_changed
        )
        self.table.itemDoubleClicked.connect(
            lambda _item: self.open_selected()
        )
        self.table.setMinimumHeight(460)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

        layout.addWidget(self.table)

        self._refresh_fields()
        self._refresh_years()
        self.refresh()

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

    def _refresh_fields(self) -> None:
        current = self.field.currentData()

        self.field.blockSignals(True)
        self.field.clear()
        self.field.addItem("Όλα", None)

        if self._table_exists("fields"):
            for row in self.db.query(
                "SELECT id,name FROM fields ORDER BY name,id"
            ):
                self.field.addItem(
                    row["name"],
                    int(row["id"]),
                )

        index = self.field.findData(current)
        self.field.setCurrentIndex(index if index >= 0 else 0)
        self.field.blockSignals(False)

    def _refresh_years(self) -> None:
        populate_year_filter(self, self.year, strings=True)

    def _append(
        self,
        *,
        date: str,
        section: str,
        field_id: int | None,
        field_name: str,
        description: str,
        value: str,
        page_index: int,
        record_id: int,
        search_text: str,
    ) -> None:
        if not hasattr(self, "_body_rows"):
            self._body_rows = {}
        self._rows.append(
            {
                "date": date,
                "section": section,
                "field_id": field_id,
                "field_name": field_name,
                "description": description,
                "value": value,
                "page_index": page_index,
                "record_id": record_id,
                "search_text": search_text.casefold(),
            }
        )

    def _load_production(self) -> None:
        if not self._table_exists("production"):
            return

        rows = self.db.query(
            """
            SELECT
                p.*,
                f.name AS field_name
            FROM production p
            LEFT JOIN fields f ON f.id=p.field_id
            """
        )

        for row in rows:
            description = "Παραγωγή"
            if "product" in row.keys() and row["product"]:
                description = str(row["product"])

            notes = row["notes"] or ""
            self._append(
                date=row["entry_date"] or "",
                section="Παραγωγή",
                field_id=row["field_id"],
                field_name=row["field_name"] or "",
                description=description,
                value=format_kg(row["quantity_kg"]),
                page_index=3,
                record_id=int(row["id"]),
                search_text=f"{description} {notes} {row['field_name'] or ''}",
            )
            if not ("product" in row.keys() and row["product"]):
                self._body_rows[id(self._rows[-1])] = {3: ("Παραγωγή", {}, {})}

    def _load_activities(self) -> None:
        if not self._table_exists("farm_activities"):
            return

        rows = self.db.query(
            """
            SELECT
                a.*,
                f.name AS field_name
            FROM farm_activities a
            LEFT JOIN fields f ON f.id=a.field_id
            """
        )

        for row in rows:
            description = row["category"] or "Καταχώρηση"
            if row["description"]:
                description += f" — {row['description']}"

            parts = []
            if float(row["water_quantity_m3"] or 0) > 0:
                parts.append(
                    f"{compact_decimal(row['water_quantity_m3'], 3)} m³"
                )
            if float(row["dose"] or 0) > 0:
                dose = compact_decimal(row["dose"], 3)
                unit = row["dose_unit"] or ""
                parts.append(f"{dose} {unit}".strip())
            if float(row["cost"] or 0) > 0:
                parts.append(f"{float(row['cost']):.2f} €")

            self._append(
                date=row["activity_date"] or "",
                section="Άρδευση & Λίπανση",
                field_id=row["field_id"],
                field_name=row["field_name"] or "",
                description=description,
                value=" | ".join(parts),
                page_index=12,
                record_id=int(row["id"]),
                search_text=" ".join(
                    str(value or "")
                    for value in (
                        row["category"],
                        row["description"],
                        row["product"],
                        row["responsible"],
                        row["notes"],
                        row["field_name"],
                    )
                ),
            )
            category = row["category"] or "Καταχώρηση"
            owned = category in ("Πότισμα", "Λίπανση", "Καταχώρηση")
            self._body_rows[id(self._rows[-1])] = {3: ("{category}{description}", {"description": (" — " + row["description"]) if row["description"] else "", **({} if owned else {"category": category})}, {"category": category} if owned else {})}

    def _load_plant_protection(self) -> None:
        if not self._table_exists("plant_protection_records"):
            return

        rows = self.db.query(
            """
            SELECT
                p.*,
                f.name AS field_name
            FROM plant_protection_records p
            LEFT JOIN fields f ON f.id=p.field_id
            """
        )

        for row in rows:
            description = row["product_name"] or "Επέμβαση"
            if row["purpose"]:
                description += f" — {row['purpose']}"

            parts = []
            if float(row["dose"] or 0) > 0:
                parts.append(
                    f"{compact_decimal(row['dose'], 3)} {row['dose_unit'] or ''}".strip()
                )
            if float(row["cost"] or 0) > 0:
                parts.append(f"{float(row['cost']):.2f} €")

            self._append(
                date=row["application_date"] or "",
                section="Φυτοπροστασία",
                field_id=row["field_id"],
                field_name=row["field_name"] or "",
                description=description,
                value=" | ".join(parts),
                page_index=19,
                record_id=int(row["id"]),
                search_text=" ".join(
                    str(value or "")
                    for value in (
                        row["product_name"],
                        row["purpose"],
                        row["active_ingredient"],
                        row["applicator"],
                        row["weather"],
                        row["notes"],
                        row["field_name"],
                    )
                ),
            )
            if not row["product_name"]:
                self._body_rows[id(self._rows[-1])] = {3: ("Επέμβαση{purpose}", {"purpose": (" — " + row["purpose"]) if row["purpose"] else ""}, {})}

    def _load_labor(self) -> None:
        if not self._table_exists("labor_entries"):
            return

        rows = self.db.query(
            """
            SELECT
                l.*,
                f.name AS field_name,
                w.name AS worker_name
            FROM labor_entries l
            LEFT JOIN fields f ON f.id=l.field_id
            LEFT JOIN workers w ON w.id=l.worker_id
            """
        )

        for row in rows:
            description = row["work_type"] or "Εργασία"
            if row["worker_name"]:
                description += f" — {row['worker_name']}"

            value = (
                f"{compact_decimal(row['hours'], 2)} ώρες"
                f" | {float(row['cost'] or 0):.2f} €"
            )

            self._append(
                date=row["work_date"] or "",
                section="Εργατικά",
                field_id=row["field_id"],
                field_name=row["field_name"] or "Γενική",
                description=description,
                value=value,
                page_index=21,
                record_id=int(row["id"]),
                search_text=" ".join(
                    str(value or "")
                    for value in (
                        row["work_type"],
                        row["worker_name"],
                        row["notes"],
                        row["field_name"],
                    )
                ),
            )
            specs = {4: ("{hours} ώρες | {cost} €", {"hours": compact_decimal(row["hours"], 2), "cost": f"{float(row['cost'] or 0):.2f}"}, {})}
            if not row["field_name"]: specs[2] = ("Γενική", {}, {})
            if not row["work_type"]: specs[3] = ("Εργασία{worker}", {"worker": (" — " + row["worker_name"]) if row["worker_name"] else ""}, {})
            self._body_rows[id(self._rows[-1])] = specs

    def _load_plantings(self) -> None:
        if not self._table_exists("planting_batches"):
            return

        rows = self.db.query(
            """
            SELECT
                p.*,
                f.name AS field_name
            FROM planting_batches p
            LEFT JOIN fields f ON f.id=p.field_id
            """
        )

        for row in rows:
            planted = int(row["trees_planted"] or 0)
            alive = int(row["trees_alive"] or 0)
            losses = max(planted - alive, 0)

            description = row["material_type"] or "Φύτευση"
            if row["source"]:
                description += f" — {row['source']}"

            value = (
                f"{planted} φυτεμένα | {alive} ζωντανά"
                f" | {losses} απώλειες"
            )
            if float(row["cost"] or 0) > 0:
                value += f" | {float(row['cost']):.2f} €"

            self._append(
                date=row["planting_date"] or "",
                section="Φυτεύσεις & Δέντρα",
                field_id=row["field_id"],
                field_name=row["field_name"] or "",
                description=description,
                value=value,
                page_index=23,
                record_id=int(row["id"]),
                search_text=" ".join(
                    str(value or "")
                    for value in (
                        row["material_type"],
                        row["source"],
                        row["variety"],
                        row["spacing"],
                        row["notes"],
                        row["field_name"],
                    )
                ),
            )
            specs = {4: ("{planted} φυτεμένα | {alive} ζωντανά | {losses} απώλειες{cost}", {"planted": planted, "alive": alive, "losses": losses, "cost": f" | {float(row['cost']):.2f} €" if float(row["cost"] or 0) > 0 else ""}, {})}
            if not row["material_type"]: specs[3] = ("Φύτευση{source}", {"source": (" — " + row["source"]) if row["source"] else ""}, {})
            self._body_rows[id(self._rows[-1])] = specs

    def refresh(self, *_args) -> None:
        self._refresh_fields()
        self._refresh_years()

        self._rows = []
        self._body_rows = {}
        self._load_production()
        self._load_activities()
        self._load_plant_protection()
        self._load_labor()
        self._load_plantings()

        year = self.year.currentData()
        month = self.month.currentData()
        field_id = self.field.currentData()
        section = self.section.currentData()
        query = self.search.text().strip().casefold()

        filtered = []

        for row in self._rows:
            parsed = QDate.fromString(
                row["date"],
                "yyyy-MM-dd",
            )

            if year and (
                not parsed.isValid()
                or str(parsed.year()) != str(year)
            ):
                continue

            if month and (
                not parsed.isValid()
                or parsed.month() != int(month)
            ):
                continue

            if (
                field_id is not None
                and row["field_id"] != field_id
            ):
                continue

            if section and row["section"] != section:
                continue

            if query and (
                query not in row["search_text"]
                and query not in row["description"].casefold()
            ):
                continue

            filtered.append(row)

        filtered.sort(
            key=lambda row: (
                row["date"],
                row["section"],
                row["record_id"],
            ),
            reverse=True,
        )

        self._rows = filtered
        self.table.setRowCount(len(filtered))

        for row_index, row in enumerate(filtered):
            values = [
                row["date"],
                row["section"],
                row["field_name"],
                row["description"],
                row["value"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 1:
                    self._set_body(item, row["section"])
                else:
                    spec = getattr(self, "_body_rows", {}).get(id(row), {}).get(column)
                    if spec is not None:
                        self._set_body(item, spec[0], _labels=spec[2], **spec[1])
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    row,
                )
                if column == 3:
                    item.setToolTip(item.text())
                self.table.setItem(
                    row_index,
                    column,
                    item,
                )

        self._body_label(self.count_label, "{count} καταχωρήσεις", count=len(filtered))

        if filtered:
            dates = [
                row["date"]
                for row in filtered
                if row["date"]
            ]
            if dates:
                self.range_label.setText(
                    f"{min(dates)} → {max(dates)}"
                )
            else:
                self.range_label.clear()
        else:
            self.range_label.clear()

        self._selection_changed()

    def _selected_row(self) -> dict | None:
        items = self.table.selectedItems()
        if not items:
            return None

        item = self.table.item(
            items[0].row(),
            0,
        )
        if item is None:
            return None

        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, dict) else None

    def _selection_changed(self) -> None:
        self.open_button.setEnabled(
            self._selected_row() is not None
        )

    def open_selected(self) -> None:
        row = self._selected_row()
        if row is None:
            return

        window = self.window()
        change_page = getattr(window, "change_page", None)
        if callable(change_page):
            change_page(int(row["page_index"]))
