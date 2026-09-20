"""One-off offline review. No network, credentials, corpus reads or historical writes."""
import base64
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from statistics import median
import sys
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / 'runs/milestone2/interface-boundaries-2026-09-16'
OLD = ROOT / 'runs/milestone2/hypothesis-fixtures-2026-09-15'
sys.path.insert(0, str(ROOT / 'tools/experiments'))
import evaluate_interface_run
import evaluate_fixtures
import interface_boundary

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def decode(record, prefix):
    raw = base64.b64decode(record[prefix + '_base64'], validate=True)
    expected = record['sha256'] if prefix == 'body' else record['response_sha256']
    assert hashlib.sha256(raw).hexdigest() == expected
    return json.loads(raw)

handoff = ROOT / 'docs/model-interface-independent-review-handoff-2026-09-16.md'
links = re.findall(r'\]\(<([^>]+)>\)', handoff.read_text())
assert all(Path(p).exists() for p in links)
fixture = read(ROOT / 'spec/diagnostics/interface-boundaries-v1.json')
plan = read(RUN / 'execution-plan.json')
assert sha(ROOT / 'spec/diagnostics/interface-boundaries-v1.json') == plan['source_fixture_sha256']
assert sha(RUN / 'requests.json') == plan['manifest_sha256']
assert sha(RUN / 'evaluator-key.json') == plan['evaluator_key_sha256']
verification = read(RUN / 'verification.json')
checked, skipped = [], []
for name, digest in verification['files_sha256'].items():
    path = ROOT / name
    # Even the synthetic PDF sentinel is unnecessary for this review.
    if path.suffix == '.pdf':
        skipped.append(name)
        continue
    assert sha(path) == digest, name
    checked.append(name)

# Independent manual answer review for these ten lexical tasks, before raw grading.
# This table is evaluator-only and is not a runtime vocabulary or detector.
selected = ['a', None, None, 'b', None, 'b', 'a', 'source-17', 'b', 'b']
expected = {}
for case, target in zip(fixture['contract_fixtures'], selected, strict=True):
    answer = {'action': 'abstain' if target is None else 'label',
              'evidence_id': target, 'role': None if target is None else 'total_label'}
    assert case['expected_model_output'] == answer
    expected[case['id']] = answer

requests = read(RUN / 'requests.json')['requests']
answers = read(RUN / 'evaluator-key.json')['cases']
assert len(requests) == len(answers) == 180
assert len({r['id'] for r in requests}) == len({a['id'] for a in answers}) == 180
reqs = {r['id']: r for r in requests}
saved = read(RUN / 'evaluation.json')
saved_rows = {r['id']: r for r in saved['rows']}
counts, pairs, failures = defaultdict(Counter), defaultdict(dict), []
for a in answers:
    r = read(RUN / 'responses' / (a['id'] + '.json'))
    start = read(RUN / 'responses' / (a['id'] + '.started.json'))
    assert start['id'] == r['id'] == a['id']
    assert start['request_sha256'] == r['request_sha256'] == reqs[a['id']]['sha256']
    assert start['started_at'] == r['started_at']
    body = decode(reqs[a['id']], 'body')
    response = decode(r, 'response')
    assert body['messages'][0]['content'] == fixture['prompts'][a['prompt']]
    assert body['provider'] == {'only': ['fireworks'], 'require_parameters': True, 'allow_fallbacks': False}
    assert body['model'] == a['model'] and body['max_tokens'] == 512 and body['temperature'] == 0
    assert body['response_format']['json_schema']['schema'] == a['schema']
    assert a['expected'] == expected[a['case']]
    detail = {'id': a['id'], 'case': a['case']}
    # Raw grading here does not use the repository's response classifier.
    if r['http_status'] == 429:
        assert a['route'] == 'flash'
        assert response['error']['code'] == 429
        assert response['error']['metadata']['provider_name'] == 'Fireworks'
        assert 'rate' in json.dumps(response).lower()
        status = 'http_error'
    else:
        assert r['http_status'] == 200 and r['transport_status'] == 'received'
        assert response['model'] == a['model'] and response['provider'] == a['provider_name']
        assert len(response['choices']) == 1
        c = response['choices'][0]
        assert not c['message'].get('refusal') and not c['message'].get('tool_calls')
        if c['finish_reason'] == 'length':
            status = 'truncated'
            assert c['message']['content'] is None
            assert response['usage']['completion_tokens'] == 512
            assert response['usage']['completion_tokens_details']['reasoning_tokens'] == 512
        else:
            assert c['finish_reason'] == 'stop'
            output = json.loads(c['message']['content'])
            assert set(output) == {'action', 'evidence_id', 'role'}
            if output == expected[a['case']]:
                status = 'passed'
            else:
                assert output == {'action': 'abstain', 'evidence_id': None, 'role': None}
                status = 'unexpected_abstention'
                detail['completion_tokens'] = response['usage']['completion_tokens']
                detail['output'] = output
    assert status == saved_rows[a['id']]['status']
    counts[a['route'] + '/' + a['prompt']][status] += 1
    pairs[(a['route'], a['case'], a['repetition'])][a['prompt']] = (body, r, response, status)
    if status != 'passed' and a['route'] != 'flash':
        failures.append({**detail, 'status': status})

