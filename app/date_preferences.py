from __future__ import annotations

from calendar import isleap
from dataclasses import replace

from PySide6.QtCore import QDate, QEvent, QObject
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)


SETTING_KEY = "date_display_format"
DEFAULT_DATE_FORMAT = "DD/MM/YY"
DATE_FORMATS = {
    "DD/MM/YY": "dd/MM/yy",
    "DD/MM/YYYY": "dd/MM/yyyy",
    "YYYY-MM-DD": "yyyy-MM-dd",
}
# Read existing explicit preferences without changing their meaning.
_LEGACY_FORMATS = {"MM/DD/YYYY": "MM/dd/yyyy"}
MONTH_DAY_FORMATS = {
    "DD/MM/YY": "dd/MM",
    "DD/MM/YYYY": "dd/MM",
    "MM/DD/YYYY": "MM/dd",
    "YYYY-MM-DD": "MM-dd",
}

_INSTALLED = False
_FILTER_ATTR = "_mastixa_date_preferences_filter"


def normalize_date_format(value: object) -> str:
    text = str(value or "").strip().upper()
    return text if text in DATE_FORMATS or text in _LEGACY_FORMATS else DEFAULT_DATE_FORMAT


def qt_date_format(value: object) -> str:
    return {**DATE_FORMATS, **_LEGACY_FORMATS}[normalize_date_format(value)]


def qt_month_day_format(value: object) -> str:
    return MONTH_DAY_FORMATS[normalize_date_format(value)]


def selected_date_format(db) -> str:
    return normalize_date_format(
        db.get_app_setting(SETTING_KEY, DEFAULT_DATE_FORMAT)
    )


def date_placeholder(db, *, optional: bool = False) -> str:
    suffix = " (προαιρετικό)" if optional else ""
    # Free-text input has no hidden full year like QDateEdit. Keep it unambiguous.
    selected = selected_date_format(db)
    return ("DD/MM/YYYY" if selected == "DD/MM/YY" else selected) + suffix


def format_iso_date(value: object, db, *, display_format: str | None = None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = QDate.fromString(text, "yyyy-MM-dd")
    if not parsed.isValid():
        return text
    # Table refreshes can resolve the preference once for their row batch. The
    # default still reads it live for individual controls and other callers.
    selected = selected_date_format(db) if display_format is None else display_format
    return parsed.toString(qt_date_format(selected))


def refresh_date_inputs(root: QWidget, db) -> None:
    """Update input presentation during a page refresh, without changing dates."""
    for edit in root.findChildren(QDateEdit):
        if _is_full_date_edit(edit):
            edit.setDisplayFormat(qt_date_format(selected_date_format(db)))


def parse_user_date_to_iso(value: object, db) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = QDate.fromString(
        text,
        qt_date_format("DD/MM/YYYY" if selected_date_format(db) == "DD/MM/YY" else selected_date_format(db)),
    )
    if not parsed.isValid():
        raise ValueError(
            f"Η ημερομηνία πρέπει να έχει μορφή {date_placeholder(db)}"
        )
    return parsed.toString("yyyy-MM-dd")


def _recurring_reference_year() -> int:
    """Use one nearby leap year for all month/day-only agricultural controls."""
    current_year = QDate.currentDate().year()
    for offset in range(8):
        year = current_year + offset
        if year <= 9998 and isleap(year):
            return year
    # Defensive fallback only for dates near Qt's upper supported year.
    return 2000


def current_year_month_day(month: int | None, day: int | None) -> QDate:
    """Represent a recurring month/day on a leap-year UI reference calendar."""
    month_value = int(month or 1)
    day_value = int(day or 1)
    reference_year = _recurring_reference_year()
    candidate = QDate(reference_year, month_value, day_value)
    if candidate.isValid():
        return candidate
    return QDate(reference_year, 1, 1)


def configure_recurring_month_day_edit(edit: QDateEdit, db=None) -> None:
    """Keep a month/day picker on one leap year and follow the profile date order."""
    current = edit.date()
    month = current.month() if current.isValid() else 1
    day = current.day() if current.isValid() else 1
    reference_year = _recurring_reference_year()

    edit.setProperty("mastixaMonthDayOnly", True)
    selected = selected_date_format(db) if db is not None else DEFAULT_DATE_FORMAT
    edit.setDisplayFormat(qt_month_day_format(selected))
    edit.setMinimumDate(QDate(reference_year, 1, 1))
    edit.setMaximumDate(QDate(reference_year, 12, 31))

    candidate = QDate(reference_year, month, day)
    edit.setDate(candidate if candidate.isValid() else QDate(reference_year, 1, 1))


def format_month_day(month: int | None, day: int | None, db) -> str:
    value = current_year_month_day(month, day)
    return value.toString(qt_month_day_format(selected_date_format(db)))


def _is_full_date_edit(edit: QDateEdit) -> bool:
    if bool(edit.property("mastixaMonthDayOnly")):
        return False
    current = str(edit.displayFormat() or "")
    return "d" in current and "M" in current and "y" in current


def _calendar_is_dark(calendar: QCalendarWidget) -> bool:
    app = QApplication.instance()
    palette = app.palette() if app is not None else calendar.palette()
    return palette.color(QPalette.ColorRole.Window).lightness() < 128


def _style_calendar(calendar: QCalendarWidget) -> None:
    dark = _calendar_is_dark(calendar)
    if getattr(calendar, "_mastixa_calendar_dark", None) == dark:
        return
    if dark:
        background = "#20282D"
        text = "#F2F5F6"
        muted = "#AAB4B9"
        header = "#171D21"
        selection = "#4F8068"
    else:
        background = "#FFFFFF"
        text = "#24312B"
        muted = "#66766E"
        header = "#F1F4F2"
        selection = "#3F765B"

    calendar.setStyleSheet(
        f"""
        QCalendarWidget QWidget {{
            background: {background};
            color: {text};
        }}
        QCalendarWidget QToolButton {{
            background: {header};
            color: {text};
            font-weight: 700;
        }}
        QCalendarWidget QSpinBox {{
            background: {background};
            color: {text};
        }}
        QCalendarWidget QAbstractItemView {{
            background: {background};
            color: {text};
            selection-background-color: {selection};
            selection-color: #FFFFFF;
        }}
        QCalendarWidget QAbstractItemView:disabled {{
            color: {muted};
        }}
        """
    )

    palette = calendar.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(background))
    palette.setColor(QPalette.ColorRole.Base, QColor(background))
    palette.setColor(QPalette.ColorRole.Text, QColor(text))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(selection))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(muted),
    )
    calendar.setPalette(palette)
    calendar._mastixa_calendar_dark = dark


