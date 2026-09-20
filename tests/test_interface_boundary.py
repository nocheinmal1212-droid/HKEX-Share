"""Reviewed boundary fixtures, independent outcomes and mutation checks; no network."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('boundary', ROOT/'tools/experiments/interface_boundary.py')
boundary=importlib.util.module_from_spec(spec);spec.loader.exec_module(boundary)


class InterfaceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=json.loads((ROOT/'spec/diagnostics/interface-boundaries-v1.json').read_text())

    def test_eleven_reviewed_fixtures(self):
        for f in self.fixtures['deterministic_fixtures']:
            with self.subTest(fixture=f['id']):
                before=deepcopy(f)
                spy=Mock(return_value=deepcopy(f['stub_model_output']))
                result=boundary.dispatch(f['request'],spy)
                self.assertEqual(result['model_calls'],f['expected_model_calls'])
                self.assertEqual(spy.call_count,f['expected_model_calls'])
                self.assertEqual(result['stage'],f['expected_stage'])
                self.assertEqual(result['state'],f['expected_state'])
                self.assertEqual(f,before)
                self.assertEqual(result['model_output'],f['stub_model_output'])
                if f['id']=='D09_semantic_error_survives_guards':
                    self.assertNotEqual(result['model_output'],f['reviewed_semantic_expected'])
                    self.assertEqual(result['state'],'accepted')

    def test_literal_ids_and_missing_target(self):
        request={'operation':'classify_target','target_id':'row-a','evidence':[{'id':'Row-A','text':'總計'}]}
        self.assertEqual(boundary.precheck(request)['reason'],'target_missing')
        request['target_id']='Row-A'
        self.assertEqual(boundary.precheck(request)['state'],'eligible')

    def test_malformed_inputs_never_call(self):
        good={'operation':'select_unique_total','target_id':None,'evidence':[{'id':'a','text':'總計'}]}
        for request in [None,[],{},dict(good,operation='execute'),dict(good,target_id='a'),
                        dict(good,evidence=None),dict(good,evidence=[{'id':'a','text':4}]),
                        dict(good,evidence=[{'id':'','text':'總計'}])]:
            spy=Mock();r=boundary.dispatch(request,spy)
            self.assertEqual(r['state'],'rejected');spy.assert_not_called()

    def test_contract_payloads_unchanged(self):
        for f in self.fixtures['contract_fixtures']:
            self.assertEqual(boundary.precheck(f['request'])['state'],'eligible')
            self.assertEqual(boundary.user_payload(f['request']),f['model_user_payload'])
            self.assertEqual(boundary.postcheck(f['request'],f['expected_model_output'])['state'],'accepted')

    def test_guard_does_not_read_label_meaning(self):
        request={'operation':'classify_target','target_id':'a','evidence':[{'id':'a','text':'收入'}]}
        wrong={'action':'label','evidence_id':'a','role':'total_label'}
        self.assertEqual(boundary.postcheck(request,wrong)['state'],'accepted')
        request['evidence'][0]['text']='completely different text'
        self.assertEqual(boundary.postcheck(request,wrong)['state'],'accepted')

    def test_transport_cannot_mutate_scope(self):
        request={'operation':'classify_target','target_id':'a','evidence':[{'id':'a','text':'總計'},{'id':'b','text':'收入'}]}
        before=deepcopy(request)
        def transport(payload):
            payload['evidence'][0]['id']='b'
            return {'action':'label','evidence_id':'b','role':'total_label'}
        self.assertEqual(boundary.dispatch(request,transport)['reason'],'selected_id_differs_from_requested_target')
        self.assertEqual(request,before)

    def test_output_never_repaired(self):
        request={'operation':'select_unique_total','target_id':None,'evidence':[{'id':'a','text':'總計'}]}
        for output in [None,[],{'action':'select','evidence_id':'a','role':'label'},
                       {'action':'label','evidence_id':None,'role':None},
                       {'action':'abstain','evidence_id':'a','role':'total_label'},
                       {'action':'label','evidence_id':'a','role':'total_label','amount':'10'}]:
            before=deepcopy(output)
            self.assertEqual(boundary.postcheck(request,output)['state'],'rejected')
            self.assertEqual(output,before)


if __name__=='__main__':unittest.main()
