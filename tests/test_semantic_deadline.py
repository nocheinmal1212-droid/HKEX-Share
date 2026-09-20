"""Offline launch deadlines, owned-process cancellation, accounting and retained replay."""
import base64
from decimal import Decimal
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from hkex_audit import semantic_cli as cli
from hkex_audit import semantic_deadline as dl
from hkex_audit.artifacts import read, write_new
from hkex_audit.semantic_attempt import Store, request, replay

ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2'
PREP=ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v1'
EVIDENCE=ROOT/'runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2'
spec=importlib.util.spec_from_file_location('offline_worker',PACKET/'offline_worker.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class DeadlineTests(unittest.TestCase):
    def args(self,out,seconds=600):
        return SimpleNamespace(selection=PREP/'selection.json',queries=PREP/'queries.json',output=out,
            max_http_calls=6,max_role_calls=2,max_seconds=seconds,max_cost=Decimal('8'),env_root=None)

    def real_run(self,mode,seconds=3):
        root=Path(tempfile.mkdtemp(prefix=mode+'-',dir=EVIDENCE));out=root/'batch'
        actual=cli.supervise
        def supervised(argv,payload,deadline,env=None):
            if 'receipt' in payload:
                return actual(argv,payload,deadline,env={})
            payload['fixture_mode']=mode
            return actual([sys.executable,'-I','-B',str(PACKET/'offline_worker.py')],payload,deadline,env={})
        start=time.monotonic()
        with patch.object(cli,'supervise',supervised),patch.object(cli.os,'environ',{}):
            code=cli.run(self.args(out,seconds))
        elapsed=time.monotonic()-start
        receipt=read(out/'supervisor.json')
        self.assertTrue(receipt['direct_child_reaped'])
        # Polling process state is observation, never an extra runtime cleanup grace.
        pid_records=[]
        for p in [out/'stage.json', *out.glob('transport-*.json'), *out.glob('descendant-*.json')]:
            if p.exists():
                pid=read(p)['pid']
                try:
                    os.kill(pid,0)
                except ProcessLookupError:
                    state='absent'
                else:
                    state='present'
                self.assertEqual(state,'absent',(pid,state))
                pid_records.append({'pid':pid,'state_after_return':state or 'absent'})
        self.assertFalse((out/'escaped').exists())
        self.assertLessEqual(elapsed,seconds+.15)
        write_new(root/'observed.json',{'mode':mode,'returncode':code,'elapsed_seconds':elapsed,'ceiling_seconds':seconds,
            'measurement_assertion_tolerance_seconds':.15,'production_ceiling_extension':0,'process_observations':pid_records,
            'offline_only':True,'real_http_calls':0})
        return out,code

    def test_real_cancellation_stages_and_descendants(self):
        for mode in ('preparation','metadata','between_metadata','paired','partial_response','consumption','between_queries'):
            with self.subTest(stage=mode):
                out,code=self.real_run(mode,20 if mode=='between_queries' else 3)
                self.assertEqual(code,2)
                self.assertFalse((out/'summary.json').exists())
                if mode=='preparation':
                    self.assertFalse(list(out.glob('*-metadata.json')))
                if mode in ('metadata','between_metadata'):
                    role='primary' if mode=='metadata' else 'research'
                    self.assertEqual(read(out/('metadata-'+role+'-launch.json'))['issued_http_calls'],'unknown_until_return')
                    self.assertFalse((out/('metadata-'+role+'-return.json')).exists())
                if mode=='partial_response':
                    self.assertEqual((out/'primary/total/response.json').read_bytes(),b'{"partial":')
                    self.assertFalse((out/'primary/total/completion.json').exists())
                    r=replay(Store(out/'primary/total'),fixture.PREPARED['queries'][0],'primary',out.name)
                    self.assertEqual(r['state'],'incomplete_attempt');self.assertIsNone(r['historical_model_calls'])
                if mode=='consumption':
                    self.assertEqual((out/'operational/total/annotations.json').read_bytes(),b'[')
                    self.assertFalse((out/'operational/total/consumption.json').exists())

    def test_real_primary_consumed_before_slow_research_and_zero_call_replay(self):
        out,code=self.real_run('slow_research',20)
        self.assertEqual(code,2)
        q=fixture.PREPARED['queries'][0]
        self.assertEqual(read(out/'operational/total/provenance.json')['outcome'],'accepted')
        original=[(out/'operational/total'/f).read_bytes() for f in ('annotations.json','provenance.json')]
        self.assertFalse((out/'research/total/completion.json').exists())
        dest=out/'replayed';dest.mkdir()
        with patch.object(cli,'transport',side_effect=AssertionError('replay transport')):
            cli.isolated('consume_worker',{'selection':read(PREP/'selection.json'),'spec':q['selection'],
                'batch':str(out),'output':str(dest),'nonce':out.name})
        self.assertEqual(original,[(dest/f).read_bytes() for f in ('annotations.json','provenance.json')])
        self.assertEqual(read(dest/'consumption.json')['model_calls'],0)
        self.assertFalse(any('/research/' in x['path'] or '/eval/' in x['path'] for x in read(dest/'consumption.json')['access_attempts']))
        # Corrupt only a disposable copy; preserve the completed cancellation artifact.
        import shutil
        corrupt=out/'corrupt';shutil.copytree(out/'primary/total',corrupt)
        (corrupt/'completion.json').write_bytes(b'{')
        self.assertEqual(replay(Store(corrupt),q,'primary',out.name)['state'],'incomplete_attempt')

    def test_accepted_research_never_promotes_failed_or_abstained_primary(self):
        for mode in ('primary_failure','primary_abstention'):
            with self.subTest(mode=mode):
                out,code=self.real_run(mode,60)
                self.assertEqual(code,0)
                for q in fixture.PREPARED['queries']:
                    n=q['selection']['name']
                    ann=read(out/'operational'/n/'annotations.json')
                    self.assertTrue(ann==[] or all(a['links']==[] for a in ann))
                    self.assertEqual(replay(Store(out/'research'/n),q,'research',out.name)['validation']['state'],'accepted')

    def test_expiry_after_reservation_before_spawn_and_after_launch_intent(self):
        with tempfile.TemporaryDirectory() as t:
            prefix=Path(t)/'call';clock=[0.]
            deadline=dl.Deadline(0,10)
            original=cli.write_new
            def write(path,value):
                original(path,value);clock[0]=deadline.work_end
            with patch.object(dl.time,'monotonic',lambda:clock[0]),patch.object(cli,'write_new',write),patch.object(cli,'transport',side_effect=AssertionError('expired transport')):
                result=cli.send_transport({'mode':'metadata','role':'primary'},prefix,deadline)
                self.assertFalse(result['request_started'])
                self.assertEqual(result['transport_status'],'budget_exhausted')
                self.assertEqual(cli.send_transport({'mode':'metadata','role':'research'},Path(t)/'never',deadline)['transport_status'],'budget_exhausted')
                self.assertFalse((Path(t)/'never-launch.json').exists())
            # Even a caller that queued transport earlier cannot spawn it after expiry.
            with patch.object(cli.time,'monotonic',lambda:10),patch.object(cli.subprocess,'run',side_effect=AssertionError('late subprocess')):
                self.assertFalse(cli.transport({'deadline_monotonic':9})['request_started'])

    def test_original_virtual_730_counterexample_and_stage_boundaries(self):
        for mode in ('original_730','preparation','before_metadata','between_metadata','between_queries','reservation_gap'):
            with self.subTest(mode=mode):
                out=Path(tempfile.mkdtemp(prefix='virtual-'+mode+'-',dir=EVIDENCE))
                clock=[0.];calls=[];consumers=[0];pairs=[0]
                deadline=dl.Deadline(0,600)
                def advance(duration,limit):
                    spent=min(duration,limit);clock[0]+=spent
                    if spent<duration:raise dl.DeadlineExpired('authored stage timeout')
                def isolated(function,payload,timeout=180):
                    if function=='prepare_worker':
                        if mode=='preparation':advance(700,timeout)
                        if mode=='original_730':advance(170,timeout)
                        if mode=='before_metadata':clock[0]=deadline.work_end
                        return fixture.PREPARED
                    consumers[0]+=1
                    if mode=='original_730':advance(170,timeout)
                    if mode=='between_queries':clock[0]=deadline.work_end
                    return {'outcome':'authored-virtual-only'}
                def transport(job,timeout=60):
                    self.assertLess(clock[0],deadline.work_end)
                    calls.append({'mode':job['mode'],'role':job['role'],'time':clock[0]})
                    if job['mode']=='metadata':
                        if mode=='original_730':advance(55,timeout)
                        if mode=='between_metadata':clock[0]=deadline.work_end
                        return fixture.metadata(job['role'])
                    target=json.loads(job['payload']['messages'][1]['content'])['target_id']
                    name=next(q['selection']['name'] for q in fixture.PREPARED['queries'] if q['context']['target_id']==target)
                    return fixture.response(name,job['role'])
                actual_paired=cli.paired
                def paired(*args,**kwargs):
                    pairs[0]+=1
                    if mode=='original_730':advance(55,deadline.remaining(60))
                    if mode=='reservation_gap':clock[0]=deadline.work_end
                    return actual_paired(*args,**kwargs)
                with patch.object(cli,'isolated',isolated),patch.object(cli,'transport',transport),patch.object(cli,'paired',paired),patch.object(dl.time,'monotonic',lambda:clock[0]),patch.object(cli.os,'environ',{'OPENROUTER_API_KEY':'INERT-AUTHORED-FIXTURE'}):
                    with self.assertRaises(dl.DeadlineExpired):cli.run_body(self.args(out),deadline)
                self.assertLessEqual(clock[0],600)
                self.assertFalse((out/'summary.json').exists())
                if mode=='original_730':self.assertEqual(clock[0],599);self.assertEqual(len(calls),6)
                if mode in ('preparation','before_metadata'):self.assertEqual(len(calls),0)
                if mode=='between_metadata':self.assertEqual(len(calls),1)
                if mode=='reservation_gap':self.assertEqual(len(calls),2)
                write_new(out/'virtual-evidence.json',{'scenario':mode,'virtual_elapsed_from_entry':clock[0],
                    'mock_calls':calls,'real_http_calls':0,'ceiling':600,'cleanup_reserved_inside_ceiling':1,
                    'normal_success':False,'original_unchanged_counterexample_elapsed':730})

if __name__=='__main__':unittest.main()
