"""One-off approved staged experiment; existing preparation/evaluation reused unchanged."""
import argparse
from copy import deepcopy
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/experiments'))
import prepare_model_selection as prep
import evaluate_model_selection as ev
from prepare_model_selection_followups import INSTRUCTION,SCHEMA
from direct_contributor_attempt_v2 import encode,sha
RUN=Path(__file__).resolve().parent
OLD=ROOT/'runs/milestone2/model-selection-2026-09-17'
prep.RUN=ev.RUN=RUN
prep.CODES=prep.CODES+['model_selection_worker_v3.py']
read,save=prep.read,prep.save

def initialize():
    for name in ['selected-cases.json','evaluator-key.json','prompt.txt']:
        with (RUN/name).open('xb') as f:f.write((OLD/name).read_bytes())
    old=read(OLD/'configurations.json');configs={}
    for k,tag in [('v4flash','deepinfra/fp8'),('v41flash','together')]:
        c=deepcopy(old[k]);metadata=read(RUN/('metadata/'+c['model'].replace('/','__')+'.json'))['data']
        assert metadata['id']==c['model']
        ep=next(e for e in metadata['endpoints'] if e['tag']==tag)
        assert ep['status']==0 and {'max_tokens','temperature','response_format','structured_outputs'}<=set(ep['supported_parameters'])
        route=next(r for r in c['routes'] if r['tag']==tag);route['metadata']=ep;c['routes']=[route];configs[k]=c
    save(RUN/'configurations.json',configs)
    prep.batch('flash-core',[{'model':k,'case':c} for k,c in [('v4flash','S08'),('v41flash','S08'),('v41flash','S11'),('v4flash','S11')]])
    save(RUN/'execution-code-hashes.json',{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [Path(__file__),ROOT/'tests/test_model_selection_transport_v3.py',ROOT/'tools/experiments/evaluate_model_selection.py',ROOT/'tools/experiments/prepare_model_selection.py']})

def launch(name,preflight_only=False):
    stage=Path('/private/tmp/audit-model-selection-2026-09-17-'+name)
    for preflight in ([True] if preflight_only else [True,False]):
        env={'PATH':'/usr/bin:/bin'}
        if not preflight:
            key=os.environ.get('OPENROUTER_API_KEY')
            if not key:
                for line in (ROOT/'.env').read_text().splitlines():
                    line=line.strip().removeprefix('export ').lstrip();field,sep,value=line.partition('=')
                    if sep and field.strip()=='OPENROUTER_API_KEY':key=value.strip().strip('\"\'');break
            if not key:raise SystemExit('Credential unavailable')
            env['OPENROUTER_API_KEY']=key
        cmd=['/usr/bin/sandbox-exec','-f',str(stage/'sandbox.sb'),str(Path(sys.executable).resolve()),'-I','-B',str(stage/'model_selection_worker_v3.py'),'--manifest',str(stage/'manifest.json'),'--out',str(RUN/name/'attempts')]
        if preflight:cmd+=['--preflight']
        subprocess.run(cmd,cwd=stage,env=env,close_fds=True,check=True)

def evaluate(name,write=True):
    rows=ev.evaluate(name)
    for r in rows:
        raw=read(RUN/name/'attempts'/r['attempt'].split('/')[1]/'response.json')
        r['transport_exception']=raw.get('transport_exception')
    out={'summary':ev.summarize(rows),'rows':rows}
    if write:save(RUN/(name+'-evaluation.json'),out)
    print(json.dumps(out['summary']),flush=True)
    return rows

def continuation(core):
    eligible=[k for k in ['v4flash','v41flash'] if len([r for r in core if r['model_key']==k and r['full_pass']])==2]
    save(RUN/'advancement.json',{'eligible':eligible,'criterion':'2/2 verified full core passes; no tuning'})
    if not eligible:return []
    specs=[]
    for n,c in enumerate(['S09','S10','H01','H02']):
        for k in eligible if n%2==0 else list(reversed(eligible)):specs.append({'model':k,'case':c})
    prep.batch('flash-confirmation',specs);launch('flash-confirmation')
    return evaluate('flash-confirmation')

def explanations(core,follow):
    selected=[];omitted=[];unavailable=[]
    for k in ['v4flash','v41flash']:
        a=[r for r in core if r['model_key']==k];b=[r for r in follow if r['model_key']==k]
        wrong=lambda rs:next((r for r in rs if r['state']=='model_refusal' or r['usable'] and not r['full_pass']),None)
        abstain=lambda rs:next((r for r in rs if r['full_pass'] and r['output']['action']=='abstain'),None)
        for r in [wrong(a),abstain(a),wrong(b) or abstain(b)]:
            if r:selected.append(r)
        picked={r['attempt'] for r in selected}
        for r in a+b:
            if not r['usable'] and r['state']!='model_refusal':unavailable.append(r['attempt'])
            elif (r['state']=='model_refusal' or not r['full_pass'] or r['output']['action']=='abstain') and r['attempt'] not in picked:omitted.append(r['attempt'])
    save(RUN/'diagnostic-sampling.json',{'selected':[r['attempt'] for r in selected],'qualifying_omitted':omitted,'unavailable_decisions':unavailable})
    specs=[]
    for r in selected:
        content=r['content']
        if content is None:
            import base64
            group,call=r['attempt'].split('/')
            raw=read(RUN/group/'attempts'/call/'response.json')
            env=json.loads(base64.b64decode(raw['body_base64']));content=env['choices'][0]['message'].get('refusal')
        assert isinstance(content,str)
        specs.append({'model':r['model_key'],'case':r['case'],'tokens':2048,'parent_attempt':r['attempt'],'diagnostic':{'original_content':content,'instruction':INSTRUCTION,'schema':SCHEMA}})
    if not specs:return []
    prep.batch('flash-diagnostics',specs);launch('flash-diagnostics');return evaluate('flash-diagnostics')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','execute','replay']);a=p.parse_args()
    if a.mode=='prepare':initialize()
    elif a.mode=='replay':
        for n in ['flash-core','flash-confirmation','flash-diagnostics']:
            if (RUN/n/'attempts/batch.json').exists():evaluate(n,False)
    else:
        for path,h in read(RUN/'execution-code-hashes.json').items():assert sha((ROOT/path).read_bytes())==h
        launch('flash-core');core=evaluate('flash-core')
        if any(r['http_status'] in (401,402,403) for r in core):raise SystemExit('Account failure; remaining stages stopped')
        follow=continuation(core)
        if any(r['http_status'] in (401,402,403) for r in follow):raise SystemExit('Account failure; remaining stages stopped')
        diagnostic=explanations(core,follow)
        rows=core+follow+diagnostic
        assert len(rows)<=18 and sum(r['tokens_cap'] for r in rows)<=61440
        cost=sum((Decimal(str(r['cost_usd'])) for r in rows if r['cost_usd'] is not None),Decimal(0));assert cost<1
        save(RUN/'completed.json',{'inference_attempts':len(rows),'reported_cost_usd':str(cost),'unknown_cost_attempts':sum(r['cost_usd'] is None for r in rows),'core':core,'confirmation':follow,'diagnostics':diagnostic})
