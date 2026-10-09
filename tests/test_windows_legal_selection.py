"""Fail-closed legal input selection, including source-only and stale materials."""
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
select = runpy.run_path(str(ROOT / 'packaging/legal_inputs.py'))['legal_data_entries']

class WindowsLegalSelectionTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'licenses').mkdir()
        rows = []
        for name, classification in [('required.txt', 'REQUIRED AND SHIPS'),
                                     ('source.txt', 'REQUIRED FOR SOURCE PACKAGE ONLY'),
                                     ('history.txt', 'NOT APPLICABLE TO CURRENT SHIPPING SURFACE')]:
            path = root / 'licenses' / name
            path.write_bytes(name.encode())
            rows.append(dict(path='licenses/' + name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                             classification=classification, shipping=classification == 'REQUIRED AND SHIPS'))
        return {'texts': rows, 'attributions': []}

    def test_shipping_selection_omits_source_only_and_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); manifest = self.fixture(root)
            (root/'licenses/manifest.json').write_text(json.dumps(manifest))
            self.assertEqual({'manifest.json', 'required.txt'}, {Path(p).name for p, _ in select(root)})

    def test_rejects_unclassified_conflicting_duplicate_changed_and_escaping_inputs(self):
        for change in ('unclassified', 'conflicting', 'duplicate', 'changed', 'escape', 'unindexed'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                root=Path(temp); manifest=self.fixture(root); row=manifest['texts'][0]
                if change == 'unclassified':row.pop('classification')
                elif change == 'conflicting':row['shipping']=False
                elif change == 'duplicate':manifest['attributions'].append(dict(row))
                elif change == 'changed':(root/row['path']).write_text('changed')
                elif change == 'escape':row['path']='licenses/../../outside.txt'
                elif change == 'unindexed':(root/'licenses/extra.txt').write_text('unindexed')
                (root/'licenses/manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):select(root)

    def test_current_inventory_is_classified_and_hash_verified(self):
        entries = select(ROOT)
        manifest=json.loads((ROOT/'licenses/manifest.json').read_text())
        required={r['path'] for r in manifest['texts']+manifest['attributions'] if r['shipping'] and r['path']!='LICENSE'}
        self.assertEqual(required|{'licenses/manifest.json'}, {Path(p).relative_to(ROOT).as_posix() for p, _ in entries})

    def test_source_candidate_is_deterministic_and_excludes_owner_data(self):
        snapshot=runpy.run_path(str(ROOT/'packaging/source_snapshot.py'))['create_snapshot']
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'repo';root.mkdir()
            names=['main.py','LICENSE','packaging/MastixaManager.spec','app/runtime.py',
                   'app/data/owner.json','app/owner.db','backups/archive.json',
                   'app/.env','app/signing.key','licenses/signing.key','unrelated.txt','.git/config']
            for name in names:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
            with patch('subprocess.check_output',return_value=('\0'.join(names)+'\0').encode()):
                first=snapshot(base/'one.zip',root);second=snapshot(base/'two.zip',root)
            self.assertEqual(first['sha256'],second['sha256'])
            self.assertEqual({'main.py','LICENSE','packaging/MastixaManager.spec','app/runtime.py'},set(first['files']))
