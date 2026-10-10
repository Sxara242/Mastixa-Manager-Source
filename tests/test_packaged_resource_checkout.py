"""Exercise real Git checkout conversion without launching the application."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackagedResourceCheckoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.git = shutil.which('git')
        if cls.git is None:
            raise RuntimeError('Git is required for packaged-resource checkout regression tests')
        cls.temp = tempfile.TemporaryDirectory(prefix='mastixa-resource-checkout-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.repo = Path(cls.temp.name) / 'source'
        cls.repo.mkdir()
        config = Path(cls.temp.name) / 'empty-config'
        config.write_bytes(b'')
        cls.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1',
                       GIT_CONFIG_GLOBAL=str(config), GIT_ATTR_NOSYSTEM='1')
        (cls.repo / '.gitattributes').write_bytes((ROOT / '.gitattributes').read_bytes())
        cls.resources = {
            'app/assets/nested/lf.svg': b'<svg>\n</svg>\n',
            'app/assets/nested/crlf.svg': b'<svg>\r\n</svg>\r\n',
            'app/assets/nested/literal[1].png': b'\x89PNG\r\n\x1a\n\x00\xff',
            'app/locales/nested/lf.json': b'{\n  "label": "test"\n}\n',
            'app/locales/nested/crlf.json': b'{\r\n  "label": "test"\r\n}\r\n',
            'app/locales/en_batch3_reports.json':
                (ROOT / 'app/locales/en_batch3_reports.json').read_bytes(),
        }
        for relative, data in cls.resources.items():
            path = cls.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        cls.run_git('init', '--quiet')
        cls.run_git('-c', 'core.autocrlf=false', 'add', '--', '.gitattributes', 'app')
        # Ensure the index contains the exact fixture bytes before testing smudge.
        indexed = cls.run_git('ls-files', '--stage', '-z').split(b'\0')
        for entry in indexed:
            if not entry:
                continue
            header, name = entry.split(b'\t', 1)
            relative = name.decode('utf-8')
            if relative in cls.resources:
                data = cls.resources[relative]
                blob = b'blob ' + str(len(data)).encode('ascii') + b'\0' + data
                if header.split()[1].decode('ascii') != hashlib.sha1(blob).hexdigest():
                    raise AssertionError('Fixture index bytes changed: ' + relative)

    @classmethod
    def run_git(cls, *args):
        result = subprocess.run([cls.git, '-C', str(cls.repo), *args],
                                env=cls.env, capture_output=True, timeout=15)
        if result.returncode:
            raise AssertionError(result.stderr.decode('utf-8', errors='replace'))
        return result.stdout

    def assert_checkout_preserves_bytes(self, autocrlf):
        self.run_git('config', 'core.autocrlf', autocrlf)
        # Require a fresh materialization, as on a hosted checkout. Only known
        # synthetic fixtures under this test's new temporary repo are removed.
        for relative in self.resources:
            (self.repo / relative).unlink()
        self.run_git('checkout-index', '--all', '--force')
        for relative, original in self.resources.items():
            with self.subTest(path=relative, autocrlf=autocrlf):
                checked_out = (self.repo / relative).read_bytes()
                self.assertEqual(checked_out, original)
                self.assertEqual(hashlib.sha256(checked_out).digest(),
                                 hashlib.sha256(original).digest())

    def test_windows_autocrlf_true(self):
        self.assert_checkout_preserves_bytes('true')

    def test_autocrlf_false(self):
        self.assert_checkout_preserves_bytes('false')

    def test_autocrlf_input(self):
        self.assert_checkout_preserves_bytes('input')


if __name__ == '__main__':
    unittest.main()
