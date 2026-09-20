"""Credential-only bootstrap; isolated worker has no .env or evaluator access."""
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('--preflight',action='store_true');a=p.parse_args()
stage=Path('/private/tmp/audit-model-selection-2026-09-17-'+a.batch)
out=ROOT/'runs/milestone2/model-selection-2026-09-17'/a.batch/'attempts'
env={'PATH':'/usr/bin:/bin'}
if not a.preflight:
 key=os.environ.get('OPENROUTER_API_KEY')
 if not key:
  for line in (ROOT/'.env').read_text().splitlines():
   line=line.strip().removeprefix('export ').lstrip();name,sep,value=line.partition('=')
   if sep and name.strip()=='OPENROUTER_API_KEY':key=value.strip().strip('\"\'');break
 if not key:raise SystemExit('Credential unavailable')
 env['OPENROUTER_API_KEY']=key
cmd=['/usr/bin/sandbox-exec','-f',str(stage/'sandbox.sb'),str(Path(sys.executable).resolve()),'-I','-B',str(stage/'model_selection_worker_v2.py'),'--manifest',str(stage/'manifest.json'),'--out',str(out)]
if a.preflight:cmd+=['--preflight']
raise SystemExit(subprocess.run(cmd,cwd=stage,env=env,close_fds=True).returncode)
