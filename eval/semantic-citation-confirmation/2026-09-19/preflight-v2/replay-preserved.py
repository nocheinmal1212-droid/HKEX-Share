"""Offline zero-call reproduction using only verified retained execution snapshots."""
import os
os.environ={}
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,sha,write_new
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
OUT=BASE/'snapshot-replay-v2';OUT.mkdir()
rows=[]
for version,batch in [('v1',BASE/'diagnostics-v1/batch-baseline'),('v2',BASE/'diagnostics-v2-followup/batch-baseline')]:
    identity=read(ROOT/('eval/semantic-citation-confirmation/2026-09-19/preflight-'+version+'/execution-identity.json'))
    prep=BASE/('prepared-'+version);snapshot=prep/'runtime-snapshot'
    assert all(sha((snapshot/p).read_bytes())==h for p,h in identity['runtime_files'].items())
    output=OUT/version
    bootstrap='import os,sys;os.environ={};sys.path.insert(0,sys.argv[1]);from hkex_audit.semantic_cli import main;raise SystemExit(main(sys.argv[2:]))'
    argv=[sys.executable,'-I','-B','-c',bootstrap,str(snapshot/'src'),'replay','--selection',str(prep/'selection.json'),'--batch',str(batch),'--output',str(output)]
    proc=subprocess.run(argv,capture_output=True,text=True,env={},timeout=120)
    write_new(OUT/(version+'-process.json'),{'argv':argv,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    assert proc.returncode==0,proc.stderr
    for name in ('total','period_groups'):
        assert all((output/name/f).read_bytes()==(batch/'operational'/name/f).read_bytes() for f in ('annotations.json','provenance.json'))
    assert read(output/'summary.json')['model_calls']==0
    rows.append({'snapshot':str(snapshot),'snapshot_members':len(identity['runtime_files']),'cases':2,'annotation_provenance_bytes_identical':True,'new_model_calls':0})
write_new(OUT/'verification.json',rows)
print(json.dumps(rows))
