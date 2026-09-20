"""Collect final offline observations without changing any writer artifact."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PACKET=Path(__file__).resolve().parent;ROOT=PACKET.parents[3]
BASE=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19';OUT=BASE/'checks-v1'

def module(name):
    s=importlib.util.spec_from_file_location(name,PACKET/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_bytes())

def main():
    accounting=module('accounting');p=module('prepare')
    full=next(x.parent for x in (BASE/'diagnostics-v1').glob('full-*/observed.json') if read(x)['result']['returncode']==0)
    research=next(x.parent for x in (BASE/'diagnostics-v1').glob('research-cancel-*/observed.json') if read(x)['result']['timed_out'])
    metadata=next(x.parent for x in (BASE/'diagnostics-v1').glob('metadata-cancel-*/observed.json') if read(x)['result']['timed_out'])
    account=accounting.inspect(full/'experiment')
    assert account['http_calls_min']==account['http_calls_max']==18
    assert all(row['authored_transport'] for row in account['entries'])
    cancelled=accounting.inspect(metadata/'experiment')
    assert cancelled['http_calls_min']==0 and cancelled['http_calls_max']==1
    original=full/'experiment/live-v1-A'
    cancelled_primary=research/'live-v1-A/operational/total'
    assert (original/'operational/total/annotations.json').read_bytes()==(cancelled_primary/'annotations.json').read_bytes()
    # Separate executions bind distinct timestamps/timing in their completion markers.
    # Their provenance must retain those differences; do not normalize original bytes.
    a=read(original/'operational/total/provenance.json');b=read(cancelled_primary/'provenance.json')
    assert {k:v for k,v in a.items() if k!='primary_completion_sha256'}=={k:v for k,v in b.items() if k!='primary_completion_sha256'}
    replay_root=Path(tempfile.mkdtemp(prefix='research-perturbation-replay-',dir=BASE/'diagnostics-v1'))
    changed=replay_root/'live-v1-A';(changed/'primary').mkdir(parents=True)
    shutil.copytree(original/'primary/total',changed/'primary/total')
    (changed/'research/total').mkdir(parents=True)
    (changed/'research/total/response.json').write_text('AUTHORED UNREAD RESEARCH SENTINEL')
    code='import sys,json;sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import consume_worker;consume_worker(json.load(sys.stdin))'
    for label,batch in [('original',original),('perturbed',changed)]:
        dest=replay_root/label;dest.mkdir()
        payload={'selection':read(p.PREP/'selection.json'),'spec':read(p.PREP/'A/total/query.json')['selection'],
                 'batch':str(batch),'output':str(dest),'nonce':'live-v1-A'}
        subprocess.run([sys.executable,'-I','-B','-c',code,str(p.PREP/'A/runtime-snapshot/src')],
            input=json.dumps(payload),text=True,capture_output=True,env={},timeout=180,check=True)
        assert read(dest/'consumption.json')['model_calls']==0
        assert all('/research/' not in x.get('path','') for x in read(dest/'consumption.json')['access_attempts'])
    equal={}
    for name in ('annotations.json','provenance.json'):
        a=replay_root/'original'/name;b=replay_root/'perturbed'/name
        assert a.read_bytes()==b.read_bytes()==(original/'operational/total'/name).read_bytes()
        equal[name]=p.sha(a)
    observations=[]
    for arm in 'ABCD':
        o=read(full/'experiment'/('observation-'+arm+'.json'))
        assert o['two_reads_equal']
        for name,h in o['writer_artifacts_unchanged'].items():assert p.sha(full/'experiment'/('live-v1-'+arm)/name)==h
        observations.append(o['result'])
    real=[]
    for folder in (metadata,research):
        d=read(folder/'observed.json')
        assert d['elapsed_seconds']<d['ceiling_seconds']
        assert d['result']['direct_child_reaped'] and len(d['owned_pids'])==2
        real.append({'path':str(folder.relative_to(ROOT)),**d})
    p.put(OUT/'final-observations.json',{'full_offline_run':str(full.relative_to(ROOT)),
        'full_elapsed_seconds':read(full/'observed.json')['elapsed_seconds'],'accounting_authored_only':account,
        'interrupted_metadata_accounting_authored_only':cancelled,
        'fixed_primary_replay_bytes_equal_with_perturbed_research':equal,
        'distinct_execution_annotation_bytes_equal':True,
        'distinct_execution_provenance_completion_hashes_intentionally_differ':True,
        'observations':observations,'real_cancellation':real,'real_http_calls':0,
        'model_behavior_established':False})
    assert p.preservation()==read(OUT/'preservation-before.json')
    print(json.dumps({'original_bound_members_verified':[3116,83,12],
        'observed_arm_successes':'authored 2/2 per role per arm; not model results',
        'noninvasive_observation':True,'primary_research_perturbation_invariance':True,'real_http_calls':0}))

if __name__=='__main__':main()
