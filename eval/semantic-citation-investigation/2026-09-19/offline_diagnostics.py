"""Zero-network investigation; authored responses are diagnostics, never repaired results."""
import base64
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import threading
from hkex_audit import semantic as sem
from hkex_audit.artifacts import encode, sha, fingerprint
from hkex_audit.semantic_attempt import Store, request, dispatch, replay, FILES, CONFIGS
from hkex_audit.semantic_cli import isolated, normalized_selection, paired
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'diagnostics'
LIVE=ROOT/'runs/paired-semantic-integration-2026-09-18/live-v1'
def read(p): return json.loads(Path(p).read_text())
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(encode(x))
def host(q,a):
    try:sem.validate_answer(q,a);return {'accepted':True,'error':None}
    except ValueError as e:return {'accepted':False,'error':str(e)}
def no_network(event,args):
    if event.startswith('socket.'):raise RuntimeError('offline investigation: networking forbidden')
sys.addaudithook(no_network)

inventory=read(ROOT/'eval/semantic-integration/2026-09-18/retained-artifacts.json')
protected=dict(inventory['files'])
for p in ['spec/semantic-operation.md','spec/paired-semantic-attempts.md',
          'eval/semantic-integration/2026-09-18/independent-review.json',
          'eval/semantic-integration/2026-09-18/pre-inference-freeze.json',
          'eval/semantic-integration/2026-09-18/retained-artifacts.json',
          'eval/semantic-integration/2026-09-18/source-review-packet.json',
          'src/hkex_audit/semantic.py','src/hkex_audit/semantic_attempt.py','src/hkex_audit/semantic_cli.py',
          'eval/semantic-integration/validate.py','docs/semantic-citation-acceptance-investigation-handoff-2026-09-18.md',
          *['schemas/'+n+'.schema.json' for n in ('evidence','evidence_manifest','audit_input','pipeline_artifacts')]]:
    protected[p]=sha((ROOT/p).read_bytes())
