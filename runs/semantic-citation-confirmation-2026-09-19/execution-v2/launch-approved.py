"""Execute the one approved frozen argv only after its read-only gate passes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
PACKET=ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2'
OUT=Path(__file__).resolve().parent
DIGEST='46c1b25173abf95490caf42b1d589de84237284afde81ce198910f9c9475c0ae'
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
proposal=json.loads((PACKET/'launch-proposal.json').read_text())
assert proposal['nonce']=='live-v2' and not Path(proposal['live_output']).exists()
assert hashlib.sha256((PACKET/'freeze.json').read_bytes()).hexdigest()==DIGEST
save('authorization.json',{'user_instruction':'Approved.','approved_freeze_sha256':DIGEST,
    'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'argv':proposal['argv'],
    'ceilings':proposal['ceilings'],'case_order':['total','period_groups'],
    'retries':0,'scope':'one live confirmation only; no fallback/substitution or automatic rerun'})
checked=subprocess.run([sys.executable,'-I','-B',str(PACKET/'check_freeze.py'),'--freeze',str(PACKET/'freeze.json'),
    '--expected-sha256',DIGEST],cwd=ROOT,env={},capture_output=True,text=True)
save('immediate-prelaunch-check.json',{'returncode':checked.returncode,'stdout':checked.stdout,'stderr':checked.stderr})
if checked.returncode:
    print('Stopped: approved freeze gate failed. No launch.');raise SystemExit(2)
# Only the required credential entry is read, never printed or persisted. No file bootstrap.
key=os.environ.get('OPENROUTER_API_KEY')
if not key:
    save('launch-not-started.json',{'reason':'OPENROUTER_API_KEY absent from launch environment','http_calls':0,'live_output_created':False})
    print('Stopped before launch: OPENROUTER_API_KEY is absent. No calls; reserved output remains unused.')
    raise SystemExit(3)
started=time.monotonic()
with (OUT/'launcher.stdout.txt').open('x') as stdout,(OUT/'launcher.stderr.txt').open('x') as stderr:
    proc=subprocess.Popen(proposal['argv'],cwd=proposal['cwd'],env={'OPENROUTER_API_KEY':key},stdout=stdout,stderr=stderr,close_fds=True)
    del key
    code=proc.wait()
save('launcher-exit.json',{'returncode':code,'launcher_wall_seconds':time.monotonic()-started,
    'runtime_total_budget_seconds':600,'live_output':proposal['live_output'],'retries':0})
print(json.dumps({'launch_returncode':code,'live_output':proposal['live_output'],'no_retry':True}))
raise SystemExit(code)
