from pathlib import Path
import json,sys,shutil,subprocess,hashlib
root=Path.cwd();out=root/'runs/semantic-citation-review-2026-09-19';base=root/'runs/paired-semantic-integration-2026-09-18';pin=root/'runs/semantic-citation-implementation-1.1.0/pinned-v1';man=root/'tools/replay-semantic-v1'
def read(p):return json.loads(p.read_text())
def run(batch,manifests,dest,role='replay',pinned=pin):
 cmd=[sys.executable,'-B',str(root/'tools/replay_semantic_v1.py'),role,'--pin',str(pinned),'--batch',str(batch),'--manifests',str(manifests),'--selection',str(base/'selection.json'),'--output',str(dest)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env={'PYTHONDONTWRITEBYTECODE':'1','PATH':'/usr/bin:/bin'})
 return {'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'output_exists':dest.exists()}
results={}
results['intact_research']=run(base/'live-v1',man,out/'historical-research','research-replay')
if results['intact_research']['returncode']==0:
 results['research_states']=[v['result']['validation']['state'] for v in read(out/'historical-research/summary.json')['results']]
for mode in ['missing_directory','corrupt_response','missing_manifest','corrupt_manifest','primary_manifest','new_query_binding','pin_bytes']:
 area=out/('replay-'+mode);area.mkdir();batch=area/'batch';batch.mkdir();manifests=area/'manifests';shutil.copytree(man,manifests)
 shutil.copy2(base/'live-v1/batch.json',batch/'batch.json')
 for role in ['primary','research']:shutil.copytree(base/'live-v1'/role,batch/role)
 if mode=='missing_directory':shutil.rmtree(batch/'research')
 if mode=='corrupt_response':(batch/'research/total/response.json').write_text('{broken')
 if mode=='missing_manifest':(manifests/'research.json').unlink()
 if mode=='corrupt_manifest':(manifests/'research.json').write_text('{broken')
 if mode=='primary_manifest':(manifests/'primary.json').write_text('{broken')
 if mode=='new_query_binding':
  value=read(batch/'batch.json');value['specs'][0]['transform']='vary_body_amounts_v1';(batch/'batch.json').write_text(json.dumps(value))
 pinned=pin
 if mode=='pin_bytes':
  pinned=area/'pin';shutil.copytree(pin,pinned);p=pinned/'src/hkex_audit/semantic.py';p.chmod(0o600);p.write_bytes(p.read_bytes()+b'\n# diagnostic mutation\n')
 primary=run(batch,manifests,area/'primary-output',pinned=pinned)
 result={'primary':primary}
 if mode in ['missing_directory','corrupt_response','missing_manifest','corrupt_manifest']:
  assert primary['returncode']==0,primary
  expected=read(man/'primary.json')['expected_outputs']
  result['annotation_provenance_byte_identity']=all(hashlib.sha256((area/'primary-output'/f).read_bytes()).hexdigest()==h for f,h in expected.items())
  result['research']=run(batch,manifests,area/'research-output','research-replay')
  assert result['research']['returncode']!=0
 else:assert primary['returncode']!=0 and not primary['output_exists']
 results[mode]=result
(out/'replay-probes.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:(v if k=='research_states' else v.get('primary',v)['returncode']) for k,v in results.items()}))
