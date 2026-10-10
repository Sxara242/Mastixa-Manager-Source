"""Pure helpers/AST contracts only; never import winreg or launch native code."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'tools/hosted_installer_qualification.py'
spec = importlib.util.spec_from_file_location('hosted_safety_only', HARNESS)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HostedQualificationSafetyTests(unittest.TestCase):
    def environment(self):
        return {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
                'RUNNER_OS': 'Windows', 'GITHUB_EVENT_NAME': 'workflow_dispatch',
                'GITHUB_REPOSITORY': 'Sxara242/Mastixa-Manager-Source',
                'MASTIXA_HOSTED_NATIVE_EXECUTE': '1', 'RUNNER_TEMP': 'synthetic',
                'GITHUB_RUN_ID': '123', 'GITHUB_SHA': 'a' * 40}

    def test_local_empty_environment_refused(self):
        with self.assertRaises(RuntimeError):
            module.require_hosted({}, 'nt')

    def test_each_hosted_guard_is_required(self):
        for key in self.environment():
            with self.subTest(key=key):
                env = self.environment()
                del env[key]
                with self.assertRaises(RuntimeError):
                    module.require_hosted(env, 'nt')

    def test_self_hosted_runner_refused(self):
        env = self.environment()
        env['RUNNER_ENVIRONMENT'] = 'self-hosted'
        with self.assertRaises(RuntimeError):
            module.require_hosted(env, 'nt')

    def test_non_windows_refused(self):
        with self.assertRaises(RuntimeError):
            module.require_hosted(self.environment(), 'posix')

    def test_manual_disposable_environment_accepted(self):
        module.require_hosted(self.environment(), 'nt')

    def test_both_defective_installers_refused_even_as_expected(self):
        for sha in module.BLOCKED:
            with self.assertRaises(RuntimeError):
                module.verify_identity(sha, sha)

    def test_unrelated_candidate_refused(self):
        with self.assertRaises(RuntimeError):
            module.verify_identity('0' * 64, module.INSTALLER_SHA256)

    def test_current_candidate_accepted(self):
        module.verify_identity(module.INSTALLER_SHA256, module.INSTALLER_SHA256)
        module.verify_identity(module.EXE_SHA256, module.EXE_SHA256)

    def test_guard_precedes_native_import_or_writes(self):
        main = next(node for node in ast.parse(HARNESS.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'main')
        guard = next(index for index, node in enumerate(main.body)
                     if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                     and isinstance(node.value.func, ast.Name) and node.value.func.id == 'require_hosted')
        native = next(index for index, node in enumerate(main.body)
                      if isinstance(node, ast.Import) and any(alias.name == 'winreg' for alias in node.names))
        self.assertLess(guard, native)
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                             any(alias.name in ('winreg', 'ctypes') for alias in node.names)
                             for node in ast.parse(HARNESS.read_text()).body))

    def test_no_rename_or_automatic_restore_path(self):
        source = HARNESS.read_text()
        for forbidden in ('RegRenameKey', 'NtRenameKey', 'ctypes', 'reg rename', '.rename(', 'shutil.move'):
            self.assertNotIn(forbidden, source)
        self.assertNotIn('winreg.DeleteKey', source)

    def test_purge_requires_separate_purge_scenario(self):
        source = HARNESS.read_text()
        self.assertIn("if args.scenario != 'purge':", source)
        self.assertIn("command.append('/PURGEDATA')", source)
        self.assertIn("PREFERENCES + r'\\Nested\\Child'", source)
        self.assertIn("for key in ('unrelated_registry', 'unrelated_data'):", source)

    def test_shortcut_contract_and_default_icon(self):
        exe = Path('synthetic-install') / 'MastixaManager.exe'
        good = {'target': str(exe), 'working_directory': str(exe.parent),
                'arguments': '', 'icon_location': ',0'}
        module.shortcut_contract(good, exe)
        module.shortcut_contract(dict(good, icon_location=str(exe) + ',0'), exe)
        for field, bad in [('target', 'wrong.exe'), ('working_directory', 'wrong-directory'),
                           ('arguments', '--unwanted'), ('icon_location', 'wrong.exe,0')]:
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                module.shortcut_contract(dict(good, **{field: bad}), exe)

    def test_workflow_is_manual_fresh_and_failure_stops_chain(self):
        workflow = (ROOT / '.github/workflows/windows-release-gate.yml').read_text()
        self.assertIn('  workflow_dispatch:', workflow)
        self.assertNotIn('  push:', workflow)
        self.assertNotIn('  pull_request:', workflow)
        self.assertEqual(workflow.count('runs-on: windows-latest'), 4)
        self.assertIn('  noicons:\n    needs: ingress', workflow)
        self.assertIn('  normal:\n    needs: noicons', workflow)
        self.assertIn('  preservation:\n    needs: normal', workflow)
        self.assertIn('  purge:\n    needs: preservation', workflow)
        self.assertEqual(workflow.count('retention-days: 1'), 6)
        self.assertNotIn('continue-on-error:', workflow)


class ShortcutObservationTests(unittest.TestCase):
    def items(self):
        return [{'kind': kind, 'path': 'synthetic/' + kind, 'exists': False}
                for kind in ('Programs', 'CommonPrograms', 'DesktopDirectory', 'CommonDesktopDirectory')]

    def failure(self, child=None, error=None, environment=None):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            with patch.object(module.subprocess, 'run', return_value=child, side_effect=error):
                with self.assertRaisesRegex(RuntimeError, 'diagnostic=shortcut-observation-after-clean-install.json'):
                    module.read_shortcuts(out, 'after-clean-install', environment or {})
            return json.loads((out / 'shortcut-observation-after-clean-install.json').read_text())

    def test_complete_success_keeps_exact_observation_and_creates_no_failure_log(self):
        items = self.items()
        items[0].update(exists=True, target='synthetic.exe', arguments='--wrong', sha256='abc')
        child = subprocess.CompletedProcess([], 0, json.dumps(items), '')
        with tempfile.TemporaryDirectory() as directory, patch.object(module.subprocess, 'run', return_value=child) as run:
            self.assertEqual(module.read_shortcuts(Path(directory), 'initial', {}), items)
            self.assertEqual(list(Path(directory).iterdir()), [])
            self.assertFalse(run.call_args.kwargs['check'])
            self.assertEqual(run.call_args.kwargs['timeout'], 30)
            self.assertEqual(run.call_args.kwargs['encoding'], 'utf-8')

    def test_child_exit_stdout_stderr_and_phase_retained_with_redaction(self):
        private = 'C:' + '\\Users\\' + 'synthetic-owner\\folder with spaces'
        token = 'gh' + 'p_' + 'syntheticCredentialValue123456789'
        child = subprocess.CompletedProcess([], 7, json.dumps({'path': private, 'arguments': 'opaqueSensitiveArgument'}),
                                            json.dumps({'phase': 'file-hash', 'kind': 'Programs', 'folder_empty': False,
                                                        'exception_type': 'CommandNotFoundException', 'detail': token}))
        detail = self.failure(child=child, environment={'UPLOAD_TOKEN': token, 'USERPROFILE': private})
        self.assertEqual(detail['exit_code'], 7)
        self.assertEqual(detail['label'], 'after-clean-install')
        self.assertIn('file-hash', detail['stderr'])
        self.assertIn('CommandNotFoundException', detail['stderr'])
        for sensitive in (private, token, 'synthetic-owner', 'opaqueSensitiveArgument'):
            self.assertNotIn(sensitive, json.dumps(detail))

    def test_timeout_retains_partial_output_without_printing_command(self):
        error = subprocess.TimeoutExpired(['private-command'], 30, output=b'partial output', stderr=b'partial error')
        detail = self.failure(error=error)
        self.assertTrue(detail['timed_out'])
        self.assertIsNone(detail['exit_code'])
        self.assertEqual(detail['stdout'], 'partial output')
        self.assertEqual(detail['stderr'], 'partial error')
        self.assertNotIn('private-command', json.dumps(detail))

    def test_missing_shell_records_errno_without_leaking_exception_path(self):
        detail = self.failure(error=FileNotFoundError(2, 'private executable path'))
        self.assertEqual(detail['errno'], 2)
        self.assertEqual(detail['exception_type'], 'FileNotFoundError')
        self.assertNotIn('private executable path', json.dumps(detail))

    def test_invalid_json_is_failure_even_with_zero_exit(self):
        detail = self.failure(child=subprocess.CompletedProcess([], 0, 'not JSON', ''))
        self.assertEqual(detail['exit_code'], 0)
        self.assertEqual(detail['exception_type'], 'JSONDecodeError')

    def test_diagnostic_write_failure_does_not_print_private_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.CompletedProcess([], 1, '', 'synthetic failure')
            with patch.object(module.subprocess, 'run', return_value=child), \
                    patch.object(Path, 'open', side_effect=PermissionError(13, 'private diagnostic path')):
                with self.assertRaisesRegex(RuntimeError, 'sanitized diagnostics could not be persisted') as raised:
                    module.read_shortcuts(Path(directory), 'initial', {})
                self.assertNotIn('private diagnostic path', str(raised.exception))

    def test_missing_duplicate_empty_or_invalid_folder_observations_fail_closed(self):
        for items in (self.items()[:-1], self.items() + [self.items()[0]],
                      [self.items()[0]] * 4, [dict(item, path='') for item in self.items()],
                      [dict(item, exists='false') for item in self.items()],
                      [dict(item, path=True) for item in self.items()]):
            with self.subTest(items=items):
                detail = self.failure(child=subprocess.CompletedProcess([], 0, json.dumps(items), ''))
                self.assertEqual(detail['status'], 'FAIL')

    def test_successful_read_does_not_weaken_shortcut_contract(self):
        exe = Path('synthetic-install') / 'MastixaManager.exe'
        good = {'target': str(exe), 'working_directory': str(exe.parent), 'arguments': '', 'icon_location': ',0'}
        for field, bad in [('target', 'wrong.exe'), ('arguments', '--unexpected'),
                           ('working_directory', 'wrong'), ('icon_location', 'wrong.ico,0')]:
            items = self.items()
            items[0].update(good, exists=True)
            items[0][field] = bad
            with tempfile.TemporaryDirectory() as directory, patch.object(module.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 0, json.dumps(items), '')):
                observed = module.read_shortcuts(Path(directory), 'initial', {})
                with self.subTest(field=field), self.assertRaises(RuntimeError):
                    module.shortcut_contract(observed[0], exe)

    def test_generic_path_url_bearer_and_json_argument_redaction_is_bounded(self):
        private = 'C:' + '\\Users\\' + 'synthetic-person\\directory with spaces\\file.lnk'
        raw = json.dumps({'path': private, 'arguments': 'opaque-value'}) + '\n' + private
        raw += '\nhttps://example.invalid/upload?sig=private-signature\nBearer private-bearer\npassword=private-password'
        redacted = module.redact_observation(raw, {})
        for value in ('synthetic-person', 'opaque-value', 'private-signature', 'private-bearer', 'private-password'):
            self.assertNotIn(value, redacted)
        self.assertEqual(len(module.redact_observation('x' * 20000, {})), 16384)

    def test_production_observation_has_no_cmdlet_hash_or_link_save_dependency(self):
        self.assertNotIn('Get-FileHash', module.SHORTCUT_OBSERVATION_SCRIPT)
        self.assertNotIn('.Save(', module.SHORTCUT_OBSERVATION_SCRIPT)
        self.assertIn('SpecialFolderEmpty', module.SHORTCUT_OBSERVATION_SCRIPT)
        self.assertIn('$hasher.Dispose()', module.SHORTCUT_OBSERVATION_SCRIPT)
        self.assertIn('$stream.Dispose()', module.SHORTCUT_OBSERVATION_SCRIPT)


if __name__ == '__main__':
    unittest.main()
