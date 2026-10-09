"""Phase 4 owner-approved canonical badge recomposition contract."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from app import icon_normalization as norm, icon_theme
from tests.test_icon_mask_prototype import rgba


FIX = Path(__file__).parent / "fixtures" / "icon_recomposition_phase4"
MANIFEST = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))
READY = set(MANIFEST["icons"])
RECOMPOSED = set(MANIFEST["recomposed_icons"])
PRODUCTION_ONLY = set(MANIFEST["preserved_cleanup_icons"])
RUNTIME_QA_SUPERSEDED = READY & set(norm._RUNTIME_QA_RECOMPOSED_SOURCE_SHA256)
ACTIVE_READY = READY - RUNTIME_QA_SUPERSEDED
ACTIVE_RECOMPOSED = RECOMPOSED - RUNTIME_QA_SUPERSEDED


def _alpha_bbox(arr: np.ndarray) -> list[int]:
    ys, xs = np.where(arr[:, :, 3] > 0)
    if not len(xs):
        return []
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


class Phase4RecompositionSourceTests(unittest.TestCase):
    def test_exact_scope_and_runtime_registry(self):
        self.assertEqual(10, len(READY))
        self.assertEqual(ACTIVE_READY, set(norm._PHASE4_RECOMPOSED_SOURCE_SHA256))
        self.assertEqual(READY, RECOMPOSED | PRODUCTION_ONLY)
        self.assertEqual({"production.png"}, PRODUCTION_ONLY)
        self.assertEqual({"production.png"}, RUNTIME_QA_SUPERSEDED)

    def test_frozen_original_and_bundled_hashes(self):
        for name, entry in MANIFEST["icons"].items():
            with self.subTest(icon=name):
                original = FIX / Path(name).stem / "original.png"
                self.assertEqual(
                    entry["original_sha256"], hashlib.sha256(original.read_bytes()).hexdigest()
                )
                if name in RUNTIME_QA_SUPERSEDED:
                    continue
                bundled = icon_theme._ICON_DIR / name
                self.assertEqual(
                    entry["bundled_sha256"], hashlib.sha256(bundled.read_bytes()).hexdigest()
                )
                self.assertEqual(
                    entry["bundled_sha256"], norm._PHASE4_RECOMPOSED_SOURCE_SHA256[name]
                )

    def test_canvas_and_owner_approved_alpha_geometry(self):
        for name, entry in MANIFEST["icons"].items():
            if name not in ACTIVE_READY:
                continue
            with self.subTest(icon=name):
                arr = rgba(QImage(str(icon_theme._ICON_DIR / name)))
                self.assertEqual((512, 512, 4), arr.shape)
                self.assertEqual(entry["alpha_bbox_xyxy_inclusive"], _alpha_bbox(arr))

    def test_recomposed_icons_share_exact_opaque_canonical_ring(self):
        ring = rgba(QImage(str(FIX / "canonical_ring.png")))
        opaque_ring = ring[:, :, 3] == 255
        self.assertGreater(int(opaque_ring.sum()), 0)

        seal_box = MANIFEST["products_seal_exclusion_bbox_xyxy"]
        x0, y0, x1, y1 = seal_box

        for name in ACTIVE_RECOMPOSED:
            with self.subTest(icon=name):
                actual = rgba(QImage(str(icon_theme._ICON_DIR / name)))
                compare = opaque_ring.copy()
                if name == "products.png":
                    # The owner-approved green seal legitimately overlaps the badge ring.
                    compare[y0 : y1 + 1, x0 : x1 + 1] = False
                self.assertTrue(np.array_equal(actual[compare], ring[compare]))

    def test_recomposed_badges_do_not_touch_canvas_edges(self):
        for name in ACTIVE_RECOMPOSED:
            with self.subTest(icon=name):
                arr = rgba(QImage(str(icon_theme._ICON_DIR / name)))
                self.assertFalse(arr[0, :, 3].any())
                self.assertFalse(arr[-1, :, 3].any())
                self.assertFalse(arr[:, 0, 3].any())
                self.assertFalse(arr[:, -1, 3].any())

    def test_products_green_seal_survives(self):
        arr = rgba(QImage(str(icon_theme._ICON_DIR / "products.png")))
        x, y = MANIFEST["products_seal_witness_xy"]
        r, g, b, a = [int(v) for v in arr[y, x]]
        self.assertGreater(a, 0)
        self.assertGreater(g, r)
        self.assertGreater(g, b)

    def test_original_sources_cannot_inherit_phase4_bypass(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                path = icon_theme._ICON_DIR / name
                original = (FIX / Path(name).stem / "original.png").read_bytes()
                self.assertFalse(norm._is_validated_masked_source(path, original))

    def test_exact_hash_and_canonical_path_are_required(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                path = icon_theme._ICON_DIR / name
                data = path.read_bytes()
                self.assertTrue(norm._is_validated_masked_source(path, data))
                self.assertFalse(norm._is_validated_masked_source(path, data + b"changed"))
                self.assertFalse(norm._is_validated_masked_source(FIX / name, data))


class Phase4RecompositionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_phase4_sources_bypass_destructive_cleanup(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name), patch.object(
                norm, "_normalize_image", side_effect=AssertionError("legacy cleanup called")
            ):
                icon = norm._normalized_icon(icon_theme._ICON_DIR / name, {})
                self.assertIsNotNone(icon)
                self.assertFalse(icon.isNull())

    def test_presentation_does_not_mutate_source_and_keeps_safe_padding(self):
        for name in ACTIVE_READY:
            with self.subTest(icon=name):
                source = QImage(str(icon_theme._ICON_DIR / name))
                before = rgba(source)
                result = norm._present_preserved_source(source)
                bounds = norm._preserved_source_bounds(result)
                self.assertTrue(np.array_equal(before, rgba(source)))
                self.assertEqual((256, 256), (result.width(), result.height()))
                self.assertGreaterEqual(
                    min(bounds.left(), bounds.top(), 255 - bounds.right(), 255 - bounds.bottom()),
                    20,
                )
                self.assertLessEqual(abs(bounds.left() + bounds.right() - 255), 1)
                self.assertLessEqual(abs(bounds.top() + bounds.bottom() - 255), 1)


if __name__ == "__main__":
    unittest.main()
