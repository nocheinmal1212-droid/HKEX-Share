"""Regression and mutation checks for the experimental dispatcher, never model inference."""
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools/experiments'
with patch.object(sys, 'path', [str(TOOLS), *sys.path]):
    spec = importlib.util.spec_from_file_location('direct_fault_runner', TOOLS / 'run_direct_contributor_boundaries.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
boundary = runner.boundary


class DirectContributorTests(unittest.TestCase):
    def execute(self):
        with tempfile.TemporaryDirectory() as tmp:
            return runner.run(Path(tmp) / 'attempts')

    def test_all_authored_scenarios_and_persisted_controls(self):
        result = self.execute()
        self.assertEqual(result['passed'], result['executed_subcases_and_controls'],
                         [r['id'] for r in result['rows'] if not r['passed']])
        self.assertEqual(result['scenarios'], 20)

    def test_suite_rejects_precheck_bypass(self):
        with patch.object(boundary, 'precheck', return_value=boundary.outcome('eligible', 'bypassed')):
            result = self.execute()
        failed = {r['id'] for r in result['rows'] if not r['passed']}
        self.assertTrue({'D01', 'D02', 'D03', 'D04', 'D06', 'D07', 'D08', 'D19'} <= failed)

    def test_suite_rejects_scope_validation_bypass(self):
        original = boundary.postcheck
        def weak(job, output):
            value = original(job, output)
            if value['reason'] == 'id_outside_requested_scope':
                return boundary.outcome('structure_accepted', 'semantic_correctness_unverified')
            return value
        with patch.object(boundary, 'postcheck', side_effect=weak):
            result = self.execute()
        self.assertFalse(next(r for r in result['rows'] if r['id'] == 'D12')['passed'])

    def test_suite_rejects_incomplete_output_acceptance(self):
        original = boundary.interpret_response
        def weak(job, response):
            value = original(job, response)
            if value['reason'] == 'truncated':
                return boundary.outcome('structure_accepted', 'semantic_correctness_unverified')
            return value
        with patch.object(boundary, 'interpret_response', side_effect=weak):
            result = self.execute()
        self.assertEqual(sum(not r['passed'] for r in result['rows'] if r['id'] == 'D11'), 2)

    def test_suite_rejects_false_persistence_success(self):
        original = boundary.Store.write
        def omit(self, name, data):
            if name != 'result.json':
                original(self, name, data)
        with patch.object(boundary.Store, 'write', omit):
            result = self.execute()
        self.assertFalse(next(r for r in result['rows'] if r['id'] == 'C01_selected')['passed'])

    def test_isolated_replay_reads_own_request_but_denies_unselected_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            runner.run(root / 'attempts')
            source = root / 'attempts/C01_selected'
            output = root / 'replay'
            output.mkdir()
            job = json.loads((source / 'request.json').read_bytes())
            payload = {'source_path': str(source / 'source.json'), 'job_path': str(source / 'request.json'),
                       'response_path': str(source / 'response.json'), 'output': str(output),
                       'identity': job['identity'], 'forbidden': [
                           str(ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json'),
                           str(root / 'attempts/D14/source.json')]}
            proc = subprocess.run([sys.executable, '-I', '-B', str(TOOLS / 'direct_contributor_offline_worker.py')],
                                  input=json.dumps(payload), capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            access = json.loads((output / 'access.json').read_bytes())
            self.assertEqual(len(access['protected_reads']), 4)
            self.assertTrue(all(r['denied'] for r in access['protected_reads']))
            self.assertEqual(access['stub_transport_calls'], 1)
            self.assertEqual(access['network_calls'], 0)
            self.assertEqual(access['result_state'], 'structure_accepted')


if __name__ == '__main__':
    unittest.main()
