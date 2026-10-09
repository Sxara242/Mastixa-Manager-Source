from __future__ import annotations

import time
from typing import Iterable

from .crop_program import CropProgramRule, generate_crop_tasks
from .database import Database
from .year_context import require_writable_years


STATUSES = frozenset({"pending", "completed", "skipped"})


def _column_names(con, table_name: str) -> set[str]:
    return {str(row[1]) for row in con.execute(f"PRAGMA table_info({table_name})")}


def _add_column_if_missing(con, table_name: str, column_name: str, declaration: str) -> None:
    if column_name not in _column_names(con, table_name):
        con.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {declaration}"
        )


def migrate_crop_programs(con) -> None:
    """Create and extend crop-program storage inside the caller transaction."""
    statements = (
        """
        CREATE TABLE IF NOT EXISTS crop_programs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            crop TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
            updated_at INTEGER NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS crop_program_rules (
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
            base_year INTEGER CHECK(base_year BETWEEN 1900 AND 9998),
            position INTEGER NOT NULL,
            PRIMARY KEY(program_id, rule_id),
            FOREIGN KEY(program_id) REFERENCES crop_programs(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS crop_program_assignments (
            program_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            season_year INTEGER NOT NULL CHECK(season_year BETWEEN 1900 AND 9998),
            generated_at INTEGER NOT NULL,
            PRIMARY KEY(program_id, field_id, season_year)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS crop_program_field_links (
            program_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            start_year INTEGER NOT NULL CHECK(start_year BETWEEN 1900 AND 9998),
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
            linked_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY(program_id, field_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS crop_tasks (
            generation_key TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            season_year INTEGER NOT NULL CHECK(season_year BETWEEN 1900 AND 9998),
            due_date TEXT NOT NULL,
            window_end_date TEXT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','completed','skipped')),
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_crop_tasks_field_due ON crop_tasks(field_id,due_date)",
        "CREATE INDEX IF NOT EXISTS idx_crop_tasks_status_due ON crop_tasks(status,due_date)",
        "CREATE INDEX IF NOT EXISTS idx_crop_tasks_assignment ON crop_tasks(program_id,field_id,season_year)",
        "CREATE INDEX IF NOT EXISTS idx_crop_links_field ON crop_program_field_links(field_id,active,start_year)",
    )
    for statement in statements:
        con.execute(statement)

    # Additive migration for databases created before program-level categories.
    _add_column_if_missing(
        con, "crop_programs", "category", "TEXT NOT NULL DEFAULT ''"
    )

    # Additive migration for databases created before Alpha 2 scheduling.
    _add_column_if_missing(
        con, "crop_program_rules", "within_period_unit", "TEXT"
    )
    _add_column_if_missing(
        con, "crop_program_rules", "within_period_interval", "INTEGER"
    )
    _add_column_if_missing(
        con,
        "crop_program_rules",
        "every_years",
        "INTEGER NOT NULL DEFAULT 1",
    )
    _add_column_if_missing(
        con,
        "crop_program_rules",
        "base_year",
        "INTEGER",
    )
    _add_column_if_missing(
        con, "crop_tasks", "window_end_date", "TEXT"
    )


def _required(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _validated_rules(
    rules: Iterable[CropProgramRule],
) -> list[CropProgramRule]:
    rule_list = list(rules)
    seen_rule_ids: set[str] = set()
    for rule in rule_list:
        if rule.id in seen_rule_ids:
            raise ValueError(f"Duplicate crop-program rule id: {rule.id}")
        seen_rule_ids.add(rule.id)
        rule.validate(rule.base_year or 2000)
    return rule_list


def _replace_program_rules(
    con,
    program_id: str,
    rules: list[CropProgramRule],
) -> None:
    con.execute(
        "DELETE FROM crop_program_rules WHERE program_id=?",
        (program_id,),
    )
    for position, rule in enumerate(rules):
        con.execute(
            """
            INSERT INTO crop_program_rules(
                program_id,rule_id,title,category,schedule_kind,notes,
                month,day,start_month,start_day,end_month,end_day,every_days,
                within_period_unit,within_period_interval,every_years,base_year,
                position
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                program_id,
                rule.id,
                rule.title,
                rule.category,
                rule.schedule_kind,
                rule.notes,
                rule.month,
                rule.day,
                rule.start_month,
                rule.start_day,
                rule.end_month,
                rule.end_day,
                rule.every_days,
                rule.within_period_unit,
                rule.within_period_interval,
                rule.every_years,
                rule.base_year,
                position,
            ),
        )


