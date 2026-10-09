"""Independent, pre-scaling source contract and separate presentation tests.

The expected regions are frozen reviewed raster annotations. These tests never
invoke the mask builder, estimate radii, or use the runtime cleanup predicate to
decide what must be protected. Fixed expected RGBA digests cover edge pixels too.
"""
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import numpy as np
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication
from app import icon_normalization as norm, icon_theme

FIX = Path(__file__).parent / "fixtures" / "icon_mask_prototype"
MANIFEST = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))
READY = {"irrigation_fertilization.png", "labor.png", "partners.png", "finance.png"}
REVIEW = {"production.png", "calendar.png", "annual_report.png"}
# Historical Phase 2 review assets may be superseded by a later owner-approved
# Phase 4 or runtime-QA recomposition contract.
LATER_SUPERSEDED = REVIEW & (
    set(norm._PHASE4_RECOMPOSED_SOURCE_SHA256) | set(norm._RUNTIME_QA_RECOMPOSED_SOURCE_SHA256)
)
ACTIVE_REVIEW = REVIEW - LATER_SUPERSEDED
# Explicit native-source metallic glints, separate from all cleanup code.
GLINT_WITNESSES = {
    "irrigation_fertilization.png": (256, 58),
    "labor.png": (256, 21),
    "partners.png": (256, 45),
    "finance.png": (256, 33),
}


def rgba(image):
    q = image.convertToFormat(QImage.Format.Format_RGBA8888)
    return np.frombuffer(q.constBits(), np.uint8).reshape(q.height(), q.bytesPerLine())[:, : q.width() * 4].reshape(q.height(), q.width(), 4).copy()


def fixture(filename):
    folder = FIX / Path(filename).stem
    original = rgba(QImage(str(folder / "original.png")))
    actual = rgba(QImage(str(icon_theme._ICON_DIR / filename)))
    protected = rgba(QImage(str(folder / "independent_protected.png")))[:, :, 0] == 255
    removal = rgba(QImage(str(folder / "approved_removal.png")))[:, :, 0] == 255
    return original, actual, protected, removal


def assert_protected_rgba(test, original, actual, protected):
    test.assertTrue(np.array_equal(original[protected], actual[protected]), "Protected source RGBA changed")


class IconMaskSourceContractTests(unittest.TestCase):
    def test_scope_is_exactly_four_prototypes_and_three_historical_reviews(self):
        self.assertEqual(READY | REVIEW, set(MANIFEST["icons"]))
        self.assertEqual(READY, set(norm._MASKED_SOURCE_SHA256))
        self.assertEqual(READY, {n for n, m in MANIFEST["icons"].items() if m["status"] == "PROTOTYPE_READY"})
        self.assertEqual(REVIEW, LATER_SUPERSEDED)

    def test_frozen_references_and_annotations_have_expected_hashes(self):
        for name, entry in MANIFEST["icons"].items():
            with self.subTest(icon=name):
                folder = FIX / Path(name).stem
                for file, field in (("original.png", "original_sha256"), ("independent_protected.png", "independent_protected_sha256"), ("approved_removal.png", "removal_mask_sha256")):
                    self.assertEqual(entry[field], hashlib.sha256((folder / file).read_bytes()).hexdigest())

    def test_independent_reference_is_not_the_cleanup_mask_complement(self):
        for name in READY:
            with self.subTest(icon=name):
                _, _, protected, removal = fixture(name)
                self.assertFalse(np.array_equal(protected, ~removal))

    def test_initial_candidates_expose_independent_boundary_conflicts(self):
        expected = {"irrigation_fertilization.png": 192, "labor.png": 45,
                    "partners.png": 9, "finance.png": 0}
        for name, count in expected.items():
            with self.subTest(icon=name):
                _, _, protected, _ = fixture(name)
                # Legacy protected.png is the frozen INITIAL candidate complement.
                # It is used only to demonstrate the independent oracle's rejection.
                initial = rgba(QImage(str(FIX / Path(name).stem / "protected.png")))[:, :, 0] == 255
                self.assertEqual(count, int((protected & ~initial).sum()))

    def test_every_protected_pixel_has_exact_original_prescaling_rgba(self):
        for name in READY | ACTIVE_REVIEW:
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                self.assertEqual((512, 512, 4), actual.shape)
                assert_protected_rgba(self, original, actual, protected)

    def test_only_frozen_approved_exterior_pixels_change_alpha(self):
        for name in READY | ACTIVE_REVIEW:
            with self.subTest(icon=name):
                original, actual, protected, removal = fixture(name)
                changed = original[:, :, 3] != actual[:, :, 3]
                self.assertFalse(np.any(changed & ~removal))
                self.assertFalse(np.any(protected & removal))
                self.assertTrue(np.all(actual[:, :, 3][removal] == 0))
                self.assertEqual(name in READY, bool(changed.any()))

    def test_all_rgb_bytes_are_original_even_in_newly_transparent_pixels(self):
        for name in READY | ACTIVE_REVIEW:
            with self.subTest(icon=name):
                original, actual, _, _ = fixture(name)
                self.assertTrue(np.array_equal(original[:, :, :3], actual[:, :, :3]))

    def test_entire_rgba_raster_matches_fixed_review_snapshot(self):
        for name in READY | ACTIVE_REVIEW:
            entry = MANIFEST["icons"][name]
            with self.subTest(icon=name):
                actual = rgba(QImage(str(icon_theme._ICON_DIR / name)))
                self.assertEqual(entry["expected_rgba_sha256"], hashlib.sha256(actual.tobytes()).hexdigest())

    def test_all_protected_very_bright_pixels_are_preserved(self):
        for name in READY:
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                glints = protected & (original[:, :, 3] > 0) & (original[:, :, :3].min(axis=2) >= 222)
                self.assertGreater(int(glints.sum()), 0)
                self.assertTrue(np.array_equal(original[glints], actual[glints]))
                x, y = GLINT_WITNESSES[name]
                self.assertTrue(glints[y, x])

    def test_deleting_even_one_known_metallic_glint_is_rejected(self):
        for name, (x, y) in GLINT_WITNESSES.items():
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                self.assertTrue(protected[y, x])
                damaged = actual.copy()
                damaged[y, x, 3] = 0
                with self.assertRaisesRegex(AssertionError, "Protected source RGBA changed"):
                    assert_protected_rgba(self, original, damaged, protected)

    def test_darkening_even_one_metallic_glint_is_rejected(self):
        for name, (x, y) in GLINT_WITNESSES.items():
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                damaged = actual.copy()
                damaged[y, x, :3] = 0
                with self.assertRaisesRegex(AssertionError, "Protected source RGBA changed"):
                    assert_protected_rgba(self, original, damaged, protected)

    def test_dark_and_colored_protected_pixels_are_exact(self):
        for name in READY:
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                rgb = original[:, :, :3].astype(int)
                dark = protected & (rgb.max(2) <= 150) & (original[:, :, 3] > 0)
                colored = protected & (np.ptp(rgb, axis=2) > 30) & (original[:, :, 3] > 0)
                self.assertGreater(int(dark.sum()), 0)
                self.assertGreater(int(colored.sum()), 0)
                self.assertTrue(np.array_equal(original[dark | colored], actual[dark | colored]))

    def test_annotated_outer_boundary_has_no_alpha_holes(self):
        for name in READY:
            with self.subTest(icon=name):
                original, actual, protected, _ = fixture(name)
                interior = protected.copy()
                for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    interior &= np.roll(protected, (dy, dx), axis=(0, 1))
                boundary = protected & ~interior
                self.assertGreater(int(boundary.sum()), 0)
                self.assertTrue(np.all(original[:, :, 3][boundary] > 0))
                self.assertTrue(np.array_equal(original[boundary], actual[boundary]))

    def test_review_assets_remain_byte_identical(self):
        for name in ACTIVE_REVIEW:
            with self.subTest(icon=name):
                self.assertEqual((FIX / Path(name).stem / "original.png").read_bytes(), (icon_theme._ICON_DIR / name).read_bytes())


class IconMaskPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_validated_bundled_assets_bypass_all_destructive_diagnosis(self):
        for name in READY:
            with self.subTest(icon=name), patch.object(norm, "_normalize_image", side_effect=AssertionError("Legacy cleaner called")), patch.object(norm, "_clear_outer_light_neutral_ring", side_effect=AssertionError("Radial cleaner called")), patch.object(norm, "_clear_outer_white_component", side_effect=AssertionError("Flood fill called")):
                icon = norm._normalized_icon(icon_theme._ICON_DIR / name, {})
                self.assertIsNotNone(icon)
                self.assertFalse(icon.isNull())

    def test_cache_hit_does_not_read_or_reprocess_the_source(self):
        path = icon_theme._ICON_DIR / "partners.png"
        cache = {}
        first = norm._normalized_icon(path, cache)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected reload")):
            self.assertIs(first, norm._normalized_icon(path, cache))

    def test_only_exact_bundled_content_can_bypass_cleanup(self):
        for name in READY:
            with self.subTest(icon=name):
                path = icon_theme._ICON_DIR / name
                data = path.read_bytes()
                self.assertTrue(norm._is_validated_masked_source(path, data))
                self.assertFalse(norm._is_validated_masked_source(path, data + b"changed"))
                self.assertFalse(norm._is_validated_masked_source(FIX / name, data))

    def test_review_assets_keep_the_existing_fallback(self):
        for name in ACTIVE_REVIEW:
            with self.subTest(icon=name), patch.object(norm, "_normalize_image", wraps=norm._normalize_image) as legacy:
                icon = norm._normalized_icon(icon_theme._ICON_DIR / name, {})
                self.assertFalse(icon.isNull())
                legacy.assert_called_once()

    def test_presentation_preserves_source_and_centers_visible_bounds(self):
        for name in READY:
            with self.subTest(icon=name):
                source = QImage(str(icon_theme._ICON_DIR / name))
                before = rgba(source)
                out = norm._present_preserved_source(source)
                self.assertTrue(np.array_equal(before, rgba(source)))
                self.assertEqual((256, 256), (out.width(), out.height()))
                b = norm._preserved_source_bounds(out)
                self.assertGreaterEqual(min(b.left(), b.top(), 255 - b.right(), 255 - b.bottom()), 20)
                self.assertLessEqual(abs(b.left() + b.right() - 255), 1)
                self.assertLessEqual(abs(b.top() + b.bottom() - 255), 1)

    def test_faint_valid_protrusion_is_included_in_safe_crop(self):
        source = QImage(512, 512, QImage.Format.Format_ARGB32)
        source.fill(Qt.GlobalColor.transparent)
        source.setPixelColor(100, 100, QColor(30, 80, 120, 255))
        source.setPixelColor(400, 300, QColor(250, 250, 250, 1))
        self.assertEqual(QRect(100, 100, 301, 201), norm._preserved_source_bounds(source))

    def test_null_missing_and_invalid_images_fail_safely(self):
        self.assertTrue(norm._present_preserved_source(QImage()).isNull())
        self.assertIsNone(norm._normalized_icon(FIX / "does-not-exist.png", {}))
        with patch.object(Path, "read_bytes", return_value=b"not a PNG"):
            self.assertIsNone(norm._normalized_icon(icon_theme._ICON_DIR / "partners.png", {}))


if __name__ == "__main__":
    unittest.main()
