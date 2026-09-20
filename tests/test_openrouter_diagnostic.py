"""Offline controls for the prompt/schema experiment."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
with patch.object(sys, 'path', [str(TOOLS), *sys.path]):
    spec = importlib.util.spec_from_file_location('diagnostic', TOOLS / 'diagnose_openrouter.py')
    diagnostic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diagnostic)


class DiagnosticTests(unittest.TestCase):
    def test_factorial_changes_are_isolated(self):
        for model in diagnostic.MODELS:
            for case in diagnostic.CASES:
                original = diagnostic.request(model, 'original', True, case)
                free = diagnostic.request(model, 'original', False, case)
                self.assertEqual(free, {k: v for k, v in original.items() if k != 'response_format'})
                clarified = diagnostic.request(model, 'clarified', True, case)
                self.assertEqual(clarified['messages'][1], original['messages'][1])
                self.assertEqual(clarified['messages'][0]['content'],
                                 original['messages'][0]['content'] + diagnostic.CLARIFICATION)
                clarified['messages'] = original['messages']
                self.assertEqual(clarified, original)
            case = diagnostic.CASES[0]
            self.assertEqual(diagnostic.request(model, 'original', True, case),
                             diagnostic.probe.request_body(case[1], model))

    def test_negative_control_removes_total_without_giving_answer(self):
        case = diagnostic.CASES[2]
        body = diagnostic.request(diagnostic.MODELS[0], 'clarified', True, case)
        payload = diagnostic.loads(body['messages'][1]['content'])
        self.assertEqual(payload['instruction'], 'Select the total label from the supplied evidence.')
        self.assertEqual(payload['evidence'], [
            {'id': 'field-one', 'text': '成本'}, {'id': 'field-two', 'text': '收入'}])
        self.assertEqual(case[2], {'action': 'abstain', 'evidence_id': None, 'role': None})
        self.assertNotIn('總計', body['messages'][0]['content'])


if __name__ == '__main__':
    unittest.main()