class CropProgramStore:
    """Local persistence for crop programs, durable field links and generated work."""

    def __init__(self, db: Database) -> None:
        self.db = db
        with self.db.connect() as con:
            migrate_crop_programs(con)

    def save_program(
        self,
        program_id: str,
        name: str,
        rules: Iterable[CropProgramRule],
        *,
        crop: str = "",
        category: str = "",
        description: str = "",
    ) -> None:
        program = _required(program_id, "program id")
        display_name = _required(name, "program name")
        # Validation is structural; rule-level base years may be later than 2000.
        rule_list = _validated_rules(rules)
        now = int(time.time() * 1000)

        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO crop_programs(
                    id,name,crop,category,description,active,updated_at
                )
                VALUES(?,?,?,?,?,1,?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    crop=excluded.crop,
                    category=excluded.category,
                    description=excluded.description,
                    active=1,
                    updated_at=excluded.updated_at
                """,
                (
                    program,
                    display_name,
                    str(crop or "").strip(),
                    str(category or "").strip(),
                    str(description or "").strip(),
                    now,
                ),
            )
            _replace_program_rules(con, program, rule_list)

    def save_rules(
        self,
        program_id: str,
        rules: Iterable[CropProgramRule],
    ) -> None:
        """Persist only a saved program's rules, leaving program metadata untouched."""
        program = _required(program_id, "program id")
        rule_list = _validated_rules(rules)
        now = int(time.time() * 1000)

        with self.db.connect() as con:
            row = con.execute(
                "SELECT active FROM crop_programs WHERE id=?",
                (program,),
            ).fetchone()
            if row is None:
                raise ValueError("Crop program does not exist")
            if int(row[0]) != 1:
                raise ValueError("Crop program is archived")

            _replace_program_rules(con, program, rule_list)
            con.execute(
                "UPDATE crop_programs SET updated_at=? WHERE id=?",
                (now, program),
            )

    def programs(self, *, active_only: bool = False) -> list[dict[str, object]]:
        clause = "WHERE p.active=1" if active_only else ""
        rows = self.db.query(
            f"""
            SELECT p.id,p.name,p.crop,p.category,p.description,p.active,p.updated_at,
                   COUNT(r.rule_id) AS rule_count
            FROM crop_programs p
            LEFT JOIN crop_program_rules r ON r.program_id=p.id
            {clause}
            GROUP BY p.id,p.name,p.crop,p.category,p.description,p.active,p.updated_at
            ORDER BY p.active DESC,p.name COLLATE NOCASE,p.id
            """
        )
        result: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            item["active"] = bool(item["active"])
            item["rule_count"] = int(item["rule_count"])
            result.append(item)
        return result

    def program(self, program_id: str) -> dict[str, object]:
        program = _required(program_id, "program id")
        row = self.db.query_one(
            """
            SELECT id,name,crop,category,description,active,updated_at
            FROM crop_programs
            WHERE id=?
            """,
            (program,),
        )
        if row is None:
            raise ValueError("Crop program does not exist")
        result = dict(row)
        result["active"] = bool(result["active"])
        result["rules"] = self._rules(program)
        return result

    def _rules(self, program_id: str) -> list[CropProgramRule]:
        rows = self.db.query(
            """
            SELECT rule_id,title,category,schedule_kind,notes,month,day,
                   start_month,start_day,end_month,end_day,every_days,
                   within_period_unit,within_period_interval,every_years,base_year
            FROM crop_program_rules
            WHERE program_id=?
            ORDER BY position,rule_id
            """,
            (program_id,),
        )
        return [
            CropProgramRule(
                id=str(row["rule_id"]),
                title=str(row["title"]),
                category=str(row["category"]),
                schedule_kind=str(row["schedule_kind"]),
                notes=str(row["notes"] or ""),
                month=row["month"],
                day=row["day"],
                start_month=row["start_month"],
                start_day=row["start_day"],
                end_month=row["end_month"],
                end_day=row["end_day"],
                every_days=row["every_days"],
                within_period_unit=row["within_period_unit"],
                within_period_interval=row["within_period_interval"],
                every_years=int(row["every_years"] or 1),
                base_year=(
                    int(row["base_year"])
                    if row["base_year"] is not None
                    else None
                ),
            )
            for row in rows
        ]

    def _require_active_program(self, program_id: str) -> None:
        row = self.db.query_one(
            "SELECT active FROM crop_programs WHERE id=?",
            (program_id,),
        )
        if row is None:
            raise ValueError("Crop program does not exist")
        if int(row["active"]) != 1:
            raise ValueError("Crop program is archived")

    def _require_field(self, field_id: str) -> None:
        row = self.db.query_one(
            "SELECT 1 FROM fields WHERE CAST(id AS TEXT)=?",
            (field_id,),
        )
        if row is None:
            raise ValueError("Field does not exist")

    def field_link(
        self, program_id: str, field_id: str | int
    ) -> dict[str, object] | None:
        row = self.db.query_one(
            """
            SELECT program_id,field_id,start_year,active,linked_at,updated_at
            FROM crop_program_field_links
            WHERE program_id=? AND field_id=?
            """,
            (_required(program_id, "program id"), _required(field_id, "field id")),
        )
        if row is None:
            return None
        item = dict(row)
        item["active"] = bool(item["active"])
        return item

    def field_links(
        self,
        *,
        program_id: str | None = None,
        field_id: str | int | None = None,
        active_only: bool = False,
    ) -> list[dict[str, object]]:
        where: list[str] = []
        params: list[object] = []
        if program_id is not None:
            where.append("program_id=?")
            params.append(str(program_id))
        if field_id is not None:
            where.append("field_id=?")
            params.append(str(field_id))
        if active_only:
            where.append("active=1")
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        rows = self.db.query(
            """
            SELECT program_id,field_id,start_year,active,linked_at,updated_at
            FROM crop_program_field_links
            """
            + clause
            + " ORDER BY start_year,program_id,field_id",
            params,
        )
        result = []
        for row in rows:
            item = dict(row)
            item["active"] = bool(item["active"])
            result.append(item)
        return result

    def generate_for_field(
        self,
        program_id: str,
        field_id: str | int,
        season_year: int,
    ) -> list[dict[str, object]]:
        program = _required(program_id, "program id")
        field = _required(field_id, "field id")
        self._require_active_program(program)
        self._require_field(field)
        rules = self._rules(program)

        existing_link = self.field_link(program, field)
        anchor_year = (
            int(existing_link["start_year"])
            if existing_link is not None
            else int(season_year)
        )
        generated = generate_crop_tasks(
            program,
            field,
            season_year,
            rules,
            anchor_year=anchor_year,
        )
        existing_dates = self.db.query(
            "SELECT due_date FROM crop_tasks WHERE program_id=? AND field_id=? AND season_year=? AND status='pending'",
            (program, field, season_year),
        )
        require_writable_years(self.db, [season_year, *(
            int(task["due_date"][:4]) for task in [*generated, *existing_dates]
        )])
        now = int(time.time() * 1000)

        with self.db.connect() as con:
            con.execute(
                """
                DELETE FROM crop_tasks
                WHERE program_id=? AND field_id=? AND season_year=? AND status='pending'
                """,
                (program, field, season_year),
            )
            for task in generated:
                con.execute(
                    """
                    INSERT OR IGNORE INTO crop_tasks(
                        generation_key,program_id,rule_id,field_id,season_year,due_date,
                        window_end_date,category,title,notes,status,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        task["generation_key"],
                        program,
                        task["rule_id"],
                        field,
                        season_year,
                        task["due_date"],
                        task.get("window_end_date"),
                        task["category"],
                        task["title"],
                        task["notes"],
                        "pending",
                        now,
                        now,
                    ),
                )
            con.execute(
                """
                INSERT INTO crop_program_assignments(program_id,field_id,season_year,generated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(program_id,field_id,season_year) DO UPDATE SET
                    generated_at=excluded.generated_at
                """,
                (program, field, season_year, now),
            )
            con.execute(
                """
                INSERT INTO crop_program_field_links(
                    program_id,field_id,start_year,active,linked_at,updated_at
                ) VALUES(?,?,?,1,?,?)
                ON CONFLICT(program_id,field_id) DO UPDATE SET
                    active=1,
                    updated_at=excluded.updated_at
                """,
                (program, field, anchor_year, now, now),
            )
        return self.tasks(
            program_id=program, field_id=field, season_year=season_year
        )

    def set_task_status(self, generation_key: str, status: str) -> None:
        key = _required(generation_key, "generation key")
        value = str(status or "").strip()
        if value not in STATUSES:
            raise ValueError(f"Unsupported crop task status: {value}")
        task = self.db.query_one("SELECT due_date FROM crop_tasks WHERE generation_key=?", (key,))
        if task is not None:
            require_writable_years(self.db, [int(task["due_date"][:4])])
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                "UPDATE crop_tasks SET status=?,updated_at=? WHERE generation_key=?",
                (value, now, key),
            ).rowcount
            if changed != 1:
                raise ValueError("Crop task does not exist")

    def tasks(
        self,
        *,
        program_id: str | None = None,
        field_id: str | int | None = None,
        season_year: int | None = None,
    ) -> list[dict[str, object]]:
        where: list[str] = []
        params: list[object] = []
        if program_id is not None:
            where.append("program_id=?")
            params.append(str(program_id))
        if field_id is not None:
            where.append("field_id=?")
            params.append(str(field_id))
        if season_year is not None:
            where.append("season_year=?")
            params.append(int(season_year))
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        rows = self.db.query(
            """
            SELECT generation_key,program_id,rule_id,field_id,season_year,due_date,
                   window_end_date,category,title,notes,status,created_at,updated_at
            FROM crop_tasks
            """
            + clause
            + " ORDER BY due_date,rule_id,generation_key",
            params,
        )
        return [dict(row) for row in rows]

    def archive_program(self, program_id: str) -> None:
        program = _required(program_id, "program id")
        require_writable_years(self.db, [int(row["due_date"][:4]) for row in self.db.query(
            "SELECT due_date FROM crop_tasks WHERE program_id=? AND status='pending'", (program,)
        )])
        now = int(time.time() * 1000)
        with self.db.connect() as con:
            changed = con.execute(
                "UPDATE crop_programs SET active=0,updated_at=? WHERE id=?",
                (now, program),
            ).rowcount
            if changed != 1:
                raise ValueError("Crop program does not exist")
            con.execute(
                "DELETE FROM crop_program_assignments WHERE program_id=?",
                (program,),
            )
            con.execute(
                "UPDATE crop_program_field_links SET active=0,updated_at=? WHERE program_id=?",
                (now, program),
            )
            con.execute(
                "DELETE FROM crop_tasks WHERE program_id=? AND status='pending'",
                (program,),
            )
