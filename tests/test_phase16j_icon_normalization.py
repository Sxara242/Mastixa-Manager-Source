import math
import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from app import icon_theme
from app.icon_normalization import (
    _alpha_bounds,
    _clear_outer_light_neutral_ring,
    _has_shaped_transparency,
    _normalize_image,
)


class IconNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _source(self, glyph: QRect, padding_card: QRect) -> QImage:
        image = QImage(220, 220, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.fillRect(padding_card, QColor(250, 250, 248, 255))
        painter.fillRect(glyph, QColor(30, 96, 70, 255))
        # Deliberate interior white detail: it must survive background cleanup.
        inset = glyph.adjusted(10, 10, -10, -10)
        if inset.width() > 2 and inset.height() > 2:
            painter.fillRect(inset, QColor(255, 255, 255, 255))
        painter.end()
        return image

    def _transparent_ring_source(self) -> QImage:
        image = QImage(220, 220, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(236, 236, 236, 255))
        painter.drawEllipse(QRect(12, 12, 196, 196))
        painter.setBrush(QColor(168, 172, 178, 255))
        painter.drawEllipse(QRect(27, 27, 166, 166))
        painter.setBrush(QColor(92, 98, 104, 255))
        painter.drawEllipse(QRect(41, 41, 138, 138))
        painter.setBrush(QColor(22, 91, 170, 255))
        painter.drawEllipse(QRect(50, 50, 120, 120))
        painter.end()
        return image

    @staticmethod
    def _visible_pixels(image: QImage) -> int:
        count = 0
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y).alpha() > 12:
                    count += 1
        return count

    @staticmethod
    def _count_outer_white_neutral(image: QImage) -> int:
        bounds = _alpha_bounds(image)
        if bounds.isNull() or bounds.isEmpty():
            return 0
        center_x = bounds.left() + (bounds.width() - 1) / 2.0
        center_y = bounds.top() + (bounds.height() - 1) / 2.0
        radius_x = max(1.0, bounds.width() / 2.0)
        radius_y = max(1.0, bounds.height() / 2.0)
        count = 0
        for y in range(bounds.top(), bounds.bottom() + 1):
            dy = (y - center_y) / radius_y
            for x in range(bounds.left(), bounds.right() + 1):
                color = image.pixelColor(x, y)
                if color.alpha() <= 12:
                    continue
                dx = (x - center_x) / radius_x
                if dx * dx + dy * dy < 0.58 * 0.58:
                    continue
                channels = (color.red(), color.green(), color.blue())
                if min(channels) >= 222 and max(channels) - min(channels) <= 30:
                    count += 1
        return count

    @staticmethod
    def _count_medium_metallic(image: QImage) -> int:
        count = 0
        for y in range(image.height()):
            for x in range(image.width()):
                color = image.pixelColor(x, y)
                if color.alpha() <= 12:
                    continue
                channels = (color.red(), color.green(), color.blue())
                chroma = max(channels) - min(channels)
                if 125 <= min(channels) <= 205 and chroma <= 40:
                    count += 1
        return count

    def test_outer_white_card_is_removed_but_interior_white_detail_survives(self):
        source = self._source(QRect(105, 78, 54, 64), QRect(18, 18, 184, 184))
        self.assertFalse(_has_shaped_transparency(source))

        normalized = _normalize_image(source)

        self.assertFalse(normalized.isNull())
        self.assertEqual(0, normalized.pixelColor(5, 5).alpha())
        bounds = _alpha_bounds(normalized)
        self.assertFalse(bounds.isNull())

        center = normalized.pixelColor(normalized.width() // 2, normalized.height() // 2)
        self.assertGreater(center.alpha(), 0)
        self.assertGreaterEqual(center.red(), 240)
        self.assertGreaterEqual(center.green(), 240)
        self.assertGreaterEqual(center.blue(), 240)

    def test_transparent_cutout_removes_only_outer_white_ring(self):
        source = self._transparent_ring_source()
        self.assertTrue(_has_shaped_transparency(source))

        before_white = self._count_outer_white_neutral(source)
        before_metallic = self._count_medium_metallic(source)
        cleaned = _clear_outer_light_neutral_ring(source)
        after_white = self._count_outer_white_neutral(cleaned)
        after_metallic = self._count_medium_metallic(cleaned)

        self.assertGreater(before_white, 100)
        self.assertLess(after_white, before_white)
        # The medium silver metallic ring is not part of the white cleanup.
        self.assertEqual(before_metallic, after_metallic)

        center = cleaned.pixelColor(cleaned.width() // 2, cleaned.height() // 2)
        self.assertEqual((22, 91, 170), (center.red(), center.green(), center.blue()))

        normalized = _normalize_image(source)
        self.assertFalse(normalized.isNull())
        bounds = _alpha_bounds(normalized)
        self.assertGreaterEqual(bounds.left(), 20)
        self.assertGreaterEqual(bounds.top(), 20)
        self.assertGreaterEqual(normalized.width() - 1 - bounds.right(), 20)
        self.assertGreaterEqual(normalized.height() - 1 - bounds.bottom(), 20)

    def test_legacy_partners_fixture_removes_white_ring_preserves_metallic_and_padding(self):
        # Keep the exact pre-mask hotfix source to exercise the legacy fallback.
        # The corrected production PNG is covered by the independent source contract.
        source = QImage(str(Path(__file__).parent / "fixtures" / "icon_mask_prototype" / "partners" / "original.png"))
        self.assertFalse(source.isNull())

        longest = max(source.width(), source.height())
        if longest > 384:
            source = source.scaled(
                384,
                384,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        before_white = self._count_outer_white_neutral(source)
        before_metallic = self._count_medium_metallic(source)
        cleaned = _clear_outer_light_neutral_ring(source)
        after_white = self._count_outer_white_neutral(cleaned)
        after_metallic = self._count_medium_metallic(cleaned)

        self.assertGreater(before_white, 100)
        self.assertLess(after_white, before_white)
        self.assertEqual(before_metallic, after_metallic)

        normalized = _normalize_image(source)
        self.assertFalse(normalized.isNull())
        bounds = _alpha_bounds(normalized)
        self.assertFalse(bounds.isNull())

        self.assertGreaterEqual(bounds.left(), 20)
        self.assertGreaterEqual(bounds.top(), 20)
        self.assertGreaterEqual(normalized.width() - 1 - bounds.right(), 20)
        self.assertGreaterEqual(normalized.height() - 1 - bounds.bottom(), 20)

        center_x = bounds.x() + bounds.width() / 2.0
        center_y = bounds.y() + bounds.height() / 2.0
        canvas_center = normalized.width() / 2.0, normalized.height() / 2.0
        self.assertLessEqual(abs(center_x - canvas_center[0]), 1.0)
        self.assertLessEqual(abs(center_y - canvas_center[1]), 1.0)

    def test_different_source_padding_and_offsets_get_same_visual_size_and_center(self):
        first = _normalize_image(
            self._source(QRect(34, 55, 50, 70), QRect(8, 8, 204, 204))
        )
        second = _normalize_image(
            self._source(QRect(130, 88, 50, 70), QRect(30, 30, 160, 160))
        )

        first_bounds = _alpha_bounds(first)
        second_bounds = _alpha_bounds(second)
        self.assertEqual(first_bounds.size(), second_bounds.size())

        canvas_center = first.width() / 2.0, first.height() / 2.0
        for bounds in (first_bounds, second_bounds):
            with self.subTest(bounds=bounds):
                center_x = bounds.x() + bounds.width() / 2.0
                center_y = bounds.y() + bounds.height() / 2.0
                self.assertLessEqual(abs(center_x - canvas_center[0]), 1.0)
                self.assertLessEqual(abs(center_y - canvas_center[1]), 1.0)

    def test_title_icons_use_one_common_size_without_per_file_exceptions(self):
        self.assertEqual(icon_theme._TITLE_ICON_SIZE, icon_theme._TITLE_ICON_SIZE_LARGE)
        self.assertEqual((88, 88), (icon_theme._TITLE_ICON_SIZE.width(), icon_theme._TITLE_ICON_SIZE.height()))
        self.assertEqual({}, icon_theme._CUSTOM_TITLE_ICON_SIZES)
        self.assertEqual(set(), icon_theme._LARGE_TITLE_ICON_FILES)


if __name__ == "__main__":
    unittest.main()