def configure_date_edit(edit: QDateEdit, db) -> None:
    if bool(edit.property("mastixaMonthDayOnly")):
        edit.setDisplayFormat(qt_month_day_format(selected_date_format(db)))
    elif _is_full_date_edit(edit):
        edit.setDisplayFormat(qt_date_format(selected_date_format(db)))
    if edit.calendarPopup():
        _style_calendar(edit.calendarWidget())


def configure_date_text_field(field: QLineEdit, db) -> None:
    if not bool(field.property("mastixaDateTextField")):
        return
    field.setPlaceholderText(
        date_placeholder(
            db,
            optional=bool(field.property("mastixaDateOptional")),
        )
    )


def apply_date_preferences(root: QWidget, db) -> int:
    changed = 0
    date_edits = []
    if isinstance(root, QDateEdit):
        date_edits.append(root)
    date_edits.extend(root.findChildren(QDateEdit))
    for edit in date_edits:
        configure_date_edit(edit, db)
        changed += 1

    text_fields = []
    if isinstance(root, QLineEdit):
        text_fields.append(root)
    text_fields.extend(root.findChildren(QLineEdit))
    for field in text_fields:
        if bool(field.property("mastixaDateTextField")):
            configure_date_text_field(field, db)
            changed += 1
    return changed


def _db_for_widget(widget: QWidget):
    current: QWidget | None = widget
    while current is not None:
        db = getattr(current, "db", None)
        if db is not None:
            return db
        current = current.parentWidget()
    window = widget.window()
    return getattr(window, "db", None)


class _DatePreferenceFilter(QObject):
    def eventFilter(self, watched, event):
        if event.type() not in {QEvent.Type.Show, QEvent.Type.Polish}:
            return False
        if isinstance(watched, QDateEdit):
            db = _db_for_widget(watched)
            if db is not None:
                configure_date_edit(watched, db)
        elif isinstance(watched, QCalendarWidget):
            _style_calendar(watched)
        return False


def _ensure_event_filter() -> None:
    app = QApplication.instance()
    if app is None or hasattr(app, _FILTER_ATTR):
        return
    date_filter = _DatePreferenceFilter(app)
    app.installEventFilter(date_filter)
    setattr(app, _FILTER_ATTR, date_filter)


