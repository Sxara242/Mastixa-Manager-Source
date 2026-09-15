from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QLabel

from . import icon_theme


_INSTALLED = False


def _same_margins(margins, left: int, top: int, right: int, bottom: int) -> bool:
    return (
        margins.left() == left
        and margins.top() == top
        and margins.right() == right
        and margins.bottom() == bottom
    )


def _apply_page_title_icons_idempotent(root) -> int:
    """Apply page-title icons without re-triggering identical layout work.

    The icon event filter intentionally observes LayoutRequest/Resize so late lazy
    pages still receive icons. Repeating geometry setters with identical values,
    however, can itself emit more layout events and create a feedback loop. Keep
    the existing visual rules but mutate geometry/pixmaps only when state changed.
    """
    changed = 0
    protection_calendar_titles = {
        icon_theme._norm("Ημερολόγιο Προστασίας"),
        icon_theme._norm("Ημερολόγιο Φυτοπροστασίας"),
    }

    for label in root.findChildren(QLabel):
        is_page_title = label.objectName() == "pageTitle"
        is_protection_calendar_title = (
            icon_theme._norm(label.text()) in protection_calendar_titles
        )
        if not (is_page_title or is_protection_calendar_title):
            continue

        path = icon_theme._path_for_text(label.text())
        icon = icon_theme._icon_for_text(label.text())
        icon_label = getattr(label, "_mastixa_title_icon_label", None)

        if icon is None or path is None:
            if icon_label is not None and not icon_label.isHidden():
                icon_label.hide()
            original = getattr(label, "_mastixa_title_original_margins", None)
            if original is not None:
                current = label.contentsMargins()
                if not _same_margins(
                    current,
                    original.left(),
                    original.top(),
                    original.right(),
                    original.bottom(),
                ):
                    label.setContentsMargins(
                        original.left(),
                        original.top(),
                        original.right(),
                        original.bottom(),
                    )
            continue

        icon_size = icon_theme._CUSTOM_TITLE_ICON_SIZES.get(
            path.name,
            icon_theme._TITLE_ICON_SIZE_LARGE
            if path.name in icon_theme._LARGE_TITLE_ICON_FILES
            else icon_theme._TITLE_ICON_SIZE,
        )

        if not hasattr(label, "_mastixa_title_original_margins"):
            label._mastixa_title_original_margins = label.contentsMargins()

        original = label._mastixa_title_original_margins
        desired_min_height = icon_size.height() + 8

        if label.maximumHeight() != icon_theme._QT_MAX_SIZE:
            label.setMaximumHeight(icon_theme._QT_MAX_SIZE)
        if label.minimumHeight() != desired_min_height:
            label.setMinimumHeight(desired_min_height)

        left_pad = original.left() + icon_size.width() + icon_theme._TITLE_ICON_GAP
        current_margins = label.contentsMargins()
        if not _same_margins(
            current_margins,
            left_pad,
            original.top(),
            original.right(),
            original.bottom(),
        ):
            label.setContentsMargins(
                left_pad,
                original.top(),
                original.right(),
                original.bottom(),
            )

        created = False
        if icon_label is None:
            icon_label = QLabel(label)
            icon_label.setObjectName("mastixaPageTitleIcon")
            icon_label.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )
            label._mastixa_title_icon_label = icon_label
            created = True

        # setFixedSize updates both min/max constraints. Calling
        # setMaximumSize -> setMinimumSize -> setFixedSize on every icon pass was
        # the measured source of repeated LayoutRequest events.
        if (
            icon_label.minimumSize() != icon_size
            or icon_label.maximumSize() != icon_size
        ):
            icon_label.setFixedSize(icon_size)

        pixmap_key = (str(path), icon_size.width(), icon_size.height())
        if getattr(icon_label, "_mastixa_pixmap_key", None) != pixmap_key:
            icon_label.setPixmap(icon.pixmap(icon_size))
            icon_label._mastixa_pixmap_key = pixmap_key

        x = original.left()
        y = max(0, (label.height() - icon_size.height()) // 2)
        if icon_label.pos().x() != x or icon_label.pos().y() != y:
            icon_label.move(x, y)

        was_hidden = icon_label.isHidden()
        if was_hidden:
            icon_label.show()
        if created or was_hidden:
            icon_label.raise_()

        changed += 1

    return changed


def install_icon_theme_performance() -> None:
    """Make repeated title-icon passes idempotent without changing visuals."""
    global _INSTALLED
    if _INSTALLED:
        return
    icon_theme._apply_page_title_icons = _apply_page_title_icons_idempotent
    icon_theme._mastixa_idempotent_title_icons = True
    _INSTALLED = True
