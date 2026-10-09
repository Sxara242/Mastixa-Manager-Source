from __future__ import annotations

import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QAbstractSpinBox, QHeaderView

from app.crop_program import CropProgramRule, generate_crop_tasks
from app.crop_program_scheduling_ui import CropProgramsPage, RuleDialog
from app.crop_program_store import CropProgramStore
from app.database import Database


class Alpha2Step2SchedulingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def make_store(self, folder: str):
        db = Database(Path(folder) / "scheduling.db")
        field_id = db.execute(
            "INSERT INTO fields(name) VALUES(?)",
            ("Alpha 2 field",),
        )
        return CropProgramStore(db), field_id

    def test_two_year_pruning_window_needs_no_day_math(self):
        rule = CropProgramRule(
            id="prune",
            title="Pruning",
            category="pruning",
            schedule_kind="interval_window",
            start_month=2,
            start_day=2,
            end_month=2,
            end_day=7,
            within_period_unit="once",
            every_years=2,
            base_year=2027,
        )

        before = generate_crop_tasks("program", "field", 2026, [rule])
        first = generate_crop_tasks("program", "field", 2027, [rule])
        skipped = generate_crop_tasks("program", "field", 2028, [rule])
        next_cycle = generate_crop_tasks("program", "field", 2029, [rule])
        third_cycle = generate_crop_tasks("program", "field", 2031, [rule])

        self.assertEqual([], before)
        self.assertEqual(1, len(first))
        self.assertEqual("2027-02-02", first[0]["due_date"])
        self.assertEqual("2027-02-07", first[0]["window_end_date"])
        self.assertEqual([], skipped)
        self.assertEqual("2029-02-02", next_cycle[0]["due_date"])
        self.assertEqual("2029-02-07", next_cycle[0]["window_end_date"])
        self.assertEqual("2031-02-02", third_cycle[0]["due_date"])

    def test_rule_base_year_overrides_field_link_anchor(self):
        rule = CropProgramRule(
            id="prune",
            title="Pruning",
            category="pruning",
            schedule_kind="interval_window",
            start_month=2,
            start_day=2,
            end_month=2,
            end_day=7,
            within_period_unit="once",
            every_years=2,
            base_year=2027,
        )
        self.assertEqual(
            [],
            generate_crop_tasks(
                "program", "field", 2028, [rule], anchor_year=2026
            ),
        )
        generated = generate_crop_tasks(
            "program", "field", 2029, [rule], anchor_year=2026
        )
        self.assertEqual(["2029-02-02"], [row["due_date"] for row in generated])

    def test_february_29_fixed_date_skips_non_leap_and_reappears(self):
        rule = CropProgramRule(
            id="leap",
            title="Leap inspection",
            category="inspection",
            schedule_kind="fixed_date",
            month=2,
            day=29,
        )
        self.assertEqual([], generate_crop_tasks("program", "field", 2027, [rule]))
        leap = generate_crop_tasks("program", "field", 2028, [rule])
        self.assertEqual(["2028-02-29"], [row["due_date"] for row in leap])
        self.assertEqual([], generate_crop_tasks("program", "field", 2029, [rule]))
        next_leap = generate_crop_tasks("program", "field", 2032, [rule])
        self.assertEqual(["2032-02-29"], [row["due_date"] for row in next_leap])

    def test_month_frequency_handles_different_month_lengths(self):
        rule = CropProgramRule(
            id="monthly",
            title="Monthly check",
            category="inspection",
            schedule_kind="interval_window",
            start_month=1,
            start_day=31,
            end_month=4,
            end_day=30,
            within_period_unit="months",
            within_period_interval=1,
        )
        tasks = generate_crop_tasks("program", "field", 2027, [rule])
        self.assertEqual(
            ["2027-01-31", "2027-02-28", "2027-03-31", "2027-04-30"],
            [task["due_date"] for task in tasks],
        )

    def test_week_frequency_uses_exact_seven_day_intervals(self):
        rule = CropProgramRule(
            id="weekly",
            title="Weekly inspection",
            category="inspection",
            schedule_kind="interval_window",
            start_month=5,
            start_day=1,
            end_month=5,
            end_day=29,
            within_period_unit="weeks",
            within_period_interval=2,
        )
        tasks = generate_crop_tasks("program", "field", 2027, [rule])
        self.assertEqual(
            ["2027-05-01", "2027-05-15", "2027-05-29"],
            [task["due_date"] for task in tasks],
        )

    def test_week_frequency_round_trips_through_store(self):
        with tempfile.TemporaryDirectory() as folder:
            store, _field_id = self.make_store(folder)
            rule = CropProgramRule(
                id="weekly-store",
                title="Weekly stored",
                category="inspection",
                schedule_kind="interval_window",
                start_month=5,
                start_day=1,
                end_month=6,
                end_day=1,
                within_period_unit="weeks",
                within_period_interval=3,
            )
            store.save_program("weekly-program", "Weekly", [rule])
            loaded = store.program("weekly-program")["rules"][0]
            self.assertEqual("weeks", loaded.within_period_unit)
            self.assertEqual(3, loaded.within_period_interval)

    def test_field_link_keeps_original_anchor_across_years_and_program_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            store, field_id = self.make_store(folder)
            rule = CropProgramRule(
                id="prune",
                title="Pruning",
                category="pruning",
                schedule_kind="fixed_date",
                month=2,
                day=5,
                every_years=2,
            )
            store.save_program("program", "Program", [rule])

            self.assertEqual(
                1, len(store.generate_for_field("program", field_id, 2026))
            )
            link = store.field_link("program", field_id)
            self.assertIsNotNone(link)
            self.assertEqual(2026, link["start_year"])
            self.assertEqual(
                [], store.generate_for_field("program", field_id, 2027)
            )

            store.save_program(
                "program",
                "Program edited",
                [replace(rule, title="Pruning revised")],
            )
            generated = store.generate_for_field("program", field_id, 2028)
            self.assertEqual(1, len(generated))
            self.assertEqual("Pruning revised", generated[0]["title"])
            self.assertEqual(
                2026,
                store.field_link("program", field_id)["start_year"],
            )

    def test_base_year_is_additively_migrated_and_persisted(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "legacy.db")
            with db.connect() as con:
                con.execute(
                    """
                    CREATE TABLE crop_programs (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        crop TEXT NOT NULL DEFAULT '',
                        description TEXT NOT NULL DEFAULT '',
                        active INTEGER NOT NULL DEFAULT 1,
                        updated_at INTEGER NOT NULL
                    )
                    """
                )
                con.execute(
                    """
                    CREATE TABLE crop_program_rules (
                        program_id TEXT NOT NULL,
                        rule_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        category TEXT NOT NULL,
                        schedule_kind TEXT NOT NULL,
                        notes TEXT NOT NULL DEFAULT '',
                        month INTEGER,
                        day INTEGER,
                        start_month INTEGER,
                        start_day INTEGER,
                        end_month INTEGER,
                        end_day INTEGER,
                        every_days INTEGER,
                        within_period_unit TEXT,
                        within_period_interval INTEGER,
                        every_years INTEGER NOT NULL DEFAULT 1,
                        position INTEGER NOT NULL,
                        PRIMARY KEY(program_id, rule_id)
                    )
                    """
                )

            store = CropProgramStore(db)
            columns = {
                str(row["name"])
                for row in db.query("PRAGMA table_info(crop_program_rules)")
            }
            self.assertIn("base_year", columns)

            rule = CropProgramRule(
                id="base",
                title="Base year",
                category="pruning",
                schedule_kind="interval_window",
                start_month=2,
                start_day=2,
                end_month=2,
                end_day=7,
                within_period_unit="once",
                every_years=2,
                base_year=2027,
            )
            store.save_program("program", "Program", [rule])
            loaded = store.program("program")["rules"][0]
            self.assertEqual(2027, loaded.base_year)
            self.assertEqual(2, loaded.every_years)

    def test_rule_dialog_hides_irrelevant_schedule_fields(self):
        fixed = RuleDialog(
            rule=CropProgramRule(
                id="fixed",
                title="Fixed",
                category="inspection",
                schedule_kind="fixed_date",
                month=3,
                day=1,
            )
        )
        try:
            self.assertFalse(fixed.fixed_date.isHidden())
            self.assertTrue(fixed.start_date.isHidden())
            self.assertTrue(fixed.end_date.isHidden())
            self.assertTrue(fixed.within_period_unit.isHidden())
            self.assertTrue(fixed.every_days.isHidden())
            self.assertTrue(fixed.base_year.isHidden())
            self.assertTrue(fixed.every_years.isHidden())
        finally:
            fixed.deleteLater()

        interval = RuleDialog(
            rule=CropProgramRule(
                id="period",
                title="Window",
                category="pruning",
                schedule_kind="interval_window",
                start_month=2,
                start_day=2,
                end_month=2,
                end_day=7,
                within_period_unit="once",
                every_years=2,
                base_year=2027,
            )
        )
        try:
            self.assertTrue(interval.fixed_date.isHidden())
            self.assertFalse(interval.start_date.isHidden())
            self.assertFalse(interval.end_date.isHidden())
            self.assertFalse(interval.within_period_unit.isHidden())
            self.assertTrue(interval.every_days.isHidden())
            self.assertFalse(interval.base_year.isHidden())
            self.assertEqual(2027, interval.base_year.value())
            self.assertFalse(interval.every_years.isHidden())

            index = interval.within_period_unit.findData("days")
            interval.within_period_unit.setCurrentIndex(index)
            self.assertFalse(interval.every_days.isHidden())
            self.assertEqual(" ημέρα", interval.every_days.suffix())
        finally:
            interval.deleteLater()

    def test_interval_frequency_options_include_weeks_and_use_correct_suffixes(self):
        interval = RuleDialog(
            rule=CropProgramRule(
                id="frequency-ui",
                title="Frequency",
                category="inspection",
                schedule_kind="interval_window",
                start_month=5,
                start_day=1,
                end_month=9,
                end_day=30,
                within_period_unit="once",
                every_years=1,
            )
        )
        try:
            self.assertEqual(
                ["once", "days", "weeks", "months"],
                [
                    interval.within_period_unit.itemData(index)
                    for index in range(interval.within_period_unit.count())
                ],
            )
            self.assertEqual("Μία φορά", interval.within_period_unit.itemText(0))
            self.assertEqual("Εβδομάδες", interval.within_period_unit.itemText(2))

            for unit, singular, plural in (
                ("days", " ημέρα", " ημέρες"),
                ("weeks", " εβδομάδα", " εβδομάδες"),
                ("months", " μήνας", " μήνες"),
            ):
                with self.subTest(unit=unit):
                    interval.within_period_unit.setCurrentIndex(
                        interval.within_period_unit.findData(unit)
                    )
                    interval.every_days.setValue(1)
                    self.assertEqual(singular, interval.every_days.suffix())
                    interval.every_days.setValue(2)
                    self.assertEqual(plural, interval.every_days.suffix())

            interval.every_years.setValue(1)
            self.assertEqual(" έτος", interval.every_years.suffix())
            interval.every_years.setValue(2)
            self.assertEqual(" έτη", interval.every_years.suffix())
        finally:
            interval.deleteLater()

    def test_crop_program_year_controls_expose_visible_one_step_arrows(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "step-controls.db")
            page = CropProgramsPage(db)
            dialog = RuleDialog()
            try:
                controls = (
                    dialog.base_year,
                    dialog.every_years,
                    page.season_year,
                )
                for spin in controls:
                    with self.subTest(control=spin):
                        self.assertTrue(
                            bool(spin.property("mastixaCropStepControl"))
                        )
                        self.assertEqual(1, spin.singleStep())
                        self.assertEqual(
                            QAbstractSpinBox.ButtonSymbols.UpDownArrows,
                            spin.buttonSymbols(),
                        )
                        self.assertGreaterEqual(spin.minimumWidth(), 108)
            finally:
                dialog.deleteLater()
                page.deleteLater()

    def test_alpha2_rule_dialog_preserves_program_association_context(self):
        dialog = RuleDialog(
            program_name="Annual Mastic",
            default_category="pruning",
        )
        try:
            self.assertIn("Annual Mastic", dialog.windowTitle())
            self.assertEqual("pruning", dialog.category_combo.currentData())
        finally:
            dialog.deleteLater()

    def test_new_interval_rule_uses_working_year_as_base_year_default(self):
        previous = self.app.property("mastixaEffectiveWorkingYear")
        self.app.setProperty("mastixaEffectiveWorkingYear", 2033)
        dialog = RuleDialog()
        try:
            interval_index = dialog.schedule_combo.findData("interval_window")
            dialog.schedule_combo.setCurrentIndex(interval_index)
            self.assertEqual(2033, dialog.base_year.value())
        finally:
            if previous is None:
                self.app.setProperty("mastixaEffectiveWorkingYear", None)
            else:
                self.app.setProperty("mastixaEffectiveWorkingYear", previous)
            dialog.deleteLater()

    def test_rules_table_keeps_schedule_readable_and_resizable(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Database(Path(folder) / "rules-table.db")
            page = CropProgramsPage(db)
            try:
                page.rules = [
                    CropProgramRule(
                        id="long-schedule",
                        title="Long schedule",
                        category="inspection",
                        schedule_kind="interval_window",
                        start_month=1,
                        start_day=15,
                        end_month=12,
                        end_day=31,
                        within_period_unit="months",
                        within_period_interval=1,
                        every_years=3,
                        base_year=2027,
                    )
                ]
                page._render_rules()

                header = page.rules_table.horizontalHeader()
                for column in range(page.rules_table.columnCount()):
                    self.assertEqual(
                        QHeaderView.ResizeMode.Interactive,
                        header.sectionResizeMode(column),
                    )
                self.assertGreaterEqual(page.rules_table.columnWidth(2), 420)
                self.assertEqual(
                    Qt.ScrollBarPolicy.ScrollBarAsNeeded,
                    page.rules_table.horizontalScrollBarPolicy(),
                )

                schedule_item = page.rules_table.item(0, 2)
                self.assertIsNotNone(schedule_item)
                self.assertTrue(schedule_item.text())
                self.assertEqual(schedule_item.text(), schedule_item.toolTip())
            finally:
                page.deleteLater()

    def test_schedule_text_follows_profile_date_order(self):
        class FakeDb:
            def __init__(self, value):
                self.value = value

            def get_app_setting(self, key, default=""):
                return self.value or default

        fixed = CropProgramRule(
            id="fixed-format", title="Fixed", category="inspection",
            schedule_kind="fixed_date", month=9, day=17,
        )
        interval = CropProgramRule(
            id="interval-format", title="Window", category="inspection",
            schedule_kind="interval_window", start_month=9, start_day=17,
            end_month=10, end_day=3, within_period_unit="once",
            every_years=1, base_year=2027,
        )

        for selected, fixed_text, interval_prefix in (
            ("DD/MM/YYYY", "17/09", "17/09 – 03/10"),
            ("MM/DD/YYYY", "09/17", "09/17 – 10/03"),
            ("YYYY-MM-DD", "09-17", "09-17 – 10-03"),
        ):
            with self.subTest(selected=selected):
                page = type("Page", (), {"db": FakeDb(selected)})()
                self.assertEqual(fixed_text, CropProgramsPage._schedule_text(page, fixed))
                self.assertTrue(
                    CropProgramsPage._schedule_text(page, interval).startswith(interval_prefix)
                )

    def test_schedule_text_uses_singular_and_week_labels(self):
        class FakeDb:
            def get_app_setting(self, key, default=""):
                return "DD/MM/YYYY"

        page = type("Page", (), {"db": FakeDb()})()
        for unit, interval, expected in (
            ("days", 1, "κάθε 1 ημέρα"),
            ("weeks", 1, "κάθε 1 εβδομάδα"),
            ("weeks", 2, "κάθε 2 εβδομάδες"),
            ("months", 1, "κάθε 1 μήνας"),
        ):
            with self.subTest(unit=unit, interval=interval):
                rule = CropProgramRule(
                    id=f"{unit}-{interval}",
                    title="Frequency",
                    category="inspection",
                    schedule_kind="interval_window",
                    start_month=5,
                    start_day=1,
                    end_month=9,
                    end_day=30,
                    within_period_unit=unit,
                    within_period_interval=interval,
                    every_years=1,
                    base_year=2027,
                )
                self.assertIn(expected, CropProgramsPage._schedule_text(page, rule))

    def test_legacy_every_days_rule_remains_compatible(self):
        legacy = CropProgramRule(
            id="legacy",
            title="Legacy watering",
            category="irrigation",
            schedule_kind="interval_window",
            start_month=5,
            start_day=1,
            end_month=5,
            end_day=15,
            every_days=7,
        )
        tasks = generate_crop_tasks("program", "field", 2026, [legacy])
        self.assertEqual(
            ["2026-05-01", "2026-05-08", "2026-05-15"],
            [task["due_date"] for task in tasks],
        )


if __name__ == "__main__":
    unittest.main()
