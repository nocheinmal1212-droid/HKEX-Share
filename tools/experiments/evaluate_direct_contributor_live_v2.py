"""Offline verification of the frozen live v2 run; evaluator keys never enter its worker."""
import argparse
import base64
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

from direct_contributor_attempt_v2 import encode, parse, replay, sha
from direct_contributor_boundary import interpret_response

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return parse(path.read_bytes())


def evaluate(run, partial=False):
    plan = read(run / 'execution-plan.json')
    for path, digest in plan['hashes'].items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    manifest_raw = (run / 'manifest.json').read_bytes()
    manifest = parse(manifest_raw)
    answers = {a['id']: a for a in read(run / 'evaluator-key.json')['cases']}
    rows, missing = [], []
    cost, missing_cost = Decimal('0'), 0
    previous_requests = read(ROOT / 'runs/milestone2/direct-contributors-2026-09-17/requests.json')['requests']
    for index, entry in enumerate(manifest['attempts']):
        directory = run / 'attempts' / entry['id']
        if not (directory / 'observation.json').exists():
            missing.append(entry['id'])
            continue
        observed = read(directory / 'observation.json')
        answer = answers[entry['id']]
        assert sha(encode(entry['configuration']['wire_request'])) == entry['configuration']['wire_request_sha256']
        assert entry['configuration']['wire_request_sha256'] == previous_requests[index if index < 14 else 0]['sha256']
        assert read(directory / 'source.json') == entry['source']
        assert read(directory / 'request.json') == entry['job']
        assert observed['id'] == entry['id'] and observed['fault'] == entry['fault']
        assert observed['network_attempts'] == 1
        assert replay(directory) == observed['replay']
        assert observed['replay']['model_calls'] == 0
        saved_result = read(directory / 'result.json')
        assert saved_result['configuration'] == entry['configuration']
        response = read(directory / 'response.json')
        assert response['wire_request_sha256'] == entry['configuration']['wire_request_sha256']
        raw_response = {k: v for k, v in response.items() if k not in ('body_base64', 'body_sha256')}
        model, provider, usage, finish, identity_match, api_error = None, None, {}, None, None, None
        if 'body_base64' in response:
            raw = base64.b64decode(response['body_base64'], validate=True)
            assert sha(raw) == response['body_sha256']
            raw_response['body'] = raw
            try:
                envelope = json.loads(raw, parse_float=Decimal)
                model, provider = envelope.get('model'), envelope.get('provider')
                usage = envelope.get('usage') or {}
                finish = (envelope.get('choices') or [{}])[0].get('finish_reason')
                api_error = envelope.get('error')
            except (ValueError, AttributeError, TypeError, IndexError):
                pass
            if response.get('http_status') == 200:
                identity_match = model == plan['model'] and provider == plan['expected_response_provider']
        if usage.get('cost') is not None:
            cost += Decimal(str(usage['cost']))
        else:
            missing_cost += 1
        decision = interpret_response(entry['job'], raw_response)
        for k, v in decision.items():
            assert saved_result[k] == v
        if entry['fault']:
            persistence_pass = (observed['dispatch']['state'] == 'persistence_failure'
                                and observed['dispatch']['persisted'] is False
                                and observed['replay']['state'] == 'incomplete_attempt'
                                and not (directory / 'completion.json').exists())
        else:
            persistence_pass = (observed['dispatch'] == {**saved_result, 'persisted': True}
                                and observed['replay'] == {**saved_result, 'model_calls': 0, 'historical_model_calls': 1})
        relation, reason, support = None, None, None
        output = decision.get('model_output')
        if identity_match and decision['state'] in ('structure_accepted', 'model_abstention'):
            expected = answer['expected']
            relation = (output['action'] == expected['action'] and output['target_id'] == expected['target_id']
                        and set(output['contributor_ids']) == set(expected['contributor_ids']))
            reason = output['reason'] == expected['reason']
            support = set(answer['support_requirements']['required_ids']) <= set(output['support_ids'])
        rows.append({'id': entry['id'], 'case': answer['case'], 'fault': entry['fault'],
                     'persistence_pass': persistence_pass, 'dispatch_state': observed['dispatch']['state'],
                     'replay_state': observed['replay']['state'], 'response_decision': decision,
                     'http_status': response.get('http_status'), 'transport_status': response['transport_status'],
                     'served_model': model, 'served_provider': provider, 'identity_match': identity_match,
                     'finish_reason': finish, 'api_error': api_error,
                     'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'),
                     'elapsed_seconds': response['elapsed_seconds'], 'credential_redacted': response.get('credential_redacted', False),
                     'relation_match': relation, 'reason_match': reason, 'required_support_complete': support,
                     'full_semantic_pass': relation is True and reason is True and support is True})
    if not partial:
        assert not missing, missing
        batch = read(run / 'attempts/batch.json')
        assert batch['manifest_sha256'] == sha(manifest_raw)
        assert len(batch['observations']) == 15
        assert len(batch['checks']) == 12 and all(c['denied'] for c in batch['checks'])
        preflight = read(run / 'attempts/preflight.json')
        assert preflight['manifest_sha256'] == sha(manifest_raw) and preflight['network_calls'] == 0
        assert len(preflight['checks']) == 12 and all(c['denied'] for c in preflight['checks'])
    ordinary = [r for r in rows if not r['fault']]
    return {'scope': plan['scope'], 'planned_network_attempts': 15, 'recorded_network_attempts': len(rows),
            'missing': missing, 'unchanged_wire_requests_from_prior_run': True,
            'persistence_passes': sum(r['persistence_pass'] for r in rows),
            'ordinary_committed_and_replayed': sum(r['persistence_pass'] for r in ordinary),
            'ordinary_full_semantic_passes': sum(r['full_semantic_pass'] for r in ordinary),
            'ordinary_relation_mismatches': sum(r['relation_match'] is False for r in ordinary),
            'ordinary_relation_unavailable': sum(r['relation_match'] is None for r in ordinary),
            'ordinary_states': dict(Counter(r['dispatch_state'] for r in ordinary)),
            'reported_cost_usd': str(cost), 'records_without_reported_cost': missing_cost,
            'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = evaluate(args.run, args.partial)
    if args.out:
        with args.out.open('xb') as stream:
            stream.write(encode(result))
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    for row in result['rows']:
        print(row['id'], row['case'], row['dispatch_state'], row['http_status'], row['finish_reason'], row['full_semantic_pass'])
