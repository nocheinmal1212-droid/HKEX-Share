"""Fast offline structural, evaluator, schedule and aggregate budget checks."""
import ast
import base64
from copy import deepcopy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

PACKET=Path(__file__).resolve().parent;ROOT=PACKET.parents[3]
BASE=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19';PREP=BASE/'prepared-v1'
sys.path.insert(0,str(PREP/'A/runtime-snapshot/src'))
from hkex_audit.artifacts import read,write_new,encode
from hkex_audit.semantic import validate_answer
from hkex_audit.semantic_attempt import CONFIGS
from hkex_audit import semantic_deadline as dl
from hkex_audit import semantic_cli as cli

def module(name):
    s=importlib.util.spec_from_file_location(name,PACKET/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def stripped(path):
    tree=ast.parse(path.read_text())
    tree.body=[n for n in tree.body if not (isinstance(n,ast.Assign) and any(getattr(t,'id','') in ('VERSION','PROMPT') for t in n.targets))]
    return ast.dump(tree,include_attributes=False)

def main():
    rows=[];original=ROOT/'src/hkex_audit/semantic.py'
    arms=read(PACKET/'arms.json');cost=Decimal(0);attempts=set()
    for arm,info in arms.items():
        assert stripped(PREP/arm/'runtime-snapshot/src/hkex_audit/semantic.py')==stripped(original)
        for path in info['runtime_files']:
            if path!='src/hkex_audit/semantic.py' or arm=='A':
                assert (ROOT/path).read_bytes()==(PREP/arm/'runtime-snapshot'/path).read_bytes()
        for row in info['requests']:
            assert row['attempt_id'] not in attempts;attempts.add(row['attempt_id'])
            cost+=Decimal(row['reservation_usd'])
    assert len(attempts)==16 and cost==Decimal(read(PACKET/'launch-proposal.json')['full_reservation_usd'])
    rows.append({'check':'only_prompt_and_operation_identity_differ','pass':True,'unique_attempts':16,'reservation_usd':str(cost)})
    observe=module('observe');expected=read(PACKET/'expectations.json')['queries']
    old=ROOT/'runs/semantic-citation-confirmation-2026-09-19/live-v2'
    for ex in expected:
        name=ex['name'];q=read(PREP/'A'/name/'query.json')
        for role in CONFIGS:
            envelope=json.loads(base64.b64decode(read(old/role/name/'response.json')['body_base64']))
            answer=json.loads(envelope['choices'][0]['message']['content'])
            try:validate_answer(q,answer)
            except ValueError as e:assert str(e)=='target support absent'
            else:raise AssertionError('historical failure repaired')
        if name=='total':
            answer={'target_id':ex['target_id'],'state':'selected','contributor_ids':ex['expected_contributor_header_ids'].copy(),'support_refs':ex['required_support_ids'].copy()}
            unit=next(n['id'] for n in q['context']['items'] if n['text']=='港幣百萬元')
            answer['contributor_ids'][0]=unit;answer['support_refs'].append(unit)
            validate_answer(q,answer)
            metrics=observe.components(answer,ex)
            assert not metrics['exact_contributors'] and all(metrics[k] for k in ('target_cited','contributors_cited','groups_cited'))
            rows.append({'check':'unit_plus_lease','host_accepted':True,**metrics,'success':False})
    rows.append({'check':'all_four_originals_still_rejected','pass':True})
    worker=module('worker')
    # Virtual stage probes use the actual experiment controller with explicitly replaced
    # send/subprocess functions. They cannot reach a live transport or a real clock delay.
    for mode in ('between_metadata','between_slots','full_budget'):
        root=Path(tempfile.mkdtemp(prefix='virtual-'+mode+'-',dir=BASE/'diagnostics-v1'));out=root/'experiment'
        clock=[0.];calls=[];slots=[]
        def send(job,prefix,deadline,fixture):
            assert clock[0]<deadline.work_end
            calls.append(job['role']);c=CONFIGS[job['role']]
            body={'data':{'id':c['model'],'endpoints':[{'tag':c['route'],'status':0,'provider_name':c['served_provider'],
                'supported_parameters':['structured_outputs','response_format','temperature','max_tokens'],
                'pricing':{'prompt':'.000005','completion':'.000020'}}]}}
            if mode=='between_metadata':clock[0]=599
            return {'transport_status':'ok','body_base64':base64.b64encode(encode(body)).decode()}
        def run(*a,**k):
            p=json.loads(k['input']);slots.append((p['arm'],p['case']))
            assert p['started']==0 and p['seconds']==600 and not k.get('start_new_session')
            if mode=='between_slots':clock[0]=599
            from types import SimpleNamespace
            return SimpleNamespace(returncode=0,stdout='',stderr='')
        with patch.object(dl.time,'monotonic',lambda:clock[0]),patch.object(worker,'send',send),patch.object(worker.subprocess,'run',run):
            data={'action':'experiment','output':str(out),'started':0,'seconds':600,'offline':True,'fixture':{}}
            try:worker.experiment(data)
            except dl.DeadlineExpired:assert mode!='full_budget'
            else:assert mode=='full_budget'
        assert len(calls)==(1 if mode=='between_metadata' else 2)
        assert len(slots)=={'between_metadata':0,'between_slots':1,'full_budget':8}[mode]
        assert (out/'summary.json').exists()==(mode=='full_budget')
        if mode=='full_budget':
            s=read(out/'summary.json');assert s['http_calls_reserved']==18 and Decimal(s['cost_reserved_usd'])==cost
        rows.append({'check':mode,'mock_metadata_invocations':calls,'slots':slots,'real_http_calls':0})
    write_new(BASE/'checks-v1/edge-checks.json',rows)
    print(json.dumps({'passed':len(rows),'real_http_calls':0}))

if __name__=='__main__':main()
