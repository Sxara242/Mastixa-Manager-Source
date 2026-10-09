"""Read-only report quantities. Registry identity owns units, never column names."""
from .ui_helpers import compact_decimal


def table_exists(db, table):
    return db.query_one("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)) is not None


def product_rows(db):
    return db.query("SELECT id,name,unit FROM products ORDER BY name,id") if table_exists(db, "products") else []


def identify_rows(db, rows):
    products = {r["id"]: dict(r) for r in product_rows(db)}
    names = {}
    for product in products.values():
        names.setdefault(product["name"].strip().casefold(), []).append(product)
    result = []
    for source in rows:
        row = dict(source)
        product = products.get(row.get("product_id"))
        name = str(row.get("product") or "")
        matches = names.get(name.strip().casefold(), [])
        if product is None and len(matches) == 1:
            product = matches[0]
        row["product_key"] = ("id", product["id"]) if product else ("legacy", name)
        row["product_name"] = product["name"] if product else name or "—"
        row["unit"] = str(product["unit"] or "") if product else ""
        result.append(row)
    return result


def source_rows(db, table, year=None, *, through=False, product_id=None, field_id=None,
                source="all", exclude_sale_id=None):
    if table not in ("production", "production_sales"):
        raise ValueError("Unsupported quantity source")
    if not table_exists(db, table):
        return []
    date = "entry_date" if table == "production" else "sale_date"
    where, params = [], []
    if year is not None:
        where.append(f"SUBSTR({date},1,4){'<=' if through else '='}?")
        params.append(str(year))
    if field_id is not None:
        where.append("field_id=?")
        params.append(field_id)
    rows = identify_rows(db, db.query(f"SELECT * FROM {table}" + (" WHERE " + " AND ".join(where) if where else ""), params))
    return [r for r in rows
            if (product_id is None or r["product_key"] == ("id", product_id))
            and (table != "production_sales" or (
                r.get("id") != exclude_sale_id
                and matches_sale_source(r, source)))]


def matches_sale_source(row, source):
    return source == "all" or row.get("source_field_id") == (None if source == "pooled" else source)


def sale_source_quantities(db, product_id=None, *, source="all", year=None, through=False, exclude_sale_id=None):
    """Field remainder is attributed only; pooled sales never get distributed."""
    production = quantities(db, year=year, product_id=product_id, through=through,
                            field_id=source if isinstance(source, int) else None)
    sales = quantities(db, "production_sales", year, product_id=product_id, through=through,
                       source=source, exclude_sale_id=exclude_sale_id)
    return production, sales, stock_quantities(production, sales)


def sale_availability(db, product_id, source_field_id=None, exclude_sale_id=None):
    if product_id is None:
        return 0.0
    _, _, total = sale_source_quantities(db, product_id, exclude_sale_id=exclude_sale_id)
    available = sum(g["quantity"] for g in total)
    if source_field_id is not None:
        _, _, field = sale_source_quantities(db, product_id, source=source_field_id, exclude_sale_id=exclude_sale_id)
        available = min(available, sum(g["quantity"] for g in field))
    return available


def sale_source_fields(db, product_id=None):
    """Real production fields plus explicitly stored sale history for report filters."""
    fields = {row["id"]: row["name"] for row in db.query("SELECT id,name FROM fields")}
    result = {}
    for row in source_rows(db, "production", product_id=product_id):
        field = row.get("field_id")
        if field in fields:
            result[field] = fields[field]
    for row in source_rows(db, "production_sales", product_id=product_id):
        field = row.get("source_field_id")
        if field is not None:
            result.setdefault(field, fields.get(field, row.get("source_field_name") or f"#{field}"))
    return sorted(result.items(), key=lambda item: (item[1], item[0]))


def group_quantities(rows):
    groups = {}
    for row in rows:
        key = row["product_key"]
        group = groups.setdefault(key, dict(key=key, product=row["product_name"], unit=row["unit"], quantity=0.0, revenue=0.0))
        group["quantity"] += float(row.get("quantity_kg") or 0)
        group["revenue"] += float(row.get("total_amount") or 0)
    return sorted(groups.values(), key=lambda g: (g["product"], str(g["key"])))


def quantities(db, table="production", year=None, **filters):
    return group_quantities(source_rows(db, table, year, **filters))


def stock_quantities(production, sales):
    groups = {g["key"]: dict(g) for g in production}
    for sale in sales:
        group = groups.setdefault(sale["key"], dict(sale, quantity=0.0))
        group["quantity"] -= sale["quantity"]
    return [dict(g, quantity=max(g["quantity"], 0.0)) for g in groups.values()]


def quantity_text(groups):
    if not groups:
        return "—"
    multiple = len(groups) > 1
    return "; ".join(
        (g["product"] + ": " if multiple else "")
        + compact_decimal(g["quantity"], 3) + " " + (g["unit"] or "[?]")
        for g in groups
    )


def coherent_quantity(groups, *, single_product=False):
    if not groups or (single_product and len(groups) != 1):
        return None
    units = {g["unit"] for g in groups}
    if len(units) != 1 or not next(iter(units)):
        return None
    return sum(g["quantity"] for g in groups), next(iter(units))


def average_price_text(groups):
    coherent = coherent_quantity(groups, single_product=True)
    if coherent is None or coherent[0] <= 0:
        return "—"
    return f"{compact_decimal(sum(g['revenue'] for g in groups) / coherent[0], 2)} €/{coherent[1]}"


def grams_per_tree(groups, trees):
    coherent = coherent_quantity(groups)
    if coherent is None or trees <= 0 or coherent[1] not in ("kg", "g"):
        return None
    return coherent[0] * (1000 if coherent[1] == "kg" else 1) / trees


def money_total(db, table, year=None):
    if table not in ("income", "expenses"):
        raise ValueError("Unsupported financial source")
    where = " WHERE SUBSTR(entry_date,1,4)=?" if year is not None else ""
    return float(db.query_one(f"SELECT COALESCE(SUM(amount),0) FROM {table}{where}", (str(year),) if year is not None else ())[0])


def unposted_activity_cost(db, field_id, year=None):
    if not table_exists(db, "farm_activities"):
        return 0.0
    columns = {r["name"] for r in db.query("PRAGMA table_info(farm_activities)")}
    if "cost" not in columns:
        return 0.0
    where, params = ["a.field_id=?"], [field_id]
    if year is not None:
        where.append("SUBSTR(a.activity_date,1,4)=?")
        params.append(str(year))
    expense_columns = {r["name"] for r in db.query("PRAGMA table_info(expenses)")}
    if {"source_type", "source_id"} <= expense_columns:
        where.append("NOT EXISTS (SELECT 1 FROM expenses e WHERE e.source_type='farm_activity' AND e.source_id=a.id)")
    return float(db.query_one("SELECT COALESCE(SUM(a.cost),0) FROM farm_activities a WHERE " + " AND ".join(where), params)[0])
