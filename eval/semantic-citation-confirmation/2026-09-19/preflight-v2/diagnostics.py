"""Authored offline diagnostics. Every external transport is replaced; no live path use."""
import os
os.environ = {}
import base64
from copy import deepcopy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
PREP = ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v2'
OUT = ROOT/'runs/semantic-citation-confirmation-2026-09-19/diagnostics-v2-followup'
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit import semantic_cli as cli
from hkex_audit import semantic_deadline as deadline_module
from hkex_audit.artifacts import read, write_new, encode, sha
from hkex_audit.semantic import project
from hkex_audit.semantic_attempt import request, dispatch, replay, Store, CONFIGS, FILES
module_spec = importlib.util.spec_from_file_location('new_evaluator',PACKET/'evaluate.py')
evaluator = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(evaluator)

EXPECT = {e['name']:e for e in read(PACKET/'expectations.json')['queries']}
QUERIES = {n:read(PREP/n/'query.json') for n in EXPECT}
SELECTION = read(PREP/'selection.json')
PREPARED = read(PREP/'preparation.json')


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    write_new(path,value)


def answer(name):
    ex = EXPECT[name]
    return {'target_id':ex['target_id'],'state':'selected',
            'contributor_ids':ex['expected_contributor_header_ids'][:],
            'support_refs':ex['required_support_ids'][:]}


def response(a,role,finish='stop',wrong_identity=False):
    body = {'model':CONFIGS[role]['model'] if not wrong_identity else 'authored-wrong-model',
            'provider':CONFIGS[role]['served_provider'],'id':'AUTHORED-DIAGNOSTIC-NOT-MODEL',
            'choices':[{'finish_reason':finish,'message':{'content':json.dumps(a)}}],
            'usage':{'prompt_tokens':10,'completion_tokens':10,'cost':0.0001}}
    return {'transport_status':'ok','request_started':True,'body_base64':base64.b64encode(encode(body)).decode()}


def metadata(role,mode):
    c = CONFIGS[role]
    ep = {'tag':c['route'],'status':0,'provider_name':c['served_provider'],
          'supported_parameters':['structured_outputs','response_format','temperature','max_tokens'],
          'pricing':{'prompt':'0.000005','completion':'0.000020','request':'0'}}
    data = {'id':c['model'],'endpoints':[ep]}
    if mode == 'route_missing': data['endpoints'] = []
    if mode == 'metadata_identity': data['id'] = 'authored-wrong-model'
    if mode == 'over_price': ep['pricing']['prompt'] = '0.000006'
    if mode == 'metadata_timeout': return {'transport_status':'timeout'}
    return {'transport_status':'ok','request_started':True,'body_base64':base64.b64encode(encode({'data':data})).decode()}


def consume(batch,name,dest):
    dest.mkdir(parents=True)
    cli.isolated('consume_worker',{'selection':SELECTION,'spec':QUERIES[name]['selection'],
        'batch':str(batch),'output':str(dest),'nonce':batch.name})
    log = read(dest/'consumption.json')
    assert log['model_calls']==0 and not log['adapter_imported']
    assert not any('/research/' in x.get('path','') or '/eval/' in x.get('path','') for x in log['access_attempts'])
    return tuple((dest/f).read_bytes() for f in ('annotations.json','provenance.json'))


