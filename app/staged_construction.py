"""One-shot secondary construction after a visible page's first paint."""
from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QAbstractSpinBox


def prepare_subtree(page, root):
    """Prepare new controls before exposing them, using the existing UI hooks."""
    from .icon_theme import apply_icon_theme
    from .ui_help import apply_help_tooltips
    for spin in root.findChildren(QAbstractSpinBox):
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    apply_help_tooltips(root)
    language = getattr(page.window(), "language", None)
    if language is not None:
        language.apply_to(root)
    apply_icon_theme(root)


class AfterFirstPaint(QObject):
    """Hide cancels pending work; a later visible paint retries it.

    The page owns the timer and filter, so deletion cancels both. The builder
    reads current state at execution, never a captured year/filter/data snapshot.
    """
    def __init__(self, page, build, *, viewport_limit=None):
        super().__init__(page)
        self.page = page
        self.builds = list(build) if isinstance(build, (tuple, list)) else [build]
        self.phase = 0
        self.viewport_limit = viewport_limit
        self.complete = False
        self.running = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish)
        page.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Hide:
            self.timer.stop()
        elif event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            if self.viewport_limit is not None and self.page.height() >= self.viewport_limit:
                self.finish_all()
        elif event.type() == QEvent.Type.Paint and not self.complete:
            # This callback cannot run until the paint event has returned.
            if not self.timer.isActive():
                self.timer.start(0)
        return False

    def finish(self):
        if self.complete or self.running or not self.page.isVisible():
            return
        self.timer.stop()
        self.running = True
        try:
            self.builds[self.phase]()
            self.phase += 1
            self.complete = self.phase == len(self.builds)
            if self.complete:
                self.page.removeEventFilter(self)
            else:
                # A second small section gets its own paint/event-loop turn.
                self.page.update()
        finally:
            self.running = False

    def finish_all(self, *_args):
        # A deliberate scroll must expose complete controls, never an empty slot.
        while not self.complete and self.page.isVisible() and not self.running:
            self.finish()
