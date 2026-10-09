"""Release guards reject ambient discovery even when DLL bytes are identical."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
gate = runpy.run_path(str(ROOT / 'packaging/tls_inputs.py'))


class WindowsTlsInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.roots = {s: self.base / s for s in ('python', 'qt')}
        self.lock = {'schema': 1, 'status': 'QUALIFIED', 'forbidden_sha256': []}
        for stack, names in [('python', ['libssl-3.dll', 'libcrypto-3.dll', 'python.exe', 'python314.dll', '_ssl.pyd', '_hashlib.pyd']), ('qt', ['libssl-3-x64.dll', 'libcrypto-3-x64.dll'])]:
            self.roots[stack].mkdir()
            files = []
            for name in names:
                p = self.roots[stack] / name
                p.write_bytes(('synthetic-' + name).encode())
                files.append({'destination': name, 'relative_path': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
            self.lock[stack] = {'classification': 'ACCEPTABLE FOR RC', 'openssl_version': '3.5.9' if stack == 'python' else '3.6.5', 'supplier_url': 'https://supplier.example/exact.zip', 'archive_sha256': 'a' * 64, 'files': files}
        self.inputs = gate['resolve_inputs'](self.lock, self.roots)
        self.toc = [(n, str(p), 'BINARY') for n, (p, h) in self.inputs.items() if n != 'python.exe']

    def write_lock(self, lock):
        folder = self.base / 'config/packaging'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'windows-tls-inputs.json').write_text(json.dumps(lock))
        return folder.parent

    def test_current_release_has_qualified_tls_suppliers(self):
        lock = gate['load_lock'](ROOT)
        self.assertEqual(lock['python']['runtime_version'], '3.14.8')
        self.assertEqual(lock['qt']['openssl_version'], '3.5.9')
        self.assertTrue(all(lock[s]['supplier_root'] for s in ('python', 'qt')))

    def test_unqualified_qt_supplier_is_rejected(self):
        self.lock['status'] = 'BLOCKED'
        with self.assertRaisesRegex(gate['TlsInputError'], 'B5 BLOCKED'):
            gate['load_lock'](self.write_lock(self.lock))

    def test_identical_qt_override_outside_pinned_root_is_rejected(self):
        lock = copy.deepcopy(self.lock)
        for stack in ('python', 'qt'):
            lock[stack]['supplier_root'] = str(self.roots[stack])
        other = self.base / 'tool-path'
        other.mkdir()
        for source in self.roots['qt'].iterdir():
            (other / source.name).write_bytes(source.read_bytes())
        with patch.object(gate['prepare'].__globals__['sys'], 'base_prefix', str(self.roots['python'])):
            with patch.dict(os.environ, {'MASTIXA_QT_TLS_ROOT': str(other)}):
                with self.assertRaisesRegex(gate['TlsInputError'], 'outside the pinned supplier root'):
                    gate['prepare'](self.write_lock(lock))

    def test_old_versions_cannot_be_declared_qualified(self):
        for stack, version in [('python', '3.5.7'), ('qt', '3.6.4'), ('qt', '4.0.1')]:
            lock = copy.deepcopy(self.lock)
            lock[stack]['openssl_version'] = version
            with self.assertRaisesRegex(gate['TlsInputError'], 'unsupported/unpatched'):
                gate['load_lock'](self.write_lock(lock))

    def test_supplier_receipt_required(self):
        self.lock['qt']['archive_sha256'] = None
        with self.assertRaisesRegex(gate['TlsInputError'], 'supplier receipt'):
            gate['load_lock'](self.write_lock(self.lock))

    def test_explicit_locked_sources_pass(self):
        gate['load_lock'](self.write_lock(self.lock))
        gate['verify_analysis'](self.toc, self.inputs)

    def test_identical_bytes_from_arbitrary_path_are_rejected(self):
        dest, source, kind = self.toc[0]
        p = self.base / 'tooling.dll'
        p.write_bytes(Path(source).read_bytes())
        with self.assertRaisesRegex(gate['TlsInputError'], 'outside supplier'):
            gate['verify_analysis']([(dest, str(p), kind), *self.toc[1:]], self.inputs)

    def test_unknown_and_duplicate_tls_are_rejected(self):
        for extra in [('libssl-unknown.dll', self.toc[0][1], 'BINARY'), self.toc[0], ('sub/libcrypto-3.dll', self.toc[0][1], 'BINARY')]:
            with self.assertRaisesRegex(gate['TlsInputError'], 'Unknown, duplicate or relocated'):
                gate['verify_analysis']([*self.toc, extra], self.inputs)

    def test_partial_pair_and_mutated_input_rejected(self):
        with self.assertRaisesRegex(gate['TlsInputError'], 'omitted'):
            gate['verify_analysis'](self.toc[:-1], self.inputs)
        Path(self.toc[0][1]).write_bytes(b'changed')
        with self.assertRaisesRegex(gate['TlsInputError'], 'changed during'):
            gate['verify_analysis'](self.toc, self.inputs)

    def test_old_hash_and_supplier_root_escape_rejected(self):
        self.lock['forbidden_sha256'] = [next(iter(self.inputs.values()))[1]]
        with self.assertRaisesRegex(gate['TlsInputError'], 'forbidden old'):
            gate['resolve_inputs'](self.lock, self.roots)
        self.lock['forbidden_sha256'] = []
        outside = self.base / 'outside.dll'
        outside.write_bytes(b'outside')
        self.lock['python']['files'][0]['relative_path'] = '../outside.dll'
        with self.assertRaisesRegex(gate['TlsInputError'], 'escapes'):
            gate['resolve_inputs'](self.lock, self.roots)

    def test_bundle_rejects_old_unknown_duplicate_or_missing_files(self):
        bundle = self.base / 'bundle'
        internal = bundle / '_internal'
        internal.mkdir(parents=True)
        for name, (p, h) in self.inputs.items():
            (internal / name).write_bytes(p.read_bytes())
        gate['verify_bundle'](bundle, self.lock)
        extra = internal / 'libssl-unknown.dll'
        extra.write_bytes(b'unknown')
        with self.assertRaises(gate['TlsInputError']):
            gate['verify_bundle'](bundle, self.lock)
        extra.unlink()
        (internal / self.toc[0][0]).write_bytes(b'old')
        with self.assertRaisesRegex(gate['TlsInputError'], 'membership/hash'):
            gate['verify_bundle'](bundle, self.lock)

    def test_discovery_environment_is_restricted_and_restored(self):
        values = {'SystemRoot': str(self.base / 'Windows'), 'PATH': 'tooling;arbitrary', 'QT_PLUGIN_PATH': 'wrong', 'OPENSSL_CONF': 'wrong'}
        with patch.dict(os.environ, values):
            with gate['supplier_environment'](self.roots):
                self.assertNotIn('tooling', os.environ['PATH'])
                self.assertNotIn('QT_PLUGIN_PATH', os.environ)
                self.assertNotIn('OPENSSL_CONF', os.environ)
                self.assertIn(str(self.roots['qt']), os.environ['PATH'])
            self.assertEqual('tooling;arbitrary', os.environ['PATH'])
            self.assertEqual('wrong', os.environ['QT_PLUGIN_PATH'])


if __name__ == '__main__':
    unittest.main()
