"""Offline checks for the bounded comparison extension; no real model calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/experiments'))
from model_selection_worker_v2 import Transport,wire_request
from direct_contributor_attempt_v2 import Store,dispatch,replay,encode,sha,freeze
from direct_contributor_live_v2 import LateResultFailure
ROOT=Path(__file__).resolve().parents[1]
class Reply:
 code=200
 def __init__(self,body):self.body=body
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return self.body[:n]
class Opener:
 def __init__(self,body):self.body=body;self.calls=0
 def open(self,req,timeout):self.calls+=1;return Reply(self.body)
class ComparisonTests(unittest.TestCase):
 def setUp(self):
  source={'container_id':'table','items':[{'id':'total','kind':'row_label','container_id':'table','text':'Total'},{'id':'part','kind':'row_label','container_id':'table','text':'Component'},{'id':'note','kind':'note','container_id':'table','text':'The component is the complete total breakdown.'}],'limitations':[]}
  identity={'evidence_sha256':sha(encode(source))}
  job=freeze(source,{'operation':'select_direct_addends','container_id':'table','target_id':'total','candidate_ids':['part']},identity)
  settings={'model':'test/model-a','max_tokens':4096,'stream':False,'provider':{'only':['test-route'],'allow_fallbacks':False,'require_parameters':True},'temperature':0}
  self.prompt='Test contract.'
  wire=wire_request(job,job['payload'],self.prompt,settings)
  self.e={'source':source,'identity':identity,'job':job,'settings':settings,'expected_provider':'Test','configuration':{'wire_request':wire,'wire_request_sha256':sha(encode(wire))}}
  out={'action':'select','target_id':'total','contributor_ids':['part'],'support_ids':['note'],'reason':'supported_direct_breakdown'}
  self.body=encode({'model':self.e['settings']['model'],'provider':self.e['expected_provider'],'choices':[{'finish_reason':'stop','message':{'content':json.dumps(out)}}]})
 def test_every_configuration_wire_and_model_binding(self):
  entries=[]
  for name in ['test/model-a','test/model-b']:
   e=deepcopy(self.e);e['settings']['model']=name
   body=wire_request(e['job'],e['job']['payload'],self.prompt,e['settings']);e['configuration']={'wire_request':body,'wire_request_sha256':sha(encode(body))};entries.append(e)
  for e in entries:
   self.assertEqual(wire_request(e['job'],e['job']['payload'],self.prompt,e['settings']),e['configuration']['wire_request'])
   mutated=deepcopy(e);mutated['settings']['model']='other/model';op=Opener(self.body)
   t=Transport(mutated,self.prompt,'test-secret',op)
   with self.assertRaises(ValueError):t(e['job']['payload'])
   self.assertEqual(op.calls,0)
 def test_payload_mutation_denied_before_network(self):
  p=deepcopy(self.e['job']['payload']);p['evidence'][0]['text']='Changed';op=Opener(self.body)
  with self.assertRaises(ValueError):Transport(self.e,self.prompt,'test-secret',op)(p)
  self.assertEqual(op.calls,0)
 def test_commit_and_late_result_failure(self):
  for cls,state in [(Store,'structure_accepted'),(LateResultFailure,'incomplete_attempt')]:
   with tempfile.TemporaryDirectory() as d:
    op=Opener(self.body);t=Transport(self.e,self.prompt,'test-secret',op)
    r=dispatch(self.e['source'],self.e['identity'],self.e['job'],t,cls(d),self.e['configuration'])
    self.assertEqual(op.calls,1);self.assertEqual(replay(d)['state'],state)
    self.assertEqual(replay(d)['model_calls'],0)
 def test_secret_redaction(self):
  op=Opener(b'test-secret');r=Transport(self.e,self.prompt,'test-secret',op)(self.e['job']['payload'])
  self.assertEqual(r['body'],b'[REDACTED]');self.assertTrue(r['credential_redacted'])
 def test_timeout_is_one_call_without_retry(self):
  op=Opener(self.body)
  with patch.object(op,'open',side_effect=TimeoutError) as mocked:
   t=Transport(self.e,self.prompt,'test-secret',op);result=t(self.e['job']['payload'])
   self.assertEqual(result['transport_status'],'timeout');self.assertEqual(mocked.call_count,1);self.assertEqual(t.network_attempts,1)
if __name__=='__main__':unittest.main()
