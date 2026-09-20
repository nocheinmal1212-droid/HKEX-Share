"""Offline behavioral checks for isolated request construction and evaluation."""
import base64
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools/experiments' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prepare = module('prepare_fixtures')
evaluator = module('evaluate_fixtures')
worker = module('fixture_worker')


class ExperimentalFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'spec/diagnostics/hypothesis-fixtures-v1.json').read_text())

    def answer(self, expected=None):
        return {'model': 'test-model', 'provider_name': 'Test provider',
                'schema': self.fixture['schema_template'],
                'expected': expected or {'action': 'label', 'evidence_id': 'field-one', 'role': 'total_label'}}

    def record(self, output, finish='stop', **changes):
        response = {'model': 'test-model', 'provider': 'Test provider', 'choices': [
            {'finish_reason': finish, 'message': {'content': json.dumps(output)}}]}
        response.update(changes)
        return {'transport_status': 'received', 'http_status': 200,
                'response_base64': base64.b64encode(json.dumps(response).encode()).decode()}

    def test_prompt_schema_and_budget_axes(self):
        c = self.fixture['cases'][0]
        a, _ = prepare.build_body(self.fixture, c, 'test-model', 'test-provider', 'P11')
        b, _ = prepare.build_body(self.fixture, c, 'test-model', 'test-provider', 'P11', False)
        self.assertEqual(b, {k:v for k,v in a.items() if k != 'response_format'})
        larger, _ = prepare.build_body(self.fixture, c, 'test-model', 'test-provider', 'P11', False, 2048)
        self.assertEqual(larger, {**b, 'max_tokens': 2048})
        self.assertEqual(json.loads(a['messages'][1]['content']), c['input'])
        self.assertNotIn('expected', json.loads(a['messages'][1]['content']))

    def test_ids_derive_from_evidence_and_missing_target_not_allowed(self):
        cases = {c['id']: c for c in self.fixture['cases']}
        _, schema = prepare.build_body(self.fixture, cases['renamed_ids'], 'm', 'p', 'P11')
        self.assertEqual(schema['properties']['evidence_id']['enum'], ['source-17', 'source-42', None])
        _, schema = prepare.build_body(self.fixture, cases['missing_target'], 'm', 'p', 'P11')
        self.assertNotIn('field-missing', schema['properties']['evidence_id']['enum'])

    def test_wrong_vocabulary_is_not_repaired(self):
        output = {'action': 'select', 'evidence_id': 'field-one', 'role': 'label'}
        result = evaluator.classify(self.record(output), self.answer())
        self.assertEqual(result['status'], 'invalid_schema')
        self.assertTrue(result['selected_id_matches_expected'])
        self.assertEqual(result['observed_output'], output)

    def test_abstention_and_wrong_selection_distinct(self):
        absent = {'action': 'abstain', 'evidence_id': None, 'role': None}
        self.assertEqual(evaluator.classify(self.record(absent), self.answer())['status'], 'unexpected_abstention')
        correct = self.answer()['expected']
        self.assertEqual(evaluator.classify(self.record(correct), self.answer(absent))['status'], 'failure_to_abstain')
        wrong = {**correct, 'evidence_id': 'field-two'}
        self.assertEqual(evaluator.classify(self.record(wrong), self.answer())['status'], 'wrong_selection')
        self.assertEqual(evaluator.classify(self.record(correct), self.answer())['status'], 'passed')

    def test_truncation_and_transport_do_not_become_semantic_failures(self):
        result = evaluator.classify(self.record(None, finish='length'), self.answer())
        self.assertEqual(result['status'], 'truncated')
        self.assertEqual(result['semantic_decision'], 'unavailable')
        self.assertEqual(evaluator.classify({'transport_status':'timeout'}, self.answer())['status'], 'timeout')

    def test_markdown_wrapped_oracle_answer_remains_format_failure(self):
        record = self.record(self.answer()['expected'])
        response = json.loads(base64.b64decode(record['response_base64']))
        response['choices'][0]['message']['content'] = '```json\n' + json.dumps(self.answer()['expected']) + '\n```'
        record['response_base64'] = base64.b64encode(json.dumps(response).encode()).decode()
        result = evaluator.classify(record, self.answer())
        self.assertEqual(result['status'], 'malformed_json')
        self.assertFalse(result['contract_valid'])
        self.assertIsNone(result['observed_output'])

    def test_identity_refusal_and_duplicate_json(self):
        correct = self.answer()['expected']
        self.assertEqual(evaluator.classify(self.record(correct, provider='Other provider'), self.answer())['status'], 'identity_mismatch')
        r = self.record(correct)
        raw = json.loads(base64.b64decode(r['response_base64']))
        raw['choices'][0]['message']['refusal'] = 'refused'
        r['response_base64'] = base64.b64encode(json.dumps(raw).encode()).decode()
        self.assertEqual(evaluator.classify(r, self.answer())['status'], 'refusal')
        with self.assertRaises(ValueError):
            evaluator.parse('{"action":"label","action":"abstain"}')

    def test_manifest_cannot_include_expected_answer_or_mutated_bytes(self):
        body, _ = prepare.build_body(self.fixture, self.fixture['cases'][0], 'm', 'p', 'P11')
        raw = prepare.encode(body)
        record = {'id':'one','body_base64':base64.b64encode(raw).decode(),'sha256':prepare.sha(raw)}
        manifest = {'version':'approved-fixtures-2026-09-15-v1','bounds':{'max_calls':1},'requests':[record]}
        worker.check_manifest(manifest)
        altered = deepcopy(manifest)
        altered['requests'][0]['expected'] = self.answer()['expected']
        with self.assertRaises(AssertionError):
            worker.check_manifest(altered)
        altered = deepcopy(manifest)
        altered['requests'][0]['sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            worker.check_manifest(altered)


if __name__ == '__main__':
    unittest.main()
