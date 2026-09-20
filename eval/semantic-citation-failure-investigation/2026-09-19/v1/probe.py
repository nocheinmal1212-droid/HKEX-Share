"""Offline diagnostic copies only; no dispatch, network or operational mutation."""
import os
os.environ={}
import base64
from copy import deepcopy
import importlib.util
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[4]
PACKET=Path(__file__).resolve().parent
OUT=ROOT/'runs/semantic-citation-failure-investigation-2026-09-19/v1'
BASE=ROOT/'runs/semantic-citation-confirmation-2026-09-19'
sys.path.insert(0,str(ROOT/'src'))
from hkex_audit.artifacts import read,write_new,sha,fingerprint
from hkex_audit.semantic import PROMPT,SCHEMA,validate_answer
from hkex_audit.semantic_attempt import CONFIGS,FILES,Store,request,replay
from hkex_audit.header_support import required_support
from jsonschema import Draft202012Validator
spec=importlib.util.spec_from_file_location('historical_evaluator',ROOT/'eval/semantic-integration/validate.py')
eval_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(eval_module)
def deny_network(event,args):
    if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}:raise AssertionError('offline investigation network denied')
sys.addaudithook(deny_network)
def integrity():
    f=ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2/freeze.json'
    assert sha(f.read_bytes())=='46c1b25173abf95490caf42b1d589de84237284afde81ce198910f9c9475c0ae'
    a=read(f)['files'];b=read(BASE/'evaluation-v2/artifact-integrity.json')['files']
    assert all(sha((ROOT/p).read_bytes())==h for p,h in a.items())
    assert all(sha((ROOT/p).read_bytes())==h for p,h in b.items())
    return {'approved_members':len(a),'result_members':len(b),'unchanged':True}
