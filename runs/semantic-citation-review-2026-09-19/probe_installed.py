from pathlib import Path
import json,subprocess,sys,hashlib
root=Path.cwd();out=root/'runs/semantic-citation-review-2026-09-19';dev=root/'runs/semantic-citation-implementation-1.1.0/development'
selection=json.loads((dev/'isolation-source/selection.json').read_text());spec=json.loads((root/'eval/semantic-citation-implementation/1.1.0/fixtures/S01_actual_sibling_outer/selection.json').read_text())
dest=out/'installed-consumption';dest.mkdir()
payload={'selection':selection,'spec':spec,'batch':str(dev/'authored-accepted'),'output':str(dest),'nonce':'authored'}
bootstrap="""import sys,json
sys.path.insert(0,'/private/tmp/hkex-citation-installed')
def offline(event,args):
 if event.startswith('socket.'):raise PermissionError('offline review')
sys.addaudithook(offline)
from hkex_audit.semantic_cli import consume_worker
consume_worker(json.load(sys.stdin))
"""
p=subprocess.run([sys.executable,'-I','-B','-c',bootstrap],input=json.dumps(payload),text=True,capture_output=True,env={'PATH':'/usr/bin:/bin'},timeout=60)
r={'returncode':p.returncode,'stderr':p.stderr,'installed_root':'/private/tmp/hkex-citation-installed','reinstalled':False,'network_calls':0}
if p.returncode==0:
 r['byte_identity']={n:(dest/(n+'.json')).read_bytes()==(dev/'authored-accepted/operational'/(n+'.json')).read_bytes() for n in ['annotations','provenance']}
 r['consumption']=json.loads((dest/'consumption.json').read_text())
(out/'installed-probe.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print({k:v for k,v in r.items() if k!='consumption'})
