"""Read-only, evaluator-side prelaunch binding check. Never launches or regenerates files.

Default mode additionally requires a ready packet. --bindings-only is diagnostic
and cannot authorize inference. A failed check must stop any proposed launch.
"""
import os
os.environ = {}
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read, sha, fingerprint
from hkex_audit import semantic, semantic_cli, semantic_attempt, header_support


def verify_hash(path, expected):
    assert not path.is_symlink(), 'symlink binding: '+str(path)
    assert sha(path.read_bytes()) == expected, 'changed binding: '+str(path)


def check(freeze_path, expected_sha, require_ready=True):
    verify_hash(freeze_path,expected_sha)
    freeze = read(freeze_path)
    for p,h in freeze['files'].items(): verify_hash(ROOT/p,h)
    identity = read(PACKET/'execution-identity.json')
    actual = {str(p.relative_to(ROOT)) for base in ('src','schemas') for p in (ROOT/base).rglob('*')
              if p.is_file() and p.suffix in ('.py','.json')}
    assert actual == set(identity['runtime_files'])-{'pyproject.toml'}, 'runtime inventory drift'
    for p,h in identity['runtime_files'].items(): verify_hash(ROOT/p,h)
    spec = importlib.util.spec_from_file_location('environment_binding',PACKET/'prepare.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    assert helper.environment() == identity['environment'], 'environment/dependency drift'
    for name,p in identity['modules'].items():
        assert str(Path(sys.modules[name].__file__).resolve())==p, 'module path drift'
    assert semantic.VERSION==identity['operation'] and semantic_attempt.VERSION==identity['attempt']
    assert semantic_cli.BATCH_VERSION==identity['batch']
    assert header_support.policy_identity()==identity['policy']
    assert semantic_cli.runtime_identity()==identity['runtime_identity']
    assert sha(semantic.PROMPT.encode())==identity['prompt_sha256']
    assert fingerprint(semantic.SCHEMA)==identity['schema_sha256']
    proposal = read(PACKET/'launch-proposal.json')
    assert not Path(proposal['live_output']).exists(), 'reserved live output already exists'
    assert Path(proposal['live_output']).name==proposal['nonce']
    prep = ROOT/freeze['prepared_path']
    selection = semantic_cli.normalized_selection(prep/'selection.json')
    specs = read(prep/'queries.json')
    assert [s['name'] for s in specs]==['total','period_groups']
    regenerated = semantic_cli.isolated('prepare_worker',{'selection':selection,'specs':specs})
    for q in regenerated['queries']:
        name=q['selection']['name']
        assert q==read(prep/name/'query.json') and q['gate']=='eligible', 'projection drift'
        for role in semantic_attempt.CONFIGS:
            assert semantic_attempt.request(q,role,proposal['nonce'])==read(prep/name/(role+'-request.json')), 'request drift'
    if require_ready:
        assert freeze['readiness']=='GO_PENDING_EXPLICIT_LIVE_APPROVAL', 'NO-GO: '+freeze['blocking_reason']
    return {'bindings_verified':True,'live_authorized':False,'ready':freeze['readiness'],
            'queries':['total','period_groups'],'model_calls':0,'metadata_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',type=Path,required=True)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--bindings-only',action='store_true')
    args=parser.parse_args()
    try:
        print(json.dumps(check(args.freeze,args.expected_sha256,not args.bindings_only)))
    except (AssertionError,OSError,ValueError) as exc:
        print(json.dumps({'bindings_or_readiness_failed':str(exc),'launch_allowed':False}))
        raise SystemExit(2)
