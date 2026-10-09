from __future__ import annotations

from collections import deque
import hashlib
import math
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap

from . import icon_theme


_INSTALLED = False
_CANVAS_SIZE = 256
_CONTENT_FRACTION = 0.84
_OUTER_SEED_FRACTION = 0.18
_ALPHA_CUTOFF = 12
_WHITE_RING_MIN_CHANNEL = 222
_WHITE_RING_MAX_CHROMA = 30
_WHITE_RING_SCAN_RAYS = 144
_WHITE_RING_SCAN_INNER_RADIUS = 0.62
_WHITE_RING_MIN_COVERAGE = 0.55
_WHITE_RING_MAX_BOUNDARY_SPREAD = 0.10
_WHITE_RING_MIN_RUN_FRACTION = 0.022
_WHITE_RING_MAX_LEADING_FRACTION = 0.040

# Only these exact bundled source files have passed the alpha-mask prototype
# contract. Names alone must never opt an unreviewed image out of legacy cleanup.
# This is source provenance metadata, not per-icon runtime pixel processing.
_MASKED_SOURCE_SHA256 = {
    "irrigation_fertilization.png": "d7fd365f919b417254b5467a3c612a8e164e851862201a085f2e09a5d96465a4",
    "labor.png": "79888a966f1c6d25b4536015af74ff9e800cbd920d1d071c5b35ff20aec9c07b",
    "partners.png": "43793eeda59ab5d0c1f021aaa67d4ffe7f036d5492f186e2212f7004d17580bc",
    "finance.png": "4e8b91feb5858d709a90f075876498ffacbcd7ab9b5fd1653d5442b496f0d99e",
}
# Phase 3 sources with separately frozen original-source preservation contracts.
# Keep provenance grouped by phase; no cleanup geometry belongs in runtime.
_PHASE3_MASKED_SOURCE_SHA256 = {
    "cultivation.png": "9a5f708560dcd7905c23260b32a1a94325145a74fb5af3f3335b1552e885c32e",
    "expenses.png": "7675670abb13a1b010964492905ac6c35996d39ac862c769fb6671c0462cca6f",
    "income.png": "1cc81503331e659df93bc60a04c646c1c85ba8c2c04726b33575b22246aa1194",
    "invoice_documents.png": "8eb084bf43fa00f995c8d8f5e0aade1cd3b8ac19267e87f4f3c272ddbd00f4e9",
    "plant_protection.png": "12250e3cdd3e4ad6654cdc7e6c6952e71a7cfb67f853229ce3350e5c9c53f829",
    "suppliers_buyers.png": "79b34ed80aa6338ebe6d7f168fdd70d9fa323de9e8fb170c8ecd0d56e60b6e70",
    "warehouse.png": "681a696f1c81dd1f7e7564aef2eb5f2c8b0543782a27b00df53af2f30154a624",
}

# Phase 4 owner-approved sources. Nine assets are canonical-badge
# recompositions and production.png is the separately approved preserved-source
# cleanup. Runtime uses only exact filename + canonical path + SHA-256 provenance;
# no Phase 4 reconstruction geometry runs at presentation time.
_PHASE4_RECOMPOSED_SOURCE_SHA256 = {
    "annual_report.png": "7a253801ca1e49f2e6938a1166da10b72d492c5fba543dd705dd50e4df63fc7b",
    "calendar.png": "0b48696c8d11243af656e6cbd2dd0466abce39479880e8c495c1680ba1fc743a",
    "alerts.png": "baaff9402af8ae8e71190d1a186d63334a498be33948ae02d6b847b3cf76e17c",
    "declaration.png": "07bba918ce36f672fdf0ed007af3b38c77ef952df21aec4cd24826d77ce4b9ac",
    "fields.png": "a9da70ac2d884c2d89bd05fdcc4950d206e510e641fb04b08c8d82df607c74cc",
    "producer.png": "d2106d33dc78db6ca31a479bb17a5241b7f8cf7a8a3af3232b55b5bab0c8f19c",
    "products.png": "c4bff4c1242183ac5e6999c67be185cf07040df8cd3bb92da321fe7514afc56b",
    "search.png": "3620338473f28b2f0e375b4b132210682c350d73d69c09d767f14dc43cde3255",
    "settings.png": "7068b3c047a06bc9eb1e908e416f7c955c796c1a5b13dbf7e77d9786a6d10da7",
}
# Post-Phase-4 runtime-QA recompositions. These two sources use the same
# owner-approved canonical badge geometry to eliminate gray bleed into the ring.
_RUNTIME_QA_RECOMPOSED_SOURCE_SHA256 = {
    "reports.png": "5fcfe0bf2edb60ea32c5daad8206ecfc1484638270527710c0868011d7d1c60c",
    "sales.png": "a48e14f56f7600658efeb06655db4f84938cf98c7e62c5f23488dccd53595994",
    "year_lock.png": "f7055b703ef6ecadf2543e17b914268f49871962f16261246190969288c3977b",
    "data_quality.png": "ecdc4e745d41836feff2547a7661016720b4bb67d29ae312a8d4b826cb8d6ee4",
    "tree_planting.png": "9ad2f9090600be84b8ecb1779cdad75318f0ec98eed0dd93e5e3d7d5bb9c52dd",
    "production.png": "e98a28ed47f281fbd60494306b85a4729ad3e28bc4cf1969c1d0908beda0ec85",
    "package_preview.png": "78508e8aa7237038729e178d7d5e1a76fe25664aaa9731b1c926f5f3b87c56fa",
    "field_profile.png": "76d25ae81a414157a51f3353f4579590011c32321a8aab391dd198652494387e",
}

