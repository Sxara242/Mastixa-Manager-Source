from __future__ import annotations

from PySide6.QtCore import QEvent, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractButton,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import appearance_theme, icon_theme, main_window
from .language import LanguageController
from .settings import SettingsPage


PUBLIC_SOURCE_URL = "https://github.com/Sxara242/Mastixa-Manager-Source"
LICENSE_URL = (
    "https://github.com/Sxara242/Mastixa-Manager-Source/blob/main/LICENSE"
)
_BASE_SOURCE_LICENSE_TAB = SettingsPage._build_open_source_tab

_INSTALLED = False
_PAGE_ICON_INITIALIZED_ATTR = "_mastixa_alpha2_icon_theme_initialized"

# Alpha 2 pages were appended after the original icon catalogue was built.
# Keep these aliases exact-only so they cannot leak into unrelated action buttons.
# Prefer a distinct existing asset when an appended page is shown next to a parent
# category/page that already owns the semantically closest icon. This avoids the
# visually confusing duplicate artwork reported in the alpha.2 manual test.
_ALPHA2_EXACT_ICON_ALIASES = {
    "products.png": (
        "Προϊόντα και καλλιέργειες",
        "Προϊόντα & καλλιέργειες",
        "Products and crops",
        "Products & crops",
    ),
    "calendar.png": (
        "Πρόγραμμα Καλλιέργειας",
        "Cultivation Program",
    ),
    "field_profile.png": (
        "Μεμονωμένα Φυτά / Δέντρα",
        "Μεμονωμένα Φυτά & Δέντρα",
        "Individual Plants / Trees",
        "Individual Plants & Trees",
    ),
    "settings.png": (
        "Αισθητήρες / API",
        "Sensors / API",
    ),
    "package_preview.png": (
        "Εξαγωγή Δεδομένων",
        "Data Export",
    ),
    "reports.png": (
        "Ιστορικό Ενεργειών",
        "Action History",
        "Audit Log",
    ),
    "sales.png": (
        "Αναφορά Πωλήσεων & Stock",
        "Πωλήσεις & Stock",
        "Sales & Stock Report",
        "Sales & Stock",
    ),
    "warehouse.png": (
        "Αναφορά Αποθήκης & Αξίας Stock",
        "Αποθήκη & Αξία Stock",
        "Inventory & Stock Value Report",
        "Inventory & Stock Value",
    ),
    "data_quality.png": (
        "Έλεγχος & Δεδομένα",
        "Checks & Data",
    ),
}


def _literal_ampersands(text: str) -> str:
    """Escape mnemonic ampersands once so Qt renders a literal '&'."""
    if "&" not in text:
        return text

    output: list[str] = []
    index = 0
    while index < len(text):
        character = text[index]
        if character != "&":
            output.append(character)
            index += 1
            continue

        if index + 1 < len(text) and text[index + 1] == "&":
            output.append("&&")
            index += 2
        else:
            output.append("&&")
            index += 1
    return "".join(output)


def _install_ampersand_rendering() -> None:
    original_impl = icon_theme._apply_icon_theme_impl

    def apply_with_literal_ampersands(root) -> int:
        # QAbstractButton/QTabBar treat '&' as a mnemonic marker. Mastixa uses
        # '&' as ordinary visible punctuation, so escape it only for rendering.
        for button in root.findChildren(QAbstractButton):
            rendered = _literal_ampersands(button.text())
            if rendered != button.text():
                button.setText(rendered)

        for tabs in root.findChildren(QTabWidget):
            for tab_index in range(tabs.count()):
                current = tabs.tabText(tab_index)
                rendered = _literal_ampersands(current)
                if rendered != current:
                    tabs.setTabText(tab_index, rendered)

        # Cover direct tab bars that are not owned by a QTabWidget.
        for bar in root.findChildren(QTabBar):
            for tab_index in range(bar.count()):
                current = bar.tabText(tab_index)
                rendered = _literal_ampersands(current)
                if rendered != current:
                    bar.setTabText(tab_index, rendered)

        return original_impl(root)

    icon_theme._apply_icon_theme_impl = apply_with_literal_ampersands

    # Language packs are loaded after this patch is installed. Add escaped
    # source/target variants so live Greek <-> English switching keeps working
    # after the visible controls have been mnemonic-escaped.
    original_load_packs = LanguageController._load_packs

    @staticmethod
    def load_packs_with_literal_ampersands():
        packs = original_load_packs()
        for code, pack in tuple(packs.items()):
            if code == "el":
                continue
            translations = dict(pack.translations)
            for source, target in tuple(pack.translations.items()):
                if "&" not in source and "&" not in target:
                    continue
                translations.setdefault(
                    _literal_ampersands(source),
                    _literal_ampersands(target),
                )
            packs[code] = type(pack)(pack.code, pack.native_name, translations)
        return packs

    LanguageController._load_packs = load_packs_with_literal_ampersands


