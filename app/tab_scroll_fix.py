from __future__ import annotations

from shiboken6 import isValid

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QTabBar, QTabWidget, QToolButton

from . import main_window


_INSTALLED = False
_RESIZE_REFRESH_DELAY_MS = 50
_BUTTON_SYNC_ATTR = "_mastixa_native_scroll_sync_connected"
_LEFT_PROXY_ATTR = "_mastixa_left_scroll_proxy"
_LEFT_PROXY_OBJECT_NAME = "MastixaLeftScrollProxy"


def _native_scroll_buttons(bar: QTabBar) -> tuple[QToolButton | None, QToolButton | None]:
    """Return Qt's private left/right tab scroll buttons without relying on order."""
    left = None
    right = None
    fallback: list[QToolButton] = []

    for button in bar.findChildren(QToolButton):
        if not isValid(button):
            continue
        if button.objectName() == _LEFT_PROXY_OBJECT_NAME:
            continue
        fallback.append(button)
        name = button.objectName().casefold()
        arrow = button.arrowType()
        if "scrollleft" in name or arrow == Qt.ArrowType.LeftArrow:
            left = button
        elif "scrollright" in name or arrow == Qt.ArrowType.RightArrow:
            right = button

    # Qt normally exposes ScrollLeftButton / ScrollRightButton. Keep a geometry
    # fallback for platform styles that use different private object names.
    visible = [button for button in fallback if button.isVisible()]
    if (left is None or right is None) and len(visible) >= 2:
        ordered = sorted(visible, key=lambda button: button.x())
        left = left or ordered[0]
        right = right or ordered[-1]

    return left, right


def _left_scroll_proxy(bar: QTabBar) -> QToolButton | None:
    proxy = getattr(bar, _LEFT_PROXY_ATTR, None)
    if proxy is not None and isValid(proxy):
        return proxy
    return None


def _click_native_left_scroll(bar: QTabBar) -> None:
    """Drive Qt's real left scroller from our guaranteed-clickable proxy."""
    if bar is None or not isValid(bar):
        return

    left, _right = _native_scroll_buttons(bar)
    if left is None or not isValid(left):
        return

    # The reported Windows build paints the native left button but does not
    # reliably deliver pointer events to it. Programmatic click() still uses
    # Qt's own private scroll connection, so the actual tab-offset behaviour
    # stays native instead of being reimplemented in application code.
    left.setEnabled(True)
    left.click()
    bar.update()


def _ensure_left_scroll_proxy(bar: QTabBar, left: QToolButton) -> QToolButton:
    proxy = _left_scroll_proxy(bar)
    if proxy is None:
        proxy = QToolButton(bar)
        proxy.setObjectName(_LEFT_PROXY_OBJECT_NAME)
        proxy.setArrowType(Qt.ArrowType.LeftArrow)
        proxy.setAutoRaise(False)
        proxy.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        proxy.setCursor(Qt.CursorShape.PointingHandCursor)
        proxy.setAccessibleName("Κύλιση καρτελών προς τα αριστερά")
        proxy.clicked.connect(lambda _checked=False, target=bar: _click_native_left_scroll(target))
        setattr(bar, _LEFT_PROXY_ATTR, proxy)

    proxy.setGeometry(left.geometry())
    proxy.setVisible(left.isVisible())
    proxy.setEnabled(left.isEnabled())
    proxy.raise_()

    # The proxy owns the pointer hit area. The native control remains visible
    # behind it and continues to provide Qt's private scrolling implementation.
    left.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    return proxy


