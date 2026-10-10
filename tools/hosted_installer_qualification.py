"""Disposable GitHub-hosted Windows only. Never execute on a local profile."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
INSTALLER_SHA256 = 'e66a1932bcb1a9c7b5ea2371e99cca0561883ba11b72189d3405010d009b8782'
EXE_SHA256 = '3e545d4257d8c15d33d5de0f55b43797f3d1a3690f9a63a69a9a26f647380403'
BLOCKED = (
    'ace3c4dbf470e19edbeef0eab62a7121af6890b809b461fe3d5cd778ecf6821e',
    '50c2291c4d8765dbfb5479a3c17c2b8a909a763236cd45d799b29ebf1c988ce3',
)
PREFERENCES = r'Software\Mastixa\Mastixa Manager'
UNINSTALL = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B9B946A2-8711-4B35-9BCB-B40210E67357}_is1'

SHORTCUT_OBSERVATION_SCRIPT = r"""
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$OutputEncoding=[Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding=$OutputEncoding
$context=[ordered]@{phase='com-create';kind=$null;folder_empty=$null;
  folder_exists=$null;link_exists=$null;powershell=$PSVersionTable.PSVersion.ToString();
  edition=$PSVersionTable.PSEdition;hash_provider='System.Security.Cryptography.SHA256'}
try {
  $shell=New-Object -ComObject WScript.Shell
  $items=@()
  foreach($kind in @('Programs','CommonPrograms','DesktopDirectory','CommonDesktopDirectory')) {
    $context.kind=$kind;$context.phase='folder-resolve'
    $context.folder_exists=$null;$context.link_exists=$null
    $folder=[Environment]::GetFolderPath([Environment+SpecialFolder]::$kind)
    $context.folder_empty=[string]::IsNullOrWhiteSpace($folder)
    if($context.folder_empty) { throw 'SpecialFolderEmpty' }
    $context.folder_exists=Test-Path -LiteralPath $folder -PathType Container
    $path=Join-Path $folder 'Mastixa Manager.lnk'
    $context.phase='link-exists'
    $item=[ordered]@{kind=$kind;path=$path;exists=(Test-Path -LiteralPath $path)}
    $context.link_exists=$item.exists
    if($item.exists) {
      $context.phase='com-read'
      $link=$shell.CreateShortcut($path)
      $item.target=$link.TargetPath;$item.arguments=$link.Arguments
      $item.working_directory=$link.WorkingDirectory;$item.icon_location=$link.IconLocation
      $context.phase='file-metadata'
      $file=Get-Item -LiteralPath $path
      $item.creation_utc=$file.CreationTimeUtc.ToString('o')
      $item.last_write_utc=$file.LastWriteTimeUtc.ToString('o')
      $context.phase='file-hash'
      $stream=$null;$hasher=$null
      try {
        $stream=[IO.File]::OpenRead($path)
        $hasher=[Security.Cryptography.SHA256]::Create()
        $item.sha256=[BitConverter]::ToString($hasher.ComputeHash($stream)).Replace('-','').ToLowerInvariant()
      } finally {
        if($null -ne $hasher) { $hasher.Dispose() }
        if($null -ne $stream) { $stream.Dispose() }
      }
    }
    $items+=$item
  }
  $context.phase='json-serialize'
  ConvertTo-Json -InputObject $items -Depth 5 -Compress
} catch {
  # Structured context contains no file paths, shortcut arguments or environment.
  $context.error_id=$_.FullyQualifiedErrorId
  $context.exception_type=$_.Exception.GetType().Name
  $context.hresult=$_.Exception.HResult
  [Console]::Error.WriteLine((ConvertTo-Json -InputObject $context -Depth 4 -Compress))
  exit 1
}
"""


def redact_observation(text, environment):
    """Bounded diagnostics only; never retain environment secrets or paths."""
    text = text.decode('utf-8', errors='replace') if isinstance(text, bytes) else str(text or '')
    for name, value in sorted(environment.items(), key=lambda item: len(item[1]), reverse=True):
        if value and (re.search(r'TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH|KEY', name, re.I)
                      or name in ('USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'RUNNER_TEMP', 'GITHUB_WORKSPACE', 'TEMP', 'TMP')):
            for form in (value, json.dumps(value)[1:-1]):
                text = text.replace(form, '<REDACTED>')
    text = re.sub(r'https?://[^\s"<>]+', '<URL>', text, flags=re.I)
    text = re.sub(r'(?i)(?:gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)', '<SECRET>', text)
    text = re.sub(r'(?i)(?:authorization|bearer|token|password|secret|credential|api[_-]?key)\s*[:= ]+[^\s,;"<>]+', '<SECRET>', text)
    text = re.sub(r'(?i)[a-z]:[\\/][^\r\n"<>]*|\\\\[^\r\n"<>]+|/(?:home|Users)/[^\r\n"<>]+', '<PATH>', text)
    # Shortcut argument strings can contain arbitrary credentials, even in JSON.
    text = re.sub(r'("arguments"\s*:\s*)"(?:\\.|[^"\\])*"', r'\1"<REDACTED>"', text)
    return text[:16384]


def read_shortcuts(out, label, environment):
    """Fail closed and preserve sanitized child diagnostics before raising."""
    command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', SHORTCUT_OBSERVATION_SCRIPT]
    context = {'operation': 'shortcut-observation', 'label': label, 'shell': 'powershell.exe',
               'timeout_seconds': 30, 'exit_code': None, 'status': 'FAIL'}
    stdout = stderr = ''
    try:
        completed = subprocess.run(command, env=environment, capture_output=True, text=True,
                                   encoding='utf-8', errors='replace', timeout=30, check=False)
        context['exit_code'] = completed.returncode
        stdout, stderr = completed.stdout, completed.stderr
        if completed.returncode != 0:
            raise RuntimeError('Shortcut observation child failed')
        items = json.loads(stdout)
        kinds = ('Programs', 'CommonPrograms', 'DesktopDirectory', 'CommonDesktopDirectory')
        if (not isinstance(items, list) or len(items) != len(kinds)
                or {item['kind'] for item in items} != set(kinds)
                or any(not isinstance(item['path'], str) or not item['path']
                       or type(item['exists']) is not bool for item in items)):
            raise ValueError('Incomplete shortcut observation')
        return items
    except (subprocess.TimeoutExpired, OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        context['exception_type'] = type(error).__name__
        if isinstance(error, subprocess.TimeoutExpired):
            stdout, stderr = error.stdout, error.stderr
            context['timed_out'] = True
        if isinstance(error, OSError):
            context['errno'] = error.errno
        context['stdout'] = redact_observation(stdout, environment)
        context['stderr'] = redact_observation(stderr, environment)
        evidence = out / ('shortcut-observation-' + label + '.json')
        try:
            with evidence.open('x', encoding='utf-8') as stream:
                json.dump(context, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError:
            raise RuntimeError('Shortcut observation failed; sanitized diagnostics could not be persisted') from None
        # Do not let CalledProcessError/TimeoutExpired print the command/output.
        raise RuntimeError('Shortcut observation failed; diagnostic=' + evidence.name) from None


def require_hosted(env, platform):
    expected = {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
                'RUNNER_OS': 'Windows', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
                'GITHUB_REPOSITORY': 'Sxara242/Mastixa-Manager-Source',
                'MASTIXA_HOSTED_NATIVE_EXECUTE': '1'}
    if platform != 'nt' or any(env.get(key) != value for key, value in expected.items()):
        raise RuntimeError('Disposable GitHub-hosted Windows workflow_dispatch only')
    for key in ('RUNNER_TEMP', 'GITHUB_RUN_ID', 'GITHUB_SHA'):
        if not env.get(key):
            raise RuntimeError('Missing hosted context: ' + key)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_identity(actual, expected):
    if actual in BLOCKED or actual != expected:
        raise RuntimeError('Candidate hash refused')


def tree(path):
    return {p.relative_to(path).as_posix(): digest(p)
            for p in sorted(path.rglob('*')) if p.is_file()}


def snapshot(registry, key):
    try:
        handle = registry.OpenKey(registry.HKEY_CURRENT_USER, key, 0, registry.KEY_READ)
    except FileNotFoundError:
        return None
    with handle:
        values, children = [], {}
        for index in range(registry.QueryInfoKey(handle)[1]):
            name, value, kind = registry.EnumValue(handle, index)
            values.append([name, repr(value), kind])
        for index in range(registry.QueryInfoKey(handle)[0]):
            name = registry.EnumKey(handle, index)
            child = snapshot(registry, key + '\\' + name)
            if child is None:
                raise RuntimeError('Key disappeared during read-only snapshot')
            children[name] = child
        return {'values': sorted(values), 'children': children}


def shortcut_contract(link, executable):
    if link is None:
        raise RuntimeError('Expected installed shortcut missing')
    target = str(executable).casefold()
    if link['target'].casefold() != target or link['arguments'] != '':
        raise RuntimeError('Incorrect shortcut target/arguments')
    if link['working_directory'].rstrip('\\').casefold() != str(executable.parent).casefold():
        raise RuntimeError('Incorrect shortcut working directory')
    icon_path, separator, icon_index = link['icon_location'].rpartition(',')
    if not separator:
        icon_path, icon_index = link['icon_location'], '0'
    # An unspecified IconFilename is Shell's default icon from the link target.
    if (icon_path or link['target']).casefold() != target or icon_index != '0':
        raise RuntimeError('Incorrect shortcut icon')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=('noicons', 'normal', 'preservation', 'purge'), required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    # This guard precedes all native imports, registry access and evidence writes.
    require_hosted(os.environ, os.name)
    import winreg
    candidate = args.candidate.resolve(strict=True)
    installers = list((candidate / 'installer').glob('*.exe'))
    if len(installers) != 1:
        raise RuntimeError('Exactly one retained candidate installer required')
    installer = installers[0]
    verify_identity(digest(installer), INSTALLER_SHA256)
    expected_bundle = candidate / 'MastixaManager'
    verify_identity(digest(expected_bundle / 'MastixaManager.exe'), EXE_SHA256)
    payload = tree(expected_bundle)
    if len(payload) != 559:
        raise RuntimeError('Unexpected retained payload inventory')
    out = args.output.resolve()
    runner_temp = Path(os.environ['RUNNER_TEMP']).resolve()
    if out.exists() or not out.is_relative_to(runner_temp):
        raise RuntimeError('Fresh evidence path under RUNNER_TEMP required')
    out.mkdir(parents=True)
    # Keep native paths short independently of repository checkout length.
    target = runner_temp / ('mrc2-' + args.scenario)
    if target.exists():
        raise RuntimeError('Fresh install target required')
    data = Path(os.environ['LOCALAPPDATA']) / 'MastixaManager'
    unrelated_data = Path(os.environ['LOCALAPPDATA']) / ('MastixaQualificationUnrelated-' + args.scenario)
    unrelated_key = 'Software\\MastixaQualificationUnrelated\\' + args.scenario
    env = os.environ.copy()
    temp = out / 'native-temp'
    temp.mkdir()
    env.update(TEMP=str(temp), TMP=str(temp), MASTIXA_DATA_HOME=str(out / 'synthetic-app-data'))
    for name in ('PYTHONPATH', 'PYTHONHOME', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
        env.pop(name, None)
    report = {'status': 'RUNNING', 'scenario': args.scenario,
              'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
              'workflow_url': 'https://github.com/' + os.environ['GITHUB_REPOSITORY'] + '/actions/runs/' + os.environ['GITHUB_RUN_ID'],
              'commit': os.environ['GITHUB_SHA'], 'branch': os.environ.get('GITHUB_REF'),
              'installer_sha256': digest(installer), 'exe_sha256': EXE_SHA256,
              'target': str(target), 'stages': [], 'observations': [],
              'synthetic_state_only': True, 'automatic_restoration': False}

    def save():
        with (out / 'result.json').open('w', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())

    def links(label):
        items = read_shortcuts(out, label, env)
        report['shortcut_paths'] = {item['kind']: item['path'] for item in items}
        return {item['kind']: item if item['exists'] else None for item in items}

    def observe(label):
        state = {'label': label, 'preferences': snapshot(winreg, PREFERENCES),
                 'uninstall_registration': snapshot(winreg, UNINSTALL),
                 'user_data': tree(data), 'unrelated_registry': snapshot(winreg, unrelated_key),
                 'unrelated_data': tree(unrelated_data), 'shortcuts': links(label),
                 'target_exists': target.exists()}
        report['observations'].append(state)
        save()
        return state

    def run(label, command, timeout, child_env=env):
        observe('before-' + label)
        stage = {'label': label, 'command': command, 'status': 'RUNNING'}
        report['stages'].append(stage)
        save()
        with (out / (label + '-stdout.log')).open('xb') as stdout, (out / (label + '-stderr.log')).open('xb') as stderr:
            result = subprocess.run(command, env=child_env, cwd=out, timeout=timeout, stdout=stdout, stderr=stderr)
        stage.update(exit_code=result.returncode, status='PASS' if result.returncode == 0 else 'FAIL')
        after = observe('after-' + label)
        if result.returncode != 0:
            raise RuntimeError(label + ' native exit ' + str(result.returncode))
        return after

    def install(label, noicons=False, desktop=False):
        switches = ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART',
                    '/NOCLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS',
                    '/TASKS=' + ('desktopicon' if desktop else ''), '/DIR=' + str(target),
                    '/LOG=' + str(out / (label + '.log'))]
        if noicons:
            switches.append('/NOICONS')
        state = run(label, [str(installer), *switches], 240)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL, 0, winreg.KEY_READ) as key:
            if winreg.QueryValueEx(key, 'DisplayVersion')[0] != '1.0.0-rc.2':
                raise RuntimeError('Wrong installed version')
            if Path(winreg.QueryValueEx(key, 'InstallLocation')[0]).resolve() != target:
                raise RuntimeError('Wrong install registration target')
        installed = tree(target)
        report.setdefault('payload_checks', []).append({'label': label, 'files': len(payload),
            'differences': [name for name, expected in payload.items() if installed.get(name) != expected]})
        save()
        if report['payload_checks'][-1]['differences']:
            raise RuntimeError('Installed payload differs from retained bundle')
        if noicons:
            if state['shortcuts'] != initial['shortcuts']:
                raise RuntimeError('/NOICONS changed a relevant shortcut; stop, no restoration')
        else:
            shortcut_contract(state['shortcuts']['Programs'], target / 'MastixaManager.exe')
            if desktop:
                shortcut_contract(state['shortcuts']['DesktopDirectory'], target / 'MastixaManager.exe')
            elif state['shortcuts']['DesktopDirectory'] is not None:
                raise RuntimeError('Unexpected default desktop shortcut')
            if any(state['shortcuts'][name] is not None for name in ('CommonPrograms', 'CommonDesktopDirectory')):
                raise RuntimeError('Unexpected all-users shortcut')
        return state

    def smoke(label):
        smoke_parent = out / (label + '-evidence')
        smoke_parent.mkdir()
        smoke_env = dict(env, RUNNER_TEMP=str(smoke_parent))
        run(label, ['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
                    str(ROOT / 'packaging/smoke_test_packaged.ps1'), '-ExecutablePath',
                    str(target / 'MastixaManager.exe'), '-TimeoutSeconds', '90'], 125, smoke_env)
        results = list(smoke_parent.glob('MastixaManager-smoke-*/result.json'))
        if len(results) != 1:
            raise RuntimeError('Missing bounded installed smoke evidence')
        detail = json.loads(results[0].read_text(encoding='utf-8-sig'))
        if detail['status'] != 'PASS' or detail['exitCode'] != 0:
            raise RuntimeError('Installed smoke did not pass')
        report.setdefault('smoke_results', []).append(detail)
        save()

    def seed():
        # Only called after disposable runner and namespace absence checks.
        for key in (PREFERENCES, unrelated_key):
            if snapshot(winreg, key) is not None:
                raise RuntimeError('Refuse to overwrite an existing registry namespace')
        if data.exists() or unrelated_data.exists():
            raise RuntimeError('Refuse to overwrite an existing data directory')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, PREFERENCES, 0, winreg.KEY_WRITE) as key:
            for name, value, kind in [('language', 'en', winreg.REG_SZ), ('windowWidth', 1279, winreg.REG_DWORD),
                ('recentItems', ['synthetic-one', 'synthetic-two'], winreg.REG_MULTI_SZ),
                ('syntheticBinary', b'\x00\x01\xfe', winreg.REG_BINARY)]:
                winreg.SetValueEx(key, name, 0, kind, value)
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, PREFERENCES + r'\Nested\Child', 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, 'sentinel', 0, winreg.REG_SZ, 'synthetic-nested-preservation')
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, unrelated_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, 'sentinel', 0, winreg.REG_SZ, 'must-not-change')
        for root, relative, content in [(data, 'data/synthetic-owner-marker.txt', 'synthetic data'),
            (data, 'backups/nested/synthetic-backup-marker.txt', 'synthetic backup'),
            (unrelated_data, 'nested/sentinel.txt', 'unrelated data')]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        return observe('synthetic-state-seeded')

    def retained(before, after):
        for key in ('preferences', 'user_data', 'unrelated_registry', 'unrelated_data'):
            if before[key] != after[key]:
                raise RuntimeError('Unexpected state change: ' + key)

    def uninstall(label, purge=False):
        command = [str(target / 'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                   '/LOG=' + str(out / (label + '.log'))]
        if purge:
            if args.scenario != 'purge':
                raise RuntimeError('Purge belongs only to its separate disposable job')
            command.append('/PURGEDATA')
        state = run(label, command, 180)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and (target.exists() or snapshot(winreg, UNINSTALL) is not None):
            time.sleep(0.2)
        state = observe(label + '-settled')
        if state['target_exists'] or state['uninstall_registration'] is not None:
            raise RuntimeError('Uninstall left install directory or registration')
        if state['shortcuts'] != initial['shortcuts']:
            raise RuntimeError('Uninstall left installer-created shortcuts')
        return state

    save()
    try:
        initial = observe('initial')
        if initial['preferences'] is not None or initial['uninstall_registration'] is not None or data.exists():
            raise RuntimeError('Hosted runner already contains Mastixa state; refuse mutation')
        if any(initial['shortcuts'].values()):
            raise RuntimeError('Hosted runner already contains a Mastixa shortcut; refuse overwrite')
        if args.scenario in ('noicons', 'normal'):
            installed = install('clean-install', noicons=args.scenario == 'noicons')
            retained(initial, installed)
            smoke('installed-smoke')
            retained(initial, observe('final'))
        elif args.scenario == 'preservation':
            baseline = seed()
            retained(baseline, install('seeded-install', desktop=True))
            library = target / '_internal/PySide6/Qt6Core.dll'
            # Only an installed candidate file on the disposable runner is damaged.
            library.write_bytes(b'HOSTED SYNTHETIC REPAIR DAMAGE')
            repaired = install('repair', desktop=True)
            retained(baseline, repaired)
            if 'Mode=repair' not in (out / 'repair.log').read_text(encoding='utf-8-sig', errors='replace'):
                raise RuntimeError('Repair did not record the expected maintenance path')
            smoke('repaired-smoke')
            retained(baseline, uninstall('ordinary-uninstall'))
            retained(baseline, install('reinstall', desktop=True))
            smoke('reinstalled-smoke')
            retained(baseline, uninstall('ordinary-uninstall-after-reinstall'))
        else:
            install('purge-clean-install', desktop=True)
            baseline = seed()
            after = uninstall('explicit-purge', purge=True)
            if after['preferences'] is not None or data.exists():
                raise RuntimeError('Explicit purge left preference subkeys or covered user data')
            for key in ('unrelated_registry', 'unrelated_data'):
                if after[key] != baseline[key]:
                    raise RuntimeError('Explicit purge changed unrelated state: ' + key)
        report['status'] = 'PASS'
        save()
    except Exception as error:
        report.update(status='FAIL', error=repr(error))
        try:
            observe('failure-read-only')
        except Exception as observation_error:
            report['observation_error'] = repr(observation_error)
        save()
        raise
    print(json.dumps({'status': report['status'], 'scenario': args.scenario, 'evidence': str(out)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
