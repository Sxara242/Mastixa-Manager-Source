"""Select release legal materials from the reviewed hash index."""
import hashlib
import json
from pathlib import Path, PurePosixPath

CLASSIFICATIONS = frozenset({
    'REQUIRED AND SHIPS', 'REQUIRED FOR SOURCE PACKAGE ONLY',
    'OPTIONAL/INFORMATIONAL', 'NOT APPLICABLE TO CURRENT SHIPPING SURFACE',
})

def legal_data_entries(root):
    root = Path(root).resolve()
    manifest = json.loads((root / 'licenses/manifest.json').read_text(encoding='utf-8'))
    entries = [(str(root / 'licenses/manifest.json'), 'licenses')]
    seen = set()
    for item in manifest['texts'] + manifest.get('attributions', []):
        name = item['path']
        if name in seen:
            raise ValueError(f'Duplicate legal path: {name}')
        seen.add(name)
        relative = PurePosixPath(name)
        path = (root / name).resolve()
        if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(root):
            raise ValueError(f'Legal path escapes source root: {name}')
        if name != 'LICENSE' and not name.startswith('licenses/'):
            raise ValueError(f'Unexpected legal input: {name}')
        classification = item.get('classification')
        if classification not in CLASSIFICATIONS:
            raise ValueError(f'Unclassified legal input: {name}')
        shipping = item.get('shipping', False)
        if shipping != (classification == 'REQUIRED AND SHIPS'):
            raise ValueError(f'Inconsistent legal shipping disposition: {name}')
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Legal input missing/changed: {name}')
        if shipping and name != 'LICENSE':
            entries.append((str(path), relative.parent.as_posix()))
    actual = {p.relative_to(root).as_posix() for p in (root / 'licenses').rglob('*') if p.is_file()}
    unexpected = actual - seen - {'licenses/manifest.json'}
    if unexpected:
        raise ValueError(f'Unindexed legal inputs: {sorted(unexpected)}')
    return sorted(entries, key=lambda entry: entry[0])
