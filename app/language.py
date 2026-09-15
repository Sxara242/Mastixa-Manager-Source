from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QObject, QTimer, Signal, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QDoubleSpinBox,
    QTabWidget,
    QTableWidget,
    QTextEdit,
    QPlainTextEdit,
    QTreeWidget,
    QWidget,
)

from .profile_manager import ProfileManager
from .app_logging import get_logger


LOCALES_DIR = Path(__file__).resolve().parent / "locales"
DEFAULT_LANGUAGE = "el"
COMBO_SOURCE_ROLE = int(Qt.ItemDataRole.UserRole) + 97
logger = get_logger(__name__)


@dataclass(frozen=True)
class LanguagePack:
    code: str
    native_name: str
    translations: dict[str, str]


def _has_greek(text: str) -> bool:
    return any(
        0x0370 <= ord(character) <= 0x03FF
        or 0x1F00 <= ord(character) <= 0x1FFF
        for character in text
    )


class LanguageController(QObject):
    """Lightweight, extensible live translation for the complete Qt UI.

    Greek source text is retained on each widget. Language packs only contain
    translations, so adding another language is a data-only change. Values
    entered by users and table body cells are deliberately left untouched.
    """

    language_changed = Signal(str)

    def __init__(self, app, profiles: ProfileManager) -> None:
        super().__init__(app)
        self.app = app
        self.profiles = profiles
        previous = getattr(app, "_mastixa_language_controller", None)
        if previous is not None and previous is not self:
            app.removeEventFilter(previous)
            previous._enabled = False
        app._mastixa_language_controller = self
        self._enabled = True
        self._packs = self._load_packs()
        saved = profiles.active_profile.language
        self._language = saved if saved in self._packs else DEFAULT_LANGUAGE
        self._cache: dict[tuple[str, str], str] = {}
        self._applying = False
        self._pending: set[int] = set()
        app.installEventFilter(self)

    @property
    def language(self) -> str:
        return self._language

    def available_languages(self) -> tuple[LanguagePack, ...]:
        return tuple(self._packs.values())

    def native_name(self, code: str | None = None) -> str:
        pack = self._packs.get(code or self._language)
        return pack.native_name if pack else code or DEFAULT_LANGUAGE

    def translate(self, source: Any) -> str:
        text = "" if source is None else str(source)
        if self._language == DEFAULT_LANGUAGE or not text:
            return text
        cache_key = (self._language, text)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        pack = self._packs[self._language]
        translated = pack.translations.get(text)
        if translated is None and _has_greek(text):
            translated = self._translate_fragments(text, pack.translations)
        if translated is None:
            translated = text
        self._cache[cache_key] = translated
        return translated

    def translate_exact(self, source: Any) -> str:
        """Translate a selectable item without touching possible user data."""
        text = "" if source is None else str(source)
        if self._language == DEFAULT_LANGUAGE or not text:
            return text
        return self._packs[self._language].translations.get(text, text)

    def set_language(self, language: str, persist: bool = True) -> None:
        language = str(language).casefold()
        if language not in self._packs:
            language = DEFAULT_LANGUAGE
        if language == self._language:
            return
        previous_language = self._language
        self._language = language
        self._cache.clear()
        if persist:
            self.profiles.set_language(
                self.profiles.active_profile.id,
                language,
            )
        self._applying = True
        windows = list(self.app.topLevelWidgets())
        for window in windows:
            window.setUpdatesEnabled(False)
        try:
            for window in windows:
                self.apply_to(window)
        finally:
            for window in windows:
                window.setUpdatesEnabled(True)
                window.update()
            self._applying = False
        self.language_changed.emit(language)
        logger.info(
            "Language changed from %s to %s",
            previous_language,
            language,
        )

    def sync_active_profile(self) -> None:
        requested = self.profiles.active_profile.language
        self.set_language(requested, persist=False)

    def apply_to(self, root: QWidget) -> None:
        self._translate_widget(root)
        for widget in root.findChildren(QWidget):
            self._translate_widget(widget)
        for action in root.findChildren(QAction):
            self._translate_action(action)

    def eventFilter(self, watched, event):
        if not self._enabled:
            return False
        if isinstance(watched, QWidget) and event.type() in {
            QEvent.Type.Show,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._schedule(watched)
        return False

    def _schedule(self, widget: QWidget) -> None:
        if self._applying:
            return
        identity = id(widget)
        if identity in self._pending:
            return
        self._pending.add(identity)
        QTimer.singleShot(0, lambda w=widget, key=identity: self._apply_pending(w, key))

    def _apply_pending(self, widget: QWidget, identity: int) -> None:
        self._pending.discard(identity)
        try:
            self.apply_to(widget)
        except RuntimeError:
            # A short-lived dialog may already have been deleted.
            return

    def _translate_fragments(
        self,
        text: str,
        translations: dict[str, str],
    ) -> str | None:
        result = text
        changed = False
        # Longest phrases win. Short fragments are intentionally included for
        # dynamic labels such as "Ενεργό προφίλ · Βάση: <path>".
        for source, target in sorted(
            translations.items(), key=lambda item: len(item[0]), reverse=True
        ):
            # Help tooltips contain escaped text inside a rich-text wrapper.
            # Match that representation and keep translated content escaped too.
            if text.startswith("<"):
                source, target = html.escape(source), html.escape(target)
            if len(source) < 3 or source not in result:
                continue
            result = result.replace(source, target)
            changed = True
        return result if changed else None

    def _translated_property(
        self,
        owner: QObject,
        key: str,
        current: str,
    ) -> str:
        state = getattr(owner, "_mastixa_i18n_state", None)
        if state is None:
            state = {}
            owner._mastixa_i18n_state = state
        previous = state.get(key)
        if previous is None or current != previous[1]:
            source = current
        else:
            source = previous[0]
        rendered = self.translate(source)
        state[key] = (source, rendered)
        return rendered

    def _set_text_property(
        self,
        owner: QObject,
        key: str,
        getter,
        setter,
    ) -> None:
        current = getter()
        rendered = self._translated_property(owner, key, current)
        if rendered != current:
            setter(rendered)

    def _translate_widget(self, widget: QWidget) -> None:
        self._set_text_property(
            widget, "windowTitle", widget.windowTitle, widget.setWindowTitle
        )
        self._set_text_property(widget, "toolTip", widget.toolTip, widget.setToolTip)
        self._set_text_property(
            widget, "statusTip", widget.statusTip, widget.setStatusTip
        )
        self._set_text_property(
            widget, "whatsThis", widget.whatsThis, widget.setWhatsThis
        )
        self._set_text_property(
            widget,
            "accessibleName",
            widget.accessibleName,
            widget.setAccessibleName,
        )
        self._set_text_property(
            widget,
            "accessibleDescription",
            widget.accessibleDescription,
            widget.setAccessibleDescription,
        )

        if isinstance(widget, (QLabel, QAbstractButton)) and not widget.property(
            "mastixaI18nSkipText"
        ):
            self._set_text_property(widget, "text", widget.text, widget.setText)
        if isinstance(widget, QGroupBox):
            self._set_text_property(widget, "title", widget.title, widget.setTitle)
        if isinstance(widget, QLineEdit):
            self._set_text_property(
                widget,
                "placeholder",
                widget.placeholderText,
                widget.setPlaceholderText,
            )
            if widget.isReadOnly() and widget.property("mastixaI18nStaticText"):
                self._set_text_property(
                    widget, "readOnlyText", widget.text, widget.setText
                )
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            self._set_text_property(
                widget,
                "placeholder",
                widget.placeholderText,
                widget.setPlaceholderText,
            )
            if widget.property("mastixaI18nStaticText"):
                self._set_text_property(
                    widget,
                    "plainText",
                    widget.toPlainText,
                    widget.setPlainText,
                )
        if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            self._set_text_property(widget, "prefix", widget.prefix, widget.setPrefix)
            self._set_text_property(widget, "suffix", widget.suffix, widget.setSuffix)
            self._set_text_property(
                widget,
                "specialValueText",
                widget.specialValueText,
                widget.setSpecialValueText,
            )
        if isinstance(widget, QTabWidget):
            self._translate_tabs(widget)
        if isinstance(widget, QComboBox):
            self._translate_combo(widget)
        if isinstance(widget, QListWidget):
            self._translate_list(widget)
        if isinstance(widget, QTableWidget):
            self._translate_table_headers(widget)
        if isinstance(widget, QTreeWidget):
            self._translate_tree_header(widget)
        if isinstance(widget, QMessageBox):
            self._set_text_property(widget, "messageText", widget.text, widget.setText)
            self._set_text_property(
                widget,
                "informativeText",
                widget.informativeText,
                widget.setInformativeText,
            )
            self._set_text_property(
                widget,
                "detailedText",
                widget.detailedText,
                widget.setDetailedText,
            )

    def _translate_action(self, action: QAction) -> None:
        self._set_text_property(action, "text", action.text, action.setText)
        self._set_text_property(action, "toolTip", action.toolTip, action.setToolTip)
        self._set_text_property(action, "statusTip", action.statusTip, action.setStatusTip)

    def _collection_source(
        self,
        owner: QObject,
        group: str,
        key: int,
        current: str,
        exact_only: bool = False,
    ) -> str:
        state = getattr(owner, "_mastixa_i18n_collections", None)
        if state is None:
            state = {}
            owner._mastixa_i18n_collections = state
        values = state.setdefault(group, {})
        previous = values.get(key)
        source = current if previous is None or current != previous[1] else previous[0]
        rendered = (
            self.translate_exact(source)
            if exact_only
            else self.translate(source)
        )
        values[key] = (source, rendered)
        return rendered

    def _translate_tabs(self, tabs: QTabWidget) -> None:
        for index in range(tabs.count()):
            current = tabs.tabText(index)
            rendered = self._collection_source(tabs, "tabs", index, current)
            if rendered != current:
                tabs.setTabText(index, rendered)
            tooltip = tabs.tabToolTip(index)
            rendered_tip = self._collection_source(
                tabs, "tabTips", index, tooltip
            )
            if rendered_tip != tooltip:
                tabs.setTabToolTip(index, rendered_tip)

    def _translate_combo(self, combo: QComboBox) -> None:
        if combo.property("mastixaI18nSkipItems") or (
            combo.isEditable()
            and not combo.property("mastixaI18nStaticItems")
        ):
            return
        for index in range(combo.count()):
            # Integer IDs identify database records, whose names are user data.
            # Explicit static enums may also have numeric IDs and opt in.
            if isinstance(combo.itemData(index), int) and not combo.property(
                "mastixaI18nStaticItems"
            ):
                continue
            current = combo.itemText(index)
            stored_source = combo.itemData(index, COMBO_SOURCE_ROLE)
            if stored_source is not None:
                state = getattr(combo, "_mastixa_i18n_collections", {})
                state.setdefault("items", {})[index] = (
                    str(stored_source),
                    current,
                )
            rendered = self._collection_source(
                combo, "items", index, current, exact_only=True
            )
            if rendered != current:
                if stored_source is None:
                    state = getattr(combo, "_mastixa_i18n_collections", {})
                    source = state.get("items", {}).get(index, (current, current))[0]
                    combo.setItemData(index, source, COMBO_SOURCE_ROLE)
                combo.setItemText(index, rendered)

    def _translate_list(self, listing: QListWidget) -> None:
        for index in range(listing.count()):
            item = listing.item(index)
            current = item.text()
            rendered = self._collection_source(
                listing, "items", index, current, exact_only=True
            )
            if rendered != current:
                item.setText(rendered)
            tooltip = item.toolTip()
            rendered_tip = self._collection_source(
                listing, "itemTips", index, tooltip
            )
            if rendered_tip != tooltip:
                item.setToolTip(rendered_tip)

    def _translate_table_headers(self, table: QTableWidget) -> None:
        for group, count, getter in (
            ("horizontalHeaders", table.columnCount(), table.horizontalHeaderItem),
            ("verticalHeaders", table.rowCount(), table.verticalHeaderItem),
        ):
            for index in range(count):
                item = getter(index)
                if item is None:
                    continue
                current = item.text()
                rendered = self._collection_source(table, group, index, current)
                if rendered != current:
                    item.setText(rendered)

    def _translate_tree_header(self, tree: QTreeWidget) -> None:
        header = tree.headerItem()
        if header is None:
            return
        for index in range(tree.columnCount()):
            current = header.text(index)
            rendered = self._collection_source(tree, "treeHeaders", index, current)
            if rendered != current:
                header.setText(index, rendered)

    @staticmethod
    def _load_packs() -> dict[str, LanguagePack]:
        packs = {
            DEFAULT_LANGUAGE: LanguagePack(DEFAULT_LANGUAGE, "Ελληνικά", {})
        }
        if not LOCALES_DIR.is_dir():
            return packs
        for path in sorted(LOCALES_DIR.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                metadata = payload["meta"]
                code = str(metadata["code"]).casefold()
                native_name = str(metadata["native_name"]).strip()
                translations = payload["translations"]
                if (
                    not code.isalpha()
                    or not 2 <= len(code) <= 8
                    or not native_name
                    or not isinstance(translations, dict)
                ):
                    continue
                clean = {
                    str(source): str(target)
                    for source, target in translations.items()
                    if str(source) and str(target)
                }
                existing = packs.get(code)
                if existing is not None:
                    merged = dict(existing.translations)
                    merged.update(clean)
                    clean = merged
                packs[code] = LanguagePack(code, native_name, clean)
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return packs


_active_controller: LanguageController | None = None


def install_language_controller(controller: LanguageController) -> None:
    global _active_controller
    _active_controller = controller


def tr(source: Any) -> str:
    """Translate non-widget output such as exports and generated reports."""
    if _active_controller is None:
        return "" if source is None else str(source)
    return _active_controller.translate(source)


def combo_source_text(combo: QComboBox) -> str:
    """Return the stable source value behind a translated combo label."""
    index = combo.currentIndex()
    if index < 0:
        return combo.currentText()
    source = combo.itemData(index, COMBO_SOURCE_ROLE)
    return str(source) if source is not None else combo.currentText()
