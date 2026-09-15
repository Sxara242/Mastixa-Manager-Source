from __future__ import annotations

from collections import deque
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap

from . import icon_theme


_INSTALLED = False
_CANVAS_SIZE = 256
_CONTENT_FRACTION = 0.88
_OUTER_SEED_FRACTION = 0.18
_ALPHA_CUTOFF = 12


def _is_background_candidate(color: QColor) -> bool:
    """Match transparent or near-white neutral pixels, not interior coloured detail."""
    if color.alpha() <= _ALPHA_CUTOFF:
        return True
    channels = (color.red(), color.green(), color.blue())
    return min(channels) >= 222 and max(channels) - min(channels) <= 30


def _clear_outer_white_component(image: QImage) -> QImage:
    """Remove only near-white background connected to the outer icon band.

    The shipped 3D PNGs use different white cards/halos and different amounts
    of padding.  Seeding the outer band avoids treating white details in the
    centre of an icon (paper, highlights, etc.) as background unless they are
    actually connected to that surrounding white card.
    """
    work = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = work.width(), work.height()
    if width <= 0 or height <= 0:
        return work

    band_x = max(1, int(width * _OUTER_SEED_FRACTION))
    band_y = max(1, int(height * _OUTER_SEED_FRACTION))
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def add_seed(x: int, y: int) -> None:
        index = y * width + x
        if visited[index]:
            return
        if not _is_background_candidate(work.pixelColor(x, y)):
            return
        visited[index] = 1
        queue.append((x, y))

    for y in range(height):
        for x in range(width):
            if x < band_x or x >= width - band_x or y < band_y or y >= height - band_y:
                add_seed(x, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            index = ny * width + nx
            if visited[index]:
                continue
            if not _is_background_candidate(work.pixelColor(nx, ny)):
                continue
            visited[index] = 1
            queue.append((nx, ny))

    transparent = QColor(0, 0, 0, 0)
    for y in range(height):
        offset = y * width
        for x in range(width):
            if visited[offset + x]:
                work.setPixelColor(x, y, transparent)
    return work


def _alpha_bounds(image: QImage) -> QRect:
    left, top = image.width(), image.height()
    right = bottom = -1
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() <= _ALPHA_CUTOFF:
                continue
            left = min(left, x)
            right = max(right, x)
            top = min(top, y)
            bottom = max(bottom, y)
    if right < left or bottom < top:
        return QRect()
    return QRect(left, top, right - left + 1, bottom - top + 1)


def _has_shaped_transparency(image: QImage) -> bool:
    """Return True when the artwork is already cut out on transparency.

    New icon assets are delivered as circular artwork on a transparent canvas.
    Their metallic silver ring is intentionally near-white, so the legacy white-
    card cleanup must not flood-fill it as background.  A real white card has an
    opaque rectangular alpha bound; shaped/circular artwork leaves transparent
    corners inside that bound.
    """
    bounds = _alpha_bounds(image)
    if bounds.isNull() or bounds.isEmpty():
        return False

    corners = (
        (bounds.left(), bounds.top()),
        (bounds.right(), bounds.top()),
        (bounds.left(), bounds.bottom()),
        (bounds.right(), bounds.bottom()),
    )
    transparent_corners = sum(
        image.pixelColor(x, y).alpha() <= _ALPHA_CUTOFF for x, y in corners
    )
    return transparent_corners >= 3


def _normalize_image(source: QImage) -> QImage:
    """Return a transparent, cropped and visually centred square icon canvas."""
    if source.isNull():
        return QImage()

    # Process at a bounded resolution: UI icons are displayed at <= 96 px and
    # the original generated PNGs are much larger.
    longest = max(source.width(), source.height())
    if longest > 384:
        source = source.scaled(
            384,
            384,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    # Already-cut-out transparent artwork must keep its metallic/white ring.
    # Only legacy rectangular white-card assets need the flood-fill cleanup.
    cleaned = source if _has_shaped_transparency(source) else _clear_outer_white_component(source)
    bounds = _alpha_bounds(cleaned)
    if bounds.isNull() or bounds.isEmpty():
        return source

    cropped = cleaned.copy(bounds)
    target = max(1, int(_CANVAS_SIZE * _CONTENT_FRACTION))
    scaled = cropped.scaled(
        target,
        target,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    canvas = QImage(
        QSize(_CANVAS_SIZE, _CANVAS_SIZE),
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    canvas.fill(Qt.GlobalColor.transparent)
    x = (_CANVAS_SIZE - scaled.width()) // 2
    y = (_CANVAS_SIZE - scaled.height()) // 2
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.drawImage(x, y, scaled)
    painter.end()
    return canvas


def _normalized_icon(path: Path, cache: dict[Path, QIcon]) -> QIcon | None:
    cached = cache.get(path)
    if cached is not None:
        return cached
    image = QImage(str(path))
    if image.isNull():
        return None
    normalized = _normalize_image(image)
    if normalized.isNull():
        return None
    icon = QIcon(QPixmap.fromImage(normalized))
    if icon.isNull():
        return None
    cache[path] = icon
    return icon


def install_icon_normalization() -> None:
    """Normalize all themed menu/tab/title icons once, preserving their artwork."""
    global _INSTALLED
    if _INSTALLED:
        return

    normalized_cache: dict[Path, QIcon] = {}

    def icon_for_text(text: str) -> QIcon | None:
        path = icon_theme._path_for_text(text)
        if path is None or not path.exists():
            return None
        return _normalized_icon(path, normalized_cache)

    # One visual title size for every icon.  The normalized transparent canvas
    # makes ad-hoc per-file compensations unnecessary.
    common_title_size = QSize(88, 88)
    icon_theme._TITLE_ICON_SIZE = common_title_size
    icon_theme._TITLE_ICON_SIZE_LARGE = common_title_size
    icon_theme._LARGE_TITLE_ICON_FILES = set()
    icon_theme._CUSTOM_TITLE_ICON_SIZES = {}
    icon_theme._ICON_CACHE.clear()
    icon_theme._icon_for_text = icon_for_text
    icon_theme._mastixa_normalized_icon_cache = normalized_cache
    _INSTALLED = True
