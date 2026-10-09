"""Remove the unused VirtualKeyboard module and its indirectly collected plugin."""
from pathlib import PureWindowsPath


# The Windows app is Widgets-only. These six DLLs are orphaned descendants
# of the excluded VirtualKeyboard plugin in the 6.11.2 dependency graph.
# QtGui's system OpenGL support remains. The unused Mesa/LLVM software fallback
# is separately qualified for exclusion in WINDOWS_MESA_NATIVE_QUALIFICATION.md.
UNUSED_QT_DLLS = frozenset({
    "qt6quick.dll", "qt6qml.dll", "qt6qmlmeta.dll", "qt6qmlmodels.dll",
    "qt6qmlworkerscript.dll", "qt6opengl.dll",
})

# Kept as source-audit provenance, but upstream README marks this as a test font.
SOURCE_ONLY_LEGAL_SUFFIX = "licenses/QtPdf-6.11.2/pdfium/third_party/NotoSansCJK/LICENSE"


def excluded_windows_file(value):
    """Windows 10+ supplies UCRT/API sets; never copy tool-PATH versions."""
    path = PureWindowsPath(str(value))
    name = path.name.casefold()
    return ("virtualkeyboard" in path.as_posix().casefold()
            or path.as_posix().casefold().endswith(SOURCE_ONLY_LEGAL_SUFFIX.casefold())
            or name in UNUSED_QT_DLLS
            or name == "opengl32sw.dll"
            or name == "ucrtbase.dll"
            or (name.startswith(("api-ms-win-", "ext-ms-win-")) and name.endswith(".dll")))


def without_unused_windows_components(entries):
    return [entry for entry in entries if not any(
        excluded_windows_file(value) for value in entry[:2]
    )]


def without_virtualkeyboard(entries):
    return [entry for entry in entries if not any(
        "virtualkeyboard" in PureWindowsPath(str(value)).as_posix().casefold()
        for value in entry[:2]
    )]