# Exact-source optical presentation adjustments from real-app owner QA.
# Scale is applied after normal cleanup/presentation, so artwork/source pixels are
# not edited for the scale-only/position-only cases. Offsets are in 256px canvas pixels.
_RUNTIME_QA_PRESENTATION_OVERRIDES = {
    "field_costs.png": ("015c66bd32aebe450cc2293865d920b0a5ffb2f589ab2aa4e129579c3ec499fe", 1.05, 0, 0),
    "package_preview.png": ("78508e8aa7237038729e178d7d5e1a76fe25664aaa9731b1c926f5f3b87c56fa", 1.00, 0, 4),
}

_ANY_ALPHA_TABLE = bytes(0 if value == 0 else 1 for value in range(256))


def _is_background_candidate(color: QColor) -> bool:
    """Match transparent or near-white neutral pixels, not interior coloured detail."""
    if color.alpha() <= _ALPHA_CUTOFF:
        return True
    channels = (color.red(), color.green(), color.blue())
    return min(channels) >= 222 and max(channels) - min(channels) <= 30


def _clear_outer_component(image: QImage, predicate) -> QImage:
    """Clear candidate pixels connected to the outside band of an image."""
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
        if not predicate(work.pixelColor(x, y)):
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
            if not predicate(work.pixelColor(nx, ny)):
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


def _clear_outer_white_component(image: QImage) -> QImage:
    """Remove a legacy rectangular white card connected to the outer band."""
    return _clear_outer_component(image, _is_background_candidate)


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
    """Return True when the artwork is already cut out on transparency."""
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


def _is_outer_white_color(color: QColor) -> bool:
    """Return True only for the near-white neutral class used by legacy halos."""
    if color.alpha() <= _ALPHA_CUTOFF:
        return False
    channels = (color.red(), color.green(), color.blue())
    return (
        min(channels) >= _WHITE_RING_MIN_CHANNEL
        and max(channels) - min(channels) <= _WHITE_RING_MAX_CHROMA
    )


