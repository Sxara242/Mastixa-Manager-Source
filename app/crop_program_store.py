from __future__ import annotations

import time
from typing import Iterable

from .crop_program import CropProgramRule, generate_crop_tasks
from .database import Database


STATUSES = frozenset({"pending", "completed", "skipped"})


def migrate_crop_programs(con) -> None:
    """Create the additive Phase 12 storage schema inside the caller transaction."""
    statements = (
        """
        CREATE TABLE IF NOT EXISTS crop_programs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            crop TEXT NOT NULL DEFAULT '',
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
        CREATE TABLE IF NOT EXISTS crop_tasks (
            generation_key TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            field_id TEXT NOT NULL,
            season_year INTEGER NOT NULL CHECK(season_year BETWEEN 1900 AND 9998),
            due_date TEXT NOT NULL,
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
    )
    for statement in statements:
        con.execute(statement)


def _required(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


class CropProgramStore:
    """Local persistence for Phase 12 programs, assignments and generated planned work."""

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
        description: str = "",
    ) -> None:
        program = _required(program_id, "program id")
        display_name = _required(name, "program name")
        rule_list = list(rules)
        generate_crop_tasks(program, "__template_validation__", 2000, rule_list)
        now = int(time.time() * 1000)

        with self.db.connect() as con:
            con.execute(
                """
                INSERT INTO crop_programs(id,name,crop,description,active,updated_at)
                VALUES(?,?,?,?,1,?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    crop=excluded.crop,
                    description=excluded.description,
                    active=1,
                    updated_at=excluded.updated_at
                """,
                (
                    program,
                    display_name,
                    str(crop or "").strip(),
                    str(description or "").strip(),
                    now,
                ),
            )
            con.execute(
                "DELETE FROM crop_program_rules WHERE program_id=?", (program,)
            )
            for position, rule in enumerate(rule_list):
                con.execute(
                    """
                    INSERT INTO crop_program_rules(
                        program_id,rule_id,title,category,schedule_kind,notes,
                        month,day,start_month,start_day,end_month,end_day,every_days,position
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        program,
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
                        position,
                    ),
                )

    def programs(self, *, active_only: bool = False) -> list[dict[str, object]]:
        clause = "WHERE p.active=1" if active_only else ""
        rows = self.db.query(
            f"""
            SELECT p.id,p.name,p.crop,p.description,p.active,p.updated_at,
                   COUNT(r.rule_id) AS rule_count
            FROM crop_programs p
            LEFT JOIN crop_program_rules r ON r.program_id=p.id
            {clause}
            GROUP BY p.id,p.name,p.crop,p.description,p.active,p.updated_at
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
            SELECT id,name,crop,description,active,updated_at
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
                   start_month,start_day,end_month,end_day,every_days
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
        generated = generate_crop_tasks(program, field, season_year, rules)
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
                        category,title,notes,status,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        task["generation_key"],
                        program,
                        task["rule_id"],
                        field,
                        season_year,
                        task["due_date"],
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
        return self.tasks(
            program_id=program, field_id=field, season_year=season_year
        )

    def set_task_status(self, generation_key: str, status: str) -> None:
        key = _required(generation_key, "generation key")
        value = str(status or "").strip()
        if value not in STATUSES:
            raise ValueError(f"Unsupported crop task status: {value}")
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
                   category,title,notes,status,created_at,updated_at
            FROM crop_tasks
            """
            + clause
            + " ORDER BY due_date,rule_id,generation_key",
            params,
        )
        return [dict(row) for row in rows]

    def archive_program(self, program_id: str) -> None:
        program = _required(program_id, "program id")
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
                "DELETE FROM crop_tasks WHERE program_id=? AND status='pending'",
                (program,),
            )
