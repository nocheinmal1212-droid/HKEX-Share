"""Evaluation preparation only. Never staged into the model worker."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import shutil
from direct_contributor_attempt_v2 import encode,sha,freeze,precheck
from model_selection_worker_v2 import wire_request
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/milestone2/model-selection-2026-09-17'
PRIOR=ROOT/'runs/milestone2/direct-contributors-2026-09-17'
CODES=['model_selection_worker_v2.py','direct_contributor_live_v2.py','direct_contributor_attempt_v2.py','direct_contributor_boundary.py','direct_contributor_worker.py']
MODELS=[('kimi','moonshotai/kimi-k3','deepinfra/bf16','wafer'),('glm','z-ai/glm-5.3','morph/fp8','friendli'),('qwen','qwen/qwen3.8-2.4t-a95b','novita','modal'),('pro','deepseek/deepseek-v4-pro-0813','baidu/fp8','deepinfra/fp8'),('v4flash','deepseek/deepseek-v4-flash-0731','open-inference/fp8','deepinfra/fp8'),('minimax','minimax/minimax-m3','coreweave/fp4','together'),('v41flash','deepseek/deepseek-v4.1-flash','deepinfra/fp8','together'),('glmflash','z-ai/glm-5.3-flash','wafer','coreweave/nvfp4'),('gemini','google/gemini-3.8-flash','google-ai-studio','google-vertex/global')]

def read(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('xb') as f:f.write(encode(v))

def initialize():
 models={m['id']:m for m in read(RUN/'metadata/models.json')['data']}
 configs={}
 for key,model,primary,secondary in MODELS:
  endpoints=read(RUN/('metadata/'+model.replace('/','__')+'.json'))['data']['endpoints']
  routes=[]
  for tag in [primary,secondary]:
   ep=next(e for e in endpoints if e['tag']==tag)
   assert ep['status']==0 and {'max_tokens','response_format','structured_outputs'}<=set(ep['supported_parameters'])
   settings={'model':model,'max_tokens':4096,'stream':False,'provider':{'only':[tag],'allow_fallbacks':False,'require_parameters':True}}
   if 'temperature' in ep['supported_parameters']:settings['temperature']=0
   # Keep native default reasoning; control total completion budget, not incomparable effort labels.
   routes.append({'tag':tag,'provider_name':ep['provider_name'],'settings':settings,'metadata':ep})
  configs[key]={'model':model,'oracle':key=='gemini','flash':key in ['v4flash','v41flash','glmflash'],'canonical_slug':models[model]['canonical_slug'],'reasoning':models[model].get('reasoning'),'routes':routes}
 save(RUN/'configurations.json',configs)
 cases={c:read(PRIOR/('prepared/'+c+'.json')) for c in ['S03','S04','S08','S11','S09','S10']}
 old={e['id']:e for e in read(ROOT/'spec/diagnostics/direct-contributors-expectations-v1.json')['cases']}
 answers={c:old[c] for c in cases}
 # One contrastive pair: distributed panel headers, same-label scope distractor,
 # nested subtotal, memo row. Only the distribution scope-link text changes.
 def item(i,k,t,refs=None):
  x={'id':i,'kind':k,'text':t,'container_id':'panel-pack'}
  if refs is not None:x['header_refs']=refs
  return x
 common=['period','units','basis']
 items=[item('scope-g','header','Group'),item('scope-c','header','Company'),item('period','header','Year ended 31 December 2025'),item('units','header','HK$ million'),item('basis','header','Originally reported'),
 item('panel-a','header','Panel A: administration', ['scope-g']+common),item('panel-b','header','Panel B: distribution; scope is specified in the panel key', ['panel-key']+common),item('panel-key','header','Panel B relates to the Group.'),item('panel-c','header','Panel C: distribution',['scope-c']+common),
 item('n-main','note','Operating expenses: the complete breakdown is Administration (analysis in Panel A) and Distribution (analysis in the panel with the same consolidation scope).'),item('n-admin','note','Panel A: payroll and premises costs are the complete analysis of Administration. Depreciation is included within these categories.'),
 item('a-sub','row_label','Administration',['panel-a']),item('a-pay','row_label','Payroll',['panel-a']),item('a-site','row_label','Premises costs',['panel-a']),item('a-memo','row_label','Depreciation — included',['panel-a']),item('b-dist','row_label','Distribution',['panel-b']),item('c-dist','row_label','Distribution',['panel-c']),item('t-exp','row_label','Operating expenses',['scope-g']+common)]
 for c in ['H01','H02']:
  src={'container_id':'panel-pack','source_kind':'authored_synthetic_logical_evidence_not_validated_ir','items':deepcopy(items),'limitations':[]}
  if c=='H02':next(i for i in src['items'] if i['id']=='panel-key')['text']='Panel B: Group / Company; allocation not identified.'
  req={'operation':'select_direct_addends','container_id':'panel-pack','target_id':'t-exp','candidate_ids':['c-dist','a-pay','a-memo','a-sub','b-dist','a-site']}
  identity={'doc_id':'synthetic-linked-panels','variant_id':c,'evidence_mode':'logical_fixture','evidence_sha256':sha(encode(src))}
  job=freeze(src,req,identity);assert precheck(src,identity,job)['state']=='eligible'
  cases[c]={'source':src,'job':job}
  answers[c]={'id':c,'expected':{'action':'select' if c=='H01' else 'abstain','target_id':'t-exp','contributor_ids':['a-sub','b-dist'] if c=='H01' else [],'reason':'supported_direct_breakdown' if c=='H01' else 'unknown_context'},'support_requirements':{'required_ids':['n-main','scope-g','period','units','basis','panel-a','panel-b','panel-key'] if c=='H01' else []},'review':'Current agent source review before candidate outputs; not independent human adjudication.'}
 save(RUN/'selected-cases.json',cases);save(RUN/'evaluator-key.json',answers)
 (RUN/'prompt.txt').write_bytes((PRIOR/'prompt.txt').read_bytes())
 print('Initialized routes, two new logical cases, and evaluator-only expectations; no calls.')

def batch(name,specs):
 # specs: model, case, optional route index, tokens, diagnostic.
 configs=read(RUN/'configurations.json');cases=read(RUN/'selected-cases.json');prompt=(RUN/'prompt.txt').read_text()
 directory=RUN/name;directory.mkdir();out=directory/'attempts';out.mkdir()
 stage=Path('/private/tmp/audit-model-selection-2026-09-17-'+name);stage.mkdir()
 entries=[]
 for n,s in enumerate(specs,1):
  key,c=s['model'],s['case'];selected=cases[c];route=configs[key]['routes'][s.get('route',0)]
  settings=deepcopy(route['settings']);settings['max_tokens']=s.get('tokens',4096)
  body=wire_request(selected['job'],selected['job']['payload'],prompt,settings,s.get('diagnostic'))
  e={'id':f'call-{n:03d}','model_key':key,'case':c,'source':selected['source'],'identity':selected['job']['identity'],'job':selected['job'],'settings':settings,'expected_provider':route['provider_name'],'configuration':{'wire_request':body,'wire_request_sha256':sha(encode(body)),'deadline_seconds':60,'retries':0,'max_response_bytes':131072,'experiment_stage':name,'parent_attempt':s.get('parent_attempt')}}
  if 'diagnostic' in s:e['diagnostic']=s['diagnostic']
  entries.append(e);(out/e['id']).mkdir()
 protected=[ROOT/'.env',ROOT/'corpus/error_detail.jsonl',ROOT/'spec/diagnostics/direct-contributors-inputs-v1.json',ROOT/'spec/diagnostics/direct-contributors-expectations-v1.json',PRIOR/'evaluator-key.json',RUN/'evaluator-key.json',RUN/'selected-cases.json']
 m={'version':'model-selection-v2','prompt':prompt,'attempts':entries,'protected_paths':[str(p) for p in protected]}
 save(directory/'manifest.json',m);shutil.copyfile(directory/'manifest.json',stage/'manifest.json')
 for code in CODES:shutil.copyfile(ROOT/'tools/experiments'/code,stage/code)
 profile='(version 1)\n(allow default)\n(deny file-read-data (subpath '+json.dumps(str(ROOT))+'))\n(allow file-read-data (subpath '+json.dumps(str(out))+'))\n(deny file-write*)\n(allow file-write* (subpath '+json.dumps(str(out))+') (subpath "/dev"))\n'
 (stage/'sandbox.sb').write_text(profile);(directory/'sandbox.sb').write_text(profile)
 save(directory/'freeze.json',{'at':datetime.now(timezone.utc).isoformat(),'calls':len(entries),'stage':str(stage),'hashes':{str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [directory/'manifest.json',directory/'sandbox.sb',RUN/'design.md',RUN/'configurations.json',RUN/'evaluator-key.json',RUN/'selected-cases.json',RUN/'prompt.txt',*[ROOT/'tools/experiments'/c for c in CODES]]}})
 print(name,len(entries),'frozen; no calls')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--spec',type=Path);a=p.parse_args()
 if a.mode=='init':initialize()
 else:batch(a.mode,read(a.spec))
