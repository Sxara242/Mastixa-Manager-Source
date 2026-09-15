from __future__ import annotations


def ensure_product_links(db) -> None:
    """Create/backfill stable product links while preserving legacy text.

    Keep the repair path idempotent, but do all inspection/backfill work through
    one SQLite connection. The old implementation opened a fresh connection for
    every row while validating existing product links, which made the first
    Production-page load scale badly with real user data.
    """
    with db.connect() as con:
        tables = {
            row["name"]
            for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "products" not in tables:
            return

        existing = con.execute("SELECT id,name FROM products ORDER BY id").fetchall()
        by_name = {
            str(row["name"] or "").strip().casefold(): int(row["id"])
            for row in existing
            if str(row["name"] or "").strip()
        }

        for table_name in ("production", "production_sales"):
            if table_name not in tables:
                continue

            columns = {
                row["name"]
                for row in con.execute(f"PRAGMA table_info({table_name})")
            }
            if "product_id" not in columns:
                con.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN product_id INTEGER"
                )

            # Only inspect rows that actually need repair. A valid product_id is
            # accepted exactly as before, even if the legacy text differs.
            rows = con.execute(
                f"""
                SELECT t.id, t.product, t.product_id
                FROM {table_name} AS t
                LEFT JOIN products AS p ON p.id = t.product_id
                WHERE TRIM(COALESCE(t.product,'')) <> ''
                  AND p.id IS NULL
                """
            ).fetchall()

            for row in rows:
                name = str(row["product"]).strip()
                key = name.casefold()
                product_id = by_name.get(key)
                if product_id is None:
                    cursor = con.execute(
                        "INSERT INTO products(name,unit,is_active) VALUES(?,?,1)",
                        (name, "kg"),
                    )
                    product_id = int(cursor.lastrowid)
                    by_name[key] = product_id

                con.execute(
                    f"UPDATE {table_name} SET product_id=? WHERE id=?",
                    (product_id, row["id"]),
                )

            con.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_product_id "
                f"ON {table_name}(product_id)"
            )


def product_row(db, product_id: int | None):
    if product_id is None:
        return None
    return db.query_one(
        "SELECT id,name,unit,is_active FROM products WHERE id=?",
        (product_id,),
    )


def add_product_choices(combo, db, *, selected_id=None, legacy_name="") -> None:
    """Active products for new records; retain selected inactive/legacy value."""
    combo.clear()
    combo.addItem("Επίλεξε προϊόν", None)
    rows = db.query(
        "SELECT id,name,unit,is_active FROM products WHERE is_active=1 ORDER BY name,id"
    )
    included = set()
    for row in rows:
        product_id = int(row["id"])
        combo.addItem(f"{row['name']} ({row['unit']})", product_id)
        included.add(product_id)

    if selected_id is not None and int(selected_id) not in included:
        row = product_row(db, int(selected_id))
        if row is not None:
            combo.addItem(
                f"{row['name']} ({row['unit']}) — Ανενεργό",
                int(row["id"]),
            )
            included.add(int(row["id"]))

    index = combo.findData(selected_id)
    if index >= 0:
        combo.setCurrentIndex(index)
    elif legacy_name:
        combo.addItem(f"{legacy_name} — Legacy", None)
        combo.setCurrentIndex(combo.count() - 1)
    else:
        combo.setCurrentIndex(0)