def _install_alpha2_icon_aliases() -> None:
    for filename, labels in _ALPHA2_EXACT_ICON_ALIASES.items():
        path = icon_theme._ICON_DIR / filename
        for label in labels:
            icon_theme._EXACT[icon_theme._norm(label)] = path


def _apply_themed_tab_icons(tabs: QTabWidget) -> int:
    """Replace legacy Qt file placeholders using the actual visible tab label."""
    if tabs.property("mastixaHiddenNavigation"):
        return 0
    changed = 0
    for tab_index in range(tabs.count()):
        themed = icon_theme._icon_for_text(tabs.tabText(tab_index))
        if themed is None:
            continue
        tabs.setTabIcon(tab_index, themed)
        changed += 1
    return changed


def _install_deterministic_icon_coverage() -> None:
    """Cover appended/lazy pages without restoring expensive full-window passes.

    Extension pages are appended after the base MainWindow constructor. Resolve
    their themed icon by page label, then run a tiny post-build pass over only the
    tabs in the nested category that was just constructed. This guarantees that a
    legacy Qt SP_FileIcon cannot survive for a known label while keeping the work
    bounded to a handful of tabs instead of rescanning the whole MainWindow.

    Page-title artwork is still applied once, scoped to the page the first time it
    becomes current.
    """
    window_cls = main_window.MainWindow
    original_tab_icon_for_page = window_cls._tab_icon_for_page
    original_build_recording_tabs = window_cls._build_recording_tabs
    original_build_report_tabs = window_cls._build_report_tabs
    original_refresh_current_tab = window_cls._refresh_current_tab

    def tab_icon_for_page(self, page_index: int):
        if 0 <= page_index < len(self.pages):
            label = self.pages[page_index][0]
            themed = icon_theme._icon_for_text(label)
            if themed is not None:
                return themed
        return original_tab_icon_for_page(self, page_index)

    def build_recording_tabs(self) -> None:
        original_build_recording_tabs(self)
        for tabs in self._recording_group_tabs:
            _apply_themed_tab_icons(tabs)

    def build_report_tabs(self) -> None:
        original_build_report_tabs(self)
        for tabs in self._report_group_tabs:
            _apply_themed_tab_icons(tabs)

    def refresh_current_tab(self) -> None:
        original_refresh_current_tab(self)

        page_index = self._current_page_index()
        if page_index is None or not (0 <= page_index < len(self.pages)):
            return

        page = self.pages[page_index][1]
        if getattr(page, _PAGE_ICON_INITIALIZED_ATTR, False):
            return

        # Detached pages are not descendants of MainWindow until their category
        # is opened. A single page-local pass makes their title icon deterministic
        # without reintroducing a full-tree navigation scan.
        icon_theme.apply_icon_theme(page)
        setattr(page, _PAGE_ICON_INITIALIZED_ATTR, True)

    window_cls._tab_icon_for_page = tab_icon_for_page
    window_cls._build_recording_tabs = build_recording_tabs
    window_cls._build_report_tabs = build_report_tabs
    window_cls._refresh_current_tab = refresh_current_tab


def _install_dark_theme_repaint_fixes() -> None:
    # These selectors are more specific in the light base stylesheet than the
    # old generic dark rules, which left the irrigation content light. Match
    # their specificity explicitly in dark mode.
    appearance_theme.DARK_STYLESHEET += """
QScrollArea#activitiesScroll,
QScrollArea#activitiesScroll QWidget#qt_scrollarea_viewport,
QWidget#activitiesContent,
QWidget#dataExportContent,
QWidget#settingsContent {
    background: #171D21;
    color: #E7ECEF;
}
"""

    original_event_filter = appearance_theme.ThemeController.eventFilter

    def event_filter_without_light_flash(self, watched, event):
        if getattr(self, "_uses_scoped_styles", False):
            return original_event_filter(self, watched, event)
        if (
            self._theme == "dark"
            and not self._applying
            and event.type() == QEvent.Type.Show
            and isinstance(watched, QWidget)
        ):
            # Show is emitted after concrete widget construction. Applying the
            # converted local stylesheet synchronously prevents one light frame
            # from being painted before the old deferred timer runs.
            self._style_new_widget(watched)
        return False

    appearance_theme.ThemeController.eventFilter = event_filter_without_light_flash


def _build_source_license_tab(self: SettingsPage) -> None:
    # Keep the installed alpha wrapper's tab identity, using the canonical
    # AGPL/legal contents from SettingsPage instead of historical license text.
    _BASE_SOURCE_LICENSE_TAB(self)
    # Escaped at creation time because QTabBar uses '&' as a mnemonic marker.
    self.tabs.setTabText(self.tabs.count() - 1, "Κώδικας && Άδεια")


def _install_source_license_tab() -> None:
    SettingsPage._build_open_source_tab = _build_source_license_tab


def install_alpha2_ui_fixes() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    _install_alpha2_icon_aliases()
    _install_deterministic_icon_coverage()
    _install_dark_theme_repaint_fixes()
    _install_ampersand_rendering()
    _install_source_license_tab()
    _INSTALLED = True
