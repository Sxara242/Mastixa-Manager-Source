"""Managed invoice ownership, independent of the currently selected UI profile."""
from pathlib import Path
import re
import sqlite3
from contextlib import closing

from .runtime_paths import BASE_DIR

LEGACY_FILES_DIR = BASE_DIR / "data" / "invoice_documents"
ATTACHMENT_MAX_BYTES = 20 * 1024**2


def managed_name(value: str) -> str:
    name = str(value)
    # Existing imports generate UUID + extension. Permit safe historical names,
    # but never Windows device names, ADS, separators or ambiguous components.
    if (not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,199}", name)
            or ".." in name or name.endswith(".")
            or Path(name).suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".pdf"}
            or name.split(".")[0].upper() in
            {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
             *(f"LPT{i}" for i in range(1, 10))}):
        raise ValueError("Unsafe managed invoice filename")
    return name


def owned_root(database_path: Path) -> Path:
    database = Path(database_path).resolve()
    root = database.parent / (database.name + ".attachments") / "invoice_documents"
    # Reject redirected directories, including Windows junctions.
    if root.resolve() != root:
        raise ValueError("Redirected invoice attachment directory")
    return root


def contained_file(root: Path, name: str) -> Path:
    root = Path(root).absolute()
    candidate = root / managed_name(name)
    if root.resolve() != root or candidate.resolve() != candidate:
        raise ValueError("Redirected invoice attachment path")
    return candidate


def owned_file(database_path: Path, name: str) -> Path:
    return contained_file(owned_root(database_path), name)


def resolve_file(database_path: Path, name: str, legacy_root: Path = LEGACY_FILES_DIR) -> Path:
    owned = owned_file(database_path, name)
    if owned.exists():
        return owned
    legacy = contained_file(legacy_root, name)
    return legacy if legacy.is_file() else owned


def referenced_names(database_path: Path) -> set[str]:
    with closing(sqlite3.connect(Path(database_path).resolve().as_uri() + "?mode=ro", uri=True)) as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='invoice_documents'").fetchone():
            return set()
        names = {managed_name(row[0]) for row in con.execute("SELECT stored_filename FROM invoice_documents")}
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("Conflicting invoice attachment filenames")
    return names
