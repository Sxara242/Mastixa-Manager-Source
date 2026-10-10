"""Non-native source contracts; executable hash cases live in the PS fixture."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackagedResourceHashContracts(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'packaging/smoke_test_packaged.ps1').read_text(encoding='utf-8')

    def test_byte_hash_has_no_cmdlet_dependency_or_error_suppression(self):
        helper = self.source.split('function Get-ResourceSha256 {', 1)[1].split('$repoRoot =', 1)[0]
        for required in ('[System.IO.File]::OpenRead($LiteralPath)',
                         '[System.Security.Cryptography.SHA256]::Create()',
                         '$sha256.ComputeHash($stream)', 'finally {',
                         '$sha256.Dispose()', '$stream.Dispose()'):
            self.assertIn(required, helper)
        self.assertNotIn('catch', helper)
        self.assertNotIn('SilentlyContinue', helper)
        self.assertNotIn('(Get-FileHash', self.source)

    def test_strict_comparison_precedes_process_and_isolation(self):
        preflight = self.source.split('$tempParent =', 1)[0]
        self.assertIn('$ErrorActionPreference = "Stop"', preflight)
        self.assertIn('Get-ChildItem -LiteralPath $sourceRoot -Recurse -File', preflight)
        self.assertIn('Test-Path -LiteralPath $packaged -PathType Leaf', preflight)
        self.assertIn('throw "Missing packaged resource:', preflight)
        self.assertIn('(Get-ResourceSha256 -LiteralPath $source.FullName) -ne\n'
                      '            (Get-ResourceSha256 -LiteralPath $packaged)', preflight)
        self.assertIn('throw "Packaged resource differs', preflight)
        self.assertNotIn('$process.Start()', preflight)

    def test_runtime_fixture_tests_actual_preflight_without_launch(self):
        fixture = (ROOT / 'tests/test_packaged_resource_hash.ps1').read_text(encoding='utf-8')
        for required in ('Parser]::ParseFile', '$loops[0].Extent.Text',
                         'function Get-FileHash { throw', '& $validate',
                         '*Packaged resource differs*', '*Missing packaged resource*',
                         "'ReadWrite', 'None'", 'BA7816BF'):
            self.assertIn(required, fixture)
        self.assertNotIn('Start-Process', fixture)
        self.assertNotIn('$process.Start()', fixture)


if __name__ == '__main__':
    unittest.main()
