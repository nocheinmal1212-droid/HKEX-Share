"""Read-only prelaunch gate. Rejection never regenerates an approved artifact."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET=Path(__file__).resolve().parent
ROOT=PACKET.parents[3]

def read(p):return json.loads(p.read_bytes())
def verify(p,h):
    assert not any(x.is_symlink() for x in (p,*p.parents)), 'symlink: '+str(p)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h,'changed binding: '+str(p)

def check(path,digest,ready=True):
    verify(path,digest);freeze=read(path)
    for name,h in freeze['files'].items():verify(ROOT/name,h)
    proposal=read(PACKET/'launch-proposal.json')
    assert not Path(proposal['output']).exists(),'reserved live output exists'
    assert Path(proposal['output']).name==proposal['nonce']
    spec=importlib.util.spec_from_file_location('original_environment_probe',ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2/prepare.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.environment()==read(PACKET/'environment.json'),'interpreter/dependency drift'
    prep=ROOT/freeze['prepared_path']
    for arm,info in read(PACKET/'arms.json').items():
        actual={str(p.relative_to(prep/arm/'runtime-snapshot')) for p in (prep/arm/'runtime-snapshot').rglob('*') if p.is_file()}
        assert actual==set(info['runtime_files']),'snapshot inventory drift'
        for name,h in info['runtime_files'].items():verify(prep/arm/'runtime-snapshot'/name,h)
    if ready:assert freeze['readiness']=='GO_PENDING_EXPLICIT_LIVE_APPROVAL','packet not ready'
    return {'bindings_verified':True,'model_calls':0,'metadata_calls':0,'live_authorized':False,'proposal':proposal}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True)
    p.add_argument('--freeze',type=Path,default=PACKET/'freeze.json');p.add_argument('--bindings-only',action='store_true')
    a=p.parse_args()
    try: print(json.dumps(check(a.freeze,a.expected_sha256,not a.bindings_only)))
    except (AssertionError,OSError,ValueError) as exc:
        print(json.dumps({'launch_allowed':False,'reason':str(exc)}));raise SystemExit(2)
