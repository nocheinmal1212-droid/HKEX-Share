"""Positive/negative checks use disposable copies; live launcher sees no credential."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PACKET=Path(__file__).resolve().parent;ROOT=PACKET.parents[3]
BASE=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19'
OUT=BASE/'freeze-checks-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')

def main():
    OUT.mkdir()
    s=importlib.util.spec_from_file_location('checker',PACKET/'check_freeze.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
    freeze=PACKET/'freeze.json';digest=sha(freeze);positive=c.check(freeze,digest)
    negative=[]
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        tmp=Path(tmp);altered=tmp/'freeze.json'
        altered.write_bytes(freeze.read_bytes()+b' ')
        try:c.check(altered,digest)
        except AssertionError as e:negative.append({'case':'freeze_digest','rejected':str(e)})
        else:raise AssertionError('changed freeze accepted')
        names=[BASE/'prepared-v1/B/runtime-snapshot/src/hkex_audit/semantic.py',
               BASE/'prepared-v1/A/runtime-snapshot/src/hkex_audit/semantic_deadline.py',
               BASE/'prepared-v1/A/runtime-snapshot/src/hkex_audit/semantic_transport.py',
               BASE/'prepared-v1/B/total/primary-request.json',
               BASE/'prepared-v1/A/runtime-snapshot/schemas/evidence.schema.json',
               PACKET/'expectations.json',PACKET/'worker.py',PACKET/'launch-proposal.json',PACKET/'environment.json',PACKET/'observe.py']
        for target in names:
            assert target.is_file(),target
            copy=tmp/'changed';copy.write_bytes(target.read_bytes()+b' ')
            data=read(freeze);expected=data['files'].pop(str(target.relative_to(ROOT)))
            data['files'][str(copy.relative_to(ROOT))]=expected
            altered.write_text(json.dumps(data))
            try:c.check(altered,sha(altered))
            except AssertionError as e:negative.append({'case':str(target.relative_to(ROOT)),'rejected':str(e)})
            else:raise AssertionError('changed member accepted')
        data=read(freeze);data['readiness']='NO_GO_TEST';altered.write_text(json.dumps(data))
        try:c.check(altered,sha(altered))
        except AssertionError as e:negative.append({'case':'not_ready','rejected':str(e)})
        else:raise AssertionError('unready packet accepted')
    proposal=read(PACKET/'launch-proposal.json')
    argv=[digest if v=='APPROVED_FREEZE_SHA256' else v for v in proposal['argv']]
    # Exact launcher path, controlled empty environment: gate passes, missing key stops
    # before output creation and transports. This is not an operational attempt.
    p=subprocess.run(argv,env={},capture_output=True,text=True,timeout=60)
    assert p.returncode==2 and 'Key absent' in p.stdout,(p.stdout,p.stderr)
    assert not Path(proposal['output']).exists()
    assert c.check(freeze,digest)==positive
    put(OUT/'verification-receipt.json',{'freeze_sha256':digest,'members':read(freeze)['members'],
        'positive':positive,'negative_checks':negative,'exact_launch_argv':argv,'ceilings':proposal['ceilings'],
        'credential_absent_launch_check':{'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},
        'live_output_exists':False,'real_http_calls':0,'credential_access_to_real_entries':False,'live_authorized':False})
    print(json.dumps({'freeze_sha256':digest,'members':read(freeze)['members'],'negative_checks':len(negative),
                      'positive_check':'pass','credential_absent_launch_check':'pass','real_http_calls':0}))

if __name__=='__main__':main()
