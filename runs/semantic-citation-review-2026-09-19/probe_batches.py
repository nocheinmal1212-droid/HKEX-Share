from pathlib import Path
from copy import deepcopy
from argparse import Namespace
from decimal import Decimal
from unittest.mock import patch
import json,sys,base64
sys.path[:0]=[str(Path.cwd()/'src'),str(Path.cwd()/'tests')]
from helpers import selection,ir_selection
from hkex_audit.cli import launch
import hkex_audit.semantic_cli as c
from hkex_audit.semantic import project
from hkex_audit.artifacts import read,write_new,sha,encode
from hkex_audit.semantic_attempt import CONFIGS
from test_semantic_integration import response
root=Path('runs/semantic-citation-review-2026-09-19').resolve()
def offline(event,args):
 if event.startswith('socket.'):raise PermissionError('offline review')
sys.addaudithook(offline)
records={'classification':'authored mock dispatch; zero provider/model completions','expectation_sha256':sha((root/'batch-probe-plan.md').read_bytes()),'local':[],'mixed':[]}
class NoCredentials(dict):
 def get(self,key,*a):
  if key=='OPENROUTER_API_KEY':raise AssertionError('credential lookup forbidden')
  return super().get(key,*a)
def args(sel,queries,out,http=0,role=0):
 return Namespace(selection=sel,queries=queries,output=out,max_http_calls=http,max_role_calls=role,max_seconds=300,max_cost=Decimal('5'),env_root=root/'forbidden')
def replay(sel,batch,out,command='replay'):
 c.replay_batch(Namespace(selection=sel,batch=batch,output=out,command=command))
for name,semantic in [('G3','missing_evidence'),('G4_revision2','ambiguous'),('G5','incompatible_context')]:
 src=Path('runs/semantic-citation-implementation-1.1.0/development')/name
 dest=root/('local-'+name)
 with patch.object(c.os,'environ',NoCredentials()),patch.object(c,'bootstrap_key',side_effect=AssertionError('bootstrap forbidden')),patch.object(c,'transport',side_effect=AssertionError('transport forbidden')):
  c.run(args(src/'selection.json',src/'queries.json',dest))
  replay(src/'selection.json',dest,root/('local-replay-'+name))
  replay(src/'selection.json',dest,root/('local-research-'+name),'research-replay')
 summary=read(dest/'summary.json');spec=read(src/'queries.json')[0];n=spec['name']
 same={stem:(dest/'operational'/n/(stem+'.json')).read_bytes()==(root/('local-replay-'+name)/n/(stem+'.json')).read_bytes() for stem in ['annotations','provenance']}
 records['local'].append({'fixture':name,'semantic_expectation':semantic,'selected_ir_sha256':sha(Path(read(src/'selection.json')['evidence']['path']).read_bytes()),'http_reserved':summary['http_calls_reserved'],'completion_reserved':summary['completion_calls_reserved'],'annotations':read(dest/'operational'/n/'annotations.json'),'provenance':read(dest/'operational'/n/'provenance.json'),'replay_byte_identity':same})
# New explicitly authored multi-table source; no evaluation expectations passed to workers.
p=Path('eval/semantic-citation-implementation/1.1.0/fixtures/S01_actual_sibling_outer/source.json');g=Path('eval/semantic-citation-investigation/2026-09-19/sources/G3/source.json')
source=read(p);source['pdf_info'][0]['preproc_blocks']+=deepcopy(read(g)['pdf_info'][0]['preproc_blocks'])
area=root/'mixed-source';area.mkdir();write_new(area/'source.json',source)
doc={'doc_id':'review-mixed-local-eligible','variant_id':'authored','source_document_sha256':None,'source_provenance':'synthetic'}
write_new(area/'native-selection.json',selection(area/'source.json',doc));assert launch('ingest',area/'native-selection.json',area/'ir')==0
write_new(area/'selection.json',ir_selection(area/'ir'));ir=read(area/'ir/evidence.json');tables=[n for n in ir['nodes'] if n['kind']=='table'];specs=[]
for index,name,label in [(1,'local','合計'),(0,'eligible','總額')]:
 target=next(n for n in ir['nodes'] if n['parent_id']==tables[index]['id'] and n['text']==label)
 specs.append({'name':name,'table_id':tables[index]['id'],'target_id':target['id'],'transform':'mask_body_amounts_v1'})
write_new(area/'queries.json',specs)
q=project(ir,specs[1]);cells={n['text']:n['id'] for n in q['context']['items'] if n['kind']=='cell'}
answer={'target_id':cells['總額'],'state':'selected','contributor_ids':[cells['合計'],cells['租賃(HKFRS 16)']],'support_refs':[cells[t] for t in ['總額','合計','租賃(HKFRS 16)','來自與客戶合約之收入(HKFRS 15)']]}
for mode in ['available','unavailable']:
 calls=[]
 def mock(job):
  calls.append({'mode':job['mode'],'role':job['role']})
  if job['mode']=='metadata':
   if mode=='unavailable':return {'transport_status':'unavailable'}
   config=CONFIGS[job['role']];body={'data':{'id':config['model'],'endpoints':[{'tag':config['route'],'status':0,'provider_name':config['served_provider'],'supported_parameters':['structured_outputs','response_format','temperature','max_tokens'],'pricing':{'prompt':'0.000001','completion':'0.000001'}}]}}
   return {'transport_status':'ok','body_base64':base64.b64encode(encode(body)).decode()}
  assert json.loads(job['payload']['messages'][1]['content'])['target_id']==q['selection']['target_id']
  return response(answer,job['role'])
 dest=root/('mixed-'+mode)
 with patch.object(c.os,'environ',{'OPENROUTER_API_KEY':'offline-nonsecret-placeholder'}),patch.object(c,'bootstrap_key',return_value=None),patch.object(c,'transport',side_effect=mock):
  a=args(area/'selection.json',area/'queries.json',dest,4,1);a.env_root=None;c.run(a)
  replay(area/'selection.json',dest,root/('mixed-replay-'+mode))
 s=read(dest/'summary.json')
 records['mixed'].append({'mode':mode,'calls':calls,'http_reserved':s['http_calls_reserved'],'completion_reserved':s['completion_calls_reserved'],'source_sha256':sha((area/'source.json').read_bytes()),'source_parents':{str(x):sha(x.read_bytes()) for x in [p,g]},'outcomes':{n:read(dest/'operational'/n/'provenance.json')['outcome'] for n in ['local','eligible']},'annotations':{n:read(dest/'operational'/n/'annotations.json') for n in ['local','eligible']},'byte_identity':{n:{stem:(dest/'operational'/n/(stem+'.json')).read_bytes()==(root/('mixed-replay-'+mode)/n/(stem+'.json')).read_bytes() for stem in ['annotations','provenance']} for n in ['local','eligible']}})
write_new(root/'batch-probes.json',records)
print('local',[(r['fixture'],r['http_reserved']) for r in records['local']]);print('mixed',[(r['mode'],r['http_reserved'],r['completion_reserved'],r['outcomes']) for r in records['mixed']])
