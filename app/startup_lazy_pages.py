from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractSpinBox, QVBoxLayout, QWidget

from . import main_window as _main_window
from .icon_theme import apply_icon_theme
from .ui_help import apply_help_tooltips


_INSTALLED = False


class LazyPage(QWidget):
    """Create a page only when navigation first needs its contents."""

    def __init__(
        self,
        factory: Callable[..., QWidget],
        *args: Any,
        skip_first_navigation_refresh: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._factory = factory
        self._factory_args = args
        self._factory_kwargs = kwargs
        self._skip_first_navigation_refresh = skip_first_navigation_refresh
        self._loaded_page: QWidget | None = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    @property
    def is_loaded(self) -> bool:
        return self._loaded_page is not None

    def resolved_page(self) -> QWidget:
        return self.ensure_loaded()

    def ensure_loaded(self) -> QWidget:
        if self._loaded_page is not None:
            return self._loaded_page

        page = self._factory(*self._factory_args, **self._factory_kwargs)
        if not isinstance(page, QWidget):
            raise TypeError("Lazy page factory must return a QWidget")

        self._loaded_page = page
        self._layout.addWidget(page)
        self._prepare_loaded_page(page)
        self._on_loaded(page)
        return page

    def _prepare_loaded_page(self, page: QWidget) -> None:
        for spinbox in page.findChildren(QAbstractSpinBox):
            spinbox.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.NoButtons
            )

        apply_help_tooltips(page)

        window = self.window()
        language = getattr(window, "language", None)
        apply_language = getattr(language, "apply_to", None)
        if callable(apply_language):
            apply_language(page)

        # Apply only to the new subtree. The global icon event filter will also
        # update the parent tab icon without rescanning every unloaded page.
        apply_icon_theme(page)

    def _on_loaded(self, _page: QWidget) -> None:
        return

    def _call_page_method(self, name: str, *args: Any, **kwargs: Any):
        was_loaded = self._loaded_page is not None
        page = self.ensure_loaded()

        # Some mature pages already populate themselves inside __init__(). When
        # first navigation is what caused construction, immediately calling their
        # refresh/load method again repeats the same DB queries and table rebuilds
        # before the user sees the page. Skip only that duplicate first call;
        # every later navigation refresh keeps the original behaviour.
        if (
            not was_loaded
            and self._skip_first_navigation_refresh
            and name in {"refresh", "load"}
        ):
            return None

        method = getattr(page, name, None)
        if callable(method):
            return method(*args, **kwargs)
        return None

    def refresh(self, *args: Any, **kwargs: Any):
        return self._call_page_method("refresh", *args, **kwargs)

    def load(self, *args: Any, **kwargs: Any):
        return self._call_page_method("load", *args, **kwargs)

    def focus_search(self, *args: Any, **kwargs: Any):
        return self._call_page_method("focus_search", *args, **kwargs)


class LazySettingsPage(LazyPage):
    profile_switch_requested = Signal(str)

    def _on_loaded(self, page: QWidget) -> None:
        signal = getattr(page, "profile_switch_requested", None)
        if signal is not None:
            signal.connect(self.profile_switch_requested.emit)


def _lazy_constructor(
    factory: Callable[..., QWidget],
    *,
    settings_page: bool = False,
    skip_first_navigation_refresh: bool = False,
):
    wrapper = LazySettingsPage if settings_page else LazyPage

    def construct(*args: Any, **kwargs: Any) -> QWidget:
        return wrapper(
            factory,
            *args,
            skip_first_navigation_refresh=skip_first_navigation_refresh,
            **kwargs,
        )

    construct.__name__ = getattr(factory, "__name__", "LazyPageFactory")
    construct.__qualname__ = getattr(factory, "__qualname__", construct.__name__)
    return construct


def install_startup_lazy_pages() -> None:
    """Defer non-dashboard page constructors until their first navigation.

    MainWindow historically constructed every page before show(), including all
    reports and extension pages. This keeps stable page indices and navigation
    widgets but replaces those eager constructors with lightweight QWidget
    holders during each MainWindow construction. The real page is created once,
    on first refresh/load, and then cached for the window lifetime.
    """
    global _INSTALLED
    if _INSTALLED:
        return

    current = _main_window.MainWindow
    original_init = current.__init__

    base_page_names = (
        "ProducerPage",
        "FieldsPage",
        "ProductionPage",
        "MoneyPage",
        "DeclarationPage",
        "UploadCenterPage",
        "ReportsPage",
        "AuditPage",
        "DataQualityPage",
        "DataExportPage",
        "ActivitiesPage",
        "InventoryPage",
        "YearLockPage",
        "AlertsPage",
        "EquipmentPage",
        "PartnersPage",
        "InvoiceDocumentsPage",
        "PlantProtectionPage",
        "FieldFinancePage",
        "LaborPage",
        "GlobalSearchPage",
        "PlantingsPage",
        "FarmCalendarPage",
        "FieldProfilePage",
        "SalesPage",
        "SalesReportPage",
        "InventoryReportPage",
        "AnnualFarmReportPage",
        "ProductsPage",
        "SettingsPage",
    )

    # These two constructors already call refresh() before returning. They are
    # the first visible pages of the two heaviest nested categories, so an
    # immediate navigation refresh only duplicates their expensive first load.
    self_refreshing_first_pages = {"ProductionPage", "ReportsPage"}

    def init(self, *args: Any, **kwargs: Any) -> None:
        from . import crop_program_integration
        from . import plant_tracking_integration
        from . import sensor_view_integration

        patches: list[tuple[object, str, object]] = []

        def patch(
            module,
            name: str,
            *,
            settings_page: bool = False,
            skip_first_navigation_refresh: bool = False,
        ) -> None:
            factory = getattr(module, name)
            patches.append((module, name, factory))
            setattr(
                module,
                name,
                _lazy_constructor(
                    factory,
                    settings_page=settings_page,
                    skip_first_navigation_refresh=skip_first_navigation_refresh,
                ),
            )

        for name in base_page_names:
            patch(
                _main_window,
                name,
                settings_page=name == "SettingsPage",
                skip_first_navigation_refresh=name in self_refreshing_first_pages,
            )

        # These Phase 12/14/15 pages are appended by MainWindow subclasses after
        # the base constructor, so patch their module globals for the same call.
        patch(crop_program_integration, "CropProgramsPage")
        patch(plant_tracking_integration, "PlantTrackingPage")
        patch(sensor_view_integration, "SensorViewPage")

        try:
            original_init(self, *args, **kwargs)
        finally:
            for module, name, factory in reversed(patches):
                setattr(module, name, factory)

    current.__init__ = init
    current._phase16j_startup_lazy_pages = True
    _INSTALLED = True
