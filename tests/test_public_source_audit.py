import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.audit_public_source import audit


class PublicSourceAuditTests(unittest.TestCase):
    def test_secret_and_owner_database_are_rejected_without_printing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = 'ghp_' + 'A' * 36
            (root / 'config.txt').write_text(value)
            (root / 'owner.sqlite').write_bytes(b'private database')
            result = audit(root)
            self.assertEqual({'credential-token', 'private-file'}, {x['kind'] for x in result['problems']})
            self.assertNotIn(value, json.dumps(result))

    def test_reviewed_archive_is_still_inspected_for_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as writer:
                writer.writestr('config.txt', 'github_pat_' + 'A' * 40)
            (root / 'docs').mkdir()
            (root / 'docs/public-binary-inputs.json').write_text(json.dumps({'files': {'fixture.zip': {'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}}}))
            self.assertTrue(any(x['kind'] == 'credential-token' and '!' in x['path'] for x in audit(root)['problems']))

    def test_changed_binary_and_archive_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'model.traineddata').write_bytes(b'unknown model')
            archive = root / 'fixture.zip'
            with zipfile.ZipFile(archive, 'w') as writer:
                writer.writestr('../escape.txt', 'fixture')
            (root / 'docs').mkdir()
            (root / 'docs/public-binary-inputs.json').write_text(json.dumps({'files': {'fixture.zip': {'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}}}))
            self.assertEqual({'unreviewed-binary-input', 'unsafe-archive'}, {x['kind'] for x in audit(root)['problems']})