assert inventory['count']==127
assert all(sha((ROOT/p).read_bytes())==h for p,h in protected.items())
OUT.mkdir(exist_ok=False)
write(OUT/'protected-before.json',protected)
spec=importlib.util.spec_from_file_location('frozen_evaluator',ROOT/'eval/semantic-integration/validate.py')
ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
review=read(ROOT/'eval/semantic-integration/2026-09-18/independent-review.json')
expect={q['name']:q for q in review['queries']}
packet=read(ROOT/'eval/semantic-integration/2026-09-18/source-review-packet.json')
nodes={n['id']:n for n in packet['nodes']}
selection=normalized_selection(ROOT/'runs/paired-semantic-integration-2026-09-18/selection.json')
batch=read(LIVE/'batch.json')
prepared=isolated('prepare_worker',{'selection':selection,'specs':batch['specs']})
assert batch['selection']==selection
write(OUT/'preparation.json',{'queries':[{'query_id':q['query_id'],'gate':q['gate']} for q in prepared['queries']], 'access_attempts':prepared['access_attempts']})
queries={q['selection']['name']:q for q in prepared['queries']}
cases=[];traces=[];research=[]
for name,q in queries.items():
    role_results={}
    for role in ('primary','research'):
        d=LIVE/role/name
        assert read(d/'query.json')==q
        req=read(d/'request.json')
        assert req==request(q,role,batch['nonce'])
        rr=replay(Store(d),q,role,batch['nonce'])
        assert rr['model_calls']==0 and 'validation' in rr
        role_results[role]=rr
    assert read(LIVE/'primary'/name/'request.json')['semantic_payload_sha256']==read(LIVE/'research'/name/'request.json')['semantic_payload_sha256']
    out=OUT/'primary-replay'/name;out.mkdir(parents=True)
    isolated('consume_worker',{'selection':selection,'spec':q['selection'],'batch':str(LIVE),'output':str(out),'nonce':batch['nonce']})
    for fn in ('annotations.json','provenance.json'):
        assert (out/fn).read_bytes()==(LIVE/'operational'/name/fn).read_bytes()
    consumption=read(out/'consumption.json')
    assert consumption['model_calls']==0 and not consumption['adapter_imported']
    assert not any('/research/' in a.get('path','') for a in consumption['access_attempts'])
    a=role_results['primary']['validation'].get('answer')
    trace={'name':name,'query_id':q['query_id'],'target_id':q['selection']['target_id'],'gate':q['gate'],
      'paths':{k:str((LIVE/k/name).relative_to(ROOT)) for k in ('primary','research','operational')},
      'evaluator':'eval/semantic-integration/validate.py::review_decision',
      'frozen_review_pointer':'/queries/'+str(next(i for i,v in enumerate(review['queries']) if v['name']==name)),
      'primary_attempt_id':role_results['primary']['attempt_id'],'primary_state':role_results['primary']['validation']['state'],
      'replay_annotation_and_provenance_byte_identical':True,'roles_have_equal_semantic_payload':True,
      'historical_model_calls':{r:role_results[r]['historical_model_calls'] for r in role_results},
      'replay_model_calls':0,'annotation_ids':[x['annotation_id'] for x in read(out/'annotations.json')]}
    if a:
        req=read(LIVE/'primary'/name/'request.json')
        assert req['payload']['messages'][0]['content']==q['prompt']==sem.PROMPT
        assert req['payload']['response_format']['json_schema']['schema']==q['schema']==sem.SCHEMA
        assert json.loads(req['payload']['messages'][1]['content'])==q['context']
        missing=sorted(set(expect[name]['required_support_ids'])-set(a['support_refs']))
        assert len(missing)==1 and nodes[missing[0]]['text']=='港幣百萬元'
        assert any(n['id']==missing[0] and n['text']=='港幣百萬元' for n in q['context']['items'])
        assert not list(Draft202012Validator(sem.SCHEMA).iter_errors(a))
        assert host(q,a)['accepted'] and ev.review_decision(q['gate'],expect[name],{'answer':a})==(True,False)
        trace.update(contributors=a['contributor_ids'],support_refs=a['support_refs'],missing_frozen_support=missing,
          missing_source=[nodes[i] for i in missing],schema_pass=True,host_pass=True,selection_correct=True,frozen_support_pass=False,
          input_unit_present=True)
        variants=[('R1', 'unchanged',deepcopy(a))]
        added=deepcopy(a);added['support_refs']+=missing;variants.append(('R2','unit_added',added))
        for ref in [a['target_id'],*a['contributor_ids']]:
            copy=deepcopy(a);copy['support_refs'].remove(ref)
            variants.append(('R2','omit_'+ref,copy))
        if name=='period_groups':
            year=next(n['id'] for n in q['context']['items'] if n['text']=='2025')
            copy=deepcopy(a);copy['support_refs'].remove(year);variants.append(('R3','omit_2025',copy))
            peers=[n['id'] for n in q['context']['items'] if n['kind']=='cell' and n['row']==1 and n['column'] in (5,6,7)]
            copy=deepcopy(a);copy['contributor_ids']=peers;copy['support_refs']=list(dict.fromkeys([*a['support_refs'],*peers]));variants.append(('R3','wrong_2024_peers',copy))
        for family,variant,response in variants:
            verdict=host(q,response);correct,supported=ev.review_decision(q['gate'],expect[name],{'answer':response})
            if variant=='unit_added':assert verdict['accepted'] and correct and supported
            if variant.startswith('omit_') or variant=='wrong_2024_peers':assert not verdict['accepted']
            cases.append({'fixture':family,'query':name,'variant':variant,'classification':'exposed_reproduction',
              'response_origin':'unchanged_saved_answer' if family=='R1' else 'authored_diagnostic_copy_not_model_result',
              'operation_version':sem.VERSION,'source_query_path':str((LIVE/'primary'/name/'query.json').relative_to(ROOT)),
              'source_query_sha256':sha((LIVE/'primary'/name/'query.json').read_bytes()),'response':response,
              'strict_schema_pass':not list(Draft202012Validator(sem.SCHEMA).iter_errors(response)),
              'actual_host':verdict,'frozen_selection_correct':correct,'frozen_support_subset':supported,
              'evaluator_note':'Subset diagnostic calculated even when host rejects; not an accepted evaluation result.'})
    else:
        assert name=='missing_target' and q['gate']=='missing_evidence'
        assert nodes[q['selection']['target_id']]['content_state']=='blank'
        assert all(x['historical_model_calls']==0 for x in role_results.values())
        assert read(out/'annotations.json')==[]
        cases.append({'fixture':'R4','query':name,'classification':'exposed_reproduction','target_id':q['selection']['target_id'],
          'operation_version':sem.VERSION,'gate':'missing_evidence','model_calls':0,'annotations':[],
          'frozen_evaluator':ev.review_decision(q['gate'],expect[name],role_results['primary']['validation'])})
    traces.append(trace)
    raw=read(LIVE/'research'/name/'response.json')
    if raw.get('body_base64'):
        body=json.loads(base64.b64decode(raw['body_base64']));choice=body['choices'][0]
        r={'name':name,'finish_reason':choice['finish_reason'],'usage':body.get('usage'),
           'replayed_state':role_results['research']['validation']['state'],'model_calls':0}
        if choice['finish_reason']=='stop':
            answer=json.loads(choice['message']['content']);r.update(answer=answer,host=host(q,answer),schema_pass=not list(Draft202012Validator(sem.SCHEMA).iter_errors(answer)))
            assert r['schema_pass'] and r['host']['error']=='abstention contains contributors'
        else:assert choice['finish_reason']=='length' and body['usage']['completion_tokens']==4096
        research.append(r)