effects = defaultdict(lambda: defaultdict(list))
assert len(pairs) == 90
for (route, case, repetition), arms in pairs.items():
    a, b = arms['B0_existing_explicit'], arms['B1_concise_equivalent']
    ba, bb = deepcopy(a[0]), deepcopy(b[0])
    ba['messages'][0]['content'] = bb['messages'][0]['content'] = ''
    assert ba == bb
    if a[3] == b[3] == 'passed':
        effects[route]['latency'].append(b[1]['elapsed_seconds'] - a[1]['elapsed_seconds'])
        for field in ['prompt_tokens', 'completion_tokens']:
            effects[route][field].append(b[2]['usage'][field] - a[2]['usage'][field])
assert evaluate_interface_run.evaluate(RUN) == saved
assert evaluate_fixtures.evaluate(OLD) == read(OLD / 'evaluation.json')

old_eval = read(OLD / 'evaluation.json')
shadow = [r for r in old_eval['rows'] if r['case'] == 'missing_target' and r['model'].startswith('deepseek/')]
assert len(shadow) == 24
shadow_counts = dict(Counter(r['status'] for r in shadow))
glm = next(r for r in old_eval['rows'] if r['id'] == 'call-120')
assert glm['status'] == 'failure_to_abstain'
assert sha(OLD / 'responses/call-120.json') == glm['record_sha256']
old_req = next(r for r in read(OLD / 'requests.json')['requests'] if r['id'] == 'call-120')
old_payload = json.loads(decode(old_req, 'body')['messages'][1]['content'])
assert old_payload['instruction'] == 'Classify field-missing as a total label if supported by the supplied evidence.'
# Explicit reviewer mapping, no host extraction of targets from prose.
typed = {'operation': 'classify_target', 'target_id': 'field-missing', 'evidence': old_payload['evidence']}
spy = Mock()
glm_precheck = interface_boundary.dispatch(typed, spy)
spy.assert_not_called()
assert glm_precheck['reason'] == 'target_missing'

limits = {}
request = deepcopy(fixture['contract_fixtures'][0]['request'])
request['evidence'][0]['text'] = 'x' * 24001
limits['text_above_existing_context_budget'] = interface_boundary.precheck(request)
spy = Mock(side_effect=TimeoutError('synthetic timeout'))
try:
    interface_boundary.dispatch(fixture['contract_fixtures'][0]['request'], spy)
except TimeoutError:
    limits['transport_timeout'] = {'exception_propagates': True, 'calls': spy.call_count}
else:
    raise AssertionError('Expected current experimental dispatch to propagate timeout')

isolation = read(RUN / 'responses/isolation.json')['checks']
assert len(isolation) == 20 and all(x['denied'] for x in isolation)
result = {
    'handoff_links_exist': len(links), 'verified_recorded_file_hashes': len(checked),
    'hash_checks_skipped': skipped, 'reviewed_lexical_expectations': len(expected),
    'raw_attempts_independently_graded': 180, 'prompt_only_pairs': len(pairs),
    'counts': dict(counts), 'nonservice_failures': failures,
    'both_pass_paired_medians': {route: {field: median(values) for field, values in fields.items()}
                                for route, fields in effects.items()},
    'exact_saved_evaluation_replay': {'2026-09-15': True, '2026-09-16': True},
    'historical_deepseek_missing_target': shadow_counts,
    'historical_glm_explicit_typed_mapping': glm_precheck,
    'integration_limit_probes': limits, 'saved_isolation_denials_checked': len(isolation),
    'scope': 'Offline review only; no model calls, corpus reads, production integration or fresh OS isolation attestation.'
}
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
