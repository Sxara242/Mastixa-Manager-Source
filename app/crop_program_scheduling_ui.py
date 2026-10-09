from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QFormLayout,
    QHeaderView,
    QSpinBox,
    QTableWidgetItem,
)

from .crop_program import CropProgramRule
from .date_preferences import format_month_day
from .language import tr
from . import crop_programs as legacy
from .year_context import working_context_date


WITHIN_PERIOD_OPTIONS = (
    ("Μία φορά", "once"),
    ("Ημέρες", "days"),
    ("Εβδομάδες", "weeks"),
    ("Μήνες", "months"),
)


def _form_layout(dialog) -> QFormLayout:
    root = dialog.layout()
    if root is None or root.count() == 0:
        raise RuntimeError("Crop-program rule form is unavailable")
    form = root.itemAt(0).layout()
    if not isinstance(form, QFormLayout):
        raise RuntimeError("Crop-program rule form is not a QFormLayout")
    return form


def _set_row_visible(form: QFormLayout, widget, visible: bool) -> None:
    label = form.labelForField(widget)
    if label is not None:
        label.setVisible(visible)
    widget.setVisible(visible)


def _enable_crop_step_buttons(spin: QSpinBox) -> None:
    spin.setProperty("mastixaCropStepControl", True)
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    spin.setSingleStep(1)
    spin.setMinimumWidth(max(spin.minimumWidth(), 108))


def _working_year_default() -> int:
    return working_context_date().year()


class RuleDialog(legacy.RuleDialog):
    """Alpha 2 agricultural scheduling editor with clear recurrence semantics."""

    def __init__(
        self,
        parent=None,
        rule: CropProgramRule | None = None,
        *,
        program_name: str = "",
        default_category: str = "",
    ):
        self._original_rule = rule
        super().__init__(
            parent,
            rule,
            program_name=program_name,
            default_category=default_category,
        )
        form = _form_layout(self)

        self.within_period_unit = QComboBox()
        self.within_period_unit.setProperty("mastixaI18nStaticItems", True)
        for label, value in WITHIN_PERIOD_OPTIONS:
            self.within_period_unit.addItem(label, value)

        unit, interval = (
            rule.effective_within_period()
            if rule is not None
            else ("once", None)
        )
        unit_index = self.within_period_unit.findData(unit)
        self.within_period_unit.setCurrentIndex(unit_index if unit_index >= 0 else 0)

        self.every_days.setRange(1, 3660)
        _enable_crop_step_buttons(self.every_days)
        self.every_days.setSuffix("")
        self.every_days.setValue(int(interval or 1))

        self.base_year = QSpinBox()
        self.base_year.setRange(1900, 9998)
        _enable_crop_step_buttons(self.base_year)
        self.base_year.setValue(
            int(rule.base_year)
            if rule is not None and rule.base_year is not None
            else _working_year_default()
        )

        self.every_years = QSpinBox()
        self.every_years.setRange(1, 50)
        _enable_crop_step_buttons(self.every_years)
        self.every_years.setValue(int(rule.every_years or 1) if rule else 1)
        self.every_years.setSuffix(" έτη")

        # Frequency belongs to interval/window mode. Base year and multi-year
        # recurrence are also interval/window concepts in the editor; fixed-date
        # mode intentionally exposes only the fixed recurring month/day field.
        interval_row = form.getWidgetPosition(self.every_days)[0]
        form.insertRow(
            interval_row,
            "Συχνότητα στην περίοδο",
            self.within_period_unit,
        )
        notes_row = form.getWidgetPosition(self.notes)[0]
        form.insertRow(notes_row, "Έτος βάσης", self.base_year)
        notes_row = form.getWidgetPosition(self.notes)[0]
        form.insertRow(notes_row, "Επανάληψη ανά (έτη)", self.every_years)

        self.within_period_unit.currentIndexChanged.connect(self._schedule_changed)
        self.every_days.valueChanged.connect(self._update_interval_suffix)
        self.every_years.valueChanged.connect(self._update_year_suffix)
        self._schedule_changed()

    def _schedule_changed(self) -> None:
        super()._schedule_changed()
        if not hasattr(self, "within_period_unit"):
            return
        form = _form_layout(self)

        fixed = self.schedule_combo.currentData() == "fixed_date"
        _set_row_visible(form, self.fixed_date, fixed)
        _set_row_visible(form, self.start_date, not fixed)
        _set_row_visible(form, self.end_date, not fixed)
        _set_row_visible(form, self.within_period_unit, not fixed)

        show_interval = (
            not fixed
            and self.within_period_unit.currentData() in {"days", "weeks", "months"}
        )
        _set_row_visible(form, self.every_days, show_interval)
        _set_row_visible(form, self.base_year, not fixed)
        _set_row_visible(form, self.every_years, not fixed)

        self._update_interval_suffix()
        self._update_year_suffix()

    def _update_interval_suffix(self, *_args) -> None:
        unit = str(self.within_period_unit.currentData() or "once")
        value = self.every_days.value()
        labels = {
            "days": (" ημέρα", " ημέρες"),
            "weeks": (" εβδομάδα", " εβδομάδες"),
            "months": (" μήνας", " μήνες"),
        }
        forms = labels.get(unit)
        self.every_days.setSuffix(
            "" if forms is None else forms[0] if value == 1 else forms[1]
        )

    def _update_year_suffix(self, *_args) -> None:
        self.every_years.setSuffix(
            " έτος" if self.every_years.value() == 1 else " έτη"
        )

    def rule(self) -> CropProgramRule:
        base = super().rule()
        if base.schedule_kind == "fixed_date":
            # New fixed-date rules are annual. Hidden legacy recurrence values
            # remain intact when an existing fixed-date rule is edited.
            original = self._original_rule
            return CropProgramRule(
                id=base.id,
                title=base.title,
                category=base.category,
                schedule_kind=base.schedule_kind,
                notes=base.notes,
                month=base.month,
                day=base.day,
                every_years=(
                    int(original.every_years or 1)
                    if original is not None
                    and original.schedule_kind == "fixed_date"
                    else 1
                ),
                base_year=(
                    original.base_year
                    if original is not None
                    and original.schedule_kind == "fixed_date"
                    else None
                ),
            )

        unit = str(self.within_period_unit.currentData() or "once")
        interval = (
            self.every_days.value()
            if unit in {"days", "weeks", "months"}
            else None
        )
        return CropProgramRule(
            id=base.id,
            title=base.title,
            category=base.category,
            schedule_kind=base.schedule_kind,
            notes=base.notes,
            start_month=base.start_month,
            start_day=base.start_day,
            end_month=base.end_month,
            end_day=base.end_day,
            every_days=interval if unit == "days" else None,
            within_period_unit=unit,
            within_period_interval=interval,
            every_years=self.every_years.value(),
            base_year=self.base_year.value(),
        )


