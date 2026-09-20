import copy
import unittest
from helpers import evidence, native
from hkex_audit.evidence import validate_evidence
from hkex_audit.artifacts import loads
from hkex_audit.contracts import preload, SCHEMAS, validate
from hkex_audit.evidence_context import build_context

class ContractTests(unittest.TestCase):
    def test_schemas_and_nonempty_fixture(self):
        preload();self.assertEqual(len(SCHEMAS),4);self.assertGreater(len(evidence()['nodes']),0)

    def test_fault_injection(self):
        base=evidence()
        mutations=[lambda e:e.update(schema_version='2.0.0'),lambda e:e['nodes'].append(e['nodes'][0]),
                   lambda e:e['nodes'][0].update(id='broken'),lambda e:e['sources'][0].update(text='changed'),
                   lambda e:next(n for n in e['nodes'] if n['kind']=='cell')['fragments'][0].update(start=99999),
                   lambda e:next(n for n in e['nodes'] if n['kind']=='cell').update(parent_id='foreign'),
                   lambda e:next(n for n in e['nodes'] if n['kind']=='cell').update(row_span=100),
                   lambda e:[n for n in e['nodes'] if n['kind']=='cell'][1].update(column=0),
                   lambda e:next(n for n in e['nodes'] if n['kind']=='cell')['source_span'].update(start=1),
                   lambda e:e.update(answers={}),lambda e:e['nodes'][0].update(parent_id=e['nodes'][0]['id'])]
        for mutate in mutations:
            e=copy.deepcopy(base);mutate(e)
            with self.assertRaises(ValueError):validate_evidence(e)

    def test_native_span_verification_and_payload(self):
        e=evidence();validate_evidence(e,native())
        ids=[n['id'] for n in e['nodes'] if n['kind']=='cell']
        payload=build_context(e,ids)
        self.assertEqual(payload['items'][0]['text'],'項目&甲')
        self.assertNotIn('document',payload);self.assertNotIn('sources',payload)
        with self.assertRaises(ValueError):build_context(e,['unknown'])
        with self.assertRaises(ValueError):build_context(e,ids*2)
        n=native();n['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html']='different'
        with self.assertRaises(ValueError):validate_evidence(e,n)

    def test_strict_json(self):
        for raw in ['{"a":1,"a":2}','{"a":NaN}','{"a":1e999}']:
            with self.assertRaises(ValueError):loads(raw)
