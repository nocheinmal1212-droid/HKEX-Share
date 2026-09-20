"""Additional offline boundary checks; controlled environments and authored replacements only."""
import os
os.environ={}
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit import semantic_cli as cli, semantic_transport as wire, semantic_deadline as dl
from hkex_audit.artifacts import read,write_new
OUT=ROOT/'runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2/edge-checks-controlled'
OUT.mkdir()
# After queuing and after DNS/bootstrap: no HTTP operation may start on an expired job.
rows=[]
for mode in ('entry','after_dns'):
    clock=[10. if mode=='entry' else 0.]
    job={'mode':'metadata','role':'primary','deadline_monotonic':9.}
    def dns(*args,**kwargs):
        clock[0]=10.;return [(None,None,None,None,('127.0.0.1',443))]
    class Connection:
        def __init__(self,*args,**kwargs):pass
        def request(self,*args,**kwargs):raise AssertionError('post-expiry HTTP request')
    import io
    output=io.StringIO()
    with patch.object(wire.sys,'stdin',io.StringIO(json.dumps(job))),patch.object(wire.sys,'stdout',output),patch.object(wire.time,'monotonic',lambda:clock[0]),patch.object(wire.os,'environ',{'OPENROUTER_API_KEY':'INERT-AUTHORED-FIXTURE'}),patch.object(wire.ssl,'create_default_context',lambda:None),patch.object(wire.socket,'getaddrinfo',dns),patch.object(wire,'install_transport_guard',lambda _:None),patch.object(wire.http.client,'HTTPSConnection',Connection):
        wire.main()
    result=json.loads(output.getvalue());assert result=={'transport_status':'budget_exhausted','request_started':False}
    rows.append({'mode':mode,**result})
# Launch-journal failure proves zero; timeout return without an HTTP marker remains unknown.
with patch.object(cli,'write_new',side_effect=OSError('authored write failure')),patch.object(cli,'transport',side_effect=AssertionError('transport after journal failure')):
    result=cli.send_transport({'mode':'metadata','role':'primary'},OUT/'journal-failure',dl.Deadline(time.monotonic(),10))
assert result['request_started'] is False
# Cleanup receipt writer itself stalls: same original ceiling, no false success/receipt.
args=type('Args',(),{})()
args.selection=ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v2/selection.json'
args.queries=ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v2/queries.json'
args.output=OUT/'receipt-cancel';args.max_seconds=2;args.max_cost='8';args.max_http_calls=6;args.max_role_calls=2;args.env_root=None
actual=cli.supervise
# Use a namespace with instance fields for the actual launch serialization.
from types import SimpleNamespace
args=SimpleNamespace(**{k:getattr(args,k) for k in ('selection','queries','output','max_seconds','max_cost','max_http_calls','max_role_calls','env_root')})
def supervise(argv,payload,deadline,env=None):
    if 'receipt' in payload:
        code='import time;time.sleep(120)'
    else:
        code="import json,sys,pathlib;p=json.load(sys.stdin);d=pathlib.Path(p['output']);d.mkdir();(d/'launch.json').write_text(json.dumps({'started_monotonic':p['started']}))"
    return actual([sys.executable,'-I','-B','-c',code],payload,deadline,env={})
start=time.monotonic()
with patch.object(cli,'supervise',supervise):code=cli.run(args)
elapsed=time.monotonic()-start
assert code==2 and elapsed<=2.15 and not (args.output/'supervisor.json').exists()
# A pre-existing output is rejected and cannot acquire a false supervisor receipt.
existing=OUT/'existing';existing.mkdir();args.output=existing;args.max_seconds=3
assert cli.run(args)==2 and list(existing.iterdir())==[]
write_new(OUT/'results.json',{'transport_expiry':rows,'journal_failure_known_zero':True,
    'receipt_cancellation':{'returncode':code,'elapsed_seconds':elapsed,'ceiling_seconds':2,'test_tolerance':.15},
    'preexisting_output_untouched':True,'real_http_calls':0})
print('Transport entry/DNS expiry, journal failure, receipt cancellation and existing-output protection passed.')
