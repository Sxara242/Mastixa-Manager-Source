import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QDateEdit, QWidget

from app.date_preferences import (
    DEFAULT_DATE_FORMAT,
    apply_date_preferences,
    configure_date_edit,
    configure_recurring_month_day_edit,
    current_year_month_day,
    date_placeholder,
    format_iso_date,
    format_month_day,
    normalize_date_format,
    parse_user_date_to_iso,
    qt_date_format,
    qt_month_day_format,
)


class FakeDb:
    def __init__(self, value=DEFAULT_DATE_FORMAT):
        self.value = value

    def get_app_setting(self, key, default=""):
        return self.value or default


class DatePreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_supported_formats_and_safe_default(self):
        self.assertEqual("DD/MM/YYYY", normalize_date_format("DD/MM/YYYY"))
        self.assertEqual("MM/DD/YYYY", normalize_date_format("mm/dd/yyyy"))
        self.assertEqual("YYYY-MM-DD", normalize_date_format("yyyy-mm-dd"))
        self.assertEqual(DEFAULT_DATE_FORMAT, normalize_date_format("unexpected"))
        self.assertEqual("dd/MM/yyyy", qt_date_format("DD/MM/YYYY"))
        self.assertEqual("MM/dd/yyyy", qt_date_format("MM/DD/YYYY"))
        self.assertEqual("yyyy-MM-dd", qt_date_format("YYYY-MM-DD"))
        self.assertEqual("dd/MM", qt_month_day_format("DD/MM/YYYY"))
        self.assertEqual("MM/dd", qt_month_day_format("MM/DD/YYYY"))
        self.assertEqual("MM-dd", qt_month_day_format("YYYY-MM-DD"))

    def test_iso_storage_round_trip_uses_selected_display_format(self):
        for visible_format, shown in (
            ("DD/MM/YYYY", "17/09/2026"),
            ("MM/DD/YYYY", "09/17/2026"),
            ("YYYY-MM-DD", "2026-09-17"),
        ):
            with self.subTest(visible_format=visible_format):
                db = FakeDb(visible_format)
                self.assertEqual(shown, format_iso_date("2026-09-17", db))
                self.assertEqual("2026-09-17", parse_user_date_to_iso(shown, db))

    def test_optional_placeholder_follows_profile_format(self):
        self.assertEqual(
            "MM/DD/YYYY (προαιρετικό)",
            date_placeholder(FakeDb("MM/DD/YYYY"), optional=True),
        )

    def test_invalid_user_date_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_user_date_to_iso("31/02/2026", FakeDb("DD/MM/YYYY"))

    def test_full_qdateedit_uses_profile_format(self):
        edit = QDateEdit(QDate(2026, 9, 17))
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM/yyyy")
        configure_date_edit(edit, FakeDb("YYYY-MM-DD"))
        self.assertEqual("yyyy-MM-dd", edit.displayFormat())
        self.assertTrue(edit.calendarWidget().styleSheet())
        edit.deleteLater()

    def test_month_day_recurring_edit_keeps_day_month_only(self):
        edit = QDateEdit(current_year_month_day(2, 2))
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd/MM")
        edit.setProperty("mastixaMonthDayOnly", True)
        configure_date_edit(edit, FakeDb("YYYY-MM-DD"))
        self.assertEqual("MM-dd", edit.displayFormat())
        self.assertNotEqual(2000, edit.date().year())
        edit.deleteLater()

    def test_current_year_month_day_uses_one_leap_reference_year(self):
        value = current_year_month_day(2, 2)
        leap = current_year_month_day(2, 29)

        self.assertTrue(value.isValid())
        self.assertEqual(2, value.month())
        self.assertEqual(2, value.day())
        self.assertGreaterEqual(value.year(), QDate.currentDate().year())
        self.assertNotEqual(2000, value.year())

        self.assertTrue(leap.isValid())
        self.assertEqual(2, leap.month())
        self.assertEqual(29, leap.day())
        self.assertEqual(value.year(), leap.year())
        self.assertTrue(QDate(value.year(), 2, 29).isValid())

    def test_recurring_month_day_calendar_always_allows_february_29(self):
        edit = QDateEdit(QDate.currentDate())
        edit.setCalendarPopup(True)
        configure_recurring_month_day_edit(edit)
        try:
            reference_year = edit.minimumDate().year()
            self.assertEqual(reference_year, edit.maximumDate().year())
            self.assertTrue(QDate(reference_year, 2, 29).isValid())

            edit.setDate(QDate(reference_year, 2, 29))
            self.assertEqual(2, edit.date().month())
            self.assertEqual(29, edit.date().day())
            self.assertEqual("dd/MM", edit.displayFormat())
        finally:
            edit.deleteLater()

    def test_month_day_format_follows_profile_order(self):
        for visible_format, shown in (
            ("DD/MM/YYYY", "17/09"),
            ("MM/DD/YYYY", "09/17"),
            ("YYYY-MM-DD", "09-17"),
        ):
            with self.subTest(visible_format=visible_format):
                self.assertEqual(
                    shown,
                    format_month_day(9, 17, FakeDb(visible_format)),
                )

    def test_apply_date_preferences_updates_month_day_edits_live(self):
        root = QWidget()
        edit = QDateEdit(current_year_month_day(9, 17), root)
        edit.setCalendarPopup(True)
        edit.setProperty("mastixaMonthDayOnly", True)
        edit.setDisplayFormat("dd/MM")

        apply_date_preferences(root, FakeDb("MM/DD/YYYY"))
        self.assertEqual("MM/dd", edit.displayFormat())

        apply_date_preferences(root, FakeDb("YYYY-MM-DD"))
        self.assertEqual("MM-dd", edit.displayFormat())
        root.deleteLater()

    def test_apply_date_preferences_updates_all_full_date_edits(self):
        root = QWidget()
        first = QDateEdit(root)
        second = QDateEdit(root)
        first.setDisplayFormat("dd/MM/yyyy")
        second.setDisplayFormat("MM/dd/yyyy")
        count = apply_date_preferences(root, FakeDb("YYYY-MM-DD"))
        self.assertGreaterEqual(count, 2)
        self.assertEqual("yyyy-MM-dd", first.displayFormat())
        self.assertEqual("yyyy-MM-dd", second.displayFormat())
        root.deleteLater()


if __name__ == "__main__":
    unittest.main()