def _sync_native_scroll_buttons(tabs: QTabWidget) -> None:
    """Keep native scroll buttons responsive and expose a reliable left hit target."""
    if tabs is None or not isValid(tabs):
        return
    bar = tabs.tabBar()
    if bar is None or not isValid(bar):
        return

    left, right = _native_scroll_buttons(bar)
    for button in (left, right):
        if button is None or not isValid(button):
            continue
        button.raise_()

        if not button.property(_BUTTON_SYNC_ATTR):
            button.setProperty(_BUTTON_SYNC_ATTR, True)

            def resync_after_click(_checked=False, target=tabs) -> None:
                QTimer.singleShot(0, lambda t=target: _sync_native_scroll_buttons(t))

            button.clicked.connect(resync_after_click)

    if bar.count() <= 0:
        proxy = _left_scroll_proxy(bar)
        if proxy is not None:
            proxy.hide()
        return

    # In the reported Windows/Qt failure the left button is painted but remains
    # non-responsive after the row scrolls right. Enable it whenever geometry
    # proves there is hidden content to the left, then place a real application
    # QToolButton over the exact native hit rectangle.
    if left is not None and isValid(left) and left.isVisible():
        first_rect = bar.tabRect(0)
        visible_left = left.geometry().right() + 1
        can_scroll_left = first_rect.left() < visible_left
        if can_scroll_left:
            left.setEnabled(True)
        proxy = _ensure_left_scroll_proxy(bar, left)
        proxy.setEnabled(can_scroll_left)
        proxy.setVisible(left.isVisible())
        proxy.raise_()
    else:
        proxy = _left_scroll_proxy(bar)
        if proxy is not None:
            proxy.hide()

    if right is not None and isValid(right) and right.isVisible():
        right.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        last_rect = bar.tabRect(bar.count() - 1)
        visible_right = right.geometry().left() - 1
        if last_rect.right() > visible_right:
            right.setEnabled(True)
            right.raise_()


def _refresh_tab_scroll_controls(tabs: QTabWidget) -> None:
    """Rebuild Qt's native tab scroller state after width/icon changes."""
    if tabs is None or not isValid(tabs):
        return

    bar = tabs.tabBar()
    if bar is None or not isValid(bar):
        return

    bar.setUsesScrollButtons(False)
    bar.setUsesScrollButtons(True)
    bar.updateGeometry()
    bar.update()
    _sync_native_scroll_buttons(tabs)


def _schedule_tab_scroll_refresh(tabs: QTabWidget) -> None:
    # Refresh once immediately after themed icons have changed tab widths, then
    # once on the next event-loop turn when the layout has its final geometry.
    # This touches only one tab bar; it is not a widget-tree/page scan.
    _refresh_tab_scroll_controls(tabs)

    def refresh_if_alive() -> None:
        if isValid(tabs):
            _refresh_tab_scroll_controls(tabs)

    QTimer.singleShot(0, refresh_if_alive)


def _known_tab_widgets(window) -> list[QTabWidget]:
    """Return Mastixa's navigation tab widgets without findChildren scans."""
    result: list[QTabWidget] = []
    seen: set[int] = set()

    candidates = [getattr(window, "tabs", None)]
    candidates.extend(getattr(window, "_recording_group_tabs", ()))
    candidates.extend(getattr(window, "_report_group_tabs", ()))

    for tabs in candidates:
        if tabs is None or not isValid(tabs):
            continue
        marker = id(tabs)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(tabs)
    return result


def _refresh_known_tab_scroll_controls(window) -> None:
    for tabs in _known_tab_widgets(window):
        _refresh_tab_scroll_controls(tabs)


def _schedule_resize_refresh(window) -> None:
    """Debounce resize refreshes so dragging the window stays cheap."""
    timer = getattr(window, "_mastixa_tab_scroll_resize_timer", None)
    if timer is None or not isValid(timer):
        timer = QTimer(window)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda w=window: _refresh_known_tab_scroll_controls(w))
        window._mastixa_tab_scroll_resize_timer = timer
    timer.start(_RESIZE_REFRESH_DELAY_MS)


def install_tab_scroll_fix() -> None:
    """Keep left/right overflow arrows responsive on every navigation tab row."""
    global _INSTALLED
    if _INSTALLED:
        return

    window_cls = main_window.MainWindow
    original_build_recording_tabs = window_cls._build_recording_tabs
    original_build_report_tabs = window_cls._build_report_tabs
    original_resize_event = window_cls.resizeEvent

    def build_recording_tabs(self) -> None:
        original_build_recording_tabs(self)
        _schedule_tab_scroll_refresh(self.tabs)
        for tabs in self._recording_group_tabs:
            _schedule_tab_scroll_refresh(tabs)

    def build_report_tabs(self) -> None:
        original_build_report_tabs(self)
        _schedule_tab_scroll_refresh(self.tabs)
        for tabs in self._report_group_tabs:
            _schedule_tab_scroll_refresh(tabs)

    def resize_event(self, event) -> None:
        original_resize_event(self, event)
        _schedule_resize_refresh(self)

    window_cls._build_recording_tabs = build_recording_tabs
    window_cls._build_report_tabs = build_report_tabs
    window_cls.resizeEvent = resize_event
    window_cls._alpha2_native_tab_scroll_fix = True
    _INSTALLED = True
