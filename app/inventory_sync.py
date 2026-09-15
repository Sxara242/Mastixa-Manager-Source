from __future__ import annotations


class InventoryStockError(ValueError):
    def __init__(self, available: float) -> None:
        super().__init__("insufficient stock")
        self.available = float(available)


def ensure_inventory_source_schema(db) -> None:
    table = db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_movements'"
    )
    if table is None:
        return
    columns = {
        row["name"] for row in db.query("PRAGMA table_info(inventory_movements)")
    }
    for name, definition in {
        "source_type": "TEXT NOT NULL DEFAULT ''",
        "source_id": "INTEGER",
    }.items():
        if name not in columns:
            db.execute(
                f"ALTER TABLE inventory_movements ADD COLUMN {name} {definition}"
            )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_inventory_movements_source "
        "ON inventory_movements(source_type, source_id)"
    )
    ensure_inventory_integrity_triggers(db)


def ensure_inventory_integrity_triggers(db) -> None:
    """Install ledger invariants that must hold for every Windows caller.

    UI validation remains useful for friendly feedback, but these guards keep the
    database valid even when a write comes from another page/helper. Automatic
    source movements may still be corrected by their owning source; only manual
    movement item reassignment is forbidden.
    """
    items_table = db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_items'"
    )
    if items_table is not None:
        db.execute(
            """
            CREATE TRIGGER IF NOT EXISTS inventory_item_unit_immutable_after_history
            BEFORE UPDATE OF unit ON inventory_items
            WHEN COALESCE(NEW.unit,'') <> COALESCE(OLD.unit,'')
             AND EXISTS(
                SELECT 1 FROM inventory_movements WHERE item_id=OLD.id LIMIT 1
             )
            BEGIN
                SELECT RAISE(ABORT, 'inventory_unit_has_history');
            END
            """
        )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS inventory_manual_movement_item_immutable
        BEFORE UPDATE OF item_id ON inventory_movements
        WHEN NEW.item_id <> OLD.item_id
         AND COALESCE(OLD.source_type,'') = ''
        BEGIN
            SELECT RAISE(ABORT, 'inventory_manual_item_immutable');
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS inventory_delete_preserves_nonnegative_stock
        BEFORE DELETE ON inventory_movements
        WHEN (
            SELECT COALESCE(SUM(
                CASE
                    WHEN movement_type IN ('Παραλαβή','Διόρθωση +') THEN quantity
                    WHEN movement_type IN ('Κατανάλωση','Διόρθωση -') THEN -quantity
                    ELSE 0
                END
            ),0)
            FROM inventory_movements
            WHERE item_id=OLD.item_id
        ) - CASE
                WHEN OLD.movement_type IN ('Παραλαβή','Διόρθωση +') THEN OLD.quantity
                WHEN OLD.movement_type IN ('Κατανάλωση','Διόρθωση -') THEN -OLD.quantity
                ELSE 0
            END < -0.000001
        BEGIN
            SELECT RAISE(ABORT, 'inventory_negative_stock');
        END
        """
    )


def current_stock(
    db,
    item_id: int,
    exclude_movement_id: int | None = None,
) -> float:
    where = ["item_id=?"]
    params = [item_id]
    if exclude_movement_id is not None:
        where.append("id<>?")
        params.append(exclude_movement_id)
    row = db.query_one(
        f"""
        SELECT COALESCE(SUM(CASE
            WHEN movement_type IN ('Παραλαβή','Διόρθωση +') THEN quantity
            WHEN movement_type IN ('Κατανάλωση','Διόρθωση -') THEN -quantity
            ELSE 0 END),0) AS stock
        FROM inventory_movements
        WHERE {' AND '.join(where)}
        """,
        params,
    )
    return float(row["stock"] if row else 0)


def ensure_can_consume(
    db,
    *,
    item_id: int | None,
    quantity: float,
    source_type: str,
    source_id: int | None,
) -> None:
    if item_id is None or quantity <= 0:
        return
    ensure_inventory_source_schema(db)
    existing = None
    if source_id is not None:
        existing = db.query_one(
            "SELECT id FROM inventory_movements WHERE source_type=? AND source_id=?",
            (source_type, source_id),
        )
    exclude_id = int(existing["id"]) if existing else None
    available = current_stock(db, int(item_id), exclude_id)
    if float(quantity) > available + 0.000001:
        raise InventoryStockError(available)


def sync_consumption(
    db,
    *,
    source_type: str,
    source_id: int,
    movement_date: str,
    item_id: int | None,
    quantity: float,
    field_id: int | None,
    notes: str,
) -> None:
    ensure_inventory_source_schema(db)
    existing = db.query_one(
        "SELECT id FROM inventory_movements WHERE source_type=? AND source_id=?",
        (source_type, source_id),
    )
    if item_id is None or quantity <= 0:
        if existing is not None:
            db.execute(
                "DELETE FROM inventory_movements WHERE id=?",
                (existing["id"],),
            )
        return
    ensure_can_consume(
        db,
        item_id=int(item_id),
        quantity=float(quantity),
        source_type=source_type,
        source_id=source_id,
    )
    values = (
        movement_date,
        int(item_id),
        "Κατανάλωση",
        float(quantity),
        field_id,
        notes,
        source_type,
        source_id,
    )
    if existing is None:
        db.execute(
            """
            INSERT INTO inventory_movements(
                movement_date,item_id,movement_type,quantity,
                field_id,notes,source_type,source_id
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            values,
        )
    else:
        db.execute(
            """
            UPDATE inventory_movements
            SET movement_date=?,item_id=?,movement_type=?,quantity=?,
                field_id=?,notes=?,source_type=?,source_id=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*values, existing["id"]),
        )


def delete_consumption(db, *, source_type: str, source_id: int) -> None:
    ensure_inventory_source_schema(db)
    db.execute(
        "DELETE FROM inventory_movements WHERE source_type=? AND source_id=?",
        (source_type, source_id),
    )
