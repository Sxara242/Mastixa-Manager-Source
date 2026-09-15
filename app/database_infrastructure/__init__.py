from .schema import SCHEMA
SCHEMA_VERSION=2

# Compatibility shim for existing imports.
try:
    from ..database import Database
except Exception:
    Database=None
