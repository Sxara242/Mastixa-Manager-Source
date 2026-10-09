"""Connection-local enforcement for dated writes, including indirect projections.

TEMP triggers leave historical databases/schema portable. Every writable Database
connection checks both OLD and NEW years; correction permission is process-local.
"""
from .year_lock_robustness import _YEAR_SOURCES


DATED_TABLES = {table: expression for table, expression, _ in _YEAR_SOURCES
                if table != 'year_locks'} | {
    'equipment_maintenance': 'CAST(SUBSTR(service_date,1,4) AS INTEGER)',
    'invoice_documents': 'CAST(SUBSTR(invoice_date,1,4) AS INTEGER)',
}


def install_write_policy(connection, path):
    from .year_context import _CORRECTIONS, _db_key
    from types import SimpleNamespace
    key = _db_key(SimpleNamespace(path=path))
    connection.create_function('mastixa_correction_year', 0,
                               lambda: _CORRECTIONS[key].year if key in _CORRECTIONS else -1)
    connection.create_function('mastixa_correction_reason', 0,
                               lambda: _CORRECTIONS[key].reason if key in _CORRECTIONS else '')
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'year_locks' not in tables:
        return
    for table, expression in DATED_TABLES.items():
        if table not in tables:
            continue
        # Older optional schemas may lack their date column until migrated.
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info({table})')}
        column = expression.split('SUBSTR(')[1].split(',')[0] if 'SUBSTR(' in expression else expression
        if column not in columns:
            continue
        for action, versions in (('INSERT', ('NEW',)), ('UPDATE', ('OLD', 'NEW')), ('DELETE', ('OLD',))):
            years = [f"CAST({expression.replace(column, f'{version}.{column}')} AS INTEGER)" for version in versions]
            blocked = ' OR '.join(
                f"(EXISTS(SELECT 1 FROM year_locks WHERE year={year} AND is_locked=1) "
                f"AND {year}<>mastixa_correction_year())" for year in years)
            connection.execute(f"""CREATE TEMP TRIGGER owner_lock_{table}_{action}
                BEFORE {action} ON main.{table} WHEN {blocked}
                BEGIN SELECT RAISE(ABORT,'Κλειδωμένο έτος — Μόνο προβολή. Ασφάλεια → Κλείδωμα Έτους → Προσωρινή διόρθωση.'); END""")
            if 'audit_events' in tables:
                corrected = ' OR '.join(f'{year}=mastixa_correction_year()' for year in years)
                version = versions[-1]
                identifier = 'id' if 'id' in columns else 'generation_key' if 'generation_key' in columns else None
                record_id = f'CAST({version}.{identifier} AS TEXT)' if identifier else "''"
                connection.execute(f"""CREATE TEMP TRIGGER owner_correction_{table}_{action}
                    AFTER {action} ON main.{table} WHEN {corrected}
                    BEGIN INSERT INTO audit_events(event_time,table_name,action,record_id,details)
                    VALUES(datetime('now','localtime'),'{table}','{action}',{record_id},
                    'Προσωρινή διόρθωση ' || mastixa_correction_year() || ' | Αιτιολογία: ' || mastixa_correction_reason()); END""")
