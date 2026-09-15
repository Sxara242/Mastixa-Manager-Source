from __future__ import annotations

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget

from . import appearance_theme, main_window
from .icon_navigation_performance import install_scoped_icon_navigation
from .icon_theme_performance import install_icon_theme_performance
from .ui_help import apply_help_tooltips


_INSTALLED = False
_THEME_GENERATION_ATTR = "_mastixa_theme_style_generation"
_HELP_INITIALIZED_ATTR = "_mastixa_context_help_initialized"


def _mark_theme_tree(controller, root: QWidget) -> None:
    """Remember that this widget tree was styled for the current theme pass."""
    generation = getattr(controller, "_mastixa_style_generation", 0)
    widgets = [root, *root.findChildren(QWidget)]
    for widget in widgets:
        setattr(widget, _THEME_GENERATION_ATTR, generation)


def install_navigation_performance() -> None:
    """Avoid repeated full-tree work when already-built pages are shown again.

    The desktop keeps its full dark-theme coverage. A full local-style scan still
    runs on every actual Light/Dark switch and for genuinely new widgets. Widgets
    that were already styled in the current theme generation are not rescanned on
    every QEvent.Show caused by category/tab navigation.

    Context help is still applied to every page once at startup. Later navigation
    rescans only the current page after its refresh, which preserves help for
    dynamically-created controls without walking every page in the application.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    # The global icon filter observes LayoutRequest/Resize so dynamically-created
    # pages receive icons. Make its title-icon pass idempotent before any window is
    # constructed, otherwise repeated size setters can feed those same events back
    # into another full icon/language pass.
    install_icon_theme_performance()

    # Navigation-specific icon refreshes are scoped to the stack/tab container
    # that changed and duplicate callbacks are coalesced. This keeps lazy-page
    # coverage without rescanning the whole MainWindow on every currentChanged.
    install_scoped_icon_navigation()

    theme_cls = appearance_theme.ThemeController
    original_set_theme = theme_cls.set_theme
    original_apply_local_styles = theme_cls._apply_local_styles
    original_event_filter = theme_cls.eventFilter
    original_style_new_widget = theme_cls._style_new_widget

    def set_theme(self, theme: str, persist: bool = True) -> None:
        normalized = "dark" if theme == "dark" else "light"
        if not self._applying and normalized != self._theme:
            self._mastixa_style_generation = (
                getattr(self, "_mastixa_style_generation", 0) + 1
            )
        original_set_theme(self, theme, persist=persist)

    def apply_local_styles(self, root: QWidget) -> None:
        original_apply_local_styles(self, root)
        _mark_theme_tree(self, root)

    def event_filter(self, watched, event):
        if (
            self._theme == "dark"
            and not self._applying
            and event.type() == QEvent.Type.Show
            and isinstance(watched, QWidget)
            and getattr(watched, _THEME_GENERATION_ATTR, -1)
            == getattr(self, "_mastixa_style_generation", 0)
        ):
            return False
        return original_event_filter(self, watched, event)

    def style_new_widget(self, widget: QWidget) -> None:
        if (
            self._theme == "dark"
            and not self._applying
            and getattr(widget, _THEME_GENERATION_ATTR, -1)
            == getattr(self, "_mastixa_style_generation", 0)
        ):
            return
        original_style_new_widget(self, widget)

    theme_cls.set_theme = set_theme
    theme_cls._apply_local_styles = apply_local_styles
    theme_cls.eventFilter = event_filter
    theme_cls._style_new_widget = style_new_widget

    window_cls = main_window.MainWindow
    original_apply_context_help = window_cls._apply_context_help

    def apply_context_help(self) -> None:
        if not getattr(self, _HELP_INITIALIZED_ATTR, False):
            original_apply_context_help(self)
            setattr(self, _HELP_INITIALIZED_ATTR, True)
            return

        page_index = self._current_page_index()
        if page_index is None:
            return
        apply_help_tooltips(self.pages[page_index][1])

    window_cls._apply_context_help = apply_context_help
    _INSTALLED = True
