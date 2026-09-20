"""Retained, read-only evidence aggregation; no model requests or artifact repair."""
import os
os.environ={}
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,sha,write_new
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
OUT=BASE/'deadline-diagnostics-v2'
def module(name):
    spec=importlib.util.spec_from_file_location(name,PACKET/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
accounting=module('accounting');evaluator=module('evaluate')
latest={}
for p in OUT.glob('*/observed.json'):
    mode=read(p)['mode']
    if mode not in latest or p.stat().st_mtime>latest[mode].stat().st_mtime:latest[mode]=p
rows=[]
for mode,p in sorted(latest.items()):
    observation=read(p);batch=p.parent/'batch'
    receipt=read(batch/'supervisor.json')
    assert observation['elapsed_seconds']<=observation['ceiling_seconds']
    assert receipt['direct_child_reaped'] and receipt['total_ceiling_satisfied']
    assert all(r['state_after_return']=='absent' for r in observation['process_observations'])
    records={'mode':mode,'observation_path':str(p.relative_to(ROOT)),'observation':observation,
             'accounting':accounting.inspect(batch),'batch_summary_exists':(batch/'summary.json').exists()}
    if (batch/'batch.json').exists():
        evaluation=evaluator.evaluate_batch(batch,authored=True)
        if mode=='consumption':assert not evaluation['results'][0]['primary_persistence']['available']
        if mode=='slow_research':
            assert evaluation['results'][0]['complete_primary_success']
            assert not evaluation['results'][0]['roles']['research']['success']
        records['evaluation']=evaluation
    rows.append(records)
assert len(rows)==10,len(rows)
oldprep=BASE/'prepared-v1';newprep=BASE/'prepared-v2'
for n in ('total','period_groups'):
    assert (oldprep/n/'query.json').read_bytes()==(newprep/n/'query.json').read_bytes()
    for role in ('primary','research'):
        a=read(oldprep/n/(role+'-request.json'));b=read(newprep/n/(role+'-request.json'))
        assert a['payload']==b['payload'] and a['semantic_payload_sha256']==b['semantic_payload_sha256']
        assert a['attempt_id']!=b['attempt_id'] and b['nonce']=='live-v2'
assert (PACKET/'expectations.json').read_bytes()==(PACKET.with_name('preflight-v1')/'expectations.json').read_bytes()
write_new(OUT/'final-results-controlled.json',{'real_tests':rows,'semantic_payloads_unchanged':True,'queries_byte_identical':True,
    'expectations_byte_identical':True,'new_role_attempt_ids':True,'live_nonce':'live-v2','real_http_calls':0,
    'measurement_tolerance_used_to_extend_proposed_ceiling':False})
print(json.dumps({'real_scenarios':len(rows),'all_observed_elapsed_inside_test_ceiling':True,'semantic_payloads_unchanged':True}))
