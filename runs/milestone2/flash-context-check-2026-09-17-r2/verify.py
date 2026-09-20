"""Read-only verification and optional exclusive summary; no inference."""
import argparse,base64
from collections import Counter
from datetime import datetime
from decimal import Decimal
import hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];RUN=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/experiments'))
import evaluate_model_selection as ev
ev.RUN=RUN
from direct_contributor_attempt_v2 import encode,sha

def read(p):return json.loads(p.read_bytes())
def verify():
    stages={};identities=[];times=[];denials=[];http=Counter();errors=[]
    for name in ['flash-r2-core','flash-r2-confirmation','flash-r2-diagnostics']:
        if not (RUN/name/'attempts/batch.json').exists():continue
        rows=ev.evaluate(name);stages[name]=rows
        manifest=read(RUN/name/'manifest.json');assert len(rows)==len(manifest['attempts'])
        checks=read(RUN/name/'attempts/batch.json')['checks'];assert len(checks)==14 and all(x['denied'] for x in checks)
        denials.append({'stage':name,'preflight':14,'live':len(checks)})
        for r in rows:
            p=RUN/name/'attempts'/r['attempt'].split('/')[1];response=read(p/'response.json')
            r['transport_exception']=response.get('transport_exception');r['transport_status']=response['transport_status']
            times.append((datetime.fromisoformat(response['started_at']).timestamp(),response['elapsed_seconds']))
            http[str(response.get('http_status'))]+=1
            if 'transport_exception' in response:errors.append({'attempt':r['attempt'],**response['transport_exception'],'http_status':response.get('http_status')})
            if 'body_base64' in response:
                env=json.loads(base64.b64decode(response['body_base64']));identities.append({'attempt':r['attempt'],'model':env.get('model'),'provider':env.get('provider'),'http_status':response.get('http_status')})
    rows=sum(stages.values(),[])
    old=read(ROOT/'runs/milestone2/model-selection-2026-09-17/final-evaluation.json')['rows']
    oracle={}
    for r in old:
        if r['model_key']=='gemini' and not r['diagnostic'] and r['usable'] and r['case'] not in oracle:oracle[r['case']]=r
    pairs=[]
    for r in rows:
        if r['diagnostic'] or not r['usable']:continue
        o=oracle[r['case']];a,b=r['output'],o['output']
        pairs.append({'attempt':r['attempt'],'oracle_attempt':'model-selection-2026-09-17/'+o['attempt'],'relationship_agrees':a['action']==b['action'] and set(a['contributor_ids'])==set(b['contributor_ids']),'reason_agrees':a['reason']==b['reason']})
    oldhashes=read(ROOT/'runs/milestone2/model-selection-2026-09-17/final-hashes.json')
    for path,h in oldhashes.items():assert sha((ROOT/path).read_bytes())==h,path
    for path,h in read(RUN/'execution-code-hashes.json').items():assert sha((ROOT/path).read_bytes())==h,path
    cost=sum((Decimal(str(r['cost_usd'])) for r in rows if r['cost_usd'] is not None),Decimal(0))
    diagnostics=[r for r in rows if r['diagnostic']]
    summary={'attempts':len(rows),'stages':{k:ev.summarize(v) for k,v in stages.items()},'reported_cost_usd':str(cost),'unknown_cost_attempts':sum(r['cost_usd'] is None for r in rows),'reported_prompt_tokens':sum(r['usage'].get('prompt_tokens',0) for r in rows),'reported_completion_tokens':sum(r['usage'].get('completion_tokens',0) for r in rows),'requested_completion_caps':sum(r['tokens_cap'] for r in rows),'elapsed_sum_seconds':sum(r['elapsed_seconds'] for r in rows),'dispatch_wall_seconds':max(t+s for t,s in times)-min(t for t,s in times),'http_statuses':dict(http),'exceptions':errors,'diagnostic_schema_valid':sum(r.get('diagnostic_schema_valid',False) for r in diagnostics),'diagnostic_item_citations_valid':sum(r.get('literal_citations_valid',False) for r in diagnostics),'completion_records_verified':len(rows),'prior_hashes_verified':len(oldhashes),'denials':denials,'oracle_comparisons':pairs,'identities':identities}
    assert len(rows)<=18 and summary['requested_completion_caps']<=61440 and cost<1
    return {'summary':summary,'rows':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--save',action='store_true');a=p.parse_args();v=verify()
    if a.save:
        with (RUN/'verification.json').open('xb') as f:f.write(encode(v))
    print(json.dumps(v['summary'],indent=2))
