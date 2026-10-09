"""Profile-local presentation preference using the existing settings store."""
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QLabel

from .localized_messages import _text

SETTING = "desktop_layout_mode"


def layout_mode(db):
    return "advanced" if db.get_app_setting(SETTING, "simple") == "advanced" else "simple"


def add_layout_preference(page):
    box = QGroupBox("Προβολή εφαρμογής", page)
    form = QFormLayout(box)
    combo = QComboBox(box)
    combo.setProperty("mastixaI18nSkipItems", True)
    combo.addItem("Απλή", "simple")
    combo.addItem("Προχωρημένη", "advanced")
    combo.setCurrentIndex(combo.findData(layout_mode(page.db)))
    form.addRow("Διάταξη αρχικής", combo)
    note = QLabel("Η προχωρημένη προβολή εμφανίζει περισσότερα χωράφια και λεπτομέρειες ιστορικού στην ίδια αρχική.")
    note.setWordWrap(True)
    form.addRow(note)
    page.tabs.widget(0).layout().insertWidget(0, box)
    page.layout_mode_combo = combo

    def labels(*_args):
        combo.setItemText(0, _text("Απλή"))
        combo.setItemText(1, _text("Προχωρημένη"))

    def changed():
        page.db.set_app_setting(SETTING, combo.currentData())
        home = getattr(page.window(), "farm_home", None)
        if home is not None:
            home.set_mode(combo.currentData())

    def refresh():
        mode = layout_mode(page.db)
        combo.blockSignals(True)
        combo.setCurrentIndex(combo.findData(mode))
        combo.blockSignals(False)
        home = getattr(page.window(), "farm_home", None)
        if home is not None:
            home.set_mode(mode)

    combo.currentIndexChanged.connect(changed)
    page.language.language_changed.connect(labels)
    page.refresh_layout_preference = refresh
    labels()
