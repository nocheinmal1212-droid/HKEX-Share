"""Post-run, read-only evaluator. Not imported by any writer or transport."""
import base64
import json
from pathlib import Path
import sys

PACKET=Path(__file__).resolve().parent
ROOT=PACKET.parents[3]
PREP=ROOT/'runs/semantic-citation-prompt-experiment-2026-09-19/prepared-v1'

def deny_network(event,args):
    if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}:
        raise PermissionError('observer has no transport authority')
sys.addaudithook(deny_network)

def components(candidate,expected):
    if not isinstance(candidate,dict):return {'target':False,'exact_contributors':False,'state':False,
        'target_cited':False,'contributors_cited':False,'groups_cited':False,'state_list_consistent':False}
    refs=set(candidate.get('support_refs',[]));chosen=set(candidate.get('contributor_ids',[]))
    required=set(expected['required_support_ids'])
    groups=required-{expected['target_id']}-set(expected['expected_contributor_header_ids'])
    return {'target':candidate.get('target_id')==expected['target_id'],
        'exact_contributors':chosen==set(expected['expected_contributor_header_ids']),
        'state':candidate.get('state')==expected['expected_status'],
        'target_cited':candidate.get('target_id') in refs,'contributors_cited':chosen<=refs,
        'groups_cited':groups<=refs,
        'state_list_consistent':bool(chosen) if candidate.get('state')=='selected' else not chosen}

def observe(arm,batch):
    sys.path.insert(0,str(PREP/arm/'runtime-snapshot/src'))
    from hkex_audit.artifacts import read,fingerprint,sha,encode
    from hkex_audit.semantic_attempt import Store,replay,request
    from hkex_audit.semantic import SCHEMA,annotation
    from hkex_audit.semantic_cli import load_evidence
    from jsonschema import Draft202012Validator
    expected=read(PACKET/'expectations.json')['queries']
    evidence=load_evidence(read(PREP/'selection.json'))
    results=[]
    for ex in expected:
        name=ex['name'];q=read(PREP/arm/name/'query.json');roles={}
        for role in ('primary','research'):
            saved=replay(Store(batch/role/name),q,role,batch.name)
            validation=saved.get('validation',{});candidate=None;schema=False;raw={};body={};finish=None
            try:
                raw=read(batch/role/name/'response.json')
                body=json.loads(base64.b64decode(raw['body_base64'],validate=True))
                choices=body['choices'];choice=choices[0];finish=choice.get('finish_reason')
                if len(choices)==1 and finish=='stop' and not choice['message'].get('refusal') and not choice['message'].get('tool_calls'):
                    candidate=json.loads(choice['message']['content'])
                    schema=not list(Draft202012Validator(SCHEMA).iter_errors(candidate))
                    if not schema:candidate=None
            except (OSError,ValueError,KeyError,IndexError,TypeError):pass
            bits=components(candidate,ex)
            host=validation.get('state',saved.get('state'))
            roles[role]={'availability':raw.get('transport_status','unavailable'), 'schema_valid':schema,
                'finish_reason':finish,'host_state':host,'host_diagnostic':validation.get('diagnostic'),
                **bits,'success':host=='accepted' and schema and all(bits.values()),
                'replay_calls':saved['model_calls'],'historical_transport_invocations':saved.get('historical_model_calls'),
                'usage':body.get('usage'),'cost':validation.get('cost'),'served':validation.get('served')}
        persisted=False
        try:
            consumed=read(batch/'operational'/name/'consumption.json')
            prov=read(batch/'operational'/name/'provenance.json');anns=read(batch/'operational'/name/'annotations.json')
            primary=replay(Store(batch/'primary'/name),q,'primary',batch.name)
            state=primary.get('validation',{}).get('state',primary.get('state'))
            expected_annotations=[annotation(evidence,q,primary['attempt_id'],primary['validation']['answer'])] if state in ('accepted','abstained') else []
            assert anns==expected_annotations and prov['annotations_sha256']==fingerprint(anns)
            assert prov['query_id']==q['query_id'] and prov['primary_attempt_id']==request(q,'primary',batch.name)['attempt_id']
            assert prov['outcome']==consumed['outcome']==state and consumed['model_calls']==0
            assert not consumed['adapter_imported']
            if anns:assert prov['primary_completion_sha256']==sha((batch/'primary'/name/'completion.json').read_bytes())
            assert all('/research/' not in a.get('path','') and '/eval/' not in a.get('path','') for a in consumed['access_attempts'])
            persisted=True
        except (OSError,ValueError,KeyError,AssertionError,TypeError):pass
        results.append({'case':name,'roles':roles,'primary_persistence_available':persisted,
            'complete_primary_success':persisted and roles['primary']['success']})
    return {'arm':arm,'denominator_per_role':2,'model_calls':0,'results':results,
            'primary_complete_successes':sum(r['complete_primary_success'] for r in results),
            'research_successes':sum(r['roles']['research']['success'] for r in results)}

if __name__=='__main__':
    arm,batch=sys.argv[1:];print(json.dumps(observe(arm,Path(batch))))
