"""Authored offline regressions; fresh paths, empty child environments, retained evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

PACKET=Path(__file__).resolve().parent;ROOT=PACKET.parents[3]
BASE=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19'
PREP=BASE/'prepared-v1';OUT=BASE/'diagnostics-v1'
OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(PREP/'A/runtime-snapshot/src'))
from hkex_audit.semantic_deadline import Deadline,supervise
from hkex_audit.artifacts import read,write_new,encode
from hkex_audit.semantic_attempt import Store,replay

def load(name):
    s=importlib.util.spec_from_file_location(name,PACKET/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def inventory(path):return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}

class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.answers={e['target_id']:{'target_id':e['target_id'],'state':'selected',
            'contributor_ids':e['expected_contributor_header_ids'],'support_refs':e['required_support_ids']}
            for e in read(PACKET/'expectations.json')['queries']}
        cls.worker=load('worker')

    def run_fixture(self,label,fixture,seconds=90,action='pair',arm='A'):
        parent=Path(tempfile.mkdtemp(prefix=label+'-',dir=OUT))
        output=parent/('experiment' if action=='experiment' else 'live-v1-'+arm)
        started=time.monotonic();deadline=Deadline(started,seconds)
        data={'action':action,'output':str(output),'started':started,'seconds':seconds,'offline':True,
              'fixture':{'answers':self.answers,**fixture}}
        if action=='pair':data.update(arm=arm,case='total',reservation={'authored':True})
        result=supervise([sys.executable,'-I','-B',str(PACKET/'worker.py')],data,deadline,env={})
        elapsed=time.monotonic()-started
        self.assertLessEqual(elapsed,seconds+.15)
        self.assertTrue(result['direct_child_reaped'])
        pids=[]
        for path in output.rglob('*.pid'):
            pid=int(path.read_text())
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
            pids.append({'pid':pid,'immediately_after_return':'absent'})
        write_new(parent/'observed.json',{'result':result,'elapsed_seconds':elapsed,'ceiling_seconds':seconds,
            'test_measurement_tolerance_seconds':.15,'ceiling_extension_seconds':0,'owned_pids':pids,
            'real_http_calls':0,'authored':True})
        return output,result

    def observe(self,arm,batch):
        before=inventory(batch)
        def once():
            p=subprocess.run([sys.executable,'-I','-B',str(PACKET/'observe.py'),arm,str(batch)],
                env={},capture_output=True,text=True,timeout=90,check=True)
            return json.loads(p.stdout)
        first=once();second=once()
        self.assertEqual(first,second);self.assertEqual(before,inventory(batch))
        write_new(batch.parent/('observation-'+arm+'.json'),{'result':first,'two_reads_equal':True,
            'writer_artifacts_unchanged':before})
        return first

    def test_01_full_schedule_observation_and_bindings(self):
        output,result=self.run_fixture('full',{},240,'experiment')
        self.assertEqual(result['returncode'],0,result['stderr'])
        summary=read(output/'summary.json');self.assertEqual(summary['http_calls_reserved'],18)
        self.assertEqual(summary['cost_reserved_usd'],read(PACKET/'launch-proposal.json')['full_reservation_usd'])
        for arm in 'ABCD':
            batch=output/('live-v1-'+arm)
            observed=self.observe(arm,batch)
            self.assertEqual(observed['primary_complete_successes'],2)
            self.assertEqual(observed['research_successes'],2)
            for name in ('total','period_groups'):
                for role in ('primary','research'):
                    self.assertEqual(read(batch/role/name/'request.json'),read(PREP/arm/name/(role+'-request.json')))

    def test_02_real_metadata_cancellation(self):
        output,result=self.run_fixture('metadata-cancel',{'stall':'metadata-primary'},3,'experiment')
        self.assertTrue(result['timed_out']);self.assertFalse((output/'summary.json').exists())
        self.assertTrue((output/'metadata-primary-launch.json').exists())
        self.assertFalse((output/'metadata-primary-return.json').exists())
        self.assertFalse((output/'metadata-research-launch.json').exists())
        self.assertEqual(len(list(output.rglob('*.pid'))),2)

    def test_03_real_completed_primary_cancelled_research(self):
        output,result=self.run_fixture('research-cancel',{'stall':'completion-research'},25)
        self.assertTrue(result['timed_out']);self.assertFalse((output/'research/total/completion.json').exists())
        self.assertEqual(read(output/'operational/total/provenance.json')['outcome'],'accepted')
        self.assertEqual(len(list(output.rglob('*.pid'))),2)
        original=inventory(output)
        q=read(PREP/'A/total/query.json')
        saved=replay(Store(output/'research/total'),q,'research',output.name)
        self.assertEqual(saved['state'],'incomplete_attempt');self.assertIsNone(saved['historical_model_calls'])
        self.assertEqual(saved['model_calls'],0)
        corrupt=output.parent/'corrupt';shutil.copytree(output/'primary/total',corrupt)
        (corrupt/'response.json').write_bytes(b'{"partial":')
        self.assertEqual(replay(Store(corrupt),q,'primary',output.name)['state'],'incomplete_attempt')
        self.assertEqual(original,inventory(output))
        self.observe('A',output)

    def test_04_research_never_promotes_primary(self):
        for mode in ('failure_role','abstain_role'):
            output,result=self.run_fixture(mode,{mode:'primary'},90)
            self.assertEqual(result['returncode'],0,result['stderr'])
            observed=self.observe('A',output)['results'][0]
            self.assertFalse(observed['complete_primary_success'])
            self.assertTrue(observed['roles']['research']['success'])
            anns=read(output/'operational/total/annotations.json')
            self.assertTrue(not anns or all(not a['links'] for a in anns))

    def test_05_expired_reservation_and_metadata_validation(self):
        parent=Path(tempfile.mkdtemp(prefix='expired-',dir=OUT))
        from hkex_audit import semantic_deadline as dl
        deadline=Deadline(0,600)
        with patch.object(dl.time,'monotonic',lambda:599),patch.object(self.worker.subprocess,'run',side_effect=AssertionError('late transport')):
            r=self.worker.send({'mode':'metadata','role':'primary'},parent/'late',deadline,{})
        self.assertFalse(r['request_started']);self.assertFalse(list(parent.iterdir()))

    def test_06_consumer_denies_unselected_access(self):
        code='''import json,sys,socket;from pathlib import Path
sys.path.insert(0,sys.argv[1])
from audit_inputs.guard import install
from hkex_audit.contracts import preload
from hkex_audit.header_support import load_policy
preload();load_policy();attempts=install([]);out=[]
for p in sys.argv[2:]:
 try:Path(p).read_bytes()
 except PermissionError:out.append(p)
 else:raise AssertionError("unexpected read")
try:socket.socket()
except PermissionError:pass
else:raise AssertionError("network allowed")
print(json.dumps({'denied':out,'attempts':attempts}))'''
        forbidden=[PACKET/'expectations.json',ROOT/'.env',PREP/'B/total/query.json',
                   ROOT/'runs/semantic-citation-confirmation-2026-09-19/live-v2/research/total/response.json']
        p=subprocess.run([sys.executable,'-I','-B','-c',code,str(PREP/'A/runtime-snapshot/src'),*map(str,forbidden)],env={},capture_output=True,text=True,check=True,timeout=30)
        write_new(Path(tempfile.mkdtemp(prefix='guard-',dir=OUT))/'denials.json',json.loads(p.stdout))

if __name__=='__main__':unittest.main(verbosity=2)
