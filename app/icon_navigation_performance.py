from __future__ import annotations

import weakref

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QListWidget,
    QStackedWidget,
    QTabWidget,
    QToolBox,
)

from . import icon_theme, main_window


_INSTALLED = False


class _ScopedIconScheduler(QObject):
    """Coalesce navigation icon refreshes and keep them inside their container."""

    def __init__(self, root) -> None:
        super().__init__(root)
        self.root = root
        self._pending: dict[tuple[int, int], weakref.ReferenceType] = {}

    def schedule(self, target, delay: int = 0) -> None:
        if not icon_theme._is_alive(target):
            return
        key = (id(target), int(delay))
        if key in self._pending:
            return
        self._pending[key] = weakref.ref(target)

        def run() -> None:
            target_ref = self._pending.pop(key, None)
            current = target_ref() if target_ref is not None else None
            if icon_theme._is_alive(current):
                icon_theme.apply_icon_theme(current)

        QTimer.singleShot(delay, run)


def _connect_scoped_navigation(root, scheduler: _ScopedIconScheduler) -> None:
    """Refresh only the navigation container that actually changed.

    The old wiring scheduled a full MainWindow icon pass for every stack/tab
    currentChanged signal and repeated the same work again 120 ms later. During
    first Records load that produced many redundant full-tree scans. Keeping the
    refresh on the emitting container preserves late/lazy icon coverage while
    avoiding unrelated pages elsewhere in the window.
    """
    for stack in root.findChildren(QStackedWidget):
        stack.currentChanged.connect(
            lambda _i, s=stack, q=scheduler: q.schedule(s, 0)
        )
        stack.currentChanged.connect(
            lambda _i, s=stack, q=scheduler: q.schedule(s, 120)
        )

    for tabs in root.findChildren(QTabWidget):
        tabs.currentChanged.connect(
            lambda _i, t=tabs, q=scheduler: q.schedule(t, 0)
        )
        tabs.currentChanged.connect(
            lambda _i, t=tabs, q=scheduler: q.schedule(t, 120)
        )

    for toolbox in root.findChildren(QToolBox):
        toolbox.currentChanged.connect(
            lambda _i, t=toolbox, q=scheduler: q.schedule(t, 0)
        )

    # Category-list and generic button changes can affect navigation outside the
    # emitting widget, so retain root coverage there. They are also coalesced.
    for lst in root.findChildren(QListWidget):
        lst.currentRowChanged.connect(
            lambda _i, r=root, q=scheduler: q.schedule(r, 0)
        )
        lst.currentRowChanged.connect(
            lambda _i, r=root, q=scheduler: q.schedule(r, 120)
        )

    for button in root.findChildren(QAbstractButton):
        button.clicked.connect(
            lambda _checked=False, r=root, q=scheduler: q.schedule(r, 80)
        )


def _install_icon_theme_scoped(root) -> None:
    """Install the existing icon theme with scoped/coalesced navigation refreshes."""
    icon_theme.apply_icon_theme(root)

    # Preserve the established startup safety passes. The measured Records delay
    # did not originate from these timers, and they protect startup timing races.
    for delay in (0, 50, 150, 350, 750, 1500, 3000, 5000, 8000):
        icon_theme._schedule_apply(root, delay)

    filt = icon_theme._LazyIconFilter(root)
    root._mastixa_icon_filter = filt
    app = QApplication.instance()
    if app is not None:
        app.installEventFilter(filt)
    else:
        root.installEventFilter(filt)

    scheduler = _ScopedIconScheduler(root)
    root._mastixa_icon_navigation_scheduler = scheduler
    _connect_scoped_navigation(root, scheduler)


def install_scoped_icon_navigation() -> None:
    """Patch MainWindow icon installation before the window is constructed."""
    global _INSTALLED
    if _INSTALLED:
        return

    # main_window imports install_icon_theme directly, so update both references.
    icon_theme.install_icon_theme = _install_icon_theme_scoped
    main_window.install_icon_theme = _install_icon_theme_scoped
    _INSTALLED = True
