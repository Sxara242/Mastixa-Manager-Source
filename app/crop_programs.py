from __future__ import annotations

from datetime import date
from uuid import uuid4

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDateEdit,
)

from .crop_program import CropProgramRule
from .crop_program_store import CropProgramStore
from .database import Database
from .language import tr
from .ui_helpers import table_widget


CATEGORY_OPTIONS = (
    ("Άρδευση", "irrigation"),
    ("Λίπανση", "fertilization"),
    ("Καλλιεργητική εργασία", "cultivation"),
    ("Φυτοπροστασία", "plant_protection"),
    ("Έλεγχος", "inspection"),
    ("Κλάδεμα", "pruning"),
    ("Άλλο", "other"),
)
CATEGORY_LABELS = {value: label for label, value in CATEGORY_OPTIONS}
STATUS_LABELS = {
    "pending": "Σε εκκρεμότητα",
    "completed": "Ολοκληρώθηκε",
    "skipped": "Παραλείφθηκε",
}


def _md_date(month: int | None, day: int | None) -> QDate:
    return QDate(2000, int(month or 1), int(day or 1))


def _display_date(value: object) -> str:
    text = str(value or "")
    parsed = QDate.fromString(text, "yyyy-MM-dd")
    return parsed.toString("dd/MM/yyyy") if parsed.isValid() else text


class RuleDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, rule: CropProgramRule | None = None):
        super().__init__(parent)
        self._rule_id = rule.id if rule is not None else str(uuid4())
        self.setWindowTitle("Κανόνας προγράμματος")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Π.χ. Άρδευση")
        if rule is not None:
            self.title_edit.setText(rule.title)
        form.addRow("Εργασία", self.title_edit)

        self.category_combo = QComboBox()
        self.category_combo.setProperty("mastixaI18nStaticItems", True)
        for label, value in CATEGORY_OPTIONS:
            self.category_combo.addItem(label, value)
        if rule is not None:
            index = self.category_combo.findData(rule.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        form.addRow("Κατηγορία", self.category_combo)

        self.schedule_combo = QComboBox()
        self.schedule_combo.setProperty("mastixaI18nStaticItems", True)
        self.schedule_combo.addItem("Σταθερή ημερομηνία", "fixed_date")
        self.schedule_combo.addItem("Επανάληψη σε περίοδο", "interval_window")
        if rule is not None:
            index = self.schedule_combo.findData(rule.schedule_kind)
            if index >= 0:
                self.schedule_combo.setCurrentIndex(index)
        self.schedule_combo.currentIndexChanged.connect(self._schedule_changed)
        form.addRow("Προγραμματισμός", self.schedule_combo)

        self.fixed_date = QDateEdit()
        self.fixed_date.setCalendarPopup(True)
        self.fixed_date.setDisplayFormat("dd/MM")
        self.fixed_date.setDate(_md_date(rule.month if rule else 1, rule.day if rule else 1))
        form.addRow("Ημερομηνία", self.fixed_date)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM")
        self.start_date.setDate(
            _md_date(rule.start_month if rule else 5, rule.start_day if rule else 1)
        )
        form.addRow("Έναρξη", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM")
        self.end_date.setDate(
            _md_date(rule.end_month if rule else 9, rule.end_day if rule else 30)
        )
        form.addRow("Λήξη", self.end_date)

        self.every_days = QSpinBox()
        self.every_days.setRange(1, 366)
        self.every_days.setValue(int(rule.every_days or 7) if rule else 7)
        self.every_days.setSuffix(" ημέρες")
        form.addRow("Κάθε", self.every_days)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(80)
        self.notes.setPlaceholderText("Σημειώσεις για την εργασία...")
        if rule is not None:
            self.notes.setPlainText(rule.notes)
        form.addRow("Σημειώσεις", self.notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._schedule_changed()

    def _schedule_changed(self) -> None:
        fixed = self.schedule_combo.currentData() == "fixed_date"
        self.fixed_date.setEnabled(fixed)
        self.start_date.setEnabled(not fixed)
        self.end_date.setEnabled(not fixed)
        self.every_days.setEnabled(not fixed)

    def _accept_if_valid(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", "Συμπλήρωσε τίτλο εργασίας.")
            return
        self.accept()

    def rule(self) -> CropProgramRule:
        fixed = self.schedule_combo.currentData() == "fixed_date"
        common = dict(
            id=self._rule_id,
            title=self.title_edit.text().strip(),
            category=str(self.category_combo.currentData()),
            schedule_kind=str(self.schedule_combo.currentData()),
            notes=self.notes.toPlainText().strip(),
        )
        if fixed:
            chosen = self.fixed_date.date()
            return CropProgramRule(
                **common,
                month=chosen.month(),
                day=chosen.day(),
            )
        start = self.start_date.date()
        end = self.end_date.date()
        return CropProgramRule(
            **common,
            start_month=start.month(),
            start_day=start.day(),
            end_month=end.month(),
            end_day=end.day(),
            every_days=self.every_days.value(),
        )


class CropProgramsPage(QWidget):
    """Phase 12D Windows UI for templates, assignment and generated tasks."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.store = CropProgramStore(db)
        self.selected_program_id: str | None = None
        self.rules: list[CropProgramRule] = []
        self._loading = False
        controller = getattr(QApplication.instance(), "_mastixa_language_controller", None)
        if controller is not None:
            controller.language_changed.connect(self.refresh)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("cropProgramsContent")
        content.setStyleSheet(
            "QWidget#cropProgramsContent { background: #f5f6f3; }"
        )
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 20, 14, 18)
        layout.setSpacing(12)
        scroll.setWidget(content)

        title = QLabel("Πρόγραμμα Καλλιέργειας")
        title.setObjectName("pageTitle")
        title.setMinimumHeight(42)
        layout.addWidget(title)

        subtitle = QLabel(
            "Δημιούργησε επαναχρησιμοποιήσιμους κανόνες εργασιών και "
            "παρήγαγε προγραμματισμένες εργασίες ανά αγροτεμάχιο και έτος."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        program_box = QGroupBox("Προγράμματα")
        program_layout = QHBoxLayout(program_box)
        self.program_list = QListWidget()
        self.program_list.setMinimumWidth(280)
        self.program_list.currentItemChanged.connect(self._program_selected)
        program_layout.addWidget(self.program_list, 1)

        editor = QWidget()
        editor_form = QFormLayout(editor)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Όνομα προγράμματος")
        self.crop_edit = QLineEdit()
        self.crop_edit.setPlaceholderText("Καλλιέργεια, π.χ. Μαστίχα")
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(74)
        self.description_edit.setPlaceholderText("Περιγραφή / παρατηρήσεις...")
        editor_form.addRow("Όνομα", self.name_edit)
        editor_form.addRow("Καλλιέργεια", self.crop_edit)
        editor_form.addRow("Περιγραφή", self.description_edit)

        program_buttons = QHBoxLayout()
        self.new_button = QPushButton("Νέο")
        self.new_button.clicked.connect(self.new_program)
        self.save_button = QPushButton("Αποθήκευση")
        self.save_button.clicked.connect(self.save_program)
        self.archive_button = QPushButton("Αρχειοθέτηση")
        self.archive_button.clicked.connect(self.archive_program)
        program_buttons.addWidget(self.new_button)
        program_buttons.addWidget(self.save_button)
        program_buttons.addWidget(self.archive_button)
        program_buttons.addStretch()
        editor_form.addRow("", program_buttons)
        program_layout.addWidget(editor, 2)
        layout.addWidget(program_box)

        rules_box = QGroupBox("Κανόνες εργασιών")
        rules_layout = QVBoxLayout(rules_box)
        self.rules_table = table_widget(
            ["Εργασία", "Κατηγορία", "Προγραμματισμός", "Σημειώσεις"]
        )
        self.rules_table.setMinimumHeight(180)
        self.rules_table.cellDoubleClicked.connect(self.edit_rule)
        rules_layout.addWidget(self.rules_table)
        rule_buttons = QHBoxLayout()
        self.add_rule_button = QPushButton("Προσθήκη κανόνα")
        self.add_rule_button.clicked.connect(self.add_rule)
        self.edit_rule_button = QPushButton("Επεξεργασία")
        self.edit_rule_button.clicked.connect(self.edit_rule)
        self.remove_rule_button = QPushButton("Αφαίρεση")
        self.remove_rule_button.clicked.connect(self.remove_rule)
        rule_buttons.addWidget(self.add_rule_button)
        rule_buttons.addWidget(self.edit_rule_button)
        rule_buttons.addWidget(self.remove_rule_button)
        rule_buttons.addStretch()
        rules_layout.addLayout(rule_buttons)
        layout.addWidget(rules_box)

        assignment_box = QGroupBox("Εφαρμογή προγράμματος")
        assignment = QHBoxLayout(assignment_box)
        self.assignment_program = QComboBox()
        self.assignment_program.setProperty("mastixaI18nSkipItems", True)
        self.assignment_field = QComboBox()
        self.assignment_field.setProperty("mastixaI18nSkipItems", True)
        self.season_year = QSpinBox()
        self.season_year.setRange(1900, 9998)
        self.season_year.setValue(date.today().year)
        self.generate_button = QPushButton("Δημιουργία / ανανέωση εργασιών")
        self.generate_button.clicked.connect(self.generate_tasks)
        assignment.addWidget(QLabel("Πρόγραμμα"))
        assignment.addWidget(self.assignment_program, 2)
        assignment.addWidget(QLabel("Αγροτεμάχιο"))
        assignment.addWidget(self.assignment_field, 2)
        assignment.addWidget(QLabel("Έτος"))
        assignment.addWidget(self.season_year)
        assignment.addWidget(self.generate_button)
        layout.addWidget(assignment_box)

        tasks_box = QGroupBox("Προγραμματισμένες εργασίες")
        tasks_layout = QVBoxLayout(tasks_box)
        filters = QHBoxLayout()
        self.task_program_filter = QComboBox()
        self.task_program_filter.setProperty("mastixaI18nSkipItems", True)
        self.task_program_filter.currentIndexChanged.connect(self.refresh_tasks)
        self.task_field_filter = QComboBox()
        self.task_field_filter.setProperty("mastixaI18nSkipItems", True)
        self.task_field_filter.currentIndexChanged.connect(self.refresh_tasks)
        self.task_status_filter = QComboBox()
        self.task_status_filter.setProperty("mastixaI18nStaticItems", True)
        self.task_status_filter.addItem("Όλες οι καταστάσεις", "")
        for value, label in STATUS_LABELS.items():
            self.task_status_filter.addItem(label, value)
        self.task_status_filter.currentIndexChanged.connect(self.refresh_tasks)
        filters.addWidget(QLabel("Πρόγραμμα"))
        filters.addWidget(self.task_program_filter, 1)
        filters.addWidget(QLabel("Αγροτεμάχιο"))
        filters.addWidget(self.task_field_filter, 1)
        filters.addWidget(QLabel("Κατάσταση"))
        filters.addWidget(self.task_status_filter)
        tasks_layout.addLayout(filters)

        self.tasks_table = table_widget(
            ["Ημερομηνία", "Αγροτεμάχιο", "Πρόγραμμα", "Εργασία", "Κατηγορία", "Κατάσταση"]
        )
        self.tasks_table.setMinimumHeight(260)
        tasks_layout.addWidget(self.tasks_table)

        task_buttons = QHBoxLayout()
        self.pending_button = QPushButton("Σε εκκρεμότητα")
        self.completed_button = QPushButton("Ολοκληρώθηκε")
        self.skipped_button = QPushButton("Παραλείφθηκε")
        self.pending_button.clicked.connect(lambda: self.set_selected_task_status("pending"))
        self.completed_button.clicked.connect(lambda: self.set_selected_task_status("completed"))
        self.skipped_button.clicked.connect(lambda: self.set_selected_task_status("skipped"))
        task_buttons.addWidget(self.pending_button)
        task_buttons.addWidget(self.completed_button)
        task_buttons.addWidget(self.skipped_button)
        task_buttons.addStretch()
        tasks_layout.addLayout(task_buttons)
        layout.addWidget(tasks_box)
        layout.addStretch()

        self.refresh()
        self.new_program()

    @staticmethod
    def _schedule_text(rule: CropProgramRule) -> str:
        if rule.schedule_kind == "fixed_date":
            return f"{int(rule.day or 0):02d}/{int(rule.month or 0):02d}"
        return (
            f"{int(rule.start_day or 0):02d}/{int(rule.start_month or 0):02d}"
            f" – {int(rule.end_day or 0):02d}/{int(rule.end_month or 0):02d}"
            f" · {tr('κάθε')} {int(rule.every_days or 0)} {tr('ημέρες')}"
        )

    def _program_selected(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if self._loading or current is None:
            return
        program_id = current.data(Qt.ItemDataRole.UserRole)
        if program_id:
            self.load_program(str(program_id))

    def _set_editor_enabled(self, enabled: bool) -> None:
        for widget in (
            self.name_edit,
            self.crop_edit,
            self.description_edit,
            self.save_button,
            self.add_rule_button,
            self.edit_rule_button,
            self.remove_rule_button,
        ):
            widget.setEnabled(enabled)

    def new_program(self) -> None:
        self.selected_program_id = None
        self.name_edit.clear()
        self.crop_edit.clear()
        self.description_edit.clear()
        self.rules = []
        self._set_editor_enabled(True)
        self.archive_button.setEnabled(False)
        self._render_rules()
        self.name_edit.setFocus()

    def load_program(self, program_id: str) -> None:
        try:
            program = self.store.program(program_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", str(exc))
            return
        self.selected_program_id = str(program["id"])
        self.name_edit.setText(str(program["name"]))
        self.crop_edit.setText(str(program["crop"] or ""))
        self.description_edit.setPlainText(str(program["description"] or ""))
        self.rules = list(program["rules"])
        active = bool(program["active"])
        self._set_editor_enabled(active)
        self.archive_button.setEnabled(active)
        self._render_rules()

    def save_program(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", "Συμπλήρωσε όνομα προγράμματος.")
            return
        program_id = self.selected_program_id or str(uuid4())
        try:
            self.store.save_program(
                program_id,
                name,
                self.rules,
                crop=self.crop_edit.text().strip(),
                description=self.description_edit.toPlainText().strip(),
            )
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", str(exc))
            return
        self.selected_program_id = program_id
        self.refresh()
        self._select_program(program_id)

    def archive_program(self) -> None:
        if not self.selected_program_id:
            return
        answer = QMessageBox.question(
            self,
            "Αρχειοθέτηση προγράμματος",
            "Η αρχειοθέτηση αφαιρεί τις εκκρεμείς εργασίες και κρατά "
            "το ιστορικό όσων ολοκληρώθηκαν ή παραλείφθηκαν. Συνέχεια;",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.archive_program(self.selected_program_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", str(exc))
            return
        archived = self.selected_program_id
        self.refresh()
        self._select_program(archived)

    def add_rule(self) -> None:
        dialog = RuleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.rules.append(dialog.rule())
            self._render_rules()

    def edit_rule(self, *_args) -> None:
        row = self.rules_table.currentRow()
        if row < 0 or row >= len(self.rules):
            return
        dialog = RuleDialog(self, self.rules[row])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.rules[row] = dialog.rule()
            self._render_rules()
            self.rules_table.selectRow(row)

    def remove_rule(self) -> None:
        row = self.rules_table.currentRow()
        if row < 0 or row >= len(self.rules):
            return
        del self.rules[row]
        self._render_rules()

    def _render_rules(self) -> None:
        self.rules_table.setRowCount(len(self.rules))
        for row, rule in enumerate(self.rules):
            values = (
                rule.title,
                tr(CATEGORY_LABELS.get(rule.category, rule.category)),
                self._schedule_text(rule),
                rule.notes,
            )
            for column, value in enumerate(values):
                self.rules_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _fields(self) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.db.query("SELECT id,name FROM fields ORDER BY name COLLATE NOCASE,id")
        ]

    def _select_program(self, program_id: str) -> None:
        for index in range(self.program_list.count()):
            item = self.program_list.item(index)
            if str(item.data(Qt.ItemDataRole.UserRole)) == program_id:
                self.program_list.setCurrentRow(index)
                return

    @staticmethod
    def _restore_combo_value(combo: QComboBox, value: object) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def refresh(self) -> None:
        selected = self.selected_program_id
        assignment_program = self.assignment_program.currentData()
        assignment_field = self.assignment_field.currentData()
        task_program = self.task_program_filter.currentData()
        task_field = self.task_field_filter.currentData()

        programs = self.store.programs()
        active_programs = [item for item in programs if item["active"]]
        fields = self._fields()

        self._loading = True
        try:
            self.program_list.clear()
            for program in programs:
                marker = "" if program["active"] else " ⏸"
                item = QListWidgetItem(
                    f'{program["name"]} ({program["rule_count"]}){marker}'
                )
                item.setData(Qt.ItemDataRole.UserRole, program["id"])
                self.program_list.addItem(item)

            self.assignment_program.clear()
            for program in active_programs:
                self.assignment_program.addItem(str(program["name"]), program["id"])
            self.assignment_field.clear()
            for field in fields:
                self.assignment_field.addItem(str(field["name"]), str(field["id"]))

            self.task_program_filter.clear()
            self.task_program_filter.addItem("Όλα τα προγράμματα", None)
            for program in programs:
                self.task_program_filter.addItem(str(program["name"]), program["id"])
            self.task_field_filter.clear()
            self.task_field_filter.addItem("Όλα τα αγροτεμάχια", None)
            for field in fields:
                self.task_field_filter.addItem(str(field["name"]), str(field["id"]))

            self._restore_combo_value(self.assignment_program, assignment_program)
            self._restore_combo_value(self.assignment_field, assignment_field)
            self._restore_combo_value(self.task_program_filter, task_program)
            self._restore_combo_value(self.task_field_filter, task_field)
        finally:
            self._loading = False

        if selected:
            self._select_program(selected)
        self._render_rules()
        self.refresh_tasks()

    def generate_tasks(self) -> None:
        program_id = self.assignment_program.currentData()
        field_id = self.assignment_field.currentData()
        if not program_id or not field_id:
            QMessageBox.warning(
                self,
                "Πρόγραμμα Καλλιέργειας",
                "Χρειάζεται ενεργό πρόγραμμα και αγροτεμάχιο.",
            )
            return
        try:
            generated = self.store.generate_for_field(
                str(program_id), str(field_id), self.season_year.value()
            )
        except (ValueError, OverflowError) as exc:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", str(exc))
            return
        self.task_program_filter.setCurrentIndex(
            max(self.task_program_filter.findData(program_id), 0)
        )
        self.task_field_filter.setCurrentIndex(
            max(self.task_field_filter.findData(field_id), 0)
        )
        self.refresh_tasks()
        QMessageBox.information(
            self,
            "Πρόγραμμα Καλλιέργειας",
            f"Οι εργασίες ενημερώθηκαν. Σύνολο για την ανάθεση: {len(generated)}.",
        )

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
            values = (
                _display_date(task["due_date"]),
                fields.get(str(task["field_id"]), str(task["field_id"])),
                programs.get(str(task["program_id"]), str(task["program_id"])),
                task["title"],
                tr(CATEGORY_LABELS.get(str(task["category"]), str(task["category"]))),
                tr(STATUS_LABELS.get(str(task["status"]), str(task["status"]))),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, task["generation_key"])
                self.tasks_table.setItem(row, column, item)

    def set_selected_task_status(self, status: str) -> None:
        row = self.tasks_table.currentRow()
        if row < 0:
            return
        item = self.tasks_table.item(row, 0)
        if item is None:
            return
        key = item.data(Qt.ItemDataRole.UserRole)
        if not key:
            return
        try:
            self.store.set_task_status(str(key), status)
        except ValueError as exc:
            QMessageBox.warning(self, "Πρόγραμμα Καλλιέργειας", str(exc))
            return
        self.refresh_tasks()
