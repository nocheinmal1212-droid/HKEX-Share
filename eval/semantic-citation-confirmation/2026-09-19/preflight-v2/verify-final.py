"""Offline positive/negative rehearsal, using disposable altered copies only."""
import os
os.environ={}
import importlib.util
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,sha,write_new,encode
spec=importlib.util.spec_from_file_location('checker',PACKET/'check_freeze.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
OUT=BASE/'freeze-checks-v2';OUT.mkdir()
f=PACKET/'freeze.json';digest=sha(f.read_bytes())
positive=c.check(f,digest)
negative=[]
with tempfile.TemporaryDirectory(dir=OUT) as tmp:
    tmp=Path(tmp)
    altered=tmp/'freeze.json';altered.write_bytes(f.read_bytes()+b' ')
    try:c.check(altered,digest)
    except AssertionError as e:negative.append({'case':'changed_freeze','rejected':True,'reason':str(e)})
    else:raise AssertionError('changed freeze accepted')
    for target in ('src/hkex_audit/semantic_deadline.py','src/hkex_audit/semantic_cli.py','src/hkex_audit/semantic_transport.py',
                   'runs/semantic-citation-confirmation-2026-09-19/prepared-v2/total/primary-request.json',
                   'eval/semantic-citation-confirmation/2026-09-19/preflight-v2/evaluate.py'):
        copy=tmp/'changed-member';copy.write_bytes((ROOT/target).read_bytes()+b' ')
        frozen=read(f);expected=frozen['files'].pop(target)
        frozen['files'][str(copy.relative_to(ROOT))]=expected
        altered.write_bytes(encode(frozen))
        try:c.check(altered,sha(altered.read_bytes()))
        except AssertionError as e:negative.append({'case':target,'rejected':True,'reason':str(e)})
        else:raise AssertionError('changed member accepted: '+target)
    # Known-no-go readiness remains fail closed even with a self-consistent diagnostic copy.
    frozen=read(f);frozen['readiness']='NO_GO_TEST';frozen['blocking_reason']='authored readiness negative'
    altered.write_bytes(encode(frozen))
    try:c.check(altered,sha(altered.read_bytes()))
    except AssertionError as e:negative.append({'case':'not_ready','rejected':True,'reason':str(e)})
    else:raise AssertionError('no-go readiness accepted')
assert not (BASE/'live-v1').exists() and not (BASE/'live-v2').exists()
# Recheck all final bindings after the negative probes, without any amendment.
assert all(sha((ROOT/p).read_bytes())==h for p,h in read(f)['files'].items())
write_new(OUT/'verification-receipt.json',{'freeze_sha256':digest,'members':read(f)['members'],
    'positive_default_check':positive,'negative_checks':negative,'all_final_bound_bytes_rechecked':True,
    'live_output':str(BASE/'live-v2'),'nonce':'live-v2','live_paths_nonexistent':True,
    'metadata_calls':0,'provider_calls':0,'live_authorized':False,
    'ceilings':read(PACKET/'launch-proposal.json')['ceilings'],
    'requirement':'Repeat the default check with the explicitly approved digest immediately before any future launch; no automatic execution.'})
print(digest)
print('Default readiness/bindings pass; seven negatives rejected; no live authorization or calls.')