write_new(OUT/'before.json',integrity())
expected={e['name']:e for e in read(ROOT/'eval/semantic-citation-confirmation/2026-09-19/preflight-v2/expectations.json')['queries']}
rows=[];routing=[];reasoning_notes=[]
for name in ('total','period_groups'):
    query=read(BASE/'prepared-v2'/name/'query.json');ex=expected[name]
    labels={i['id']:i.get('text') for i in query['context']['items']}
    pair=[]
    for role in CONFIGS:
        directory=BASE/'live-v2'/role/name
        req=read(directory/'request.json');q=read(directory/'query.json')
        assert q==query and req==request(query,role,'live-v2')
        assert (directory/'request.json').read_bytes()==(BASE/'prepared-v2'/name/(role+'-request.json')).read_bytes()
        assert req['payload']['messages'][0]=={'role':'system','content':PROMPT}
        assert json.loads(req['payload']['messages'][1]['content'])==query['context']
        assert req['payload']['response_format']['json_schema']['schema']==SCHEMA
        assert req['payload']['response_format']['json_schema']['strict'] is True
        pair.append(req['semantic_payload_sha256'])
        replayed=replay(Store(directory),query,role,'live-v2')
        assert replayed['model_calls']==0 and replayed['historical_model_calls']==1
        assert replayed['validation']['state']=='invalid_output'
        response=read(directory/'response.json');body=json.loads(base64.b64decode(response['body_base64'],validate=True))
        choice=body['choices'][0];answer=json.loads(choice['message']['content'])
        assert response['transport_status']=='ok' and response['http_status']==200
        assert body['model']==CONFIGS[role]['model'] and body['provider']==CONFIGS[role]['served_provider']
        assert choice['finish_reason']=='stop'
        assert read(directory/'transport-return.json')==response
        # Required IDs recompute from host source structure, never from evaluation operands.
        source_needed=required_support(query['host_analysis'],answer['target_id'],answer['contributor_ids'])
        assert source_needed==set(ex['required_support_ids'])
        assert set(answer['contributor_ids'])==set(ex['expected_contributor_header_ids'])
        variants={'original':deepcopy(answer),'target_only':deepcopy(answer),'target_and_contributors':deepcopy(answer)}
        variants['target_only']['support_refs']=list(dict.fromkeys(answer['support_refs']+[answer['target_id']]))
        variants['target_and_contributors']['support_refs']=list(dict.fromkeys(answer['support_refs']+[answer['target_id']]+answer['contributor_ids']))
        if role=='research':
            variants['selected_state_with_complete_support']=deepcopy(variants['target_and_contributors'])
            variants['selected_state_with_complete_support']['state']='selected'
            variants['empty_contributor_abstention']=deepcopy(variants['target_and_contributors'])
            variants['empty_contributor_abstention']['contributor_ids']=[]
        results={}
        for variant,a in variants.items():
            valid_schema=not list(Draft202012Validator(SCHEMA).iter_errors(a))
            assert valid_schema
            try:
                validate_answer(query,a);host='accepted' if a['state']=='selected' else 'abstained';reason=None
            except ValueError as exc:host='rejected';reason=str(exc)
            correct,support=eval_module.review_decision(query['gate'],ex,{'answer':a})
            results[variant]={'schema_valid':valid_schema,'host':host,'reason':reason,
                'reviewed_contributor_and_state_match':correct,'required_support_present':support,
                'diagnostic_copy_only':variant!='original','new_model_result':False}
        assert results['original']['reason']=='target support absent'
        assert results['target_only']['reason']=='contributor support absent'
        if role=='primary':assert results['target_and_contributors']['host']=='accepted'
        else:
            assert results['target_and_contributors']['reason']=='abstention contains contributors'
            assert results['selected_state_with_complete_support']['host']=='accepted'
            assert results['empty_contributor_abstention']['host']=='abstained'
            assert not results['empty_contributor_abstention']['reviewed_contributor_and_state_match']
        rows.append({'case':name,'role':role,'saved_response_sha256':sha((directory/'response.json').read_bytes()),
            'original_state':answer['state'],'contributor_ids_match_separately':True,
            'source_required_matches_reviewed_support':True,
            'missing_support':[{'id':i,'literal_text':labels[i]} for i in sorted(source_needed-set(answer['support_refs']))],
            'variants':results,'original_remains_rejected':True})
        routing.append({'case':name,'role':role,'saved_request_equals_approved_and_reconstructed':True,
            'response_return_equals_persisted':True,'completion_marker_replay':'valid rejection, zero calls',
            'served_model':body['model'],'served_provider':body['provider'],'finish_reason':choice['finish_reason'],
            'native_finish_reason':choice.get('native_finish_reason'),'max_tokens':4096,
            'completion_tokens':body['usage']['completion_tokens'],
            'reasoning_tokens':body['usage']['completion_tokens_details'].get('reasoning_tokens'),
            'raw_message_fields':list(choice['message'])})
        reason=choice['message'].get('reasoning') or ''
        # Short literal evidence from provider-returned diagnostics, not an inference about internals.
        phrases={('total','primary'):'whether this array includes the target ID, contributor IDs, and source groups, or just contextual support',
                 ('total','research'):"The prompt says \"Return only the schema's IDs and labels.\" It doesn't specify JSON schema.",
                 ('period_groups','research'):'Since no abstention.'}
        phrase=phrases.get((name,role))
        if phrase:
            assert phrase in reason
            reasoning_notes.append({'case':name,'role':role,'source_response_sha256':sha((directory/'response.json').read_bytes()),
                'provider_returned_diagnostic_excerpt':phrase,
                'limitation':'Self-report; cannot establish provider schema injection or causal decoding behavior.'})
    assert pair[0]==pair[1]
    assert read(BASE/'live-v2/operational'/name/'annotations.json')==[]
    assert read(BASE/'live-v2/operational'/name/'provenance.json')['outcome']=='invalid_output'
write_new(OUT/'localization.json',rows)
write_new(OUT/'request-response-integrity.json',routing)
write_new(OUT/'provider-diagnostic-evidence.json',reasoning_notes)
write_new(OUT/'interface-audit.json',{'prompt_mentions_support_refs':'support_refs' in PROMPT,
    'prompt_mentions_selected_label':"'selected'" in PROMPT or 'state=selected' in PROMPT or 'state: selected' in PROMPT,
    'prompt_mentions_field_names':{k:k in PROMPT for k in SCHEMA['required']},
    'prompt_ambiguous_format_sentence':"Return only the schema's IDs and labels.",
    'schema_required':SCHEMA['required'],'schema_fields_have_descriptions':{k:'description' in v for k,v in SCHEMA['properties'].items()},
    'schema_positive_state_available_in_enum':'selected' in SCHEMA['properties']['state']['enum'],
    'schema_expresses_cross_field_membership':False,
    'diagnostic_variants':sum(len(r['variants']) for r in rows),'originals_still_rejected':4,
    'live_calls':0,'model_or_transport_invocations':0,'new_operational_outputs':0})
write_new(OUT/'after.json',integrity())
print(json.dumps({'original_rejections_reproduced':4,'diagnostic_variants':sum(len(r['variants']) for r in rows),
    'request_pairs_identical':2,'primary_citation_only_localization':2,'research_state_contradictions_localized':2,
    'preserved':integrity(),'network_calls':0}))
