"""Independent checks for paired reporting and raw/guard outcome separation."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools/experiments'
with patch.object(sys,'path',[str(TOOLS),*sys.path]):
    spec=importlib.util.spec_from_file_location('interface_evaluation',TOOLS/'evaluate_interface_run.py')
    ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)


class InterfaceEvaluationTests(unittest.TestCase):
    def test_pairing_keeps_failures_but_excludes_them_from_efficiency(self):
        fixture=json.loads((ROOT/'spec/diagnostics/interface-boundaries-v1.json').read_text())
        c=fixture['contract_fixtures'][0]
        schema=fixture['output_contract']['schema_template']
        schema['properties']['evidence_id']['enum']=['a','b',None]
        encode=lambda x:json.dumps(x).encode()
        sha=lambda x:hashlib.sha256(x).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);(run/'responses').mkdir()
            requests=[];answers=[]
            for index,(rep,prompt,elapsed,prompt_tokens,timeout) in enumerate([
                (1,'B0_existing_explicit',1.0,100,False),
                (1,'B1_concise_equivalent',3.0,80,False),
                (2,'B0_existing_explicit',2.0,100,False),
                (2,'B1_concise_equivalent',30.0,80,True)]):
                id=f'test-{index}'
                body=encode({'messages':[{'role':'system','content':'test'}, {'role':'user','content':json.dumps(c['model_user_payload'])}]})
                requests.append({'id':id,'sha256':sha(body),'body_base64':base64.b64encode(body).decode()})
                answers.append({'id':id,'route':'test','role':'baseline','case':'one','repetition':rep,'prompt':prompt,
                    'model':'test-model','provider_name':'test-provider','typed_request':c['request'],
                    'host_precheck':ev.precheck(c['request']),'schema':schema,'expected':c['expected_model_output']})
                record={'id':id,'request_sha256':sha(body),'elapsed_seconds':elapsed,'transport_status':'timeout' if timeout else 'received'}
                if not timeout:
                    raw=encode({'model':'test-model','provider':'test-provider','choices':[{'finish_reason':'stop',
                        'message':{'content':json.dumps(c['expected_model_output'])}}],
                        'usage':{'prompt_tokens':prompt_tokens,'completion_tokens':20,'total_tokens':prompt_tokens+20,'cost':0}})
                    record.update(http_status=200,response_base64=base64.b64encode(raw).decode(),response_sha256=sha(raw))
                (run/'responses'/(id+'.json')).write_bytes(encode(record))
            raw=encode({'requests':requests});(run/'requests.json').write_bytes(raw)
            key=encode({'cases':answers});(run/'evaluator-key.json').write_bytes(key)
            (run/'execution-plan.json').write_bytes(encode({'manifest_sha256':sha(raw),'evaluator_key_sha256':sha(key),'routes':{'test':{}}}))
            (run/'responses/completed.json').write_bytes(encode({'calls':4}))
            result=ev.evaluate(run)
            effect=result['paired_comparisons'][0]
            self.assertEqual(effect['matched_pairs'],2)
            self.assertEqual(effect['both_pass_pairs'],1)
            self.assertEqual(effect['median_prompt_tokens_difference_concise_minus_baseline'],-20)
            self.assertEqual(effect['median_latency_difference_concise_minus_baseline'],2.0)
            self.assertEqual(result['counts']['test/B1_concise_equivalent'],{'passed':1,'timeout':1})
            self.assertEqual(result['rows'][-1]['boundary']['state'],'not_evaluated')


if __name__=='__main__':unittest.main()
