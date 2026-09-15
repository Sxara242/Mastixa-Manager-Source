from __future__ import annotations

from .activities import ActivitiesPage
from .alerts import AlertsPage
from .audit import AuditPage
from .crop_programs import CropProgramsPage
from .dashboard import DashboardPage
from .data_export import DataExportPage
from .data_quality import DataQualityPage
from .declaration import DeclarationPage
from .equipment import EquipmentPage
from .field_finance import FieldFinancePage
from .field_profile import FieldProfilePage
from .fields import FieldsPage
from .global_search import GlobalSearchPage
from .farm_calendar import FarmCalendarPage
from .inventory import InventoryPage
from .inventory_report import InventoryReportPage
from .annual_report import AnnualFarmReportPage
from .invoice_documents import InvoiceDocumentsPage
from .labor import LaborPage
from .money import MoneyPage
from .partners import PartnersPage
from .plant_protection import PlantProtectionPage
from .plantings import PlantingsPage
from .producer import ProducerPage
from .production import ProductionPage
from .products import ProductsPage
from .settings import SettingsPage
from .reports import ReportsPage
from .sales import SalesPage
from .sales_report import SalesReportPage
from .upload_center import UploadCenterPage
from .year_lock import YearLockPage

__all__ = [
    "DashboardPage",
    "ProducerPage",
    "FieldsPage",
    "ProductionPage",
    "MoneyPage",
    "DeclarationPage",
    "UploadCenterPage",
    "ReportsPage",
    "AuditPage",
    "ActivitiesPage",
    "AlertsPage",
    "InventoryPage",
    "InventoryReportPage",
    "AnnualFarmReportPage",
    "EquipmentPage",
    "PartnersPage",
    "InvoiceDocumentsPage",
    "PlantProtectionPage",
    "FieldFinancePage",
    "FieldProfilePage",
    "SalesPage",
    "SalesReportPage",
    "LaborPage",
    "GlobalSearchPage",
    "FarmCalendarPage",
    "PlantingsPage",
    "CropProgramsPage",
    "DataQualityPage",
    "DataExportPage",
    "YearLockPage",
    "ProductsPage",
    "SettingsPage",
]
