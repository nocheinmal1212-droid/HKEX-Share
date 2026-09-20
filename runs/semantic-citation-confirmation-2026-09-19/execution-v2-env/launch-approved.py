"""One approved frozen launch; owner-directed root .env credential supply, no shell sourcing."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
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
save('authorization.json',{'live_user_instruction':'Approved.','credential_user_instruction':'Check .env at root.',
    'approved_freeze_sha256':DIGEST,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'argv':proposal['argv'],'ceilings':proposal['ceilings'],'case_order':['total','period_groups'],
    'scope':'Use only root .env OPENROUTER_API_KEY as launch environment; no CLI/runtime/request modification; one live confirmation; zero retries'})
checked=subprocess.run([sys.executable,'-I','-B',str(PACKET/'check_freeze.py'),'--freeze',str(PACKET/'freeze.json'),
    '--expected-sha256',DIGEST],cwd=ROOT,env={},capture_output=True,text=True)
save('immediate-prelaunch-check.json',{'returncode':checked.returncode,'stdout':checked.stdout,'stderr':checked.stderr})
if checked.returncode:
    print('Stopped: approved freeze gate failed; no credential access or launch.');raise SystemExit(2)
# Read only the explicitly requested root file. Never source shell code, substitute variables,
# log values, hash credentials, or forward other entries from this file or the host environment.
try:
    fd=os.open(ROOT/'.env',os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'r',encoding='utf-8') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>1048576:raise ValueError('unsupported credential file')
        values=[]
        for line in stream:
            line=line.strip()
            if line.startswith('export '):line=line[7:].lstrip()
            name,sep,value=line.partition('=')
            if sep and name.strip()=='OPENROUTER_API_KEY':
                parts=shlex.split(value,comments=True,posix=True)
                if len(parts)!=1 or not parts[0]:raise ValueError('invalid key entry')
                values.append(parts[0])
    if len(values)!=1:raise ValueError('missing or ambiguous key entry')
    key=values.pop();del values,line,value,parts
except (OSError,ValueError,UnicodeError) as exc:
    save('launch-not-started.json',{'reason':'root .env unavailable or required key entry missing/invalid/ambiguous',
        'error_type':type(exc).__name__,'http_calls':0,'live_output_created':False})
    print('Stopped: root .env did not supply one usable OPENROUTER_API_KEY entry. No calls.')
    raise SystemExit(3)
save('credential-source.json',{'source':'owner-directed root .env','required_key_present':True,
    'values_logged_or_saved':False,'other_environment_entries_forwarded':False,'argv_changed':False})
print('Root .env supplies the required key; freeze gate passed. Starting the single approved launch.',flush=True)
started=time.monotonic()
with (OUT/'launcher.stdout.txt').open('x') as stdout,(OUT/'launcher.stderr.txt').open('x') as stderr:
    proc=subprocess.Popen(proposal['argv'],cwd=proposal['cwd'],env={'OPENROUTER_API_KEY':key},stdout=stdout,stderr=stderr,close_fds=True)
    del key
    code=proc.wait()
save('launcher-exit.json',{'returncode':code,'launcher_wall_seconds':time.monotonic()-started,
    'runtime_total_budget_seconds':600,'live_output':proposal['live_output'],'retries':0})
print(json.dumps({'launch_returncode':code,'live_output':proposal['live_output'],'no_retry':True}))
raise SystemExit(code)
