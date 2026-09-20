"""Replay raw responses and separate relation, reason and support grading. Offline only."""
import argparse
import base64
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path

from direct_contributor_boundary import encode, sha, interpret_response

ROOT = Path(__file__).resolve().parents[2]


def evaluate(run, partial=False):
    run = Path(run)
    plan = json.loads((run / 'execution-plan.json').read_bytes())
    for path, digest in plan['hashes'].items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    requests = json.loads((run / 'requests.json').read_bytes())['requests']
    key = json.loads((run / 'evaluator-key.json').read_bytes())['cases']
    assert len({r['id'] for r in requests}) == len(requests) == len(key) == 42
    requests = {r['id']: r for r in requests}
    rows, missing, cost, missing_cost = [], [], Decimal('0'), 0
    for answer in key:
        id = answer['id']
        path = run / 'responses' / (id + '.json')
        if not path.exists():
            missing.append(id)
            continue
        record_raw = path.read_bytes()
        record = json.loads(record_raw)
        request = requests[id]
        request_raw = base64.b64decode(request['body_base64'], validate=True)
        assert sha(request_raw) == request['sha256'] == record['request_sha256']
        start = json.loads((run / 'responses' / (id + '.started.json')).read_bytes())
        assert start['request_sha256'] == record['request_sha256'] and start['id'] == record['id'] == id
        assert start['started_at'] == record['started_at']
        response = {'transport_status': record['transport_status'], 'http_status': record.get('http_status')}
        metadata = {}
        if 'response_base64' in record:
            raw = base64.b64decode(record['response_base64'], validate=True)
            assert sha(raw) == record['response_sha256']
            response['body'] = raw
            body = json.loads(raw)
            usage = body.get('usage', {})
            raw_cost = json.loads(raw, parse_float=Decimal).get('usage', {}).get('cost')
            if raw_cost is not None:
                cost += Decimal(str(raw_cost))
            else:
                missing_cost += 1
            metadata = {'served_model': body.get('model'), 'served_provider': body.get('provider'),
                        'prompt_tokens': usage.get('prompt_tokens'), 'completion_tokens': usage.get('completion_tokens'),
                        'finish_reason': (body.get('choices') or [{}])[0].get('finish_reason')}
        else:
            missing_cost += 1
        decision = interpret_response(answer['job'], response)
        if record.get('http_status') == 200 and (metadata['served_model'] != plan['model'] or metadata['served_provider'] != plan['provider']):
            decision = {'state': 'identity_mismatch', 'reason': 'unexpected_served_identity'}
        output = decision.get('model_output')
        relation_match = reason_match = support_complete = None
        if decision['state'] in ('structure_accepted', 'model_abstention'):
            expected = answer['expected']
            relation_match = (output['action'] == expected['action'] and output['target_id'] == expected['target_id']
                              and set(output['contributor_ids']) == set(expected['contributor_ids']))
            reason_match = output['reason'] == expected['reason']
            support_complete = set(answer['support_requirements']['required_ids']) <= set(output['support_ids'])
        rows.append({'id': id, 'case': answer['case'], 'repetition': answer['repetition'],
                     **decision, **metadata, 'relation_match': relation_match, 'reason_match': reason_match,
                     'required_support_complete': support_complete,
                     'full_pass': relation_match is True and reason_match is True and support_complete is True,
                     'elapsed_seconds': record['elapsed_seconds'], 'request_sha256': request['sha256'],
                     'response_record_sha256': sha(record_raw), 'http_status': record.get('http_status')})
    if not partial:
        assert not missing, missing
        assert json.loads((run / 'responses/completed.json').read_bytes())['calls'] == 42
    by_case = defaultdict(Counter)
    for row in rows:
        status = 'full_pass' if row['full_pass'] else row['state']
        if row['relation_match'] is False:
            status = 'wrong_relation_or_abstention'
        elif row['relation_match'] is True and not row['full_pass']:
            status = 'reason_or_support_mismatch'
        by_case[row['case']][status] += 1
    return {'planned': 42, 'recorded': len(rows), 'missing': missing,
            'transport_and_boundary_states': dict(Counter(r['state'] for r in rows)),
            'relation_matches': sum(r['relation_match'] is True for r in rows),
            'relation_mismatches': sum(r['relation_match'] is False for r in rows),
            'relation_unavailable': sum(r['relation_match'] is None for r in rows),
            'full_passes': sum(r['full_pass'] for r in rows),
            'cases_with_at_least_one_structurally_valid_answer': len({r['case'] for r in rows if r['relation_match'] is not None}),
            'counts_by_case': {k: dict(v) for k, v in sorted(by_case.items())},
            'reported_cost_usd': str(cost), 'records_without_reported_cost': missing_cost,
            'rows': rows,
            'scope': 'Fixture interpretation only. Full-pass support coverage is mechanical; review extra support relevance separately. Timeouts remain unavailable, not incorrect semantic answers.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('run', type=Path)
    p.add_argument('--partial', action='store_true')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    result = evaluate(args.run, args.partial)
    if args.out:
        with args.out.open('xb') as stream:
            stream.write(encode(result))
    print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'missing')}, indent=2))
    for row in result['rows']:
        if not row['full_pass']:
            print(row['id'], row['case'], row['state'], row.get('model_output'))
