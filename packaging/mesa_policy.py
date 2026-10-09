"""Build-only rejection of the qualified unused Mesa/LLVM fallback.

Mastixa uses raster Widgets; adding an OpenGL consumer requires fresh native
qualification. This policy does not restrict users replacing installed Qt DLLs.
"""
from pathlib import Path, PureWindowsPath
import hashlib

MESA_FILENAME = "opengl32sw.dll"
# Exact excluded wheel member plus its retained Qt supplier signing variants.
MESA_SHA256 = frozenset({
    "34b444c016289b560662ff896deceb7f4b2c0723aed3d319ae167c9186ce42b3",
    "b04de4541863bc7d8879040a78889c4849c1b1da2784c4630f734c146c2998ce",
    "d303dd60bbf11418063f4bb72292e481ca1e88d84915fbd049a21666b92c0ee0",
})


def is_mesa_filename(value):
    return PureWindowsPath(str(value)).name.casefold() == MESA_FILENAME


def verify_analysis(entries):
    for destination, source, *rest in entries:
        if is_mesa_filename(destination) or is_mesa_filename(source):
            raise RuntimeError(f"Excluded Mesa/LLVM fallback in Analysis: {destination}")
        path = Path(source)
        if (path.is_file() and path.suffix.casefold() in {".dll", ".pyd"}
                and hashlib.sha256(path.read_bytes()).hexdigest() in MESA_SHA256):
            raise RuntimeError(f"Renamed excluded Mesa/LLVM fallback: {destination}")


def bundle_errors(bundle):
    errors = []
    for path in Path(bundle).rglob("*"):
        if not path.is_file():
            continue
        if is_mesa_filename(path) or (
            path.suffix.casefold() in {".dll", ".pyd"}
            and hashlib.sha256(path.read_bytes()).hexdigest() in MESA_SHA256
        ):
            errors.append(f"Excluded Mesa/LLVM fallback in bundle: {path.relative_to(bundle).as_posix()}")
    return errors


def verify_bundle(bundle):
    errors = bundle_errors(bundle)
    if errors:
        raise RuntimeError("\n".join(errors))
