"""B2 central-runtime deployment: hash-locked third-party imports, no Microsoft DLLs.

This transforms build output only. Original suppliers/wheels remain immutable.
Recipients install Microsoft's official x64 VC Redist independently of Mastixa.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath


class CrtPolicyError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_crt(name):
    name = PureWindowsPath(name).name.casefold()
    return name.endswith('.dll') and name.startswith(
        ('msvcp', 'msvcr', 'vcruntime', 'concrt', 'vccorlib', 'vcomp'))


def load_policy(root):
    policy = json.loads((Path(root) / 'packaging/windows-crt-policy.json').read_text(encoding='utf-8'))
    if policy['schema'] != 1 or policy['route'] != 'independently-installed-official-x64-redist':
        raise CrtPolicyError('Unknown CRT deployment policy')
    removed = [r['destination'].casefold() for r in policy['removed_inputs']]
    patched = [r['destination'].casefold() for r in policy['import_normalization']]
    if len(removed) != 13 or len(set(removed)) != 13 or len(patched) != 5 or len(set(patched)) != 5:
        raise CrtPolicyError('Incomplete/duplicate B2 input lock')
    return policy


def normalize_import(data, row):
    """Change exactly one unsigned third-party PE import string and its checksum."""
    import pefile
    if hashlib.sha256(data).hexdigest() != row['source_sha256']:
        raise CrtPolicyError('Third-party importer source hash mismatch: ' + row['destination'])
    pe = pefile.PE(data=data)
    if pe.FILE_HEADER.Machine != 0x8664 or pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size or pe.OPTIONAL_HEADER.DATA_DIRECTORY[11].Size:
        raise CrtPolicyError('Unsupported architecture, signed or bound importer')
    entries = [e for e in pe.DIRECTORY_ENTRY_IMPORT if e.dll.decode().casefold() == row['old_import'].casefold()]
    if len(entries) != 1 or entries[0].struct.TimeDateStamp:
        raise CrtPolicyError('Unexpected import table')
    entry = entries[0]
    offset = pe.get_offset_from_rva(entry.struct.Name)
    old, new = entry.dll + b'\0', b'msvcp140.dll\0'
    if len(new) >= len(old) or data[offset:offset+len(old)] != old:
        raise CrtPolicyError('Unexpected import string storage')
    output = bytearray(data)
    output[offset:offset+len(old)] = new.ljust(len(old), b'\0')
    edited = pefile.PE(data=bytes(output))
    checksum_offset = edited.OPTIONAL_HEADER.get_field_absolute_offset('CheckSum')
    output[checksum_offset:checksum_offset+4] = edited.generate_checksum().to_bytes(4, 'little')
    result = bytes(output)
    if hashlib.sha256(result).hexdigest() != row['output_sha256']:
        raise CrtPolicyError('Normalized importer output hash mismatch')
    return result


def normalize_analysis(binaries, root, output_directory):
    policy = load_policy(root)
    removed = {r['destination'].casefold(): r for r in policy['removed_inputs']}
    patched = {r['destination'].casefold(): r for r in policy['import_normalization']}
    output_directory = Path(output_directory).resolve()
    result, removed_seen, patched_seen, destinations = [], set(), set(), set()
    for destination, source, kind in binaries:
        key = destination.replace('\\', '/').casefold()
        if key in destinations:
            raise CrtPolicyError('Duplicate binary destination: ' + destination)
        destinations.add(key)
        if key in removed:
            if kind != 'BINARY' or digest(source) != removed[key]['sha256']:
                raise CrtPolicyError('CRT supplier input changed: ' + destination)
            removed_seen.add(key)
            continue
        if is_crt(destination):
            raise CrtPolicyError('Unexpected Microsoft runtime collection: ' + destination)
        if key in patched:
            if kind not in ('BINARY', 'EXTENSION'):
                raise CrtPolicyError('Importer is not a binary')
            content = normalize_import(Path(source).read_bytes(), patched[key])
            target = output_directory / destination.replace('\\', '/')
            if not target.resolve().is_relative_to(output_directory):
                raise CrtPolicyError('Importer output path escapes build directory')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            source = str(target)
            patched_seen.add(key)
        result.append((destination, source, kind))
    if removed_seen != set(removed) or patched_seen != set(patched):
        raise CrtPolicyError('Missing locked CRT input/importer in Analysis')
    return result


def verify_bundle(bundle, root):
    policy = load_policy(root)
    bundle = Path(bundle)
    crt_files = [p for p in bundle.rglob('*') if p.is_file() and is_crt(p.name)]
    if crt_files:
        raise CrtPolicyError('Central-runtime bundle contains Microsoft CRT: ' + str(crt_files[0]))
    for row in policy['import_normalization']:
        p = bundle / '_internal' / row['destination']
        if not p.is_file() or digest(p) != row['output_sha256']:
            raise CrtPolicyError('Missing/changed normalized bundled importer: ' + row['destination'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    args = parser.parse_args()
    verify_bundle(args.bundle, Path(__file__).resolve().parents[1])
