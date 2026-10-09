"""Scoped real language controller for presentation-dependent tests."""
from contextlib import contextmanager
from types import SimpleNamespace

from app import language


@contextmanager
def scoped_language(app, code):
    previous_global = language._active_controller
    had_controller = hasattr(app, "_mastixa_language_controller")
    previous_app = getattr(app, "_mastixa_language_controller", None)
    previous_enabled = getattr(previous_app, "_enabled", False)
    controller = language.LanguageController(
        app, SimpleNamespace(active_profile=SimpleNamespace(language=code))
    )
    language.install_language_controller(controller)
    try:
        yield controller
    finally:
        try:
            # Drain this controller's queued widget translations before restoring.
            app.processEvents()
        finally:
            app.removeEventFilter(controller)
            controller._enabled = False
            if had_controller:
                app._mastixa_language_controller = previous_app
            else:
                del app._mastixa_language_controller
            if previous_app is not None:
                previous_app._enabled = previous_enabled
                if previous_enabled:
                    app.installEventFilter(previous_app)
            language.install_language_controller(previous_global)
            controller.deleteLater()
