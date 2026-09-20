import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from helpers import native, selection, ir_selection
from hkex_audit.artifacts import encode, read, write_new, fingerprint
from hkex_audit.cli import launch
from hkex_audit.semantic import project, verify_query, validate_answer
from hkex_audit.semantic_attempt import CONFIGS, FILES, Store, request, dispatch, replay
from hkex_audit.semantic_cli import isolated, paired


def response(answer, role='primary', **changes):
    body={'model':CONFIGS[role]['model'],'provider':CONFIGS[role]['served_provider'],'id':'fixture-response',
          'choices':[{'finish_reason':'stop','message':{'content':json.dumps(answer)}}], 'usage':{'prompt_tokens':10,'completion_tokens':10,'cost':0.0001}}
    body.update(changes)
    return {'transport_status':'ok','body_base64':base64.b64encode(encode(body)).decode()}


class SemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.root=Path(cls.tmp.name).resolve()
        value=native(); value['pdf_info']=value['pdf_info'][:1];value['pdf_info'][0]['preproc_blocks']=value['pdf_info'][0]['preproc_blocks'][:1]
        value['pdf_info'][0]['preproc_blocks'][0]['blocks'][0]['lines'][0]['spans'][0]['html']='<table><tr><td>商品</td><td>服務</td><td>總額</td></tr><tr><td>100</td><td>200</td><td>300</td></tr><tr><td></td><td>其他</td><td>—</td></tr></table>'
        write_new(cls.root/'native.json',value);write_new(cls.root/'native-selection.json',selection(cls.root/'native.json'))
        assert launch('ingest',cls.root/'native-selection.json',cls.root/'ir')==0
        cls.selection=ir_selection(cls.root/'ir');cls.evidence=read(cls.root/'ir/evidence.json')
        table=next(n for n in cls.evidence['nodes'] if n['kind']=='table');cls.table=table
        cls.cells=[n for n in cls.evidence['nodes'] if n['kind']=='cell'];cls.target=cls.cells[2]['id']
        cls.spec={'name':'example','table_id':table['id'],'target_id':cls.target,'transform':'mask_body_amounts_v1'}
        cls.query=project(cls.evidence,cls.spec)
        cls.answer={'target_id':cls.target,'state':'selected','contributor_ids':[n['id'] for n in cls.cells[:2]],'support_refs':[n['id'] for n in cls.cells[:3]]}

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def store(self,root,role='primary'):
        d=root/role/'example';d.mkdir(parents=True);return Store(d)

    def consume(self,root,name='out'):
        out=root/name;out.mkdir()
        isolated('consume_worker',{'selection':self.selection,'spec':self.spec,'batch':str(root),'output':str(out),'nonce':'fixed'})
        return (out/'annotations.json').read_bytes(),(out/'provenance.json').read_bytes()

    def test_paired_hashes_and_no_cache_collision(self):
        p=request(self.query,'primary','fixed');r=request(self.query,'research','fixed')
        self.assertEqual(p['semantic_payload_sha256'],r['semantic_payload_sha256'])
        self.assertEqual(p['query_sha256'],r['query_sha256']);self.assertNotEqual(p['attempt_id'],r['attempt_id'])
        for field in ('model','route','temperature','max_tokens'):
            changed=deepcopy(p);changed['configuration'][field]='changed'
            with tempfile.TemporaryDirectory() as t, self.assertRaises(ValueError): dispatch(self.query,changed,lambda _:response(self.answer),Store(t))
        for mutate in ('selection','context','schema','prompt'):
            q=deepcopy(self.query)
            if mutate in ('selection','context'):q[mutate]['target_id']='alien'
            else:q[mutate]={} if mutate=='schema' else 'changed'
            with self.assertRaises(ValueError):verify_query(self.evidence,q)

    def test_invalid_selection_vs_missing_source(self):
        for change in ({'target_id':'alien'},{'transform':'other'},{'table_id':self.target}):
            with self.assertRaises(ValueError):project(self.evidence,{**self.spec,**change})
        missing=project(self.evidence,{**self.spec,'target_id':self.cells[6]['id']})
        self.assertEqual(missing['gate'],'missing_evidence')
        with tempfile.TemporaryDirectory() as t:
            result=dispatch(missing,request(missing,'primary','fixed'),lambda _:self.fail('must not call'),Store(t))
            self.assertEqual(result['model_calls'],0);self.assertEqual(result['validation']['state'],'missing_evidence')
        bad=deepcopy(self.evidence);next(n for n in bad['nodes'] if n['id']==self.table['id'])['grid_state']='partial'
        self.assertEqual(project(bad,self.spec)['gate'],'invalid_extraction')

    def test_amount_invariance_and_literal_headers(self):
        a=project(self.evidence,self.spec);b=project(self.evidence,{**self.spec,'transform':'vary_body_amounts_v1'})
        changed=[]
        for x,y in zip(a['context']['items'],b['context']['items']):
            if x!=y:
                changed.append(x['id']);self.assertGreaterEqual(x['row'],1)
                self.assertEqual({k:v for k,v in x.items() if k not in ('text','transformation')},{k:v for k,v in y.items() if k not in ('text','transformation')})
        self.assertTrue(changed);self.assertEqual(validate_answer(a,self.answer),validate_answer(b,self.answer))
        self.assertEqual(self.cells[3]['text'],'100')

    def test_full_response_failures(self):
        cases=[('timeout',{'transport_status':'timeout'}),('transport_error',{'transport_status':'transport_error'}),
               ('refusal',response(self.answer,choices=[{'finish_reason':'stop','message':{'refusal':'no'}}])),
               ('truncation',response(self.answer,choices=[{'finish_reason':'length','message':{}}])),
               ('invalid_output',response(self.answer,choices=[{'finish_reason':'stop','message':{'content':'{'}}])),
               ('identity_mismatch',response(self.answer,model=CONFIGS['research']['model'])),
               ('identity_mismatch',response(self.answer,provider='wrong'))]
        for state,raw in cases:
            with self.subTest(state=state),tempfile.TemporaryDirectory() as t:
                result=dispatch(self.query,request(self.query,'primary','fixed'),lambda _:raw,Store(t))
                self.assertEqual(result['validation']['state'],state)
                self.assertEqual(replay(Store(t),self.query,'primary','fixed')['validation'],result['validation'])

    def test_answer_validation_scope_support_and_duplicates(self):
        for change in ({'target_id':'alien'},{'contributor_ids':[self.cells[3]['id'],self.cells[4]['id']]},
                       {'support_refs':[self.target]}, {'contributor_ids':[self.cells[0]['id']]*2},
                       {'state':'ambiguous'},{'amount':'300'}):
            with self.assertRaises(ValueError):validate_answer(self.query,{**self.answer,**change})

    def test_operational_noninterference_persisted_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=self.store(root)
            dispatch(self.query,request(self.query,'primary','fixed'),lambda _:response(self.answer),p)
            baseline=self.consume(root,'baseline')
            research=root/'research'/'example';research.mkdir(parents=True)
            variants=['agreement','disagreement','unsupported','refusal','malformed','timeout','missing','persistence_failure']
            for variant in variants:
                for f in research.iterdir():f.unlink()
                a=deepcopy(self.answer)
                if variant=='disagreement':a.update(state='not_a_total',contributor_ids=[])
                if variant=='unsupported':a['contributor_ids']=['plausible-but-unsupported']
                raw=response(a,'research')
                if variant=='refusal':raw=response(a,'research',choices=[{'finish_reason':'stop','message':{'refusal':'no'}}])
                if variant=='timeout':raw={'transport_status':'timeout'}
                if variant=='malformed':(research/'completion.json').write_text('{')
                elif variant=='persistence_failure':(research/'result.json').write_text('{')
                elif variant!='missing':dispatch(self.query,request(self.query,'research','fixed'),lambda _:raw,Store(research))
                self.assertEqual(baseline,self.consume(root,variant),variant)
                log=read(root/variant/'consumption.json')
                self.assertFalse(log['adapter_imported'])
                self.assertFalse(any('/research/' in a.get('path','') for a in log['access_attempts']))

    def test_primary_failure_and_abstention_never_promote(self):
        for mode in ('timeout','refusal','abstained','missing'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();p=self.store(root);r=self.store(root,'research')
                dispatch(self.query,request(self.query,'research','fixed'),lambda _:response(self.answer,'research'),r)
                answer={**self.answer,'state':'ambiguous','contributor_ids':[]}
                raw=response(answer) if mode=='abstained' else ({'transport_status':'timeout'} if mode=='timeout' else response(answer,choices=[{'finish_reason':'stop','message':{'refusal':'no'}}]))
                if mode!='missing':dispatch(self.query,request(self.query,'primary','fixed'),lambda _:raw,p)
                annotations=json.loads(self.consume(root)[0]);self.assertEqual(len(annotations),int(mode=='abstained'))
                if annotations:self.assertEqual(annotations[0]['links'],[])

    def test_stalled_research_consumption_synchronization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=self.store(root);r=self.store(root,'research')
            entered=threading.Event();consumed=threading.Event()
            def slow(_):
                entered.set()
                if not consumed.wait(15):raise AssertionError('primary blocked on research')
                return {'transport_status':'timeout'}
            def primary(_):
                self.assertTrue(entered.wait(15));return response(self.answer)
            def consume():
                try:return self.consume(root)
                finally:consumed.set()
            result=paired(self.query,'fixed',p,r,primary,slow,consume)
            self.assertTrue(consumed.is_set());self.assertTrue(json.loads(result['consumption'][0]))
            self.assertEqual(result['research']['validation']['state'],'timeout')

    def test_exhaustion_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=self.store(root);r=self.store(root,'research')
            result=paired(self.query,'fixed',p,r,lambda _:response(self.answer),lambda _:{'transport_status':'budget_exhausted'},lambda:self.consume(root))
            self.assertEqual(result['research']['model_calls'],0);self.assertEqual(result['research']['validation']['state'],'budget_exhausted')
            self.assertTrue(json.loads(result['consumption'][0]))

    def test_all_write_faults_early_and_late_both_roles(self):
        for role in CONFIGS:
            for name in FILES:
                for late in (False,True):
                    with self.subTest(role=role,name=name,late=late),tempfile.TemporaryDirectory() as tmp:
                        class Fault(Store):
                            def write(s,n,v):
                                if n==name:
                                    if late:super().write(n,v)
                                    raise OSError('fault')
                                super().write(n,v)
                        result=dispatch(self.query,request(self.query,role,'fixed'),lambda _:response(self.answer,role),Fault(tmp))
                        saved=replay(Store(tmp),self.query,role,'fixed')
                        if name=='completion.json':
                            self.assertEqual(result['state'],'commit_unknown')
                            self.assertEqual(saved.get('validation',{}).get('state'),'accepted' if late else None)
                        else:
                            self.assertEqual(result['state'],'persistence_failure');self.assertEqual(saved['state'],'incomplete_attempt')

    def test_completion_corruption_and_wrong_config(self):
        for role in CONFIGS:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);store=Store(root);dispatch(self.query,request(self.query,role,'fixed'),lambda _:response(self.answer,role),store)
                saved={f:(root/f).read_bytes() for f in FILES}
                for name in FILES:
                    for action in ('missing','truncate','corrupt'):
                        with self.subTest(role=role,name=name,action=action):
                            p=root/name
                            if action=='missing':p.unlink()
                            else:p.write_bytes(b'{' if action=='truncate' else b'{}')
                            self.assertEqual(replay(store,self.query,role,'fixed')['state'],'incomplete_attempt')
                            p.write_bytes(saved[name])
                self.assertEqual(replay(store,self.query,role,'changed')['state'],'incomplete_attempt')
                self.assertEqual(replay(store,self.query,'research' if role=='primary' else 'primary','fixed')['state'],'incomplete_attempt')

    def test_research_promotion_fault_detected_by_real_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();r=self.store(root,'research')
            dispatch(self.query,request(self.query,'research','fixed'),lambda _:response(self.answer,'research'),r)
            p=root/'primary'/'example';p.parent.mkdir();shutil.copytree(r.directory,p)
            self.assertEqual(json.loads(self.consume(root)[0]),[])
            self.assertEqual(read(root/'out/provenance.json')['outcome'],'incomplete_attempt')

    def test_actual_protected_reads_and_operational_research_denial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=self.store(root)
            dispatch(self.query,request(self.query,'primary','fixed'),lambda _:response(self.answer),p)
            out=root/'out';out.mkdir()
            payload={'selection':self.selection,'spec':self.spec,'batch':str(root),'output':str(out),'nonce':'fixed'}
            # Inject an accidental broad-loader read inside the real consumer after its guard.
            bootstrap='''import sys,json;sys.path.insert(0,sys.argv[1]);import hkex_audit.semantic_cli as c
p=json.load(sys.stdin)
original=c.replay
def bad(*args):
    denied=[]
    for path in p.pop('denied_paths'):
        try:open(path,'rb')
        except PermissionError:denied.append(path)
    assert len(denied)==6
    return original(*args)
c.replay=bad
c.consume_worker(p)
'''
            payload['denied_paths']=[str(root/'research/example/completion.json'),str(root/'.env'),str(root/'corpus/error_detail.jsonl'),str(root/'raw.pdf'),str(root/'eval/expectations.json'),str(root/'clean/evidence.json')]
            for path in payload['denied_paths']:
                sentinel=Path(path);sentinel.parent.mkdir(parents=True,exist_ok=True)
                sentinel.write_text('synthetic denial marker; no source data or credential')
            proc=subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(Path(__file__).resolve().parents[1]/'src')],input=json.dumps(payload),text=True,capture_output=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            log=read(out/'consumption.json');self.assertEqual(sum(x['decision']=='denied' for x in log['access_attempts']),6)
            self.assertTrue(read(out/'annotations.json'))

    def test_replay_rejects_changed_names_before_output_creation(self):
        from argparse import Namespace
        from hkex_audit.semantic_cli import replay_batch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();batch=root/'batch';batch.mkdir()
            selection_path=root/'selection.json';write_new(selection_path,self.selection)
            write_new(batch/'batch.json',{'selection':self.selection,'specs':[{**self.spec,'name':'../escaped'}],
                                        'configurations':CONFIGS,'nonce':'fixed'})
            with self.assertRaises(ValueError):
                replay_batch(Namespace(batch=batch,selection=selection_path,output=root/'out',command='replay'))
            self.assertFalse((root/'out').exists());self.assertFalse((root/'escaped').exists())

    def test_cli_relative_selection(self):
        import os
        from hkex_audit.semantic_cli import normalized_selection
        path=self.root/'ir-selection.json'
        write_new(path,self.selection)
        self.assertEqual(normalized_selection(Path(os.path.relpath(path))),self.selection)

    def test_transport_file_and_host_denials_without_network(self):
        bootstrap="""import sys;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_transport import install_transport_guard;import socket
install_transport_guard({'127.0.0.1'})
for path in ['.env','corpus/error_detail.jsonl','raw.pdf','research/completion.json']:
    try:open(path)
    except PermissionError:pass
    else:raise AssertionError('file read escaped')
try:socket.getaddrinfo('example.com',443)
except PermissionError:pass
else:raise AssertionError('foreign DNS escaped')
s=socket.socket()
try:s.connect(('127.0.0.1',80))
except PermissionError:pass
else:raise AssertionError('foreign port escaped')
print('denied')
"""
        p=subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(Path(__file__).resolve().parents[1]/'src')],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('denied',p.stdout)

    def test_altered_query_rejected_before_dispatch(self):
        q=deepcopy(self.query);q['context']['items'][0]['text']='edited'
        with tempfile.TemporaryDirectory() as tmp,self.assertRaises(ValueError):
            dispatch(q,request(q,'primary','fixed'),lambda _:self.fail('called'),Store(tmp))

    def test_operational_persistence_failure_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=self.store(root);r=self.store(root,'research')
            def failed():raise OSError('cannot persist annotation')
            result=paired(self.query,'fixed',p,r,lambda _:response(self.answer),lambda _:response(self.answer,'research'),failed)
            self.assertEqual(result['consumption']['outcome'],'persistence_failure')

    def test_replay_has_zero_transport_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);dispatch(self.query,request(self.query,'primary','fixed'),lambda _:response(self.answer),store)
            with patch('hkex_audit.semantic_cli.transport',side_effect=AssertionError('no call')):
                result=replay(store,self.query,'primary','fixed')
            self.assertEqual(result['model_calls'],0);self.assertEqual(result['historical_model_calls'],1)

if __name__=='__main__':unittest.main()
