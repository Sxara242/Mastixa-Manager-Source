from __future__ import annotations

from .main_window import MainWindow
from .version import APP_NAME, APP_VERSION
from .localized_messages import _text


_INSTALLED = False


def install_version_ui() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    original_init = MainWindow.__init__

    def init_with_canonical_version(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        profile = self.profile_manager.active_profile
        self.setProperty("mastixaI18nSkipWindowTitle", True)
        self.setWindowTitle(_text("{app} v{version} — {profile}", app=APP_NAME, version=APP_VERSION, profile=profile.name))

    MainWindow.__init__ = init_with_canonical_version
    _INSTALLED = True
