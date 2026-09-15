from pathlib import Path


repo_root = Path(SPECPATH).resolve().parent
app_icon = repo_root / "packaging" / "mastixa_manager.ico"

analysis = Analysis(
    [str(repo_root / "main.py")],
    pathex=[str(repo_root)],
    binaries=[],
    datas=[
        (str(repo_root / "app" / "assets"), "app/assets"),
        (str(repo_root / "app" / "locales"), "app/locales"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "test", "tests"],
    noarchive=False,
    optimize=1,
)

# The Codex build runtime exposes Poppler's ICU 78 DLLs on PATH. Qt 6 on
# Windows links against the operating system ICU API; bundling Poppler's
# same-named DLL would shadow that API and prevent QtCore from loading.
incompatible_icu = {"icuuc.dll", "icudt78.dll"}
analysis.binaries = [
    entry
    for entry in analysis.binaries
    if Path(entry[0]).name.casefold() not in incompatible_icu
]

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="MastixaManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(app_icon),
    version=str(repo_root / "packaging" / "version_info.txt"),
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MastixaManager",
)
