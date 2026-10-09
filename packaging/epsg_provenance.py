"""Hash-locked, metadata-only EPSG provenance overlay for the Windows bundle.

Supplier wheels/databases are immutable. Only the build-work copy is adapted;
accuracy, grids, parameters, interpolation context and ranking stay untouched.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import closing
import re
from pathlib import Path
import shutil
import sqlite3

DB_DESTINATION = "pyproj/proj_dir/share/proj/proj.db"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def policy(root):
    return json.loads((Path(root) / "packaging/windows-epsg-provenance.json").read_text(encoding="utf-8"))


def configuration_errors(root):
    try:
        lock = policy(root)
        if (lock.get("schema") != 1 or set(lock["operation_notes"]) != {"1312", "1462", "7001"}
                or any(not re.fullmatch(r"[0-9a-f]{64}", lock[key]) for key in ("input_sha256", "output_sha256"))
                or lock["input_sha256"] == lock["output_sha256"]
                or "unofficial" not in lock["alias_name"]
                or any("PROJ" not in note or "NOT" not in note for note in lock["operation_notes"].values())):
            return ["EPSG: invalid/unqualified provenance policy"]
    except (OSError, ValueError, KeyError, TypeError):
        return ["EPSG: missing/invalid provenance policy"]
    return []


def prepare(source, destination, root):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    lock = policy(root)
    if configuration_errors(root):
        raise ValueError("EPSG: invalid/unqualified provenance policy")
    if source == destination or destination.is_relative_to(source.parent):
        raise ValueError("EPSG: overlay must be outside the immutable supplier data directory")
    if digest(source) != lock["input_sha256"]:
        raise ValueError("EPSG: unknown/changed supplier proj.db")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Existing work is never overwritten unless it is this exact qualified output.
    if destination.exists():
        if digest(destination) != lock["output_sha256"]:
            raise ValueError("EPSG: unknown existing work-copy database")
        return destination
    shutil.copyfile(source, destination)
    with closing(sqlite3.connect(destination)) as connection, connection:
        for code in (1312, 1462, 7001):
            cursor = connection.execute(
                "UPDATE grid_transformation SET description = description || ? "
                "WHERE auth_name = 'EPSG' AND code = ?",
                (" " + lock["operation_notes"][str(code)], code),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"EPSG: missing/duplicate operation {code}")
        cursor = connection.execute(
            "UPDATE projected_crs SET auth_name = 'PROJ', name = ?, description = ? "
            "WHERE auth_name = 'EPSG' AND code = 900913",
            (lock["alias_name"], lock["alias_note"]),
        )
        if cursor.rowcount != 1:
            raise ValueError("EPSG: missing/duplicate legacy alias")
        cursor = connection.execute(
            "UPDATE usage SET object_auth_name = 'PROJ' WHERE object_table_name = 'projected_crs' "
            "AND object_auth_name = 'EPSG' AND object_code = 900913"
        )
        if cursor.rowcount != 1:
            raise ValueError("EPSG: unexpected legacy alias usage")
    if digest(source) != lock["input_sha256"] or digest(destination) != lock["output_sha256"]:
        raise ValueError("EPSG: unqualified generated database; do not package")
    return destination


def normalize_analysis(entries, root, work_directory):
    entries = list(entries)
    databases = [entry for entry in entries if Path(entry[0]).name.casefold() == "proj.db"]
    if len(databases) != 1 or databases[0][0].replace("\\", "/") != DB_DESTINATION:
        raise ValueError("EPSG: missing, duplicate or relocated proj.db in Analysis")
    original = databases[0]
    derived = prepare(original[1], Path(work_directory) / "proj.db", root)
    return [(entry[0], str(derived), *entry[2:]) if entry is original else entry for entry in entries]


def bundle_errors(bundle, root):
    bundle = Path(bundle)
    databases = [p for p in bundle.rglob("*") if p.is_file() and p.name.casefold() == "proj.db"]
    expected = bundle / "_internal" / DB_DESTINATION
    if databases != [expected] or digest(expected) != policy(root)["output_sha256"]:
        return ["EPSG: missing, duplicate, relocated or unmarked bundle database"]
    return []


def verify_bundle(bundle, root):
    errors = bundle_errors(bundle, root)
    if errors:
        raise RuntimeError("\n".join(errors))
