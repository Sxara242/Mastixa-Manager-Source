"""B2 fail-closed build and bundle boundary; no global runtime changes."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = runpy.run_path(str(ROOT / 'packaging/crt_policy.py'))
ERROR = POLICY['CrtPolicyError']


class WindowsCrtPolicyTests(unittest.TestCase):
    def test_rejects_unexpected_renamed_crt_before_collection(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaisesRegex(ERROR, 'Unexpected Microsoft runtime'):
                POLICY['normalize_analysis']([('vendor/msvcp140-unqualified.dll', 'unused', 'BINARY')], ROOT, out)

    def test_missing_locked_inputs_cannot_silently_pass(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaisesRegex(ERROR, 'Missing locked CRT input'):
                POLICY['normalize_analysis']([], ROOT, out)

    def test_changed_crt_supplier_bytes_cannot_be_silently_removed(self):
        row = POLICY['load_policy'](ROOT)['removed_inputs'][0]
        with tempfile.TemporaryDirectory() as out:
            p = Path(out) / 'changed.dll'; p.write_bytes(b'changed supplier')
            with self.assertRaisesRegex(ERROR, 'CRT supplier input changed'):
                POLICY['normalize_analysis']([(row['destination'], str(p), 'BINARY')], ROOT, out)

    def test_duplicate_destinations_are_rejected_case_insensitively(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaisesRegex(ERROR, 'Duplicate binary destination'):
                POLICY['normalize_analysis']([('vendor/a.dll', 'unused', 'BINARY'), ('VENDOR\\A.DLL', 'unused', 'BINARY')], ROOT, out)

    def test_changed_importer_is_rejected_before_pe_edit(self):
        row = POLICY['load_policy'](ROOT)['import_normalization'][0]
        with self.assertRaisesRegex(ERROR, 'source hash mismatch'):
            POLICY['normalize_import'](b'wrong PE input', row)

    def test_bundle_rejects_even_one_hashed_microsoft_copy(self):
        with tempfile.TemporaryDirectory() as out:
            p = Path(out) / '_internal/vendor/msvcp140-unknown.dll'; p.parent.mkdir(parents=True); p.write_bytes(b'fixture')
            with self.assertRaisesRegex(ERROR, 'contains Microsoft CRT'):
                POLICY['verify_bundle'](out, ROOT)

    def test_bundle_requires_each_normalized_importer(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaisesRegex(ERROR, 'Missing/changed normalized'):
                POLICY['verify_bundle'](out, ROOT)

    def test_policy_and_installer_are_a_no_copy_prerequisite(self):
        policy = POLICY['load_policy'](ROOT)
        self.assertEqual('independently-installed-official-x64-redist', policy['route'])
        self.assertEqual('14.51.36247.0', policy['minimum_version'])
        text = (ROOT / 'installer/vc_redist_prerequisite.iss').read_text()
        self.assertNotIn('ShellExec(', text)
        self.assertNotIn('Exec(', text)
        setup = (ROOT / 'installer/MastixaManager.iss').read_text()
        self.assertIn('Result := VcRedistPrerequisiteReady;', setup)
        self.assertNotIn('Source: "vc_redist', setup)


if __name__ == '__main__':
    unittest.main()
