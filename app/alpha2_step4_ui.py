from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QComboBox,
    QFrame,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionComboBox,
    QVBoxLayout,
    QWidget,
)

from . import icon_theme
from .data_export import DataExportPage
from .data_quality import DataQualityPage
from .fields import FieldsPage
from .plant_protection import PlantProtectionPage


_INSTALLED = False
_CHECKMARK_ICON = (
    Path(__file__).resolve().parent / "assets" / "checkmark.svg"
).as_posix()


def _message_box_ancestor(button: QAbstractButton) -> QMessageBox | None:
    parent = button.parentWidget()
    while parent is not None:
        if isinstance(parent, QMessageBox):
            return parent
        parent = parent.parentWidget()
    return None


def _restore_standard_dialog_mnemonics(root: QWidget) -> None:
    candidates: list[QAbstractButton] = []
    if isinstance(root, QAbstractButton):
        candidates.append(root)
    candidates.extend(root.findChildren(QAbstractButton))

    for button in candidates:
        box = _message_box_ancestor(button)
        if box is None:
            continue
        if box.standardButton(button) == QMessageBox.StandardButton.NoButton:
            continue
        text = button.text()
        if "&&" in text:
            button.setText(text.replace("&&", "&"))


def _install_standard_dialog_ampersand_fix() -> None:
    original_impl = icon_theme._apply_icon_theme_impl

    def apply_without_visible_system_ampersands(root) -> int:
        changed = original_impl(root)
        if isinstance(root, QWidget):
            _restore_standard_dialog_mnemonics(root)
        return changed

    icon_theme._apply_icon_theme_impl = apply_without_visible_system_ampersands


def _fit_combo_to_contents(combo: QComboBox) -> None:
    texts = [
        combo.itemText(index)
        for index in range(combo.count())
        if combo.itemText(index)
    ]
    current = combo.currentText()
    if current:
        texts.append(current)
    if combo.isEditable() and combo.lineEdit() is not None:
        edit_text = combo.lineEdit().text()
        if edit_text:
            texts.append(edit_text)
    if not texts:
        return

    metrics = combo.fontMetrics()
    widest = max(texts, key=metrics.horizontalAdvance)
    text_width = metrics.horizontalAdvance(widest)

    # Let the active Qt/QSS style calculate the real closed-control chrome.
    # This accounts for app stylesheet padding (currently 48 px on the right),
    # frame width and the drop-down subcontrol instead of guessing them.
    option = QStyleOptionComboBox()
    combo.initStyleOption(option)
    option.currentText = widest
    styled = combo.style().sizeFromContents(
        QStyle.ContentsType.CT_ComboBox,
        option,
        QSize(text_width, metrics.height()),
        combo,
    )
    control_width = styled.width() + 8

    arrow_width = combo.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
    popup_width = text_width + arrow_width + 36

    combo.setMinimumWidth(max(combo.minimumWidth(), control_width))
    combo.updateGeometry()
    view = combo.view()
    if view is not None:
        view.setMinimumWidth(max(view.minimumWidth(), popup_width))


def _install_plant_protection_combo_fix() -> None:
    original_init = PlantProtectionPage.__init__

    def init_with_content_width(self, db) -> None:
        original_init(self, db)
        _fit_combo_to_contents(self.dose_unit)
        model = self.dose_unit.model()
        model.rowsInserted.connect(
            lambda *_args: _fit_combo_to_contents(self.dose_unit)
        )
        model.dataChanged.connect(
            lambda *_args: _fit_combo_to_contents(self.dose_unit)
        )
        self.dose_unit.currentTextChanged.connect(
            lambda *_args: _fit_combo_to_contents(self.dose_unit)
        )
        line_edit = self.dose_unit.lineEdit()
        if line_edit is not None:
            line_edit.textChanged.connect(
                lambda *_args: _fit_combo_to_contents(self.dose_unit)
            )

    PlantProtectionPage.__init__ = init_with_content_width


