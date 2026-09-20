from pathlib import Path
import json, hashlib, subprocess, sys, zipfile
sys.path.insert(0,str(Path.cwd()/'src'))
from hkex_audit.semantic import SCHEMA, PROMPT, VERSION
from hkex_audit.semantic_cli import runtime_identity
from hkex_audit.semantic_attempt import CONFIGS, VERSION as AV
from hkex_audit.header_support import policy_identity
from hkex_audit.artifacts import fingerprint
root=Path.cwd();packet=root/'eval/semantic-citation-implementation/1.1.0';out=root/'runs/semantic-citation-review-2026-09-19'
def read(p):return json.loads(p.read_text())
def digest(p):
 assert not any(x in p.parts for x in ('corpus','clean','.env')) and p.suffix.lower()!='.pdf', str(p)
 return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(mapping,base=root):
 mismatches=[]
 for file,want in mapping.items():
  p=base/file
  actual=digest(p) if p.exists() else 'missing'
  if actual!=want:mismatches.append({'path':str(p),'expected':want,'actual':actual})
 return {'count':len(mapping),'mismatches':mismatches}
preserve=read(packet/'preservation-verification.json');binding=read(packet/'implementation-bindings.json');old=read(root/'eval/semantic-citation-investigation/2026-09-19/bundle-integrity.json');freeze=read(packet/'fixture-freeze.json');baseline=read(packet/'baseline.json')
r={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'ancestor_exit':subprocess.run(['git','merge-base','--is-ancestor',baseline['commit'],'HEAD']).returncode,'original_retained':verify(preserve['original_127_hashes']),'original_inventory_matches':preserve['original_127_hashes']==read(root/'eval/semantic-integration/2026-09-18/retained-artifacts.json')['files'],'prior_investigation':verify(old['files']),'prior_report':verify({old['report']['path']:old['report']['sha256']}),'protected_current':verify(preserve['protected_frozen_current_hashes']),'fixture_freeze':verify(freeze['files'],packet),'implementation_artifacts':verify(read(packet/'artifact-integrity.json')['files']),'implementation_bindings':verify(binding['files'])}
r['binding_values']={'operation':VERSION==binding['operation_version'],'attempt':AV==binding['attempt_version'],'prompt':fingerprint(PROMPT)==binding['prompt_sha256'],'schema':fingerprint(SCHEMA)==binding['schema_sha256'],'runtime':runtime_identity()==binding['runtime_sha256'],'policy':policy_identity()==binding['policy'],'configurations':CONFIGS==binding['configurations']}
# Confirm preserved contracts/review/schema and original runtime directly against Git objects.
paths=['spec/semantic-operation.md','spec/paired-semantic-attempts.md','eval/semantic-integration/2026-09-18/independent-review.json','eval/semantic-integration/2026-09-18/pre-inference-freeze.json','eval/semantic-integration/validate.py']+[str(p.relative_to(root)) for p in (root/'schemas').glob('*.json')]
r['git_preservation']={p:hashlib.sha256(subprocess.check_output(['git','show',baseline['commit']+':'+p])).hexdigest()==digest(root/p) for p in paths}
shared=read(root/'tools/replay-semantic-v1/shared.json');pin=root/'runs/semantic-citation-implementation-1.1.0/pinned-v1'
r['pin_files']=verify(shared['runtime_files'],pin)
r['pin_matches_commit']={p:hashlib.sha256(subprocess.check_output(['git','show',baseline['commit']+':'+p])).hexdigest()==h for p,h in shared['runtime_files'].items()}
r['source_review_inputs']=verify({v['path']:v['sha256'] for v in read(packet/'review/independent-review.json')['exposure']['read_inputs']})
r['wheel']={}
for whl in Path('/private/tmp/hkex-citation-wheel').glob('*.whl'):
 recorded=read(packet/'installed-wheel-verification.json');details={'path':str(whl),'sha256':digest(whl),'matches_recorded_hash':digest(whl)==recorded['wheel_sha256']}
 with zipfile.ZipFile(whl) as z:
  details['policy_included']='hkex_audit/header_support_policy.json' in z.namelist()
  details['runtime_member_matches']={p:hashlib.sha256(z.read('hkex_audit/'+p)).hexdigest()==digest(root/'src/hkex_audit'/p) for p in ['header_support.py','header_support_policy.json','semantic.py','semantic_attempt.py','semantic_cli.py','semantic_transport.py']}
 r['wheel']=details
r['installed_files']=verify({p.name:digest(p) for p in (root/'src/hkex_audit').glob('*') if p.name in ['header_support.py','header_support_policy.json','semantic.py','semantic_attempt.py','semantic_cli.py','semantic_transport.py']},Path('/private/tmp/hkex-citation-installed/hkex_audit'))
(out/'integrity.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ('git_preservation','pin_matches_commit')},indent=2))
