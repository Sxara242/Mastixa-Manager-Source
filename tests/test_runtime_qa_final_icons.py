"""Owner-approved post-Phase-4 runtime visual QA icon contract."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from app import icon_normalization as norm, icon_theme

EXPECTED = {
    "reports.png": "5fcfe0bf2edb60ea32c5daad8206ecfc1484638270527710c0868011d7d1c60c",
    "sales.png": "a48e14f56f7600658efeb06655db4f84938cf98c7e62c5f23488dccd53595994",
    "year_lock.png": "f7055b703ef6ecadf2543e17b914268f49871962f16261246190969288c3977b",
    "data_quality.png": "ecdc4e745d41836feff2547a7661016720b4bb67d29ae312a8d4b826cb8d6ee4",
    "tree_planting.png": "9ad2f9090600be84b8ecb1779cdad75318f0ec98eed0dd93e5e3d7d5bb9c52dd",
    "production.png": "e98a28ed47f281fbd60494306b85a4729ad3e28bc4cf1969c1d0908beda0ec85",
    "package_preview.png": "78508e8aa7237038729e178d7d5e1a76fe25664aaa9731b1c926f5f3b87c56fa",
    "field_profile.png": "76d25ae81a414157a51f3353f4579590011c32321a8aab391dd198652494387e"
}

class RuntimeQaFinalIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_exact_runtime_qa_registry(self):
        self.assertEqual(EXPECTED, norm._RUNTIME_QA_RECOMPOSED_SOURCE_SHA256)

    def test_bundled_hashes_match_owner_approved_sources(self):
        for name, digest in EXPECTED.items():
            with self.subTest(icon=name):
                path = icon_theme._ICON_DIR / name
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertTrue(norm._is_validated_masked_source(path, path.read_bytes()))

    def test_runtime_qa_sources_bypass_destructive_cleanup(self):
        for name in EXPECTED:
            with self.subTest(icon=name), patch.object(norm, "_normalize_image", side_effect=AssertionError("legacy cleanup called")):
                icon = norm._normalized_icon(icon_theme._ICON_DIR / name, {})
                self.assertIsNotNone(icon)
                self.assertFalse(icon.isNull())

    def test_wrong_hash_or_wrong_path_cannot_bypass(self):
        for name in EXPECTED:
            with self.subTest(icon=name):
                path = icon_theme._ICON_DIR / name
                data = path.read_bytes()
                self.assertFalse(norm._is_validated_masked_source(path, data + b"changed"))
                self.assertFalse(norm._is_validated_masked_source(Path(__file__).parent / name, data))

    def test_owner_approved_presentation_overrides(self):
        self.assertEqual(
            ("015c66bd32aebe450cc2293865d920b0a5ffb2f589ab2aa4e129579c3ec499fe", 1.05, 0, 0),
            norm._RUNTIME_QA_PRESENTATION_OVERRIDES["field_costs.png"],
        )
        self.assertEqual(
            ("78508e8aa7237038729e178d7d5e1a76fe25664aaa9731b1c926f5f3b87c56fa", 1.00, 0, 4),
            norm._RUNTIME_QA_PRESENTATION_OVERRIDES["package_preview.png"],
        )
        self.assertEqual({"field_costs.png", "package_preview.png"}, set(norm._RUNTIME_QA_PRESENTATION_OVERRIDES))

if __name__ == "__main__":
    unittest.main()