def _make_data_quality_scrollable(page: DataQualityPage) -> None:
    if page.findChild(QScrollArea, "dataQualityScroll") is not None:
        return

    outer = page.layout()
    if outer is None:
        return

    margins = outer.contentsMargins()
    spacing = outer.spacing()

    content = QWidget(page)
    content.setObjectName("dataQualityContent")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom(),
    )
    content_layout.setSpacing(spacing)

    while outer.count():
        item = outer.takeAt(0)
        if item is None:
            continue

        widget = item.widget()
        if widget is not None:
            widget.setParent(content)
            content_layout.addWidget(widget)
            continue

        child_layout = item.layout()
        if child_layout is not None:
            content_layout.addLayout(child_layout)
            continue

        content_layout.addItem(item)

    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    scroll = QScrollArea(page)
    scroll.setObjectName("dataQualityScroll")
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(content)
    outer.addWidget(scroll)


def _install_data_quality_card_fix() -> None:
    original_init = DataQualityPage.__init__

    def init_with_safe_metric_heights(self, db) -> None:
        original_init(self, db)
        for box, value_label in (
            self.error_card,
            self.warning_card,
            self.total_card,
            self.status_card,
        ):
            box.setMinimumHeight(max(box.minimumHeight(), 112))
            box.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Minimum,
            )
            value_label.setMinimumHeight(max(value_label.minimumHeight(), 42))
            value_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            card_layout = box.layout()
            if card_layout is not None:
                card_layout.setContentsMargins(12, 12, 12, 12)
                card_layout.setSpacing(4)

        _make_data_quality_scrollable(self)

    DataQualityPage.__init__ = init_with_safe_metric_heights


def _make_checkbox_indicator_explicit(check: QCheckBox) -> None:
    check.setMinimumHeight(max(check.minimumHeight(), 28))
    check.setCursor(Qt.CursorShape.PointingHandCursor)
    check.setStyleSheet(
        f"""
        QCheckBox {{
            spacing: 9px;
            padding: 3px 4px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid palette(mid);
            border-radius: 3px;
            background: palette(base);
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid palette(highlight);
            background: palette(highlight);
            image: url("{_CHECKMARK_ICON}");
        }}
        QCheckBox::indicator:unchecked:hover {{
            border-color: palette(highlight);
        }}
        QCheckBox::indicator:checked:hover {{
            border-color: palette(highlight);
            background: palette(highlight);
        }}
        QCheckBox:focus {{
            border: 1px solid palette(highlight);
            border-radius: 5px;
        }}
        """
    )


def _install_data_export_checkbox_fix() -> None:
    original_init = DataExportPage.__init__

    def init_with_visible_checks(self, db) -> None:
        original_init(self, db)
        _make_checkbox_indicator_explicit(self.product_filter_check)
        for check in self.section_checks.values():
            _make_checkbox_indicator_explicit(check)

    DataExportPage.__init__ = init_with_visible_checks


def _make_fields_page_scrollable(page: FieldsPage) -> None:
    if page.findChild(QScrollArea, "fieldsScroll") is not None:
        return

    outer = page.layout()
    if outer is None:
        return

    margins = outer.contentsMargins()
    spacing = outer.spacing()

    content = QWidget(page)
    content.setObjectName("fieldsContent")
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom(),
    )
    content_layout.setSpacing(spacing)

    # Moving a QLayoutItem alone does not reliably transfer QObject ownership
    # of its widget in Qt. Explicitly reparent widgets to the scroll content so
    # every visible control is genuinely clipped/scrolled by the QScrollArea.
    while outer.count():
        item = outer.takeAt(0)
        if item is None:
            continue

        widget = item.widget()
        if widget is not None:
            widget.setParent(content)
            content_layout.addWidget(widget)
            continue

        child_layout = item.layout()
        if child_layout is not None:
            content_layout.addLayout(child_layout)
            continue

        content_layout.addItem(item)

    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    scroll = QScrollArea(page)
    scroll.setObjectName("fieldsScroll")
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(content)
    outer.addWidget(scroll)

    page.table.setMinimumHeight(max(page.table.minimumHeight(), 260))


def _install_fields_scroll_fix() -> None:
    original_init = FieldsPage.__init__

    def init_with_scroll(self, db) -> None:
        original_init(self, db)
        _make_fields_page_scrollable(self)

    FieldsPage.__init__ = init_with_scroll


def install_alpha2_step4_ui() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    _install_standard_dialog_ampersand_fix()
    _install_plant_protection_combo_fix()
    _install_data_quality_card_fix()
    _install_data_export_checkbox_fix()
    _install_fields_scroll_fix()
    _INSTALLED = True
