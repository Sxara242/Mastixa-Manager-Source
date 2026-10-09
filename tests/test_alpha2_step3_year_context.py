from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QScrollArea

from app import appearance_theme, main_window
from app.database import Database
from app.widgets import date_input
from app.year_context import (
    ACTIVE_WORKING_YEAR_KEY,
    active_working_year,
    begin_year_correction,
    correction_state,
    effective_working_year,
    finish_year_correction,
    initialize_year_context,
    is_year_physically_locked,
    is_year_write_blocked,
    set_active_working_year,
)
from app.year_context_ui import (
    CorrectionMutationGuard,
    EnhancedYearLockPage,
    YearContextBar,
)


class Alpha2Step3YearContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def make_db(self, root: Path) -> Database:
        return Database(root / "farm.db")

    @staticmethod
    def make_audit(db: Database) -> None:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TEXT NOT NULL,
                table_name TEXT NOT NULL,
                action TEXT NOT NULL,
                record_id TEXT NOT NULL DEFAULT '',
                details TEXT NOT NULL DEFAULT ''
            )
            """
        )

    @staticmethod
    def lock_year(db: Database, year: int, reason: str = "closed") -> None:
        # The production Year Lock page creates this additive table lazily.
        # Ensure the same schema path exists before the focused fixture writes.
        is_year_physically_locked(db, year)
        db.execute(
            """
            INSERT INTO year_locks(year,is_locked,locked_at,unlocked_at,reason)
            VALUES(?,1,CURRENT_TIMESTAMP,NULL,?)
            ON CONFLICT(year) DO UPDATE SET
                is_locked=1,locked_at=CURRENT_TIMESTAMP,unlocked_at=NULL,reason=excluded.reason
            """,
            (year, reason),
        )

    def test_active_working_year_is_persisted_per_profile_database(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = self.make_db(root)
            initialize_year_context(db)
            set_active_working_year(db, 2027, audit=False)
            self.assertEqual("2027", db.get_app_setting(ACTIVE_WORKING_YEAR_KEY))

            reopened = self.make_db(root)
            self.assertEqual(2027, active_working_year(reopened))
            self.assertEqual(2027, initialize_year_context(reopened))

    def test_correction_keeps_physical_lock_and_restores_active_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            self.make_audit(db)
            set_active_working_year(db, 2026, audit=False)
            self.lock_year(db, 2025)

            state = begin_year_correction(db, 2025, "Ξεχασμένο έξοδο")
            self.assertEqual(2025, state.year)
            self.assertEqual(2026, state.active_year)
            self.assertTrue(is_year_physically_locked(db, 2025))
            self.assertFalse(is_year_write_blocked(db, 2025))
            self.assertEqual(2025, effective_working_year(db))
            self.assertEqual(2026, active_working_year(db))

            audit = db.query_one(
                "SELECT details FROM audit_events WHERE table_name='year_context' ORDER BY id DESC LIMIT 1"
            )
            self.assertIsNotNone(audit)
            self.assertIn("Ξεχασμένο έξοδο", audit["details"])

            finish_year_correction(db)
            self.assertIsNone(correction_state(db))
            self.assertTrue(is_year_physically_locked(db, 2025))
            self.assertTrue(is_year_write_blocked(db, 2025))
            self.assertEqual(2026, effective_working_year(db))

    def test_restart_clears_temporary_correction_without_unlocking_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = self.make_db(root)
            set_active_working_year(db, 2028, audit=False)
            self.lock_year(db, 2024)
            begin_year_correction(db, 2024, "Correction")
            self.assertIsNotNone(correction_state(db))

            reopened = self.make_db(root)
            initialize_year_context(reopened, reset_temporary=True)
            self.assertIsNone(correction_state(reopened))
            self.assertEqual(2028, active_working_year(reopened))
            self.assertTrue(is_year_physically_locked(reopened, 2024))
            self.assertTrue(is_year_write_blocked(reopened, 2024))

    def test_new_entry_date_follows_effective_working_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2030, audit=False)
            initialize_year_context(db, reset_temporary=False)

            edit = date_input()
            try:
                self.assertEqual(2030, edit.date().year())
                edit.setDate(QDate.currentDate())
                self.assertEqual(2030, edit.date().year())
            finally:
                edit.deleteLater()

            self.lock_year(db, 2025)
            begin_year_correction(db, 2025, "Old invoice")
            correction_edit = date_input()
            try:
                self.assertEqual(2025, correction_edit.date().year())
            finally:
                correction_edit.deleteLater()
            finish_year_correction(db)

    def test_active_year_banner_uses_theme_styles_not_inline_light_colours(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2027, audit=False)
            bar = YearContextBar(db)
            try:
                self.assertEqual("active", bar.property("yearContextState"))
                self.assertEqual("", bar.styleSheet())

                selector = 'QFrame#yearContextBar[yearContextState="active"]'
                self.assertIn(selector, main_window.STYLESHEET)
                self.assertIn("#E8F1EC", main_window.STYLESHEET)
                self.assertIn(selector, appearance_theme.DARK_STYLESHEET)
                self.assertIn("#1F2B25", appearance_theme.DARK_STYLESHEET)

                # A normal refresh must not reintroduce the old inline mint style.
                bar.refresh()
                self.assertEqual("active", bar.property("yearContextState"))
                self.assertEqual("", bar.styleSheet())
            finally:
                bar.deleteLater()

    def test_year_lock_separates_unlocked_state_from_active_year_indicator(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2027, audit=False)
            page = EnhancedYearLockPage(db)
            try:
                self.assertEqual(6, page.table.columnCount())
                self.assertEqual("Ενεργό έτος", page.table.horizontalHeaderItem(5).text())

                rows = {}
                for row in range(page.table.rowCount()):
                    year_item = page.table.item(row, 0)
                    if year_item is not None:
                        rows[int(year_item.data(Qt.ItemDataRole.UserRole))] = row

                self.assertIn(2027, rows)
                self.assertIn(2028, rows)
                active_row = rows[2027]
                future_row = rows[2028]

                self.assertEqual("Ξεκλείδωτο", page.table.item(active_row, 1).text())
                self.assertEqual("✓", page.table.item(active_row, 5).text())
                self.assertEqual("", page.table.item(future_row, 5).text())
            finally:
                page.deleteLater()

    def test_year_lock_page_defaults_management_year_to_active_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2027, audit=False)
            page = EnhancedYearLockPage(db)
            try:
                self.assertIn(2028, page._available_years())
                self.assertEqual(2027, page.year.currentData())
            finally:
                page.deleteLater()

    def test_year_lock_page_has_page_level_vertical_scroll(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            page = EnhancedYearLockPage(db)
            try:
                self.assertIsInstance(page.page_scroll, QScrollArea)
                self.assertTrue(page.page_scroll.widgetResizable())
                self.assertIs(page.page_scroll.widget(), page.page_content)
                self.assertIs(page.page_content.layout(), page.content_layout)
                self.assertGreaterEqual(page.table.minimumHeight(), 260)
            finally:
                page.deleteLater()

    def test_year_lock_refresh_preserves_explicit_management_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2027, audit=False)
            page = EnhancedYearLockPage(db)
            try:
                index = page.year.findData(2028)
                self.assertGreaterEqual(index, 0)
                page.year.setCurrentIndex(index)
                page.refresh()
                self.assertEqual(2028, page.year.currentData())
            finally:
                page.deleteLater()

    def test_locking_active_year_can_advance_to_next_working_year(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2026, audit=False)
            page = EnhancedYearLockPage(db)
            try:
                index = page.year.findData(2026)
                self.assertGreaterEqual(index, 0)
                page.year.setCurrentIndex(index)
                page.reason.setText("Ολοκληρώθηκε η χρήση")

                with patch.object(
                    QMessageBox,
                    "warning",
                    return_value=QMessageBox.StandardButton.Yes,
                ), patch.object(
                    QMessageBox,
                    "question",
                    return_value=QMessageBox.StandardButton.Yes,
                ), patch.object(QMessageBox, "information", return_value=None), patch.object(
                    QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes,
                ):
                    page.lock_year()

                self.assertTrue(is_year_physically_locked(db, 2026))
                self.assertEqual(2027, active_working_year(db))
                self.assertIn(2027, page._available_years())
            finally:
                page.deleteLater()

    def test_locked_year_correction_requires_reason_and_is_session_only(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            db = self.make_db(Path(folder))
            set_active_working_year(db, 2026, audit=False)
            self.lock_year(db, 2025)
            page = EnhancedYearLockPage(db)
            try:
                index = page.year.findData(2025)
                self.assertGreaterEqual(index, 0)
                page.year.setCurrentIndex(index)
                page.correction_reason.setText("Ξεχασμένο παραστατικό")
                with patch.object(
                    QMessageBox,
                    "warning",
                    return_value=QMessageBox.StandardButton.Yes,
                ), patch.object(
                    QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes,
                ):
                    page.begin_correction()
                state = correction_state(db)
                self.assertIsNotNone(state)
                self.assertEqual(2025, state.year)
                self.assertEqual("Ξεχασμένο παραστατικό", state.reason)
                self.assertTrue(is_year_physically_locked(db, 2025))
            finally:
                finish_year_correction(db)
                page.deleteLater()

    def test_mutation_guard_recognizes_record_changes_not_navigation(self) -> None:
        self.assertTrue(CorrectionMutationGuard.is_mutating_text("Προσθήκη"))
        self.assertTrue(CorrectionMutationGuard.is_mutating_text("Αποθήκευση"))
        self.assertTrue(CorrectionMutationGuard.is_mutating_text("Διαγραφή"))
        self.assertTrue(CorrectionMutationGuard.is_mutating_text("Save"))
        self.assertFalse(CorrectionMutationGuard.is_mutating_text("Ακύρωση"))
        self.assertFalse(CorrectionMutationGuard.is_mutating_text("Μετάβαση"))
        self.assertFalse(CorrectionMutationGuard.is_mutating_text("Αποθήκευση ρυθμίσεων"))


if __name__ == "__main__":
    unittest.main()
