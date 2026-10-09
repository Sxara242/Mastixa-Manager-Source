"""Build-time TLS provenance gates; never enforce hashes in an installed app."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys


class TlsInputError(RuntimeError):
    pass


def is_openssl(name):
    name = PureWindowsPath(name).name.casefold()
    return name.endswith('.dll') and name.startswith(('libssl', 'libcrypto', 'ssleay', 'libeay'))


def load_lock(root):
    lock = json.loads((Path(root) / 'packaging/windows-tls-inputs.json').read_text(encoding='utf-8'))
    if lock.get('schema') != 1 or lock.get('status') != 'QUALIFIED':
        raise TlsInputError('B5 BLOCKED: TLS supplier inputs are not qualified; ambient PATH is forbidden')
    for stack in ('python', 'qt'):
        item = lock[stack]
        if item.get('classification') != 'ACCEPTABLE FOR RC':
            raise TlsInputError(f'{stack}: TLS security qualification missing')
        version = tuple(int(v) for v in item['openssl_version'].split('.'))
        minimum = {(3, 5): 9, (3, 6): 5}.get(version[:2])
        if len(version) != 3 or minimum is None or version[2] < minimum:
            raise TlsInputError(f'{stack}: unsupported/unpatched TLS version')
        if not (item.get('supplier_url') or '').startswith('https://') or not re.fullmatch(r'[0-9a-f]{64}', item.get('archive_sha256') or ''):
            raise TlsInputError(f'{stack}: immutable supplier receipt missing')
    return lock


def resolve_inputs(lock, roots):
    """Only exact locked paths under explicit supplier roots are accepted."""
    inputs = {}
    for stack in ('python', 'qt'):
        root = Path(roots[stack]).resolve(strict=True)
        files = lock[stack]['files']
        expected = {'libssl-3.dll', 'libcrypto-3.dll'} if stack == 'python' else {'libssl-3-x64.dll', 'libcrypto-3-x64.dll'}
        if {r['destination'].casefold() for r in files if is_openssl(r['destination'])} != expected:
            raise TlsInputError(f'{stack}: exact TLS DLL pair missing')
        if stack == 'python' and not {'python.exe', 'python314.dll', '_ssl.pyd', '_hashlib.pyd'}.issubset({r['destination'].casefold() for r in files}):
            raise TlsInputError('Coherent Python supplier runtime/extension pins missing')
        for row in files:
            name = row['destination']
            if name != PureWindowsPath(name).name or name.casefold() in inputs:
                raise TlsInputError('TLS lock contains a nested/duplicate destination')
            source = (root / row['relative_path']).resolve(strict=True)
            if not source.is_relative_to(root):
                raise TlsInputError('TLS supplier path escapes its explicit root')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest in lock['forbidden_sha256'] or digest != row['sha256']:
                raise TlsInputError(f'{name}: TLS hash mismatch or forbidden old binary')
            inputs[name.casefold()] = (source, digest)
    return inputs


def verify_analysis(binaries, inputs):
    seen = set()
    for dest, source, kind in binaries:
        name = PureWindowsPath(dest).name.casefold()
        if not is_openssl(dest) and name not in inputs:
            continue
        if name not in inputs or name in seen or dest.replace('\\', '/') != PureWindowsPath(dest).name:
            raise TlsInputError(f'Unknown, duplicate or relocated TLS binary: {dest}')
        approved, digest = inputs[name]
        if Path(source).resolve(strict=True) != approved:
            raise TlsInputError(f'TLS discovery outside supplier input (including PATH/tooling): {dest}')
        if hashlib.sha256(approved.read_bytes()).hexdigest() != digest:
            raise TlsInputError(f'TLS input changed during Analysis: {dest}')
        seen.add(name)
    expected = {n for n in inputs if n != 'python.exe'}
    if seen != expected:
        raise TlsInputError('Analysis omitted one or more approved TLS DLLs')


def verify_bundle(bundle, lock):
    expected = {r['destination'].casefold(): r['sha256'] for s in ('python', 'qt') for r in lock[s]['files'] if r['destination'].casefold() != 'python.exe'}
    actual = {}
    for p in Path(bundle).rglob('*'):
        if p.is_file() and (is_openssl(p.name) or p.name.casefold() in expected):
            relative = p.relative_to(bundle).as_posix()
            name = p.name.casefold()
            if name not in expected or name in actual or relative.casefold() != '_internal/' + name:
                raise TlsInputError(f'Unknown, duplicate or relocated bundled TLS binary: {relative}')
            actual[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected or any(h in lock['forbidden_sha256'] for h in actual.values()):
        raise TlsInputError('Bundled TLS membership/hash mismatch or forbidden old binary')


@contextmanager
def supplier_environment(roots):
    """Restrict discovery in the build process before any Qt hook is imported."""
    names = ('PATH', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'QT_CONF_PATH', 'OPENSSL_CONF', 'OPENSSL_MODULES')
    old = {n: os.environ.get(n) for n in names}
    system = Path(os.environ['SystemRoot'])
    os.environ['PATH'] = os.pathsep.join(str(p) for p in (Path(roots['qt']), Path(roots['python']) / 'DLLs', system / 'System32', system))
    for n in names[1:]:
        os.environ.pop(n, None)
    try:
        yield
    finally:
        for n, value in old.items():
            if value is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = value


def prepare(root):
    lock = load_lock(root)
    roots = {stack: (Path(root) / lock[stack]['supplier_root']).resolve(strict=True)
             for stack in ('python', 'qt')}
    if Path(sys.base_prefix).resolve(strict=True) != roots['python']:
        raise TlsInputError('Build interpreter is outside the pinned Python supplier root')
    override = os.environ.get('MASTIXA_QT_TLS_ROOT')
    if override and Path(override).resolve(strict=True) != roots['qt']:
        raise TlsInputError('Qt TLS override is outside the pinned supplier root')
    if sys.version.split()[0] != lock['python']['runtime_version']:
        raise TlsInputError('Build interpreter does not match qualified supplier runtime')
    return lock, roots, resolve_inputs(lock, roots)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    verify_bundle(args.bundle, load_lock(Path(__file__).resolve().parent.parent))
