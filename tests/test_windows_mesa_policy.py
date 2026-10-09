"""Reappearance and new graphics-consumer regressions for Mesa exclusion."""
import ast
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = runpy.run_path(str(ROOT / 'packaging/mesa_policy.py'))
FILTER = runpy.run_path(str(ROOT / 'packaging/qt_exclusions.py'))


class WindowsMesaPolicyTests(unittest.TestCase):
    def test_exact_name_from_wheel_or_tool_path_is_removed_from_binaries_and_data(self):
        entries = [('PySide6/OPENGL32SW.DLL', r'C:\wheel\opengl32sw.dll', 'BINARY'),
                   ('other/fallback.dll', r'C:\tool\OPENGL32SW.DLL', 'DATA'),
                   ('opengl32.dll', r'C:\Windows\System32\opengl32.dll', 'BINARY'),
                   ('Qt6Gui.dll', r'C:\wheel\Qt6Gui.dll', 'BINARY'),
                   ('qpdf.dll', r'C:\wheel\qpdf.dll', 'BINARY')]
        self.assertEqual(entries[2:], FILTER['without_unused_windows_components'](entries))

    def test_post_analysis_rejects_reintroduction_with_any_origin(self):
        for source in (r'C:\wheel\opengl32sw.dll', r'C:\tools\OPENGL32SW.DLL'):
            with self.assertRaisesRegex(RuntimeError, 'Mesa/LLVM'):
                POLICY['verify_analysis']([('nested/alias.dll', source, 'BINARY')])

    def test_real_legacy_bytes_cannot_be_reintroduced_under_an_alias(self):
        import PySide6
        original = Path(PySide6.__file__).parent / 'opengl32sw.dll'
        # This test runs against the pinned RC build wheel, not a synthetic hash.
        self.assertTrue(original.is_file())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            alias = root / 'graphics.pyd'
            alias.write_bytes(original.read_bytes())
            with self.assertRaisesRegex(RuntimeError, 'Renamed'):
                POLICY['verify_analysis']([('plugins/graphics.pyd', str(alias), 'BINARY')])
            with self.assertRaisesRegex(RuntimeError, 'Mesa/LLVM'):
                POLICY['verify_bundle'](root)

    def test_final_release_validator_rejects_nested_named_fallback(self):
        gate = runpy.run_path(str(ROOT / 'packaging/validate_windows_release.py'))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / '_internal' / 'plugins' / 'nested'
            folder.mkdir(parents=True)
            (folder / 'OPENGL32SW.DLL').write_bytes(b'new supplier or PATH file')
            self.assertTrue(any('Mesa/LLVM' in e for e in gate['bundle_errors'](root)))

    def test_new_OpenGL_or_Quick_application_consumer_requires_requalification(self):
        forbidden = {'QOpenGLContext', 'QOpenGLWidget', 'QOpenGLWindow',
                     'QOpenGLPaintDevice', 'QQuickWidget', 'QQuickWindow',
                     'QQmlApplicationEngine', 'QRhiWidget'}
        for file in [ROOT / 'main.py', *(ROOT / 'app').rglob('*.py')]:
            tree = ast.parse(file.read_text(encoding='utf-8-sig'))
            for node in ast.walk(tree):
                symbols = []
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    symbols = [alias.name.rsplit('.', 1)[-1] for alias in node.names]
                elif isinstance(node, ast.Attribute):
                    symbols = [node.attr]
                elif isinstance(node, ast.Name):
                    symbols = [node.id]
                self.assertFalse(forbidden.intersection(symbols), str(file))
