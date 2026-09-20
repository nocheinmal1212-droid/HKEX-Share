"""Read-only offline replay, source scoring and accounting for model-selection v2."""
import argparse,base64
from collections import Counter,defaultdict
from decimal import Decimal
import json
from pathlib import Path
import statistics
from direct_contributor_attempt_v2 import encode,sha,replay
from direct_contributor_boundary import interpret_response
from model_selection_worker_v2 import wire_request
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/milestone2/model-selection-2026-09-17'
def read(p):return json.loads(p.read_bytes())
def evaluate(batch):
 d=RUN/batch;freeze=read(d/'freeze.json')
 for path,h in freeze['hashes'].items():assert sha((ROOT/path).read_bytes())==h,path
 m=read(d/'manifest.json');answers=read(RUN/'evaluator-key.json');rows=[]
 for e in m['attempts']:
  a=d/'attempts'/e['id']
  if not (a/'observation.json').exists():continue
  obs=read(a/'observation.json');rp=replay(a);saved=read(a/'result.json');response=read(a/'response.json')
  assert obs['replay']==rp and rp['model_calls']==0 and rp['historical_model_calls']==1
  assert obs['dispatch']=={**saved,'persisted':True}
  assert saved['configuration']==e['configuration']
  assert read(a/'source.json')==e['source'] and read(a/'request.json')==e['job']
  assert e['configuration']['wire_request']==wire_request(e['job'],e['job']['payload'],m['prompt'],e['settings'],e.get('diagnostic'))
  assert response['wire_request_sha256']==e['configuration']['wire_request_sha256']
  raw={k:v for k,v in response.items() if k not in ('body_base64','body_sha256')}
  env={}
  if 'body_base64' in response:
   body=base64.b64decode(response['body_base64'],validate=True);assert sha(body)==response['body_sha256'];raw['body']=body
   try:env=json.loads(body)
   except ValueError:pass
  decision=interpret_response(e['job'],raw)
  for k,v in decision.items():assert saved[k]==v
  choice=(env.get('choices') or [{}])[0];usage=env.get('usage') or {};content=(choice.get('message') or {}).get('content')
  output=decision.get('model_output');usable=decision['state'] in ('structure_accepted','model_abstention')
  identity=env.get('model')==e['settings']['model'] and env.get('provider')==e['expected_provider']
  expected=answers[e['case']]['expected'];relation=reason=support=None
  if usable:
   relation=output['action']==expected['action'] and output['target_id']==expected['target_id'] and set(output['contributor_ids'])==set(expected['contributor_ids'])
   reason=output['reason']==expected['reason'];support=set(answers[e['case']]['support_requirements']['required_ids'])<=set(output['support_ids'])
  if usable:
   category=('correct_selection' if output['action']=='select' else 'correct_abstention') if relation else ('unsupported_selection' if output['action']=='select' else 'unnecessary_abstention')
  elif decision['state']=='incomplete_response':category='truncation' if decision['reason']=='truncated' else 'incomplete'
  elif decision['state']=='transport_failure':category='timeout' if decision['reason']=='timeout' else 'service_error'
  elif decision['state']=='model_refusal':category='refusal'
  else:category='invalid_output'
  row={'attempt':batch+'/'+e['id'],'model_key':e['model_key'],'case':e['case'],'diagnostic':'diagnostic' in e,'parent_attempt':e['configuration'].get('parent_attempt'),'state':decision['state'],'category':category,'usable':usable,'relation_match':relation,'reason_match':reason,'required_support_complete':support,'full_pass':bool(identity and relation and reason and support),'identity_match':identity,'served_model':env.get('model'),'served_provider':env.get('provider'),'requested_provider':e['settings']['provider']['only'],'tokens_cap':e['settings']['max_tokens'],'output':output,'content':content,'finish_reason':choice.get('finish_reason'),'http_status':response.get('http_status'),'api_error':env.get('error'),'elapsed_seconds':response['elapsed_seconds'],'usage':usage,'cost_usd':usage.get('cost'),'credential_redacted':response.get('credential_redacted'),'network_attempts':obs['network_attempts']}
  if row['diagnostic']:
   row['diagnostic_schema_valid']=False
   try:
    import jsonschema
    val=json.loads(content);jsonschema.validate(val,e['diagnostic']['schema']);row['diagnostic_schema_valid']=True;row['explanation']=val
    evidence={i['id']:i['text'] for i in e['source']['items']}
    row['literal_citations_valid']=all(c['id'] in evidence and c['excerpt'] in evidence[c['id']] for c in val['citations'])
   except (ValueError,TypeError,KeyError,jsonschema.ValidationError):pass
  rows.append(row)
 if (d/'attempts/batch.json').exists():
  b=read(d/'attempts/batch.json');p=read(d/'attempts/preflight.json')
  assert b['manifest_sha256']==p['manifest_sha256']==sha((d/'manifest.json').read_bytes())
  assert len(b['checks'])==14 and all(c['denied'] for c in b['checks'])
  assert len(p['checks'])==14 and all(c['denied'] for c in p['checks']) and p['network_calls']==0
 return rows

def summarize(rows):
 groups=defaultdict(list)
 for r in rows:groups[r['model_key']].append(r)
 out={}
 for k,rs in groups.items():
  costs=[Decimal(str(r['cost_usd'])) for r in rs if r['cost_usd'] is not None]
  out[k]={'attempts':len(rs),'outcomes':dict(Counter(r['category'] for r in rs)),'full_pass':sum(r['full_pass'] for r in rs),'usable':sum(r['usable'] for r in rs),'source_correct':sum(r['relation_match'] is True for r in rs),'reason_correct':sum(r['reason_match'] is True for r in rs),'support_complete':sum(r['required_support_complete'] is True for r in rs),'reported_cost_usd':str(sum(costs,Decimal(0))),'unknown_cost_attempts':len(rs)-len(costs),'median_latency':statistics.median(r['elapsed_seconds'] for r in rs),'max_latency':max(r['elapsed_seconds'] for r in rs)}
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch',nargs='+');p.add_argument('--out',type=Path);a=p.parse_args();rows=sum((evaluate(b) for b in a.batch),[]);v={'summary':summarize(rows),'rows':rows}
 if a.out:
  with a.out.open('xb') as f:f.write(encode(v))
 print(json.dumps(v['summary'],indent=2))
