import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication

from app import icon_theme
from app.icon_normalization import (
    _alpha_bounds,
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
        pen = QPen(QColor(242, 244, 246, 255), 22)
        painter.setPen(pen)
        painter.setBrush(QColor(22, 91, 170, 255))
        painter.drawEllipse(QRect(24, 24, 172, 172))
        painter.end()
        return image

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

    def test_transparent_cutout_preserves_near_white_metallic_ring(self):
        source = self._transparent_ring_source()
        self.assertTrue(_has_shaped_transparency(source))

        normalized = _normalize_image(source)
        self.assertFalse(normalized.isNull())

        near_white_pixels = 0
        for y in range(normalized.height()):
            for x in range(normalized.width()):
                color = normalized.pixelColor(x, y)
                if (
                    color.alpha() > 200
                    and min(color.red(), color.green(), color.blue()) >= 220
                    and max(color.red(), color.green(), color.blue())
                    - min(color.red(), color.green(), color.blue())
                    <= 35
                ):
                    near_white_pixels += 1

        self.assertGreater(near_white_pixels, 500)

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
