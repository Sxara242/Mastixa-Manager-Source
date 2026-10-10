"""Pure helpers/AST contracts only; never import winreg or launch native code."""
import ast
import importlib.util
from pathlib import Path
import unittest

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


if __name__ == '__main__':
    unittest.main()
