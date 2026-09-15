from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage

from . import icon_normalization


_INSTALLED = False
_ALPHA_PRESENT_TABLE = bytes(
    0 if value <= icon_normalization._ALPHA_CUTOFF else 1
    for value in range(256)
)


def _alpha_bounds_reference(image: QImage) -> QRect:
    """Reference implementation retained as a compatibility fallback."""
    left, top = image.width(), image.height()
    right = bottom = -1
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() <= icon_normalization._ALPHA_CUTOFF:
                continue
            left = min(left, x)
            right = max(right, x)
            top = min(top, y)
            bottom = max(bottom, y)
    if right < left or bottom < top:
        return QRect()
    return QRect(left, top, right - left + 1, bottom - top + 1)


def _alpha_bounds_fast(image: QImage) -> QRect:
    """Find visible-alpha bounds without one Python/Qt call per pixel.

    The previous implementation called pixelColor() for every pixel. Generated
    menu icons are up to 384x384 during normalization, so first use of several
    uncached icons could spend seconds crossing the Python/C++ boundary.

    RGBA8888 has byte-ordered channels, which lets Python's bytes slicing,
    translate(), find() and rfind() do the pixel scanning in native code while
    keeping the exact alpha cutoff used by the existing normalization.
    """
    width, height = image.width(), image.height()
    if width <= 0 or height <= 0:
        return QRect()

    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    stride = rgba.bytesPerLine()
    expected = stride * height

    try:
        raw = bytes(rgba.constBits())
    except (TypeError, ValueError, BufferError):
        raw = b""

    if len(raw) < expected:
        return _alpha_bounds_reference(image)

    left, top = width, height
    right = bottom = -1
    table = _ALPHA_PRESENT_TABLE

    for y in range(height):
        row_start = y * stride
        alpha = raw[row_start + 3 : row_start + width * 4 : 4].translate(table)
        first = alpha.find(b"\x01")
        if first < 0:
            continue
        last = alpha.rfind(b"\x01")
        if first < left:
            left = first
        if last > right:
            right = last
        if top == height:
            top = y
        bottom = y

    if right < left or bottom < top:
        return QRect()
    return QRect(left, top, right - left + 1, bottom - top + 1)


def install_icon_normalization_performance() -> None:
    """Use bulk alpha reads for normalization without changing visual rules."""
    global _INSTALLED
    if _INSTALLED:
        return

    icon_normalization._alpha_bounds = _alpha_bounds_fast
    icon_normalization._mastixa_bulk_alpha_bounds = True
    _INSTALLED = True
