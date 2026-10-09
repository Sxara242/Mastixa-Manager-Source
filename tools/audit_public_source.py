"""Fail closed on private files and credential patterns in a public source tree.

This is a bounded publication check, not proof of absence of every possible
secret or copyright claim. Human review of data/rights remains necessary.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PARTS = {'.git', '__pycache__', '.gradle', '.venv', 'venv', 'build', 'dist', '.tools'}
PRIVATE_PARTS = {'data', 'backups', 'logs', 'profile_trash', 'secrets', '.aws', '.ssh'}
PRIVATE_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.pem', '.pfx', '.p12', '.key', '.jks', '.keystore', '.mastixaprofile', '.log', '.apk', '.aab', '.exe', '.dll'}
PATTERNS = {
    'credential-token': re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{25,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{25,}'),
    'signed-token': re.compile(r'eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'signed-download': re.compile(r'https://release-assets\.githubusercontent\.com/[^\s"<>]*[?&](?:sig|jwt)='),
    'personal-path': re.compile(r'(?i)(?:[A-Z]:[/\\]+Users[/\\]+(?!Public\b|Default\b|<|\()[^/\\\s"<>]+|/home/(?!<|\()[^/\s"<>]+)'),
    'credential-url': re.compile(r'https?://[^/\s:@]+:[^/\s@]+@'),
}

def source_paths(root):
    root = Path(root).resolve()
    if (root / '.git').exists():
        result = subprocess.check_output(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'])
        return sorted({n for n in result.decode('utf-8').split('\0') if n})
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*')
                  if p.is_file() and not set(p.relative_to(root).parts) & RUNTIME_PARTS)

def text_findings(data, name):
    # latin1 also exposes ASCII credential strings embedded in binary fixtures.
    text = data.decode('utf-8', errors='replace')
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        for kind, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append({'path': name, 'line': number, 'kind': kind})
    return findings

def audit(root=ROOT):
    root = Path(root).resolve()
    problems = []
    index_path = root / 'docs/public-binary-inputs.json'
    approved = json.loads(index_path.read_text(encoding='utf-8'))['files'] if index_path.is_file() else {}
    count = 0
    for name in source_paths(root):
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            problems.append({'path': name, 'kind': 'unsafe-path'}); continue
        if not p.is_file():
            problems.append({'path': name, 'kind': 'missing-source'}); continue
        count += 1
        parts = set(Path(name).parts)
        if parts & PRIVATE_PARTS or p.suffix.lower() in PRIVATE_SUFFIXES or p.name in {'local.properties', 'key.properties', 'google-services.json'} or p.name.startswith('.env'):
            problems.append({'path': name, 'kind': 'private-file'}); continue
        data = p.read_bytes()
        problems.extend(text_findings(data, name))
        if p.suffix.lower() in {'.zip', '.jar', '.traineddata'}:
            row = approved.get(name)
            if not row or hashlib.sha256(data).hexdigest() != row['sha256']:
                problems.append({'path': name, 'kind': 'unreviewed-binary-input'}); continue
            if p.suffix.lower() in {'.zip', '.jar'}:
                try:
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        if sum(x.file_size for x in archive.infolist()) > 64 * 1024 * 1024:
                            raise ValueError('Oversized fixture')
                        for item in archive.infolist():
                            if item.is_dir(): continue
                            relative = Path(item.filename)
                            if relative.is_absolute() or '..' in relative.parts:
                                raise ValueError('Archive path escape')
                            problems.extend(text_findings(archive.read(item), name + '!' + item.filename))
                except (ValueError, zipfile.BadZipFile, RuntimeError):
                    problems.append({'path': name, 'kind': 'unsafe-archive'})
    return {'files_scanned': count, 'problems': problems,
            'limits': 'Pattern/file/hash checks plus human fixture and rights review; not an exhaustive secret or legal proof.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    result = audit(args.root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result['problems']:
            print(f"{item['kind']}: {item['path']}:{item.get('line', 0)}")
        print(f"{'BLOCKED' if result['problems'] else 'PASS'}: {result['files_scanned']} source files scanned")
    raise SystemExit(bool(result['problems']))
