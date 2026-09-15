from __future__ import annotations


def _table_exists(db, name: str) -> bool:
    return (
        db.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        )
        is not None
    )


def _columns(db, table: str) -> set[str]:
    return {row["name"] for row in db.query(f"PRAGMA table_info({table})")}


def _ensure_inventory_receipt_atomicity(db) -> None:
    """Keep inventory receipt movements and their expense projection atomic."""
    if not _table_exists(db, "inventory_movements"):
        return

    movement_columns = _columns(db, "inventory_movements")
    for name, definition in {
        "partner_id": "INTEGER",
        "supplier_name": "TEXT NOT NULL DEFAULT ''",
        "unit_price": "REAL NOT NULL DEFAULT 0",
        "total_cost": "REAL NOT NULL DEFAULT 0",
        "expense_id": "INTEGER",
    }.items():
        if name not in movement_columns:
            db.execute(
                f"ALTER TABLE inventory_movements ADD COLUMN {name} {definition}"
            )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS inventory_receipt_expense_after_insert
        AFTER INSERT ON inventory_movements
        BEGIN
            INSERT INTO expenses(
                entry_date, field_id, category, description, supplier,
                partner_id, payment_method, amount, notes, source_type, source_id
            )
            SELECT
                NEW.movement_date,
                NULL,
                'Αποθήκη & Εφόδια',
                'Παραλαβή αποθήκης — ' || COALESCE(
                    (SELECT name FROM inventory_items WHERE id=NEW.item_id),
                    'Είδος #' || CAST(NEW.item_id AS TEXT)
                ),
                COALESCE(NEW.supplier_name,''),
                NEW.partner_id,
                '',
                NEW.total_cost,
                'Αυτόματο έξοδο από παραλαβή αποθήκης #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END,
                'inventory_receipt',
                NEW.id
            WHERE NEW.movement_type='Παραλαβή'
              AND COALESCE(NEW.total_cost,0)>0
              AND NOT EXISTS(
                    SELECT 1 FROM expenses
                    WHERE source_type='inventory_receipt' AND source_id=NEW.id
              );

            UPDATE expenses
            SET
                entry_date=NEW.movement_date,
                field_id=NULL,
                category='Αποθήκη & Εφόδια',
                description='Παραλαβή αποθήκης — ' || COALESCE(
                    (SELECT name FROM inventory_items WHERE id=NEW.item_id),
                    'Είδος #' || CAST(NEW.item_id AS TEXT)
                ),
                supplier=COALESCE(NEW.supplier_name,''),
                partner_id=NEW.partner_id,
                payment_method='',
                amount=NEW.total_cost,
                notes='Αυτόματο έξοδο από παραλαβή αποθήκης #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END
            WHERE source_type='inventory_receipt'
              AND source_id=NEW.id
              AND NEW.movement_type='Παραλαβή'
              AND COALESCE(NEW.total_cost,0)>0;

            DELETE FROM expenses
            WHERE source_type='inventory_receipt'
              AND source_id=NEW.id
              AND (
                    NEW.movement_type<>'Παραλαβή'
                    OR COALESCE(NEW.total_cost,0)<=0
              );
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS inventory_receipt_expense_after_update
        AFTER UPDATE OF
            movement_date, item_id, movement_type, quantity, field_id, notes,
            partner_id, supplier_name, unit_price, total_cost
        ON inventory_movements
        BEGIN
            INSERT INTO expenses(
                entry_date, field_id, category, description, supplier,
                partner_id, payment_method, amount, notes, source_type, source_id
            )
            SELECT
                NEW.movement_date,
                NULL,
                'Αποθήκη & Εφόδια',
                'Παραλαβή αποθήκης — ' || COALESCE(
                    (SELECT name FROM inventory_items WHERE id=NEW.item_id),
                    'Είδος #' || CAST(NEW.item_id AS TEXT)
                ),
                COALESCE(NEW.supplier_name,''),
                NEW.partner_id,
                '',
                NEW.total_cost,
                'Αυτόματο έξοδο από παραλαβή αποθήκης #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END,
                'inventory_receipt',
                NEW.id
            WHERE NEW.movement_type='Παραλαβή'
              AND COALESCE(NEW.total_cost,0)>0
              AND NOT EXISTS(
                    SELECT 1 FROM expenses
                    WHERE source_type='inventory_receipt' AND source_id=NEW.id
              );

            UPDATE expenses
            SET
                entry_date=NEW.movement_date,
                field_id=NULL,
                category='Αποθήκη & Εφόδια',
                description='Παραλαβή αποθήκης — ' || COALESCE(
                    (SELECT name FROM inventory_items WHERE id=NEW.item_id),
                    'Είδος #' || CAST(NEW.item_id AS TEXT)
                ),
                supplier=COALESCE(NEW.supplier_name,''),
                partner_id=NEW.partner_id,
                payment_method='',
                amount=NEW.total_cost,
                notes='Αυτόματο έξοδο από παραλαβή αποθήκης #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END
            WHERE source_type='inventory_receipt'
              AND source_id=NEW.id
              AND NEW.movement_type='Παραλαβή'
              AND COALESCE(NEW.total_cost,0)>0;

            DELETE FROM expenses
            WHERE source_type='inventory_receipt'
              AND source_id=NEW.id
              AND (
                    NEW.movement_type<>'Παραλαβή'
                    OR COALESCE(NEW.total_cost,0)<=0
              );
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS inventory_receipt_expense_after_delete
        AFTER DELETE ON inventory_movements
        BEGIN
            DELETE FROM expenses
            WHERE source_type='inventory_receipt' AND source_id=OLD.id;
        END
        """
    )


def _ensure_equipment_maintenance_atomicity(db) -> None:
    """Project maintenance cost and meter changes in the source SQL statement."""
    if not (
        _table_exists(db, "equipment")
        and _table_exists(db, "equipment_maintenance")
    ):
        return

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS equipment_meter_type_history_guard
        BEFORE UPDATE OF meter_type ON equipment
        WHEN COALESCE(OLD.meter_type,'')<>COALESCE(NEW.meter_type,'')
         AND EXISTS(
             SELECT 1 FROM equipment_maintenance
             WHERE equipment_id=OLD.id
         )
        BEGIN
            SELECT RAISE(ABORT, 'equipment_meter_type_locked');
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS equipment_service_expense_after_insert
        AFTER INSERT ON equipment_maintenance
        BEGIN
            INSERT INTO expenses(
                entry_date, field_id, category, description, supplier,
                partner_id, payment_method, amount, notes, source_type, source_id
            )
            SELECT
                NEW.service_date,
                NULL,
                'Μηχανήματα & Συντήρηση',
                NEW.service_type || ' — ' || COALESCE(
                    (SELECT name FROM equipment WHERE id=NEW.equipment_id),
                    'Μηχάνημα #' || CAST(NEW.equipment_id AS TEXT)
                ),
                COALESCE(NEW.technician,''),
                NULL,
                '',
                NEW.cost,
                'Αυτόματο έξοδο από συντήρηση μηχανήματος #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END,
                'equipment_maintenance',
                NEW.id
            WHERE COALESCE(NEW.cost,0)>0
              AND NOT EXISTS(
                    SELECT 1 FROM expenses
                    WHERE source_type='equipment_maintenance' AND source_id=NEW.id
              );

            UPDATE expenses
            SET
                entry_date=NEW.service_date,
                field_id=NULL,
                category='Μηχανήματα & Συντήρηση',
                description=NEW.service_type || ' — ' || COALESCE(
                    (SELECT name FROM equipment WHERE id=NEW.equipment_id),
                    'Μηχάνημα #' || CAST(NEW.equipment_id AS TEXT)
                ),
                supplier=COALESCE(NEW.technician,''),
                partner_id=NULL,
                payment_method='',
                amount=NEW.cost,
                notes='Αυτόματο έξοδο από συντήρηση μηχανήματος #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END
            WHERE source_type='equipment_maintenance'
              AND source_id=NEW.id
              AND COALESCE(NEW.cost,0)>0;

            DELETE FROM expenses
            WHERE source_type='equipment_maintenance'
              AND source_id=NEW.id
              AND COALESCE(NEW.cost,0)<=0;

            UPDATE equipment
            SET current_meter=MAX(current_meter, COALESCE(NEW.meter_value,0)),
                updated_at=CURRENT_TIMESTAMP
            WHERE id=NEW.equipment_id;
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS equipment_service_expense_after_update
        AFTER UPDATE OF
            equipment_id, service_date, service_type, cost, meter_value,
            technician, notes, next_service_date, next_service_meter
        ON equipment_maintenance
        BEGIN
            INSERT INTO expenses(
                entry_date, field_id, category, description, supplier,
                partner_id, payment_method, amount, notes, source_type, source_id
            )
            SELECT
                NEW.service_date,
                NULL,
                'Μηχανήματα & Συντήρηση',
                NEW.service_type || ' — ' || COALESCE(
                    (SELECT name FROM equipment WHERE id=NEW.equipment_id),
                    'Μηχάνημα #' || CAST(NEW.equipment_id AS TEXT)
                ),
                COALESCE(NEW.technician,''),
                NULL,
                '',
                NEW.cost,
                'Αυτόματο έξοδο από συντήρηση μηχανήματος #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END,
                'equipment_maintenance',
                NEW.id
            WHERE COALESCE(NEW.cost,0)>0
              AND NOT EXISTS(
                    SELECT 1 FROM expenses
                    WHERE source_type='equipment_maintenance' AND source_id=NEW.id
              );

            UPDATE expenses
            SET
                entry_date=NEW.service_date,
                field_id=NULL,
                category='Μηχανήματα & Συντήρηση',
                description=NEW.service_type || ' — ' || COALESCE(
                    (SELECT name FROM equipment WHERE id=NEW.equipment_id),
                    'Μηχάνημα #' || CAST(NEW.equipment_id AS TEXT)
                ),
                supplier=COALESCE(NEW.technician,''),
                partner_id=NULL,
                payment_method='',
                amount=NEW.cost,
                notes='Αυτόματο έξοδο από συντήρηση μηχανήματος #' || CAST(NEW.id AS TEXT)
                    || CASE
                        WHEN TRIM(COALESCE(NEW.notes,''))<>''
                        THEN ' | ' || NEW.notes
                        ELSE ''
                    END
            WHERE source_type='equipment_maintenance'
              AND source_id=NEW.id
              AND COALESCE(NEW.cost,0)>0;

            DELETE FROM expenses
            WHERE source_type='equipment_maintenance'
              AND source_id=NEW.id
              AND COALESCE(NEW.cost,0)<=0;

            UPDATE equipment
            SET current_meter=MAX(current_meter, COALESCE(NEW.meter_value,0)),
                updated_at=CURRENT_TIMESTAMP
            WHERE id=NEW.equipment_id;
        END
        """
    )

    db.execute(
        """
        CREATE TRIGGER IF NOT EXISTS equipment_service_expense_after_delete
        AFTER DELETE ON equipment_maintenance
        BEGIN
            DELETE FROM expenses
            WHERE source_type='equipment_maintenance' AND source_id=OLD.id;
        END
        """
    )


