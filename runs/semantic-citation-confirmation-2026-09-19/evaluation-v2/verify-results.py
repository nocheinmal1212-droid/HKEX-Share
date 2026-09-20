"""Offline evaluation/replay after the one authorized live launch; no transport calls."""
import os
os.environ={}
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
PACKET=ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2'
OUT=Path(__file__).resolve().parent
LIVE=BASE/'live-v2';PREP=BASE/'prepared-v2'
DIGEST='46c1b25173abf95490caf42b1d589de84237284afde81ce198910f9c9475c0ae'
def read(path):return json.loads(path.read_bytes())
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert read(BASE/'execution-v2-env/launcher-exit.json')['live_output']==str(LIVE)
assert digest(PACKET/'freeze.json')==DIGEST
frozen=read(PACKET/'freeze.json')
assert all(digest(ROOT/p)==h for p,h in frozen['files'].items())
# No later launch-gate invocation: it is correct for that gate to reject an already-used output.
# Verify frozen member bytes directly instead, preserving the immediate prelaunch receipt.
args=[sys.executable,'-I','-B',str(PACKET/'evaluate.py'),'--batch',str(LIVE),'--output',str(OUT/'evaluation.json')]
evaluated=subprocess.run(args,cwd=ROOT,env={},capture_output=True,text=True)
save('evaluator-process.json',{'argv':args,'returncode':evaluated.returncode,'stdout':evaluated.stdout,'stderr':evaluated.stderr})
assert evaluated.returncode==0,'bound evaluator failed; see retained process evidence'
evaluation=read(OUT/'evaluation.json')
spec=importlib.util.spec_from_file_location('accounting',PACKET/'accounting.py')
accounting=importlib.util.module_from_spec(spec);spec.loader.exec_module(accounting)
save('accounting.json',accounting.inspect(LIVE))
identity=read(PACKET/'execution-identity.json')
assert all(digest(ROOT/identity['snapshot']/p)==h for p,h in identity['runtime_files'].items())
replays=[]
for role,command in [('primary','replay'),('research','research-replay')]:
    output=OUT/(role+'-replay')
    bootstrap='import os,sys;os.environ={};sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import main;raise SystemExit(main(sys.argv[2:]))'
    argv=[sys.executable,'-I','-B','-c',bootstrap,str(ROOT/identity['snapshot']/'src'),command,
        '--batch',str(LIVE),'--selection',str(PREP/'selection.json'),'--output',str(output)]
    proc=subprocess.run(argv,cwd=ROOT,env={},capture_output=True,text=True,timeout=180)
    record={'role':role,'argv':argv,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
    save(role+'-replay-process.json',record)
    assert proc.returncode==0,'snapshot replay failed'
    assert read(output/'summary.json')['model_calls']==0
    if role=='primary':
        same={n:all((output/n/f).read_bytes()==(LIVE/'operational'/n/f).read_bytes()
                    for f in ('annotations.json','provenance.json')) for n in ('total','period_groups')}
        assert all(same.values()),'primary replay changed bytes'
        record['primary_annotation_provenance_bytes_identical']=same
    replays.append(record)
rows=[];reported=Decimal(0);reported_count=0
for n in ('total','period_groups'):
    for role in ('primary','research'):
        d=LIVE/role/n
        expected=PREP/n/(role+'-request.json')
        same=digest(d/'request.json')==digest(expected)
        assert same,'request differs from approved request'
        result=read(d/'result.json');validation=result['validation']
        if validation.get('cost_status')=='reported':
            reported+=Decimal(validation['cost']);reported_count+=1
        rows.append({'case':n,'role':role,'approved_request_bytes_identical':same,
            'attempt_id':result['attempt_id'],'model_calls':result['model_calls'],
            'state':validation['state'],'served':validation.get('served'),'usage':validation.get('usage'),
            'reported_cost':validation.get('cost'),'cost_status':validation.get('cost_status')})
    log=read(LIVE/'operational'/n/'consumption.json')
    assert log['model_calls']==0 and not log['adapter_imported']
    assert not any('/research/' in x.get('path','') or '/eval/' in x.get('path','') for x in log['access_attempts'])
supervisor=read(LIVE/'supervisor.json');summary=read(LIVE/'summary.json')
assert summary['http_calls_reserved']<=6 and all(v<=2 for v in summary['completion_calls_reserved'].values())
assert Decimal(summary['cost_reserved_usd'])<=Decimal('8')
assert supervisor['elapsed_seconds']<=600 and supervisor['direct_child_reaped'] and supervisor['total_ceiling_satisfied']
assert not (BASE/'live-v1').exists()
assert all(digest(ROOT/p)==h for p,h in frozen['files'].items())
old=ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v1/freeze.json'
assert digest(old)=='f98cab8947112698dc2e8d58ba30441dc6d8f40f3d1a35125994ce50a34e7643'
save('verification.json',{'verified_at_utc':datetime.now(timezone.utc).isoformat(),'approved_freeze_sha256':DIGEST,
    'frozen_members_unchanged':len(frozen['files']),'attempts':rows,'replays':replays,
    'supervisor':supervisor,'budget_summary':{k:summary[k] for k in ('http_calls_reserved','completion_calls_reserved','cost_reserved_usd','elapsed_seconds')},
    'provider_reported_completion_cost_sum_usd':str(reported),'completions_with_reported_cost':reported_count,
    'metadata_cost':'not reported here; no zero-cost inference from absence',
    'primary_successes':evaluation['primary_successes'],'complete_primary_successes':evaluation['complete_primary_successes'],
    'research_successes':evaluation['research_successes'],'denominator_per_role':2,
    'offline_verification_http_calls':0,'research_excluded_from_primary_reads':True,
    'historical_no_go_freeze_unchanged':True,'old_live_v1_absent':True,
    'limits':'Exposed development confirmation only; no statistical/human acceptance, numerical compatibility or M2 completion.'})
print(json.dumps({'primary_successes':evaluation['primary_successes'],'complete_primary_successes':evaluation['complete_primary_successes'],
    'research_successes':evaluation['research_successes'],'reported_completion_cost_usd':str(reported),
    'operational_elapsed_seconds':supervisor['elapsed_seconds'],'frozen_members_unchanged':len(frozen['files']),
    'primary_replay_bytes_identical':True,'offline_verification_http_calls':0}))