def _install_settings_controls() -> None:
    from .settings import SettingsPage

    original_build_general = SettingsPage._build_general_tab
    original_refresh = SettingsPage.refresh

    def build_general_with_date_format(self) -> None:
        original_build_general(self)
        if hasattr(self, "date_format_combo"):
            return
        tab = self.tabs.widget(0)
        if tab is None or tab.layout() is None:
            return

        box = QGroupBox("Μορφή ημερομηνίας")
        box_layout = QVBoxLayout(box)
        combo = QComboBox()
        combo.setProperty("mastixaI18nSkipItems", True)
        combo.blockSignals(True)
        for visible_format in DATE_FORMATS:
            combo.addItem(DATE_FORMATS[visible_format], visible_format)
        combo.blockSignals(False)
        self.date_format_combo = combo
        box_layout.addWidget(combo)

        note = QLabel(
            "Η μορφή αλλάζει αμέσως και αποθηκεύεται ξεχωριστά για κάθε "
            "προφίλ. Οι ημερομηνίες παραμένουν εσωτερικά αποθηκευμένες σε "
            "ασφαλή μορφή ISO."
        )
        note.setWordWrap(True)
        box_layout.addWidget(note)

        layout = tab.layout()
        insert_at = max(0, layout.count() - 1)
        layout.insertWidget(insert_at, box)

        def changed(_index: int) -> None:
            value = normalize_date_format(combo.currentData())
            self.db.set_app_setting(SETTING_KEY, value)
            window = self.window()
            if isinstance(window, QWidget):
                apply_date_preferences(window, self.db)

        combo.currentIndexChanged.connect(changed)

    def refresh_with_date_format(self) -> None:
        original_refresh(self)
        combo = getattr(self, "date_format_combo", None)
        if combo is None:
            return
        selected = selected_date_format(self.db)
        combo.blockSignals(True)
        index = combo.findData(selected)
        if index < 0 and selected in _LEGACY_FORMATS:
            combo.addItem(_LEGACY_FORMATS[selected], selected)
            index = combo.findData(selected)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)
        window = self.window()
        if isinstance(window, QWidget):
            apply_date_preferences(window, self.db)

    SettingsPage._build_general_tab = build_general_with_date_format
    SettingsPage.refresh = refresh_with_date_format


def _install_crop_program_calendar_fix() -> None:
    from . import crop_programs

    crop_programs._md_date = current_year_month_day
    original_rule_init = crop_programs.RuleDialog.__init__

    def rule_init_with_recurring_reference_year(self, *args, **kwargs) -> None:
        original_rule_init(self, *args, **kwargs)
        for edit in (self.fixed_date, self.start_date, self.end_date):
            configure_recurring_month_day_edit(edit, _db_for_widget(edit))
            _style_calendar(edit.calendarWidget())

    crop_programs.RuleDialog.__init__ = rule_init_with_recurring_reference_year


def _install_plant_date_text_fix() -> None:
    from . import plant_tracking_ui

    original_init = plant_tracking_ui.PlantDialog.__init__
    original_record = plant_tracking_ui.PlantDialog.record

    def plant_init_with_user_date_format(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self.planted_date.setProperty("mastixaDateTextField", True)
        self.planted_date.setProperty("mastixaDateOptional", True)
        current = self.planted_date.text().strip()
        if current:
            parsed = QDate.fromString(current, "yyyy-MM-dd")
            self.planted_date.setText(parsed.toString(qt_date_format(date_placeholder(self.db))) if parsed.isValid() else current)
        configure_date_text_field(self.planted_date, self.db)

    def plant_record_with_iso_date(self):
        record = original_record(self)
        return replace(
            record,
            planted_date=parse_user_date_to_iso(record.planted_date, self.db),
        )

    plant_tracking_ui.PlantDialog.__init__ = plant_init_with_user_date_format
    plant_tracking_ui.PlantDialog.record = plant_record_with_iso_date


def _install_main_window_application() -> None:
    from . import main_window

    original_init = main_window.MainWindow.__init__
    original_refresh_current_tab = main_window.MainWindow._refresh_current_tab

    def main_init_with_date_preferences(self, *args, **kwargs) -> None:
        _ensure_event_filter()
        original_init(self, *args, **kwargs)
        apply_date_preferences(self, self.db)

    def refresh_current_tab_with_date_preferences(self) -> None:
        original_refresh_current_tab(self)
        page_index = self._current_page_index()
        if page_index is None or not (0 <= page_index < len(self.pages)):
            return
        page = self.pages[page_index][1]
        if isinstance(page, QWidget):
            apply_date_preferences(page, self.db)

    main_window.MainWindow.__init__ = main_init_with_date_preferences
    main_window.MainWindow._refresh_current_tab = refresh_current_tab_with_date_preferences


def install_date_preferences() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    _install_settings_controls()
    _install_crop_program_calendar_fix()
    _install_plant_date_text_fix()
    _install_main_window_application()
    _ensure_event_filter()

    _INSTALLED = True
