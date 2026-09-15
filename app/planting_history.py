from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from .database import Database


@dataclass(frozen=True)
class Replanting:
    id: str
    planting_batch_id: str
    replanting_date: str
    tree_count: int
    notes: str = ""

    def validate(self) -> None:
        if not self.id.strip() or not self.planting_batch_id.strip():
            raise ValueError("Replanting and planting-batch ids are required.")
        try:
            date.fromisoformat(self.replanting_date)
        except ValueError as error:
            raise ValueError("Replanting date must be YYYY-MM-DD.") from error
        if isinstance(self.tree_count, bool) or not isinstance(self.tree_count, int) or self.tree_count <= 0:
            raise ValueError("Replanting tree count must be a positive integer.")


@dataclass(frozen=True)
class PlantingTotals:
    positions: int
    replantings: int
    historical_plantings: int
    living: int
    historical_losses: int
    vacant_positions: int


class PlantingHistoryStore:
    """Append-only aggregate replanting history for a planting batch.

    ``trees_planted`` keeps its legacy meaning: original planted positions.
    Replantings add to historical plantings but never increase field capacity.
    ``trees_alive`` remains the authoritative current living count.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with self.db.connect() as con:
            exists = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='planting_batches'"
            ).fetchone()
            if exists is None:
                raise RuntimeError("planting_batches must exist before planting history is enabled")
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS planting_replantings (
                    id TEXT PRIMARY KEY,
                    planting_batch_id INTEGER NOT NULL,
                    replanting_date TEXT NOT NULL,
                    tree_count INTEGER NOT NULL CHECK(tree_count > 0),
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(planting_batch_id)
                        REFERENCES planting_batches(id) ON DELETE RESTRICT
                );
                CREATE INDEX IF NOT EXISTS idx_planting_replantings_batch_date
                ON planting_replantings(planting_batch_id,replanting_date,id);
                """
            )

    @staticmethod
    def _batch_id(value: str) -> int:
        try:
            result = int(str(value).strip())
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid planting-batch id.") from error
        if result <= 0:
            raise ValueError("Invalid planting-batch id.")
        return result

    def add_replanting(
        self,
        planting_batch_id: str,
        replanting_date: str,
        tree_count: int,
        notes: str = "",
        *,
        event_id: str | None = None,
    ) -> str:
        event = Replanting(
            id=(event_id or str(uuid4())).strip(),
            planting_batch_id=str(planting_batch_id).strip(),
            replanting_date=str(replanting_date).strip(),
            tree_count=tree_count,
            notes=str(notes).strip(),
        )
        event.validate()
        batch_id = self._batch_id(event.planting_batch_id)
        with self.db.connect() as con:
            batch = con.execute(
                "SELECT planting_date FROM planting_batches WHERE id=?",
                (batch_id,),
            ).fetchone()
            if batch is None:
                raise ValueError("Planting batch does not exist.")
            if event.replanting_date < str(batch["planting_date"] or ""):
                raise ValueError("Replanting cannot predate the original planting.")
            try:
                con.execute(
                    """
                    INSERT INTO planting_replantings(
                        id,planting_batch_id,replanting_date,tree_count,notes
                    ) VALUES(?,?,?,?,?)
                    """,
                    (
                        event.id,
                        batch_id,
                        event.replanting_date,
                        event.tree_count,
                        event.notes,
                    ),
                )
            except Exception as error:
                if "UNIQUE constraint failed" in str(error):
                    raise ValueError("Replanting event id already exists.") from error
                raise
        return event.id

    def replantings(self, planting_batch_id: str) -> list[Replanting]:
        batch_id = self._batch_id(planting_batch_id)
        rows = self.db.query(
            """
            SELECT id,planting_batch_id,replanting_date,tree_count,notes
            FROM planting_replantings
            WHERE planting_batch_id=?
            ORDER BY replanting_date,id
            """,
            (batch_id,),
        )
        return [
            Replanting(
                id=str(row["id"]),
                planting_batch_id=str(row["planting_batch_id"]),
                replanting_date=str(row["replanting_date"]),
                tree_count=int(row["tree_count"]),
                notes=str(row["notes"] or ""),
            )
            for row in rows
        ]

    def totals(self, planting_batch_id: str) -> PlantingTotals:
        batch_id = self._batch_id(planting_batch_id)
        row = self.db.query_one(
            """
            SELECT
                p.trees_planted AS positions,
                p.trees_alive AS living,
                COALESCE(SUM(r.tree_count),0) AS replantings
            FROM planting_batches p
            LEFT JOIN planting_replantings r ON r.planting_batch_id=p.id
            WHERE p.id=?
            GROUP BY p.id,p.trees_planted,p.trees_alive
            """,
            (batch_id,),
        )
        if row is None:
            raise ValueError("Planting batch does not exist.")
        positions = int(row["positions"] or 0)
        living = int(row["living"] or 0)
        replacements = int(row["replantings"] or 0)
        if positions < 0 or living < 0 or living > positions:
            raise ValueError("Invalid planting-batch tree counts.")
        historical = positions + replacements
        return PlantingTotals(
            positions=positions,
            replantings=replacements,
            historical_plantings=historical,
            living=living,
            historical_losses=max(historical - living, 0),
            vacant_positions=max(positions - living, 0),
        )