def _detect_outer_white_shell_radius(image: QImage, bounds: QRect) -> float | None:
    """Detect a *continuous* circular white shell and return its inner radius.

    A few bright metallic highlights must never be enough to trigger cleanup.
    We therefore sample many radial rays and only accept a white layer when it
    covers most of the circumference, has real radial thickness, and has a
    consistent inner boundary.  The returned radius is normalized to the
    circular badge radius (1.0 == the alpha bounds' outer circle).
    """
    if bounds.isNull() or bounds.isEmpty():
        return None

    width = bounds.width()
    height = bounds.height()
    longest = max(width, height)
    if longest <= 0 or abs(width - height) / float(longest) > 0.12:
        return None

    center_x = bounds.left() + (width - 1) / 2.0
    center_y = bounds.top() + (height - 1) / 2.0
    radius = max(1.0, min(width, height) / 2.0)
    radial_step = 1.0 / radius
    min_run_pixels = max(2, int(round(radius * _WHITE_RING_MIN_RUN_FRACTION)))
    max_leading_pixels = max(
        2, int(round(radius * _WHITE_RING_MAX_LEADING_FRACTION))
    )
    detect_alpha = max(_ALPHA_CUTOFF, 48)

    boundaries: list[float] = []
    thicknesses: list[float] = []
    total_steps = int(
        math.ceil((1.04 - _WHITE_RING_SCAN_INNER_RADIUS) / radial_step)
    ) + 1

    for ray in range(_WHITE_RING_SCAN_RAYS):
        angle = (2.0 * math.pi * ray) / _WHITE_RING_SCAN_RAYS
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        leading_pixels = 0
        run_pixels = 0
        run_outer_radius: float | None = None
        last_xy: tuple[int, int] | None = None

        for step_index in range(total_steps):
            normalized_radius = 1.04 - step_index * radial_step
            if normalized_radius < _WHITE_RING_SCAN_INNER_RADIUS:
                break

            x = int(round(center_x + cos_a * radius * normalized_radius))
            y = int(round(center_y + sin_a * radius * normalized_radius))
            if x < 0 or y < 0 or x >= image.width() or y >= image.height():
                continue
            if last_xy == (x, y):
                continue
            last_xy = (x, y)

            color = image.pixelColor(x, y)
            if color.alpha() <= detect_alpha:
                continue

            if _is_outer_white_color(color):
                if run_pixels == 0:
                    run_outer_radius = normalized_radius
                run_pixels += 1
                continue

            if run_pixels >= min_run_pixels and run_outer_radius is not None:
                boundary = min(1.0, normalized_radius + radial_step * 0.5)
                boundaries.append(boundary)
                thicknesses.append(max(0.0, run_outer_radius - boundary))
                break

            # A tiny white glint is a metallic highlight, not a shell. Keep
            # looking only while we are still very close to the outside.
            leading_pixels += max(1, run_pixels)
            run_pixels = 0
            run_outer_radius = None
            leading_pixels += 1
            if leading_pixels > max_leading_pixels:
                break

    minimum_rays = int(math.ceil(_WHITE_RING_SCAN_RAYS * _WHITE_RING_MIN_COVERAGE))
    if len(boundaries) < minimum_rays:
        return None

    boundaries.sort()
    thicknesses.sort()
    count = len(boundaries)
    q10 = boundaries[min(count - 1, int(count * 0.10))]
    q90 = boundaries[min(count - 1, int(count * 0.90))]
    if q90 - q10 > _WHITE_RING_MAX_BOUNDARY_SPREAD:
        return None

    median_thickness = thicknesses[count // 2]
    if median_thickness < min_run_pixels * radial_step * 0.75:
        return None

    # Use a conservative low percentile of the consistent boundary so no white
    # wedge is left behind.  A half-pixel inset removes the antialiased blend at
    # the white/metal transition.  The cut itself is perfectly circular, so it
    # cannot create cardinal seams or unequal top/bottom ring thickness.
    trimmed = boundaries[
        max(0, int(count * 0.08)) : max(1, count - int(count * 0.08))
    ]
    if not trimmed:
        trimmed = boundaries
    boundary_index = min(len(trimmed) - 1, int(len(trimmed) * 0.18))
    cut_radius = trimmed[boundary_index] - (0.5 / radius)
    return max(_WHITE_RING_SCAN_INNER_RADIUS, min(0.98, cut_radius))


def _clear_outer_light_neutral_ring(image: QImage) -> QImage:
    """Remove only a detected outer white shell with a symmetric circular cut.

    The old flood-fill could walk from white pixels into bright metallic
    highlights and create radial black seams or eat different amounts of the
    ring at different angles.  This version first proves that a continuous,
    near-white shell exists around most of the badge.  It then clears only the
    geometry outside that shell's inner boundary.  Everything inward is copied
    byte-for-byte, including metallic highlights, dark rim and coloured artwork.
    """
    work = image.convertToFormat(QImage.Format.Format_ARGB32)
    bounds = _alpha_bounds(work)
    if bounds.isNull() or bounds.isEmpty():
        return work

    cut_radius = _detect_outer_white_shell_radius(work, bounds)
    if cut_radius is None:
        return work

    width = bounds.width()
    height = bounds.height()
    center_x = bounds.left() + (width - 1) / 2.0
    center_y = bounds.top() + (height - 1) / 2.0
    radius = max(1.0, min(width, height) / 2.0)
    cut_sq = cut_radius * cut_radius
    transparent = QColor(0, 0, 0, 0)

    for y in range(bounds.top(), bounds.bottom() + 1):
        dy = (y - center_y) / radius
        for x in range(bounds.left(), bounds.right() + 1):
            dx = (x - center_x) / radius
            if dx * dx + dy * dy <= cut_sq:
                continue
            # Never erase medium silver, dark rim or coloured artwork.  Only
            # pixels that still belong to the detected near-white shell become
            # transparent. This keeps the metallic badge byte-for-byte intact
            # even when its outer silhouette is not a mathematically perfect
            # circle.
            if _is_outer_white_color(work.pixelColor(x, y)):
                work.setPixelColor(x, y, transparent)

    return work


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

    shaped = _has_shaped_transparency(source)
    cleaned = (
        _clear_outer_light_neutral_ring(source)
        if shaped
        else _clear_outer_white_component(source)
    )
    bounds = _alpha_bounds(cleaned)
    if bounds.isNull() or bounds.isEmpty():
        return source

    # Crop only after removing the disposable outer white ring.  Scaling is
    # proportional, so the metallic ring and all inward artwork keep their
    # original relationship while receiving consistent safe padding.
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


def _preserved_source_bounds(image: QImage) -> QRect:
    """Include every nonzero-alpha pixel, including faint valid protrusions."""
    rgba = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = rgba.width(), rgba.height()
    raw = bytes(rgba.constBits())
    stride = rgba.bytesPerLine()
    left, top, right, bottom = width, height, -1, -1
    for y in range(height):
        start = y * stride
        alpha = raw[start + 3 : start + width * 4 : 4].translate(_ANY_ALPHA_TABLE)
        first, last = alpha.find(b"\x01"), alpha.rfind(b"\x01")
        if first < 0:
            continue
        left, right = min(left, first), max(right, last)
        top, bottom = min(top, y), y
    return QRect() if right < left else QRect(left, top, right - left + 1, bottom - top + 1)


def _present_preserved_source(source: QImage) -> QImage:
    """Present a validated clean asset; never classify or erase source pixels.

    Source validation happens before this function. Resampling belongs only to
    presentation, once, after an exact crop including all nonzero alpha.
    """
    if source.isNull():
        return QImage()
    bounds = _preserved_source_bounds(source)
    if bounds.isEmpty():
        return source.copy()
    target = max(1, int(_CANVAS_SIZE * _CONTENT_FRACTION))
    scaled = source.copy(bounds).scaled(
        target, target,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QImage(QSize(_CANVAS_SIZE, _CANVAS_SIZE), QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.drawImage((_CANVAS_SIZE - scaled.width()) // 2, (_CANVAS_SIZE - scaled.height()) // 2, scaled)
    painter.end()
    return canvas


def _is_validated_masked_source(path: Path, data: bytes) -> bool:
    expected = (
        _MASKED_SOURCE_SHA256.get(path.name)
        or _PHASE3_MASKED_SOURCE_SHA256.get(path.name)
        or _PHASE4_RECOMPOSED_SOURCE_SHA256.get(path.name)
        or _RUNTIME_QA_RECOMPOSED_SOURCE_SHA256.get(path.name)
    )
    return (
        expected is not None
        and path.resolve().parent == icon_theme._ICON_DIR.resolve()
        and hashlib.sha256(data).hexdigest() == expected
    )


def _apply_runtime_qa_presentation_override(
    image: QImage, path: Path, data: bytes
) -> QImage:
    """Apply exact-source optical scale/offset tweaks requested from real-app QA."""
    entry = _RUNTIME_QA_PRESENTATION_OVERRIDES.get(path.name)
    if entry is None or path.resolve().parent != icon_theme._ICON_DIR.resolve():
        return image
    expected_hash, scale, offset_x, offset_y = entry
    if hashlib.sha256(data).hexdigest() != expected_hash:
        return image
    bounds = _preserved_source_bounds(image)
    if bounds.isEmpty():
        return image
    cropped = image.copy(bounds)
    target_w = max(1, int(round(cropped.width() * scale)))
    target_h = max(1, int(round(cropped.height() * scale)))
    scaled = cropped.scaled(
        target_w,
        target_h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    canvas = QImage(
        QSize(_CANVAS_SIZE, _CANVAS_SIZE),
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    x = (_CANVAS_SIZE - scaled.width()) // 2 + offset_x
    y = (_CANVAS_SIZE - scaled.height()) // 2 + offset_y
    painter.drawImage(x, y, scaled)
    painter.end()
    return canvas

def _normalized_icon(path: Path, cache: dict[Path, QIcon]) -> QIcon | None:
    cached = cache.get(path)
    if cached is not None:
        return cached
    try:
        data = path.read_bytes()
    except OSError:
        return None
    image = QImage.fromData(data)
    if image.isNull():
        return None
    normalized = (
        _present_preserved_source(image)
        if _is_validated_masked_source(path, data)
        else _normalize_image(image)
    )
    if normalized.isNull():
        return None
    normalized = _apply_runtime_qa_presentation_override(normalized, path, data)
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

    # One visual title size for every icon. The normalized transparent canvas
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
