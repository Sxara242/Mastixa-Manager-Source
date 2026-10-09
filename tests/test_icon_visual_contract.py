import math
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

from app import icon_normalization, icon_theme


class IconVisualContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _rgba(image: QImage, x: int, y: int) -> tuple[int, int, int, int]:
        color = image.pixelColor(x, y)
        return color.red(), color.green(), color.blue(), color.alpha()

    @staticmethod
    def _cardinal_extent(image: QImage, direction: tuple[int, int]) -> int:
        bounds = icon_normalization._alpha_bounds(image)
        cx = int(round(bounds.left() + (bounds.width() - 1) / 2.0))
        cy = int(round(bounds.top() + (bounds.height() - 1) / 2.0))
        dx, dy = direction
        distance = 0
        last_visible = 0
        while True:
            x = cx + dx * distance
            y = cy + dy * distance
            if x < 0 or y < 0 or x >= image.width() or y >= image.height():
                break
            if image.pixelColor(x, y).alpha() > icon_normalization._ALPHA_CUTOFF:
                last_visible = distance
            distance += 1
        return last_visible

    def test_four_bright_metallic_highlights_are_not_cut_into_black_seams(self):
        image = QImage(180, 180, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#A8A8A8"))
        painter.drawEllipse(QRect(10, 10, 160, 160))
        painter.setBrush(QColor("#5E646A"))
        painter.drawEllipse(QRect(24, 24, 132, 132))
        painter.setBrush(QColor("#124F86"))
        painter.drawEllipse(QRect(34, 34, 112, 112))

        # Four bright metallic glints touching the outer badge edge reproduce the
        # old flood-fill's cardinal-seam failure mode. They are NOT a white shell.
        painter.setBrush(QColor("#F3F3F3"))
        painter.drawEllipse(QRect(82, 9, 16, 22))
        painter.drawEllipse(QRect(82, 149, 16, 22))
        painter.drawEllipse(QRect(9, 82, 22, 16))
        painter.drawEllipse(QRect(149, 82, 22, 16))
        painter.end()

        bounds = icon_normalization._alpha_bounds(image)
        self.assertIsNone(
            icon_normalization._detect_outer_white_shell_radius(image, bounds)
        )

        before = {
            "top": self._rgba(image, 90, 17),
            "bottom": self._rgba(image, 90, 162),
            "left": self._rgba(image, 17, 90),
            "right": self._rgba(image, 162, 90),
        }
        cleaned = icon_normalization._clear_outer_light_neutral_ring(image)
        after = {
            "top": self._rgba(cleaned, 90, 17),
            "bottom": self._rgba(cleaned, 90, 162),
            "left": self._rgba(cleaned, 17, 90),
            "right": self._rgba(cleaned, 162, 90),
        }

        self.assertEqual(before, after)
        for rgba in after.values():
            self.assertGreater(rgba[3], icon_normalization._ALPHA_CUTOFF)

    def test_continuous_white_shell_is_removed_with_symmetric_boundary(self):
        image = QImage(180, 180, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        # Actual approved layer order for this defect:
        # transparent -> disposable white shell -> metallic ring -> dark rim.
        painter.setBrush(QColor("#FAFAFA"))
        painter.drawEllipse(QRect(5, 5, 170, 170))
        painter.setBrush(QColor("#A8A8A8"))
        painter.drawEllipse(QRect(20, 20, 140, 140))
        painter.setBrush(QColor("#5E646A"))
        painter.drawEllipse(QRect(31, 31, 118, 118))
        painter.setBrush(QColor("#124F86"))
        painter.drawEllipse(QRect(39, 39, 102, 102))

        # Bright highlights are part of the metallic badge and must survive.
        painter.setBrush(QColor("#F1F1F1"))
        painter.drawEllipse(QRect(84, 20, 12, 12))
        painter.drawEllipse(QRect(84, 148, 12, 12))
        painter.end()

        bounds = icon_normalization._alpha_bounds(image)
        cut = icon_normalization._detect_outer_white_shell_radius(image, bounds)
        self.assertIsNotNone(cut)
        self.assertGreater(cut, 0.70)
        self.assertLess(cut, 0.90)

        cleaned = icon_normalization._clear_outer_light_neutral_ring(image)
        self.assertFalse(cleaned.isNull())

        # The near-white shell itself is transparent at all four cardinal
        # directions; metallic pixels immediately inward must remain intact.
        for x, y in ((90, 10), (90, 169), (10, 90), (169, 90)):
            self.assertLessEqual(
                cleaned.pixelColor(x, y).alpha(),
                icon_normalization._ALPHA_CUTOFF,
            )

        # Metallic body and its bright inner highlights are preserved.
        for x, y in ((90, 24), (90, 155), (24, 90), (155, 90)):
            self.assertGreater(
                cleaned.pixelColor(x, y).alpha(),
                icon_normalization._ALPHA_CUTOFF,
            )

        extents = [
            self._cardinal_extent(cleaned, direction)
            for direction in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ]
        self.assertLessEqual(max(extents) - min(extents), 2)

    def test_real_badges_never_mutate_pixels_inside_the_detected_boundary(self):
        filenames = (
            "production.png",
            "irrigation_fertilization.png",
            "labor.png",
            "partners.png",
            "finance.png",
        )

        for filename in filenames:
            with self.subTest(filename=filename):
                source = QImage(str(icon_theme._ICON_DIR / filename))
                self.assertFalse(source.isNull())
                longest = max(source.width(), source.height())
                if longest > 384:
                    source = source.scaled(
                        384,
                        384,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )

                bounds = icon_normalization._alpha_bounds(source)
                cut = icon_normalization._detect_outer_white_shell_radius(
                    source, bounds
                )
                cleaned = icon_normalization._clear_outer_light_neutral_ring(source)

                width = bounds.width()
                height = bounds.height()
                cx = bounds.left() + (width - 1) / 2.0
                cy = bounds.top() + (height - 1) / 2.0
                radius = max(1.0, min(width, height) / 2.0)
                safe_radius = 0.90 if cut is None else max(0.60, cut - 0.035)

                for ray in range(72):
                    angle = 2.0 * math.pi * ray / 72.0
                    x = int(round(cx + math.cos(angle) * radius * safe_radius))
                    y = int(round(cy + math.sin(angle) * radius * safe_radius))
                    if not (0 <= x < source.width() and 0 <= y < source.height()):
                        continue
                    self.assertEqual(
                        self._rgba(source, x, y),
                        self._rgba(cleaned, x, y),
                        msg=f"{filename} changed interior pixel at ray {ray}",
                    )


if __name__ == "__main__":
    unittest.main()
