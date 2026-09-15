from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Mapping


APP_DATA_FOLDER = "MastixaManager"
DATA_HOME_ENV = "MASTIXA_DATA_HOME"


def resolve_base_dir(
    *,
    frozen: bool | None = None,
    environ: Mapping[str, str] | None = None,
    module_file: str | Path = __file__,
) -> Path:
    """Return the writable root used for databases, profiles, backups and logs.

    Source checkouts keep their existing repository-local ``data`` and
    ``backups`` folders. Packaged Windows builds use LocalAppData, keeping user
    records separate from program files and safe across upgrades/uninstalls.
    ``MASTIXA_DATA_HOME`` is an explicit override used by diagnostics and
    packaged smoke tests.
    """
    values = os.environ if environ is None else environ
    override = str(values.get(DATA_HOME_ENV, "")).strip()
    if override:
        return Path(override).expanduser().resolve()

    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if not is_frozen:
        return Path(module_file).resolve().parent.parent

    local_app_data = str(values.get("LOCALAPPDATA", "")).strip()
    if local_app_data:
        return (Path(local_app_data) / APP_DATA_FOLDER).resolve()
    return (Path.home() / "AppData" / "Local" / APP_DATA_FOLDER).resolve()


BASE_DIR = resolve_base_dir()
