from __future__ import annotations

from pathlib import Path
import unittest

from app.runtime_paths import resolve_base_dir


class RuntimePathTests(unittest.TestCase):
    def test_source_checkout_uses_repository_root(self) -> None:
        module = Path("C:/work/MastixaManager/app/runtime_paths.py")
        self.assertEqual(
            Path("C:/work/MastixaManager").resolve(),
            resolve_base_dir(
                frozen=False,
                environ={},
                module_file=module,
            ),
        )

    def test_packaged_build_uses_local_app_data(self) -> None:
        self.assertEqual(
            Path("C:/Users/test/AppData/Local/MastixaManager").resolve(),
            resolve_base_dir(
                frozen=True,
                environ={"LOCALAPPDATA": "C:/Users/test/AppData/Local"},
            ),
        )

    def test_explicit_data_home_has_priority(self) -> None:
        self.assertEqual(
            Path("D:/MastixaData").resolve(),
            resolve_base_dir(
                frozen=True,
                environ={
                    "LOCALAPPDATA": "C:/Users/test/AppData/Local",
                    "MASTIXA_DATA_HOME": "D:/MastixaData",
                },
            ),
        )


if __name__ == "__main__":
    unittest.main()
