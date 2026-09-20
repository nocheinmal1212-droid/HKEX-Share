"""Evaluator-only comparison of exposed, source-reviewed header expectations.

No transport, repair or fallback. Raw candidate diagnostics are separate from host
acceptance. Truncated text is never promoted to a candidate or operational answer.
"""
import os
os.environ = {}
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PACKET = Path(__file__).resolve().parent
PREP = ROOT/'runs/semantic-citation-confirmation-2026-09-19/prepared-v1'
sys.path.insert(0,str(ROOT/'src'))
from jsonschema import Draft202012Validator
from hkex_audit.artifacts import read, write_new, fingerprint, sha
from hkex_audit.semantic import SCHEMA
from hkex_audit.semantic_attempt import Store, replay, request

spec = importlib.util.spec_from_file_location('historical_evaluator',ROOT/'eval/semantic-integration/validate.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def evaluate_store(query, expected, directory, role, nonce):
    saved = replay(Store(directory),query,role,nonce)
    validation = saved.get('validation',{})
    state = validation.get('state',saved.get('state'))
    candidate = None
    schema_valid = None
    transport_state = 'missing'
    finish = None
    try:
        raw = read(Path(directory)/'response.json')
        transport_state = raw.get('transport_status')
        if transport_state == 'ok':
            body = json.loads(base64.b64decode(raw['body_base64'],validate=True))
            choice = body['choices'][0]
            finish = choice.get('finish_reason')
            if len(body['choices']) == 1 and finish == 'stop' and not choice['message'].get('refusal') and not choice['message'].get('tool_calls'):
                value = json.loads(choice['message']['content'])
                schema_valid = not list(Draft202012Validator(SCHEMA).iter_errors(value))
                if schema_valid: candidate = value
    except (OSError,ValueError,KeyError,TypeError,IndexError):
        schema_valid = False if transport_state == 'ok' else None
    correct, supported = old.review_decision(query['gate'],expected,{'answer':candidate})
    if candidate and candidate['target_id'] != expected['target_id']:
        correct = False
    host_accepted = state == 'accepted'
    return {'availability':transport_state, 'finish_reason':finish, 'schema_valid':schema_valid,
            'host_state':state, 'host_accepted':host_accepted,
            'exact_reviewed_contributors_and_state':correct, 'required_source_support_present':supported,
            'success':host_accepted and correct is True and supported is True,
            'candidate_diagnostic_only':candidate, 'attempt_id':saved['attempt_id'],
            'completion_replay_calls':saved['model_calls'],
            'historical_transport_invocations':saved.get('historical_model_calls'),
            'served':validation.get('served'), 'cost':validation.get('cost'),
            'host_diagnostic':validation.get('diagnostic')}


def evaluate_batch(batch_path, authored=False):
    batch_path = Path(batch_path).resolve()
    proposed = read(PACKET/'launch-proposal.json')
    if not authored:
        assert batch_path == Path(proposed['live_output']), 'wrong live output'
    batch = read(batch_path/'batch.json')
    expected = read(PACKET/'expectations.json')
    specs = read(PREP/'queries.json')
    assert batch['specs'] == specs and batch['selection'] == read(PREP/'selection.json')
    assert batch['nonce'] == batch_path.name
    if not authored: assert batch['nonce'] == proposed['nonce']
    results = []
    for ex in expected['queries']:
        name = ex['name']
        q = read(PREP/name/'query.json')
        roles = {}
        for role in ('primary','research'):
            directory = batch_path/role/name
            # Missing attempts remain visible rather than shrinking denominator.
            if (directory/'request.json').exists():
                assert read(directory/'request.json') == request(q,role,batch['nonce'])
            roles[role] = evaluate_store(q,ex,directory,role,batch['nonce'])
        ann_path = batch_path/'operational'/name/'annotations.json'
        prov_path = batch_path/'operational'/name/'provenance.json'
        persisted = {'available':False}
        if ann_path.exists() and prov_path.exists():
            ann,prov = read(ann_path),read(prov_path)
            assert prov['annotations_sha256'] == fingerprint(ann)
            assert prov['query_id'] == q['query_id']
            assert prov['primary_attempt_id'] == request(q,'primary',batch['nonce'])['attempt_id']
            if ann:
                assert prov['primary_completion_sha256'] == sha((batch_path/'primary'/name/'completion.json').read_bytes())
            persisted = {'available':True,'annotation_count':len(ann),'provenance':prov,
                         'annotations_sha256':sha(ann_path.read_bytes())}
        results.append({'name':name,'roles':roles,'primary_persistence':persisted})
    return {'version':'confirmation-evaluator-1.0.0','authored_diagnostic':authored,
            'model_results':not authored,'model_calls_on_evaluation':0,
            'denominator_per_role':2,'primary_successes':sum(x['roles']['primary']['success'] for x in results),
            'research_successes':sum(x['roles']['research']['success'] for x in results),
            'results':results,
            'limits':'Research is independent, never fallback/consensus/veto/annotation input. Candidate diagnostics do not override host rejection. Header semantics only; no numeric or downstream findings claim.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--authored-diagnostic',action='store_true')
    args = p.parse_args()
    result = evaluate_batch(args.batch,args.authored_diagnostic)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    write_new(args.output,result)
    print(json.dumps({'denominator':2,'primary_successes':result['primary_successes'],
                      'research_successes':result['research_successes'],'authored':args.authored_diagnostic}))
