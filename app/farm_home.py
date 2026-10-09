"""Read-only Home composition around the existing Dashboard metrics."""
from PySide6.QtCore import QDate, QSize, Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .audit import ACTION_LABELS, TABLE_LABELS
from .alerts import AlertsPage
from .icon_theme import _icon_for_text
from .layout_preferences import layout_mode
from .localized_messages import _text
from .year_context import active_working_year, correction_state, effective_working_year


class FarmHome:
    def __init__(self, dashboard, navigation, profile_name):
        self.dashboard, self.navigation = dashboard, navigation
        self.db, self.profile_name = dashboard.db, profile_name
        self.mode = layout_mode(self.db)
        self.snapshot = {}
        outer = dashboard.layout()
        content = QWidget(dashboard)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)
        outer.itemAt(0).widget().setText("Αρχική")
        # Move the original KPI widgets, preserving their identity and calculations.
        while outer.count():
            item = outer.takeAt(0)
            if item.widget():
                layout.addWidget(item.widget())
            elif item.layout():
                layout.addLayout(item.layout())
            # The old trailing spacer is replaced after the Home sections.
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea(dashboard)
        self.scroll.setObjectName("farmHomeScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(content)
        outer.addWidget(self.scroll)
        self.context = self.label()
        layout.insertWidget(2, self.context)

        quick = QGroupBox("Γρήγορη καταχώρηση")
        quick_layout = QGridLayout(quick)
        self.quick_buttons = {}
        for index, (key, caption, icon) in enumerate((
            ("production", "+ Παραγωγή", "Παραγωγή"), ("sale", "+ Πώληση", "Πωλήσεις"),
            ("expense", "+ Έξοδο", "Έξοδα"), ("income", "+ Άλλο έσοδο", "Έσοδα"),
            ("activity", "+ Εργασία", "Άρδευση & Λίπανση"), ("planting", "+ Φύτευση", "Φυτεύσεις & Δέντρα"))):
            button = QPushButton(caption)
            button.setIcon(_icon_for_text(icon))
            button.setIconSize(QSize(54, 54))
            button.setMinimumHeight(72)
            button.clicked.connect(lambda _checked=False, route=key: navigation.quick_entry(route))
            quick_layout.addWidget(button, index // 3, index % 3)
            self.quick_buttons[key] = button
        layout.addWidget(quick)
        self.add_link(layout, "Αναζήτηση", "search")

        attention = QGroupBox("Χρειάζονται προσοχή")
        attention_layout = QVBoxLayout(attention)
        self.attention = self.label()
        attention_layout.addWidget(self.attention)
        self.add_link(attention_layout, "Όλες οι ειδοποιήσεις", "alerts")
        layout.addWidget(attention)

        self.field_box = QGroupBox("Χωράφια")
        field_layout = QVBoxLayout(self.field_box)
        self.field_summary = self.label()
        field_layout.addWidget(self.field_summary)
        self.field_rows = [self.label() for _ in range(6)]
        for label in self.field_rows:
            field_layout.addWidget(label)
        self.add_link(field_layout, "Άνοιγμα χωραφιών", "fields")
        layout.addWidget(self.field_box)

        recent = QGroupBox("Πρόσφατη δραστηριότητα")
        recent_layout = QVBoxLayout(recent)
        self.recent_empty = self.label()
        recent_layout.addWidget(self.recent_empty)
        self.recent_rows = [self.label() for _ in range(6)]
        for label in self.recent_rows:
            recent_layout.addWidget(label)
        self.add_link(recent_layout, "Άνοιγμα ιστορικού", "history")
        layout.addWidget(recent)
        layout.addStretch()
        navigation.window.language.language_changed.connect(self.render)

    @staticmethod
    def label():
        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setProperty("mastixaI18nSkipText", True)
        label.setMinimumWidth(0)
        return label

    def add_link(self, layout, text, route):
        button = QPushButton(text)
        button.clicked.connect(lambda: self.navigation.open(route))
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)

    def refresh(self):
        # Optional lazy-page tables are read only when present, never created here.
        tables = {row["name"] for row in self.db.query("SELECT name FROM sqlite_master WHERE type='table'")}
        active, year = active_working_year(self.db), effective_working_year(self.db)
        lock = self.db.query_one("SELECT is_locked FROM year_locks WHERE year=?", (year,)) if "year_locks" in tables else None
        today = QDate.currentDate()
        overdue = upcoming = low = 0
        if "farm_activities" in tables:
            counts = self.db.query_one("""SELECT
                COALESCE(SUM(activity_date < ?),0) AS overdue,
                COALESCE(SUM(activity_date >= ? AND activity_date <= ?),0) AS upcoming
                FROM farm_activities WHERE status='Προγραμματισμένη' AND date(activity_date) IS NOT NULL""",
                (today.toString("yyyy-MM-dd"), today.toString("yyyy-MM-dd"), today.addDays(7).toString("yyyy-MM-dd")))
            overdue, upcoming = counts["overdue"], counts["upcoming"]
        if {"inventory_items", "inventory_movements"} <= tables:
            low = self.db.query_one(f"""SELECT COUNT(*) AS total FROM (
                SELECT i.minimum_stock, {AlertsPage._stock_expression()} AS stock
                FROM inventory_items i LEFT JOIN inventory_movements m ON m.item_id=i.id
                GROUP BY i.id HAVING stock <= 0 OR (i.minimum_stock > 0 AND stock <= i.minimum_stock)
                )""")["total"]
        fields = self.db.query("SELECT name,location FROM fields ORDER BY name,id LIMIT 6")
        field_count = self.db.query_one("SELECT COUNT(*) AS total FROM fields")["total"]
        recent = self.db.query("SELECT event_time,table_name,action,record_id,details FROM audit_events ORDER BY id DESC LIMIT 6") if "audit_events" in tables else []
        self.snapshot = dict(active=active, year=year, locked=bool(lock and lock["is_locked"]),
                             correction=correction_state(self.db) is not None, overdue=overdue, upcoming=upcoming,
                             low=low, fields=fields, field_count=field_count, recent=recent)
        self.set_mode(layout_mode(self.db))

    def set_mode(self, mode):
        self.mode = "advanced" if mode == "advanced" else "simple"
        self.render()

    def render(self, *_args):
        data = self.snapshot
        if not data:
            return
        state = _text("Προσωρινή διόρθωση" if data["correction"] else "Κλειδωμένο" if data["locked"] else "Ανοιχτό")
        self.context.setText(_text("Προφίλ: {profile} · Ενεργό έτος: {active} · Προβολή: {year} · {state}",
                                   profile=self.profile_name, active=data["active"], year=data["year"], state=state))
        self.attention.setText(_text("Σήμερα και επόμενες 7 ημέρες\nΕκπρόθεσμες εργασίες: {overdue} · Προσεχείς: {upcoming}\nΕίδη με χαμηλό ή μηδενικό απόθεμα: {low}",
                                     overdue=data["overdue"], upcoming=data["upcoming"], low=data["low"]))
        self.field_summary.setText(_text("Χωράφια: {count}", count=data["field_count"]))
        limit = 6 if self.mode == "advanced" else 3
        for i, label in enumerate(self.field_rows):
            visible = i < min(limit, len(data["fields"]))
            label.setVisible(visible)
            if visible:
                row = data["fields"][i]
                label.setText(str(row["name"] or "") + (" · " + row["location"] if row["location"] else ""))
        self.recent_empty.setText(_text("Δεν υπάρχουν ακόμη εγγραφές ιστορικού."))
        self.recent_empty.setVisible(not data["recent"])
        for i, label in enumerate(self.recent_rows):
            visible = i < min(limit, len(data["recent"]))
            label.setVisible(visible)
            if visible:
                row = data["recent"][i]
                table = _text(TABLE_LABELS[row["table_name"]]) if row["table_name"] in TABLE_LABELS else row["table_name"]
                action = _text(ACTION_LABELS[row["action"]]) if row["action"] in ACTION_LABELS else row["action"]
                text = f'{row["event_time"]} · {table} · {action} · #{row["record_id"]}'
                if self.mode == "advanced" and row["details"]:
                    text += "\n" + row["details"]
                label.setText(text)
