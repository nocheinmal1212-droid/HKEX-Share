"""Evaluator interpretation regression, outside runtime imports."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('semantic_evaluation',Path(__file__).resolve().parents[1]/'eval/semantic-integration/validate.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ReviewDecisionTests(unittest.TestCase):
    def test_frozen_abstention_reason_is_distinct_from_status(self):
        expected={'expected_status':'abstained','expected_abstention_reason':'missing_evidence'}
        self.assertEqual(module.review_decision('missing_evidence',expected,{'state':'missing_evidence'}),(True,None))
        self.assertEqual(module.review_decision('missing_evidence',expected,{'state':'timeout'}),(False,None))

    def test_correct_selection_does_not_erase_missing_support(self):
        expected={'expected_status':'selected','expected_contributor_header_ids':['a','b'],'required_support_ids':['a','b','target','unit']}
        answer={'state':'selected','contributor_ids':['b','a'],'support_refs':['target','a','b']}
        self.assertEqual(module.review_decision('eligible',expected,{'answer':answer}),(True,False))
        self.assertEqual(module.review_decision('eligible',expected,{'state':'truncation'}),(None,None))
