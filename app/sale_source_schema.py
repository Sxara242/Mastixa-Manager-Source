"""Additive sale provenance; NULL is deliberately unallocated, never backfilled."""


def migrate_sale_sources(con):
    columns = {row["name"] for row in con.execute("PRAGMA table_info(production_sales)")}
    if not columns:
        return
    if "source_field_id" not in columns:
        con.execute("ALTER TABLE production_sales ADD COLUMN source_field_id INTEGER REFERENCES fields(id) ON DELETE RESTRICT")
    if "source_field_name" not in columns:
        con.execute("ALTER TABLE production_sales ADD COLUMN source_field_name TEXT NOT NULL DEFAULT ''")
    con.execute("CREATE INDEX IF NOT EXISTS idx_sales_source_field ON production_sales(source_field_id)")


def install_source_audit(con):
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='audit_events' AND type='table'").fetchone():
        return
    for action, record in (("insert", "NEW"), ("update", "NEW"), ("delete", "OLD")):
        name = "audit_production_sales_" + action
        existing = con.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (name,)).fetchone()
        if existing and "source_field_name" in existing[0]:
            continue
        con.execute(f"DROP TRIGGER IF EXISTS {name}")
        con.execute(f"""CREATE TRIGGER {name} AFTER {action.upper()} ON production_sales
            BEGIN
              INSERT INTO audit_events(event_time,table_name,action,record_id,details)
              VALUES(datetime('now','localtime'),'production_sales','{action.upper()}',CAST({record}.id AS TEXT),
                'Πώληση: '||{record}.buyer_name||' | '||ROUND({record}.quantity_kg,3)||' '||
                COALESCE((SELECT unit FROM products WHERE id={record}.product_id),'[?]')||' | '||
                ROUND({record}.total_amount,2)||' € | Πηγή: '||
                CASE WHEN {record}.source_field_id IS NULL THEN 'Συνολικό απόθεμα'
                     ELSE {record}.source_field_name||' [#'||{record}.source_field_id||']' END);
            END""")