class CropProgramsPage(legacy.CropProgramsPage):
    def __init__(self, db) -> None:
        super().__init__(db)
        _enable_crop_step_buttons(self.season_year)
        self._configure_rules_table()

    def _configure_rules_table(self) -> None:
        table = self.rules_table
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(90)
        for column in range(table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.Interactive,
            )

        # Keep schedule text genuinely readable instead of forcing all four
        # columns to divide the viewport equally. Smaller windows can scroll.
        for column, width in enumerate((180, 160, 420, 260)):
            table.setColumnWidth(column, width)
        table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        table.setWordWrap(False)

    def _render_rules(self) -> None:
        super()._render_rules()
        for row in range(self.rules_table.rowCount()):
            for column in range(self.rules_table.columnCount()):
                item = self.rules_table.item(row, column)
                if item is not None:
                    item.setToolTip(item.text())

    def _schedule_text(self, rule: CropProgramRule) -> str:
        if rule.schedule_kind == "fixed_date":
            return format_month_day(rule.month, rule.day, self.db)

        years = int(rule.every_years or 1)
        year_text = (
            tr("κάθε χρόνο")
            if years == 1
            else f"{tr('κάθε')} {years} {tr('έτη')}"
        )
        if rule.base_year is not None:
            year_text += f" · {tr('έτος βάσης')} {int(rule.base_year)}"

        base = (
            f"{format_month_day(rule.start_month, rule.start_day, self.db)}"
            f" – {format_month_day(rule.end_month, rule.end_day, self.db)}"
        )
        unit, interval = rule.effective_within_period()
        if unit == "once":
            frequency = tr("μία φορά στην περίοδο")
        else:
            count = int(interval or 0)
            forms = {
                "days": ("ημέρα", "ημέρες"),
                "weeks": ("εβδομάδα", "εβδομάδες"),
                "months": ("μήνας", "μήνες"),
            }
            singular, plural = forms.get(unit, (unit, unit))
            frequency = (
                f"{tr('κάθε')} {count} "
                f"{tr(singular if count == 1 else plural)}"
            )
        return f"{base} · {frequency} · {year_text}"

    def refresh_tasks(self) -> None:
        if self._loading:
            return
        program_id = self.task_program_filter.currentData()
        field_id = self.task_field_filter.currentData()
        tasks = self.store.tasks(
            program_id=str(program_id) if program_id else None,
            field_id=str(field_id) if field_id else None,
        )
        status = str(self.task_status_filter.currentData() or "")
        if status:
            tasks = [task for task in tasks if task["status"] == status]

        fields = {str(row["id"]): str(row["name"]) for row in self._fields()}
        programs = {
            str(item["id"]): str(item["name"]) for item in self.store.programs()
        }
        self.tasks_table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            shown_date = legacy._display_date(task["due_date"])
            if task.get("window_end_date"):
                shown_date += " – " + legacy._display_date(task["window_end_date"])
            values = (
                shown_date,
                fields.get(str(task["field_id"]), str(task["field_id"])),
                programs.get(str(task["program_id"]), str(task["program_id"])),
                task["title"],
                tr(
                    legacy.CATEGORY_LABELS.get(
                        str(task["category"]), str(task["category"])
                    )
                ),
                tr(
                    legacy.STATUS_LABELS.get(
                        str(task["status"]), str(task["status"])
                    )
                ),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(
                        legacy.Qt.ItemDataRole.UserRole,
                        task["generation_key"],
                    )
                self.tasks_table.setItem(row, column, item)
