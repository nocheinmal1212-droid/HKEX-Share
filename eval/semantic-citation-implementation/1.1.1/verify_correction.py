"""Offline correction diagnostics in a new, exclusive output directory."""
from pathlib import Path
from argparse import Namespace
from decimal import Decimal
from unittest.mock import patch
import json,subprocess,sys
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from hkex_audit.artifacts import read,sha,write_new,encode,fingerprint
from hkex_audit.semantic import project,SCHEMA,PROMPT
from hkex_audit.semantic_cli import isolated,runtime_identity
import hkex_audit.semantic_cli as cli
from hkex_audit.semantic_attempt import dispatch,request,Store
from hkex_audit.cli import launch
from helpers import selection,ir_selection
from test_semantic_integration import response

def offline(event,args):
    if event.startswith('socket.'):raise PermissionError('offline correction verification')
sys.addaudithook(offline)
OUT=ROOT/'runs/semantic-citation-correction-1.1.1/persisted';OUT.mkdir()
results={'classification':'post-exposure authored offline correction; mock dispatch only','provider_calls':0,'network_calls':0,'fixtures':[],'local_controls':[],'persisted':[]}
for case in read(HERE/'fixture-freeze.json')['cases']:
    p=HERE/'fixtures'/case;ir=read(p/'evidence.json')
    for spec,expected in zip(read(p/'selections.json'),read(p/'expectations.json')):
        q=project(ir,spec)
        assert q['gate']==expected['gate']
        results['fixtures'].append({'case':case,'target':spec['name'],'query_id':q['query_id'],'gate':q['gate'],'source_sha256':q['source_sha256'],'analysis':q['host_analysis']})
# Export only the selected authored source to runtime input paths.
p=HERE/'fixtures/nested';area=OUT/'source';area.mkdir();(area/'source.json').write_bytes((p/'source.json').read_bytes())
ir=read(p/'evidence.json');write_new(area/'native-selection.json',selection(area/'source.json',ir['document']))
assert launch('ingest',area/'native-selection.json',area/'ir')==0
assert read(area/'ir/evidence.json')==ir
sel=ir_selection(area/'ir')
for spec,expected in zip(read(p/'selections.json'),read(p/'expectations.json')):
    q=project(ir,spec);a={'target_id':spec['target_id'],'state':'selected','contributor_ids':expected['contributors'],'support_refs':expected['support']}
    for role in ('primary','research'):
        dest=OUT/role/spec['name'];dest.mkdir(parents=True)
        dispatch(q,request(q,role,'correction-authored'),lambda _,r=role:response(a,r),Store(dest))
    for phase in ('consume','replay'):
        dest=OUT/phase/spec['name'];dest.mkdir(parents=True)
        isolated('consume_worker',{'selection':sel,'spec':spec,'batch':str(OUT),'output':str(dest),'nonce':'correction-authored'})
    assert all((OUT/'consume'/spec['name']/f).read_bytes()==(OUT/'replay'/spec['name']/f).read_bytes() for f in ['annotations.json','provenance.json'])
    guard=read(OUT/'consume'/spec['name']/'consumption.json');assert not guard['adapter_imported'] and not any('/research/' in x.get('path','') for x in guard['access_attempts'])
    results['persisted'].append({'target':spec['name'],'byte_identical':True,'annotations':read(OUT/'consume'/spec['name']/'annotations.json'),'provenance':read(OUT/'consume'/spec['name']/'provenance.json'),'consumption':guard})
class NoCredentials(dict):
    def get(self,key,*args):
        if key=='OPENROUTER_API_KEY':raise AssertionError('credential access')
        return super().get(key,*args)
for case in ['G3','G4_revision2','G5']:
    p=ROOT/'runs/semantic-citation-implementation-1.1.0/development'/case
    batch=OUT/case
    args=Namespace(selection=p/'selection.json',queries=p/'queries.json',output=batch,max_http_calls=0,max_role_calls=0,max_seconds=30,max_cost=Decimal('1'),env_root=OUT/'forbidden')
    with patch.object(cli.os,'environ',NoCredentials()),patch.object(cli,'bootstrap_key',side_effect=AssertionError('bootstrap')),patch.object(cli,'transport',side_effect=AssertionError('transport')):
        assert cli.run(args)==0
    summary=read(batch/'summary.json');name=read(p/'queries.json')[0]['name'];annotations=read(batch/'operational'/name/'annotations.json')
    assert summary['http_calls_reserved']==0 and annotations==[]
    results['local_controls'].append({'case':case,'http_reserved':0,'completion_reserved':summary['completion_calls_reserved'],'annotations':annotations,'outcome':read(batch/'operational'/name/'provenance.json')['outcome']})
# Prior uncommitted 1.1 runtime is preserved exactly, not rebuilt from HEAD.
oldroot=HERE/'runtime-before';baseline=read(HERE/'baseline.json')
assert all(sha((oldroot/p).read_bytes())==h for p,h in baseline['runtime_files'].items())
dev=ROOT/'runs/semantic-citation-implementation-1.1.0/development';dest=OUT/'prior-runtime-consumption';dest.mkdir()
payload={'selection':read(dev/'isolation-source/selection.json'),'spec':read(ROOT/'eval/semantic-citation-implementation/1.1.0/fixtures/S01_actual_sibling_outer/selection.json'),'batch':str(dev/'authored-accepted'),'output':str(dest),'nonce':'authored'}
bootstrap="""import sys,json
sys.path.insert(0,sys.argv[1])
def offline(event,args):
 if event.startswith('socket.'):raise PermissionError('offline preservation')
sys.addaudithook(offline)
from hkex_audit.semantic_cli import consume_worker
consume_worker(json.load(sys.stdin))
"""
proc=subprocess.run([sys.executable,'-I','-B','-c',bootstrap,str(oldroot/'src')],input=json.dumps(payload),text=True,capture_output=True,env={'PATH':'/usr/bin:/bin'},timeout=60)
assert proc.returncode==0,proc.stderr
same={f:(dest/f).read_bytes()==(dev/'authored-accepted/operational'/f).read_bytes() for f in ['annotations.json','provenance.json']};assert all(same.values())
results['prior_runtime_replay']={'snapshot_files_verified':len(baseline['runtime_files']),'byte_identity':same,'model_calls':0}
try:cli.replay_batch(Namespace(batch=dev/'G3/batch',selection=dev/'G3/selection.json',output=OUT/'old-batch-rejected',command='replay'))
except ValueError as e:results['old_batch_rejection']=str(e)
else:raise AssertionError('old batch silently accepted')
assert not (OUT/'old-batch-rejected').exists()
results['runtime_sha256']=runtime_identity();results['schema_sha256']=fingerprint(SCHEMA);results['prompt_sha256']=sha(PROMPT.encode())
write_new(HERE/'offline-results.json',results)
print('13 source/target gates, two persisted relationships, three zero-call controls and old-runtime replay verified.')
