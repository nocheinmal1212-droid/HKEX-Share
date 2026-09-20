"""Verify historical bytes without rewriting their hashes; enumerate intentional current deltas."""
import os
os.environ={}
import difflib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[4]
PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,sha,write_new
OLD=PACKET.with_name('preflight-v1')
SNAP=ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v1/runtime-snapshot'
expected_changes={'src/hkex_audit/semantic_cli.py','src/hkex_audit/semantic_attempt.py','src/hkex_audit/semantic_transport.py','README.md','PLAN.md','docs/development-logs.md'}
retained={p:SNAP/p for p in expected_changes if p.startswith('src/')}
retained.update({p:PACKET/'prior-authorities'/Path(p).name for p in expected_changes if not p.startswith('src/')})
assert sha((OLD/'freeze.json').read_bytes())=='f98cab8947112698dc2e8d58ba30441dc6d8f40f3d1a35125994ce50a34e7643'
rows=[]
for label,path,base in [
    ('no_go_freeze',OLD/'freeze.json',ROOT),
    ('correction_bindings',ROOT/'eval/semantic-citation-implementation/1.1.1/implementation-bindings.json',ROOT),
    ('correction_artifacts',ROOT/'eval/semantic-citation-implementation/1.1.1/artifact-integrity.json',ROOT),
    ('fixture_freeze',ROOT/'eval/semantic-citation-implementation/1.1.1/fixture-freeze.json',ROOT/'eval/semantic-citation-implementation/1.1.1'),
    ('original_retained',ROOT/'eval/semantic-integration/2026-09-18/retained-artifacts.json',ROOT),
    ('investigation_members',ROOT/'eval/semantic-citation-investigation/2026-09-19/bundle-integrity.json',ROOT)]:
    files=read(path)['files'];deltas=[];unchanged=0
    for p,h in files.items():
        actual=base/p
        if sha(actual.read_bytes())==h:unchanged+=1;continue
        key=str(actual.relative_to(ROOT))
        assert key in expected_changes,(label,key)
        assert sha(retained[key].read_bytes())==h,(label,key,'retained mismatch')
        deltas.append({'path':key,'old_sha256':h,'current_sha256':sha(actual.read_bytes()),'retained_original':str(retained[key].relative_to(ROOT))})
    rows.append({'label':label,'members':len(files),'unchanged_current_members':unchanged,'intentional_current_deltas':deltas,'all_original_bytes_verified':True})
identity=read(PACKET/'execution-identity.json')
assert all(sha((ROOT/p).read_bytes())==h for p,h in identity['runtime_files'].items())
assert all(sha((ROOT/identity['snapshot']/p).read_bytes())==h for p,h in identity['runtime_files'].items())
for n in ('live-v1','live-v2'):assert not (ROOT/'runs/semantic-citation-confirmation-2026-09-19'/n).exists()
subprocess.run(['git','merge-base','--is-ancestor','e8000e2c001983f1f65fac75de97945c628a2287','HEAD'],check=True,env={},capture_output=True)
diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True,env={});assert diff.returncode==0,diff.stdout+diff.stderr
patch=[]
for p in sorted(expected_changes):
    patch.extend(difflib.unified_diff(retained[p].read_text().splitlines(True),(ROOT/p).read_text().splitlines(True),fromfile='before/'+p,tofile='after/'+p))
for p in ('src/hkex_audit/semantic_deadline.py','spec/paired-semantic-attempts-1.2.md','tests/test_semantic_deadline.py'):
    patch.extend(difflib.unified_diff([], (ROOT/p).read_text().splitlines(True),fromfile='/dev/null',tofile='after/'+p))
(PACKET/'correction.patch').write_text(''.join(patch))
write_new(PACKET/'preservation-verification.json',{'inventories':rows,'current_runtime_files':len(identity['runtime_files']),
    'old_runtime_snapshot_members_verified':33,'new_runtime_snapshot_members_verified':34,
    'git_diff_check':'pass','ancestry_verified':True,'old_freeze_rehashed':False,'live_paths_absent':True,
    'historical_claim':'0/4 complete frozen support; three research truncations; invalid research abstention'})
write_new(PACKET/'implementation-bindings.json',{'batch':identity['batch'],'attempt':identity['attempt'],'operation':identity['operation'],
    'runtime_identity':identity['runtime_identity'],'configurations_unchanged':True,'policy':identity['policy'],
    'files':{p:sha((ROOT/p).read_bytes()) for p in [*identity['runtime_files'],'spec/paired-semantic-attempts-1.2.md','tests/test_semantic_deadline.py']},
    'review':'same-agent inspection; no independent approval','historical_replay':'retained snapshots only; no rebinding'})
print(json.dumps({'inventories':[{'label':r['label'],'members':r['members'],'current_deltas':len(r['intentional_current_deltas'])} for r in rows]}))
