from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import unittest


class IconNormalizationPerformanceTests(unittest.TestCase):
    def test_bulk_alpha_bounds_preserves_cutoff_and_geometry(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtCore import QRect, Qt
            from PySide6.QtGui import QColor, QImage
            from PySide6.QtWidgets import QApplication
            from app import icon_normalization
            from app.icon_normalization_performance import (
                _alpha_bounds_fast,
                _alpha_bounds_reference,
            )

            app = QApplication.instance() or QApplication([])
            assert icon_normalization._alpha_bounds is _alpha_bounds_fast
            assert getattr(icon_normalization, "_mastixa_bulk_alpha_bounds", False)

            image = QImage(13, 9, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            cutoff = icon_normalization._ALPHA_CUTOFF

            # Exactly-at-cutoff pixels remain invisible.
            image.setPixelColor(1, 1, QColor(10, 20, 30, cutoff))
            # Visible pixels exercise both bounds and partial alpha.
            image.setPixelColor(3, 2, QColor(10, 20, 30, cutoff + 1))
            image.setPixelColor(10, 7, QColor(10, 20, 30, 255))
            image.setPixelColor(6, 4, QColor(10, 20, 30, 127))

            expected = QRect(3, 2, 8, 6)
            assert _alpha_bounds_reference(image) == expected
            assert _alpha_bounds_fast(image) == expected
            """
        )
        env = dict(os.environ)
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=os.getcwd(),
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_existing_transparent_ring_normalization_still_uses_fast_bounds(self) -> None:
        code = textwrap.dedent(
            """
            import os
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

            from PySide6.QtCore import QRect, Qt
            from PySide6.QtGui import QColor, QImage, QPainter, QPen
            from PySide6.QtWidgets import QApplication
            from app import icon_normalization
            from app.icon_normalization_performance import _alpha_bounds_fast

            app = QApplication.instance() or QApplication([])
            source = QImage(220, 220, QImage.Format.Format_ARGB32)
            source.fill(Qt.GlobalColor.transparent)
            painter = QPainter(source)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(QPen(QColor(242, 244, 246, 255), 22))
            painter.setBrush(QColor(22, 91, 170, 255))
            painter.drawEllipse(QRect(24, 24, 172, 172))
            painter.end()

            assert icon_normalization._alpha_bounds is _alpha_bounds_fast
            assert icon_normalization._has_shaped_transparency(source)
            normalized = icon_normalization._normalize_image(source)
            assert not normalized.isNull()
            assert normalized.pixelColor(5, 5).alpha() == 0
            """
        )
        env = dict(os.environ)
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=os.getcwd(),
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
