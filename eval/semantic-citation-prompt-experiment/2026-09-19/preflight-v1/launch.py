"""One explicitly approved experiment only; key from environment, no dotenv/bootstrap."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

PACKET=Path(__file__).resolve().parent
ROOT=PACKET.parents[3]
PREP=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19/prepared-v1'
sys.path.insert(0,str(PREP/'A/runtime-snapshot/src'))
from hkex_audit.semantic_deadline import Deadline,supervise,DeadlineExpired

def main():
    started=time.monotonic()
    p=argparse.ArgumentParser();p.add_argument('--expected-sha256',required=True);a=p.parse_args()
    deadline=Deadline(started,900)
    gate=supervise([sys.executable,'-I','-B',str(PACKET/'check_freeze.py'),
                    '--expected-sha256',a.expected_sha256],{},deadline,env={})
    if gate['timed_out'] or gate['returncode']!=0:
        print(gate['stdout']);return 2
    # No other host environment entries are inspected or forwarded.
    key=os.environ.get('OPENROUTER_API_KEY')
    if not key: print('Key absent; no operational output or HTTP calls.');return 2
    proposal=json.loads(gate['stdout'])['proposal']
    payload={'action':'experiment','started':started,'seconds':900,'output':proposal['output'],'offline':False}
    result=supervise([sys.executable,'-I','-B',str(PACKET/'worker.py')],payload,deadline,
                     env={'OPENROUTER_API_KEY':key})
    del key
    success=not result['timed_out'] and result['returncode']==0
    receipt={**result,'state':'finished' if success else 'interrupted_or_failed',
             'freeze_sha256':a.expected_sha256,'total_ceiling_satisfied':time.monotonic()<deadline.end,
             'historical_calls':'per-transport records; missing returns are unknown, not zero'}
    writer="import json,sys,pathlib;p=json.load(sys.stdin);d=pathlib.Path(p['output']);assert not any(x.is_symlink() for x in [d,*d.parents]);assert json.loads((d/'launch.json').read_text())['started_monotonic']==p['started'];(d/'supervisor.json').open('x').write(json.dumps(p['receipt']))"
    receipt_deadline=Deadline(started,900);receipt_deadline.work_end=deadline.end-.05
    try:
        published=supervise([sys.executable,'-I','-B','-c',writer],
            {'output':proposal['output'],'started':started,'receipt':receipt},receipt_deadline,env={})
    except DeadlineExpired:return 2
    return 0 if success and published['returncode']==0 and not published['timed_out'] else 2

if __name__=='__main__':raise SystemExit(main())