def ensure_expense_source_schema(db) -> None:
    table = db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
    )
    if table is None:
        return

    columns = _columns(db, "expenses")
    for name, definition in {
        "source_type": "TEXT NOT NULL DEFAULT ''",
        "source_id": "INTEGER",
        "partner_id": "INTEGER",
    }.items():
        if name not in columns:
            db.execute(f"ALTER TABLE expenses ADD COLUMN {name} {definition}")

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_expenses_source
        ON expenses(source_type, source_id)
        """
    )

    _ensure_inventory_receipt_atomicity(db)
    _ensure_equipment_maintenance_atomicity(db)


def _projected_source_exists(db, source_type: str, source_id: int) -> bool:
    table = {
        "inventory_receipt": "inventory_movements",
        "equipment_maintenance": "equipment_maintenance",
    }.get(source_type)
    if table is None or not _table_exists(db, table):
        return False
    return db.query_one(
        f"SELECT id FROM {table} WHERE id=?",
        (source_id,),
    ) is not None


def sync_expense(
    db,
    *,
    source_type: str,
    source_id: int,
    entry_date: str,
    category: str,
    description: str,
    supplier: str,
    payment_method: str,
    amount: float,
    notes: str,
    partner_id: int | None = None,
) -> int | None:
    ensure_expense_source_schema(db)

    existing = db.query_one(
        """
        SELECT id
        FROM expenses
        WHERE source_type=? AND source_id=?
        ORDER BY id
        LIMIT 1
        """,
        (source_type, source_id),
    )

    # These source rows project their expense inside the same SQLite statement.
    # Legacy UI calls remain compatible and idempotent.
    if _projected_source_exists(db, source_type, source_id):
        if amount > 0 and existing is not None:
            return int(existing["id"])
        if amount <= 0 and existing is None:
            return None
        # A legacy pre-trigger row may still need a one-time repair below.

    if amount <= 0:
        if existing is not None:
            db.execute("DELETE FROM expenses WHERE id=?", (existing["id"],))
        return None

    values = (
        entry_date,
        None,
        category,
        description,
        supplier,
        partner_id,
        payment_method,
        float(amount),
        notes,
        source_type,
        source_id,
    )

    if existing is None:
        return int(
            db.execute(
                """
                INSERT INTO expenses(
                    entry_date, field_id, category, description, supplier,
                    partner_id, payment_method, amount, notes, source_type, source_id
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                values,
            )
        )

    db.execute(
        """
        UPDATE expenses
        SET
            entry_date=?, field_id=?, category=?, description=?, supplier=?,
            partner_id=?, payment_method=?, amount=?, notes=?, source_type=?,
            source_id=?
        WHERE id=?
        """,
        (*values, existing["id"]),
    )
    return int(existing["id"])


def delete_expense(
    db,
    *,
    source_type: str,
    source_id: int,
) -> None:
    ensure_expense_source_schema(db)

    # When the source row still exists, its AFTER DELETE trigger owns removal of
    # the projection. A rejected source deletion therefore cannot orphan history.
    if _projected_source_exists(db, source_type, source_id):
        return

    db.execute(
        """
        DELETE FROM expenses
        WHERE source_type=? AND source_id=?
        """,
        (source_type, source_id),
    )