def budget_batch(mode,real_consumer=False):
    out = OUT/('batch-'+mode)
    clock = [0.0]
    calls = []
    original_isolated, original_paired = cli.isolated,cli.paired
    def isolated(function,payload,timeout=180):
        if function == 'prepare_worker':
            return PREPARED
        if real_consumer: return original_isolated(function,payload,timeout=timeout)
        return {'outcome':'authored-budget-control-only'}
    def transport(job,timeout=60):
        calls.append({'mode':job['mode'],'role':job['role'],'virtual_time':clock[0]})
        if job['mode'] == 'metadata':
            return metadata(job['role'],mode)
        target = json.loads(job['payload']['messages'][1]['content'])['target_id']
        name = next(n for n,e in EXPECT.items() if e['target_id'] == target)
        assert job['payload'] == request(QUERIES[name],job['role'],out.name)['payload']
        return response(answer(name),job['role'])
    def paired(*args,**kwargs):
        return original_paired(*args,**kwargs)
    args = SimpleNamespace(selection=PREP/'selection.json',queries=PREP/'queries.json',output=out,
        max_http_calls=3 if mode=='http_cap' else 6,max_role_calls=1 if mode=='role_cap' else 2,
        max_seconds=600,max_cost=Decimal('.01') if mode=='cost_cap' else Decimal('8'),env_root=None)
    with patch.object(cli,'isolated',isolated), patch.object(cli,'paired',paired), patch.object(cli,'transport',transport), \
         patch.object(cli.os,'environ',{'OPENROUTER_API_KEY':'INERT-AUTHORED-FIXTURE'}), \
         patch.object(cli,'time',SimpleNamespace(monotonic=lambda:clock[0])), \
         patch.object(deadline_module,'time',SimpleNamespace(monotonic=lambda:clock[0])):
        out.mkdir(parents=True)
        assert cli.run_body(args,cli.Deadline(0,600))==0
    summary = read(out/'summary.json')
    result = {'mode':mode,'authored_only':True,'actual_http_calls':0,'mock_calls':calls,
              'dispatcher_summary':summary,'virtual_elapsed_from_run_entry':clock[0]}
    assert summary['http_calls_reserved'] <= args.max_http_calls
    assert all(v<=args.max_role_calls for v in summary['completion_calls_reserved'].values())
    assert Decimal(summary['cost_reserved_usd']) <= args.max_cost
    if mode == 'baseline':
        assert len(calls)==6 and summary['completion_calls_reserved']=={'primary':2,'research':2}
        evaluation = evaluator.evaluate_batch(out,authored=True)
        assert evaluation['primary_successes']==2 and evaluation['research_successes']==2
        put(OUT/'baseline-evaluation.json',evaluation)
    if mode in ('route_missing','metadata_identity','over_price','metadata_timeout','cost_cap'):
        assert all(c['mode']=='metadata' for c in calls)
    put(OUT/('budget-'+mode+'.json'),result)
    print('budget diagnostic:',mode,len(calls),clock[0],flush=True)
    return result


def case_matrix():
    variants = [('total','missing_group'),('period_groups','missing_group'),('period_groups','wrong_period'),
                ('total','contradictory_abstention'),('total','timeout'),('total','truncation'),
                ('total','schema_invalid'),('total','identity_mismatch'),('total','unit_plus_lease'),('total','abstention')]
    rows = []
    for name,mode in variants:
        batch = OUT/('case-'+name+'-'+mode)
        a = answer(name)
        if mode=='missing_group': a['support_refs'].remove(EXPECT[name]['required_support_ids'][-1])
        if mode=='wrong_period':
            a['contributor_ids'] = [n['id'] for n in QUERIES[name]['context']['items']
                                    if n['kind']=='cell' and n['row']==1 and n['column'] in (5,6,7)]
            assert len(a['contributor_ids'])==3
            group = next(n['id'] for n in QUERIES[name]['context']['items'] if n['text']=='2024')
            a['support_refs'] += a['contributor_ids'] + [group]
        if mode in ('contradictory_abstention','abstention'): a['state']='ambiguous'
        if mode=='abstention': a['contributor_ids']=[]
        if mode=='unit_plus_lease':
            unit = next(n['id'] for n in QUERIES[name]['context']['items'] if n['text']=='港幣百萬元')
            a['contributor_ids'][0]=unit
            a['support_refs'].append(unit)
        if mode=='schema_invalid': a['unexpected']='authored-invalid'
        raw = {'transport_status':'timeout'} if mode=='timeout' else response(a,'primary',
                finish='length' if mode=='truncation' else 'stop',wrong_identity=mode=='identity_mismatch')
        for role in CONFIGS:
            d = batch/role/name;d.mkdir(parents=True)
            chosen = raw if role=='primary' else response(answer(name),role)
            dispatch(QUERIES[name],request(QUERIES[name],role,batch.name),lambda _,v=chosen:v,Store(d))
        evaluated = evaluator.evaluate_store(QUERIES[name],EXPECT[name],batch/'primary'/name,'primary',batch.name)
        assert evaluated['success'] is False
        assert evaluator.evaluate_store(QUERIES[name],EXPECT[name],batch/'research'/name,'research',batch.name)['success']
        expected_host = {'timeout':'timeout','truncation':'truncation','identity_mismatch':'identity_mismatch',
                         'unit_plus_lease':'accepted','abstention':'abstained'}.get(mode,'invalid_output')
        assert evaluated['host_state']==expected_host,(mode,evaluated)
        if mode=='unit_plus_lease':
            assert evaluated['schema_valid'] and evaluated['required_source_support_present']
            assert evaluated['exact_reviewed_contributors_and_state'] is False
        if mode=='missing_group':
            assert evaluated['exact_reviewed_contributors_and_state'] is True
            assert evaluated['required_source_support_present'] is False
        persisted = consume(batch,name,batch/'operational'/name)
        annotations = json.loads(persisted[0])
        assert len(annotations)==int(mode in ('unit_plus_lease','abstention'))
        if mode=='abstention': assert annotations[0]['links']==[]
        rows.append({'case':name,'variant':mode,'evaluation':evaluated,'annotation_count':len(annotations),
                     'diagnostic_path':str(batch.relative_to(ROOT))})
        print('case diagnostic:',name,mode,evaluated['host_state'],flush=True)
    put(OUT/'case-matrix.json',rows)