# Original body-amount contrast, without inferring relationships from the values.
a,b=queries['total'],queries['varied_total'];changed=[]
for x,y in zip(a['context']['items'],b['context']['items']):
    if x!=y:
        assert {k:v for k,v in x.items() if k not in ('text','transformation')}=={k:v for k,v in y.items() if k not in ('text','transformation')}
        assert x['text']=='[amount]' and y['text']=='[amount:987654321]';changed.append(x['id'])
assert changed
assert set(traces[0]['contributors'])==set(traces[-1]['contributors'])
write(OUT/'reproductions.json',{'model_calls':0,'network_calls':0,'cases':cases})
write(OUT/'evidence-trace.json',traces)
write(OUT/'research-diagnostics.json',research)
write(OUT/'amount-contrast.json',{'changed_body_ids':changed,'selected_contributors_unchanged':True,'independent_reports':False})

# Persisted role-isolation probes use literal authored transport stubs, never provider calls.
q=queries['total'];saved=read(LIVE/'primary/total/result.json')['validation']['answer']
def stub(a,role):
    body={'model':CONFIGS[role]['model'],'provider':CONFIGS[role]['served_provider'],'id':'authored-offline-diagnostic',
      'choices':[{'finish_reason':'stop','message':{'content':json.dumps(a)}}]}
    return {'transport_status':'ok','body_base64':base64.b64encode(encode(body)).decode()}
isolation=[]
for mode in ('timeout','abstained','missing_completion','slow_research'):
    root=OUT/'authored-isolation'/mode
    for role in ('primary','research'):(root/role/'total').mkdir(parents=True)
    out=root/'operational';out.mkdir();nonce='offline-authored-'+mode
    p,r=Store(root/'primary/total'),Store(root/'research/total')
    def consume():
        return isolated('consume_worker',{'selection':selection,'spec':q['selection'],'batch':str(root),'output':str(out),'nonce':nonce})
    if mode=='slow_research':
        entered=threading.Event();persisted=threading.Event()
        def slow(req):
            entered.set();assert persisted.wait(30);return {'transport_status':'timeout'}
        def primary(req):assert entered.wait(30);return stub(saved,'primary')
        def consume_signal():
            v=consume();assert read(out/'annotations.json');persisted.set();return v
        pair=paired(q,nonce,p,r,primary,slow,consume_signal)
        assert persisted.is_set() and pair['research']['validation']['state']=='timeout'
    else:
        dispatch(q,request(q,'research',nonce),lambda req:stub(saved,'research'),r)
        abstention={**saved,'state':'ambiguous','contributor_ids':[]}
        if mode!='missing_completion':dispatch(q,request(q,'primary',nonce),lambda req:stub(abstention,'primary') if mode=='abstained' else {'transport_status':'timeout'},p)
        consume()
    anns=read(out/'annotations.json');prov=read(out/'provenance.json');access=read(out/'consumption.json')
    if mode!='slow_research':assert not any(a['links'] for a in anns)
    assert not any('/research/' in x.get('path','') for x in access['access_attempts'])
    assert prov['primary_attempt_id']==request(q,'primary',nonce)['attempt_id']
    isolation.append({'mode':mode,'provenance':prov,'annotation_count':len(anns),'link_count':sum(len(a['links']) for a in anns),
      'guarded_primary_only_reads':True,'actual_provider_calls':0,'dispatch_model_calls_field_note':'Counts invoked authored stubs, not real provider calls.',
      'path':str(root.relative_to(ROOT))})
write(OUT/'isolation.json',{'origin':'authored offline transport fixtures, not model completions','actual_provider_calls':0,'cases':isolation,'future_downstream_noninterference':'not established'})
assert all(sha((ROOT/p).read_bytes())==h for p,h in protected.items())
write(OUT/'verification.json',{'retained_hashes_checked':127,'protected_hashes_unchanged':True,'protected_file_count':len(protected),
  'schema_fingerprint':fingerprint(sem.SCHEMA),'operation_version':sem.VERSION,'model_calls':0,'network_calls':0,
  'R_diagnostic_count':len(cases),'primary_replays':5,'research_replays':5,'role_isolation_cases':len(isolation),
  'v1_replay':'Current exact e8000e2 code; requests/completions recomputed, no permissive hash acceptance.'})
print('Verified',len(cases),'R diagnostics, 10 zero-call role replays, 5 byte-identical primary annotation/provenance replays, 4 persisted isolation probes, 127 retained hashes.')
