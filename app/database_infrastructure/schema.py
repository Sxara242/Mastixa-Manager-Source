SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT
);
"""
