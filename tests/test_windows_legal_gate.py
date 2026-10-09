"""Legal gate failures cannot be bypassed by audit scores or readiness flags."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
check = runpy.run_path(str(ROOT / 'packaging/validate_windows_release.py'))['legal_readiness_errors']


class WindowsLegalGateTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'packaging/windows-rc.json').read_text(encoding='utf-8'))

    def test_current_remediated_b3_passes_with_prebuild_materials_ready(self):
        self.assertTrue(self.config['native_notices_complete'])
        self.assertTrue(self.config['corresponding_source_ready'])
        self.assertEqual('PASS', self.config['distribution_legal_gates']['B3']['legal_status'])
        self.assertEqual([], check(self.config))

    def test_audit_gaps_do_not_block_hypothetical_legally_complete_config(self):
        config = copy.deepcopy(self.config)
        config['distribution_legal_gates']['B3']['legal_status'] = 'PASS'
        self.assertEqual('INCOMPLETE', config['distribution_legal_gates']['B1']['audit_status'])
        self.assertEqual('INCOMPLETE', config['distribution_legal_gates']['B4']['audit_status'])
        self.assertEqual([], check(config))

    def test_every_required_legal_gate_fails_closed(self):
        for name in ('B1', 'B2', 'B3', 'B4', 'B5'):
            for status in ('BLOCKED', 'UNKNOWN', 'INCOMPLETE', None):
                with self.subTest(name=name, status=status):
                    config = copy.deepcopy(self.config)
                    for gate in config['distribution_legal_gates'].values():
                        gate['legal_status'] = 'PASS'
                    config['distribution_legal_gates'][name]['legal_status'] = status
                    self.assertEqual(1, len(check(config)))
                    self.assertTrue(check(config)[0].startswith(name + '-LEGAL:'))

    def test_missing_gate_schema_cannot_be_bypassed_with_flags(self):
        config = copy.deepcopy(self.config)
        del config['distribution_legal_gates']
        self.assertEqual(5, len(check(config)))

    def test_missing_source_or_notice_readiness_still_blocks(self):
        for key in ('native_notices_complete', 'corresponding_source_ready'):
            with self.subTest(key=key):
                config = copy.deepcopy(self.config)
                for gate in config['distribution_legal_gates'].values():
                    gate['legal_status'] = 'PASS'
                config[key] = False
                self.assertTrue(check(config))


if __name__ == '__main__':
    unittest.main()