def role_isolation():
    baseline = OUT/'batch-baseline'
    records = []
    for variant in ('research_missing','research_corrupt','primary_corrupt'):
        dest = OUT/('isolation-'+variant)
        shutil.copytree(baseline,dest)
        # Requests remain bound to original nonce; the copy is not a new attempt.
        if variant=='research_missing': shutil.rmtree(dest/'research')
        elif variant=='research_corrupt':
            for name in EXPECT: (dest/'research'/name/'completion.json').write_bytes(b'{')
        else:
            for name in EXPECT: (dest/'primary'/name/'completion.json').write_bytes(b'{')
        for name in EXPECT:
            out = dest/'checked'/name;out.mkdir(parents=True)
            cli.isolated('consume_worker',{'selection':SELECTION,'spec':QUERIES[name]['selection'],
                'batch':str(dest),'output':str(out),'nonce':baseline.name})
            r = cli.isolated('research_replay_worker',{'selection':SELECTION,'spec':QUERIES[name]['selection'],
                'batch':str(dest),'nonce':baseline.name})
            if variant.startswith('research'):
                assert all((out/f).read_bytes()==(baseline/'operational'/name/f).read_bytes()
                           for f in ('annotations.json','provenance.json'))
                assert r['result']['state']=='incomplete_attempt'
            else:
                assert read(out/'annotations.json')==[]
                assert r['result']['validation']['state']=='accepted'
            log = read(out/'consumption.json')
            assert log['model_calls']==0 and not any('/research/' in x.get('path','') for x in log['access_attempts'])
            assert r['result']['model_calls']==0
            records.append({'variant':variant,'name':name,'primary':read(out/'provenance.json')['outcome'],
                            'research':r['result'].get('validation',{}).get('state',r['result'].get('state')),
                            'primary_bytes_identical':variant.startswith('research'),'replay_model_calls':0})
        print('role isolation:',variant,flush=True)
    put(OUT/'role-isolation.json',records)


def main():
    OUT.mkdir()
    put(OUT/'diagnostic-identity.json',{'authored_only':True,'model_results':False,'live_path_used':False,
        'probe_plan_sha256':sha((PACKET/'probe-plan.md').read_bytes()),
        'expectations_sha256':sha((PACKET/'expectations.json').read_bytes()),'external_calls':0})
    budget_batch('baseline',real_consumer=True)
    for mode in ('route_missing','metadata_identity','over_price','metadata_timeout','cost_cap','http_cap','role_cap'):
        budget_batch(mode)
    case_matrix()
    role_isolation()
    # Blank/G3/G4r2/G5 controls are cited retained evidence; no added live case.
    assert not Path(read(PACKET/'launch-proposal.json')['live_output']).exists()
    print('Authored budget/evaluator/isolation diagnostics complete; deadline probes are separate.',flush=True)


if __name__=='__main__': main()
