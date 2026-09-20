"""Read-only inference replay and exclusive derived reporting; no API calls."""
import base64
from collections import Counter
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools/experiments'))
from evaluate_model_selection import evaluate,summarize,ROOT,RUN
from prepare_model_selection import read,save
from direct_contributor_attempt_v2 import sha,encode
names=['availability','screen-s04','screen-s08','screen-s11','screen-s09','screen-s10','confirmation','diagnostics']
rows=sum((evaluate(n) for n in names),[])
sc=[r for r in rows if r['attempt'].split('/')[0] not in ['confirmation','diagnostics']]
cf=[r for r in rows if r['attempt'].startswith('confirmation/')]
dg=[r for r in rows if r['diagnostic']]
agreement={}
for k in read(RUN/'configurations.json'):
 if k=='gemini':continue
 pairs=[]
 for r in sc:
  if r['model_key']!=k:continue
  o=next(x for x in sc if x['model_key']=='gemini' and x['case']==r['case'])
  if r['usable'] and o['usable']:
   a,b=r['output'],o['output'];pairs.append({'case':r['case'],'relation_agrees':a['action']==b['action'] and set(a['contributor_ids'])==set(b['contributor_ids']),'reason_agrees':a['reason']==b['reason']})
 agreement[k]={'relation_matches':sum(x['relation_agrees'] for x in pairs),'reason_matches':sum(x['reason_agrees'] for x in pairs),'usable_pairs':len(pairs),'pairs':pairs}
cost=sum((Decimal(str(r['cost_usd'])) for r in rows if r['cost_usd'] is not None),Decimal(0))
rawtally=Counter();identity=[];times=[];denials=[]
for n in names:
 m=read(RUN/n/'manifest.json');batch=read(RUN/n/'attempts/batch.json');pre=read(RUN/n/'attempts/preflight.json')
 assert len(batch['observations'])==len(m['attempts'])
 denials.append({'batch':n,'preflight_denied':len(pre['checks']),'live_denied':len(batch['checks'])})
 for e in m['attempts']:
  p=RUN/n/'attempts'/e['id'];r=read(p/'response.json');times.append((datetime.fromisoformat(r['started_at']),r['elapsed_seconds']))
  result=read(p/'result.json');rawtally[result['state']]+=1
  if 'body_base64' in r:
   env=json.loads(base64.b64decode(r['body_base64']));identity.append({'attempt':n+'/'+e['id'],'model':env.get('model'),'provider':env.get('provider'),'service_tier':env.get('service_tier'),'system_fingerprint':env.get('system_fingerprint'),'http_status':r.get('http_status')})
# Independent semantic recount, not using source scoring booleans from the evaluator.
key=read(RUN/'evaluator-key.json');manual=Counter()
for r in sc+cf:
 if not r['usable']:manual['unavailable']+=1;continue
 gold=key[r['case']]['expected'];out=r['output']
 relation=(out['action'],out['target_id'],sorted(out['contributor_ids']))==(gold['action'],gold['target_id'],sorted(gold['contributor_ids']))
 manual['source_correct' if relation else 'unsupported_relation']+=1
 assert relation==r['relation_match']
for k,conf in read(RUN/'configurations.json').items():
 for r in rows:
  if r['model_key']==k and r['http_status']==200:assert r['identity_match']
source=read(RUN/'selected-cases.json');a=source['H01']['source'];b=source['H02']['source']
diffs=[i['id'] for i,j in zip(a['items'],b['items']) if i!=j];assert diffs==['panel-key']
summary={'total_inference_attempts':len(rows),'semantic_screen_attempts':len(sc),'screen_planned':54,'screen_not_dispatched':54-len(sc),'confirmation_attempts':len(cf),'diagnostic_attempts':len(dg),'screen':summarize(sc),'confirmation':summarize(cf),'oracle_agreement':agreement,'reported_cost_usd':str(cost),'unknown_cost_attempts':sum(r['cost_usd'] is None for r in rows),'reported_prompt_tokens':sum(r['usage'].get('prompt_tokens',0) for r in rows),'reported_completion_tokens':sum(r['usage'].get('completion_tokens',0) for r in rows),'requested_completion_token_caps':sum(r['tokens_cap'] for r in rows),'sum_attempt_elapsed_seconds':sum(r['elapsed_seconds'] for r in rows),'dispatch_wall_seconds':max(t.timestamp()+elapsed for t,elapsed in times)-min(t.timestamp() for t,elapsed in times),'diagnostic_schema_valid':sum(r.get('diagnostic_schema_valid',False) for r in dg),'diagnostic_literal_citations_valid':sum(r.get('literal_citations_valid',False) for r in dg),'completion_records_verified':len(rows),'independent_semantic_tally':dict(manual),'persisted_terminal_states':dict(rawtally),'denials':denials,'source_pair_changed_ids':diffs}
assert len(rows)<=117 and sum(r['tokens_cap'] for r in rows)<=1000000 and cost<Decimal('35')
save(RUN/'final-evaluation.json',{'summary':summary,'rows':rows,'identity_observations':identity})
# Inventory excludes this later inventory itself; no raw corpus or credentials scanned.
paths=[p for p in RUN.rglob('*') if p.is_file()]
paths += [ROOT/'tools/experiments'/n for n in ['model_selection_worker_v2.py','prepare_model_selection.py','launch_model_selection.py','run_model_selection_screen.py','evaluate_model_selection.py','prepare_model_selection_followups.py']]
paths += [ROOT/'tests/test_model_selection_v2.py']
save(RUN/'final-hashes.json',{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in paths})
print(json.dumps(summary,indent=2))
