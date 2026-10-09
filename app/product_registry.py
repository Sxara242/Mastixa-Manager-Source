from __future__ import annotations

from PySide6.QtCore import QObject, QSignalBlocker, Slot

from .localized_messages import _language, _text


class _InactiveProductLabel(QObject):
    """Refresh only the owned suffix; names and units never enter translation."""

    def __init__(self, combo, controller):
        super().__init__(combo)
        self.combo = combo
        self.product_id = None
        self.prefix = ""
        controller.language_changed.connect(self.refresh)

    @Slot(str)
    def refresh(self, _code):
        if self.product_id is None:
            return
        index = self.combo.findData(self.product_id)
        if index >= 0:
            with QSignalBlocker(self.combo):
                self.combo.setItemText(index, self.prefix + _text("Ανενεργό"))


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


class ProductionStockError(ValueError):
    def __init__(self, product: str, sold: float, proposed: float, *, field=None, unit=None):
        super().__init__("Existing sales require more production")
        self.product = product
        self.sold = sold
        self.proposed = proposed
        self.field = field
        self.unit = unit


def ensure_production_stock(db, production_id: int, *, product_id=None, quantity=0.0, field_id=None):
    """Check an edit/deletion without writing; None target means deletion.

    Page initialization/refresh already repairs legacy links via ensure_product_links.
    Like SalesPage, totals include all fields/years and inactive-product history.
    Valid IDs, not historical names, own stock even after a product rename.
    """
    old = db.query_one("SELECT product_id,field_id FROM production WHERE id=?", (production_id,))
    if old is None:
        return
    # A fresh profile may reach Production before the lazy Sales page creates
    # its table. There are no sales to constrain production in that case.
    if db.query_one("SELECT 1 FROM sqlite_master WHERE type='table' AND name='production_sales'") is None:
        return
    for affected_id in dict.fromkeys((old["product_id"], product_id)):
        if affected_id is None:
            continue
        totals = db.query_one(
            """SELECT
                (SELECT COALESCE(SUM(quantity_kg),0) FROM production
                 WHERE product_id=? AND id<>?) AS remaining,
                (SELECT COALESCE(SUM(quantity_kg),0) FROM production_sales
                 WHERE product_id=?) AS sold""",
            (affected_id, production_id, affected_id),
        )
        proposed = float(totals["remaining"]) + (quantity if affected_id == product_id else 0.0)
        sold = float(totals["sold"])
        # Match SalesPage.save_sale's practical floating-point tolerance.
        if proposed + 0.000001 < sold:
            product = product_row(db, affected_id)
            raise ProductionStockError(product["name"] if product else str(affected_id), sold, proposed)

    # Moving/removing production must also preserve its explicit field-sale history.
    if old["field_id"] is not None and old["product_id"] is not None:
        from .report_quantities import source_rows
        remaining = sum(float(r["quantity_kg"] or 0) for r in source_rows(
            db, "production", product_id=old["product_id"], field_id=old["field_id"])
            if r["id"] != production_id)
        proposed = remaining + (quantity if product_id == old["product_id"] and field_id == old["field_id"] else 0)
        sold = sum(float(r["quantity_kg"] or 0) for r in source_rows(
            db, "production_sales", product_id=old["product_id"], source=old["field_id"]))
        if proposed + 0.000001 < sold:
            product = product_row(db, old["product_id"])
            field = db.query_one("SELECT name FROM fields WHERE id=?", (old["field_id"],))
            raise ProductionStockError(product["name"], sold, proposed,
                                       field=field["name"] if field else str(old["field_id"]), unit=product["unit"])


def product_row(db, product_id: int | None):
    if product_id is None:
        return None
    return db.query_one(
        "SELECT id,name,unit,is_active FROM products WHERE id=?",
        (product_id,),
    )


def add_product_choices(combo, db, *, selected_id=None, legacy_name="") -> None:
    """Active products for new records; retain selected inactive/legacy value."""
    label = getattr(combo, "_mastixa_inactive_product_label", None)
    if label is not None:
        label.product_id = None
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
            prefix = f"{row['name']} ({row['unit']}) — "
            combo.addItem(
                prefix + _text("Ανενεργό"),
                int(row["id"]),
            )
            controller = _language()
            if controller is not None:
                if label is None:
                    label = _InactiveProductLabel(combo, controller)
                    combo._mastixa_inactive_product_label = label
                label.product_id = int(row["id"])
                label.prefix = prefix
            included.add(int(row["id"]))

    index = combo.findData(selected_id)
    if index >= 0:
        combo.setCurrentIndex(index)
    elif legacy_name:
        combo.addItem(f"{legacy_name} — Legacy", None)
        combo.setCurrentIndex(combo.count() - 1)
    else:
        combo.setCurrentIndex(0)
