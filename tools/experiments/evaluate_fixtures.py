"""Offline evaluator for frozen synthetic experiments; never imported by worker."""
import argparse
import base64
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate JSON key')
            value[key] = item
        return value
    def bad_constant(value):
        raise ValueError('non-finite JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


def classify(record, answer):
    result = {'status': record['transport_status'], 'complete': False, 'contract_valid': False,
              'semantic_decision': 'unavailable', 'observed_output': None}
    if record['transport_status'] != 'received':
        return result
    if record['http_status'] != 200:
        result['status'] = 'access_or_parameter_unsupported' if record['http_status'] in (400, 401, 403, 404, 422) else 'http_error'
        return result
    try:
        response = parse(base64.b64decode(record['response_base64'], validate=True))
        if not isinstance(response, dict):
            raise ValueError('response object required')
        result.update(observed_model=response.get('model'), observed_provider=response.get('provider'),
                      system_fingerprint=response.get('system_fingerprint'), checkpoint_revision=None,
                      usage=response.get('usage'), response_id=response.get('id'))
        if response.get('model') != answer['model'] or response.get('provider') != answer['provider_name']:
            result['status'] = 'identity_mismatch'
            return result
        choices = response['choices']
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError('one choice required')
        choice = choices[0]
        result['finish_reason'] = choice.get('finish_reason')
        if choice.get('finish_reason') != 'stop':
            result['status'] = 'truncated' if choice.get('finish_reason') == 'length' else 'incomplete_response'
            return result
        message = choice['message']
        result['complete'] = True
        if message.get('refusal'):
            result['status'] = 'refusal'
            return result
        if message.get('tool_calls'):
            result['status'] = 'unexpected_response_mode'
            return result
        result['returned_reasoning_present'] = bool(message.get('reasoning') or message.get('reasoning_details'))
        try:
            output = parse(message['content'])
        except (ValueError, TypeError, KeyError):
            result['status'] = 'malformed_json'
            return result
        result['observed_output'] = output
        if isinstance(output, dict):
            result['selected_id_matches_expected'] = output.get('evidence_id') == answer['expected']['evidence_id']
            if output == answer['expected']:
                result['semantic_decision'] = 'expected'
            elif output.get('action') == 'abstain' and answer['expected']['action'] == 'label':
                result['semantic_decision'] = 'unexpected_abstention'
            elif output.get('action') != 'abstain' and answer['expected']['action'] == 'abstain':
                result['semantic_decision'] = 'failure_to_abstain'
            else:
                result['semantic_decision'] = 'wrong_selection_or_labels'
        if list(Draft202012Validator(answer['schema']).iter_errors(output)):
            result['status'] = 'invalid_schema'
            return result
        result['contract_valid'] = True
        if output == answer['expected']:
            result['status'] = 'passed'
        elif answer['expected']['action'] == 'abstain':
            result['status'] = 'failure_to_abstain'
        elif output.get('action') == 'abstain':
            result['status'] = 'unexpected_abstention'
        else:
            result['status'] = 'wrong_selection'
        return result
    except (ValueError, TypeError, KeyError, IndexError):
        result['status'] = 'malformed_response'
        return result


def evaluate(run, partial=False):
    plan = json.loads((run / 'execution-plan.json').read_text())
    manifest_raw = (run / 'requests.json').read_bytes()
    assert sha(manifest_raw) == plan['manifest_sha256']
    assert sha((run / 'evaluator-key.json').read_bytes()) == plan['evaluator_key_sha256']
    manifest = json.loads(manifest_raw)
    key = json.loads((run / 'evaluator-key.json').read_text())
    requests = {r['id']: r for r in manifest['requests']}
    rows, total_cost, unknown_cost, absent = [], Decimal('0'), 0, []
    for answer in key['cases']:
        path = run / 'responses' / (answer['id'] + '.json')
        if not path.exists():
            absent.append(answer['id'])
            continue
        record = json.loads(path.read_text())
        request = requests[answer['id']]
        assert record['id'] == answer['id']
        assert record['request_sha256'] == request['sha256'] == sha(base64.b64decode(request['body_base64'], validate=True))
        if 'response_base64' in record:
            raw = base64.b64decode(record['response_base64'], validate=True)
            assert sha(raw) == record['response_sha256']
            try:
                response = json.loads(raw, parse_float=Decimal)
                cost = response.get('usage', {}).get('cost')
                if cost is None:
                    unknown_cost += 1
                else:
                    total_cost += Decimal(str(cost))
            except (ValueError, AttributeError):
                unknown_cost += 1
        else:
            unknown_cost += 1
        rows.append({**answer, **classify(record, answer), 'elapsed_seconds': record['elapsed_seconds'],
                     'record_sha256': sha(path.read_bytes()), 'request_sha256': record['request_sha256'],
                     'credential_redacted': record.get('credential_redacted', False)})
    if not partial:
        assert not absent, absent
        assert json.loads((run / 'responses/completed.json').read_text())['calls'] == len(requests)
    oracle = {(r['case'], r['prompt'], r['strict'], r['budget']): r for r in rows if r['role'] == 'oracle'}
    for row in rows:
        if row['role'] == 'subject':
            comparison = oracle.get((row['case'], row['prompt'], row['strict'], row['budget']))
            row['oracle_comparison'] = ({'id': comparison['id'], 'status': comparison['status'],
                'same_final_output': row['observed_output'] is not None and row['observed_output'] == comparison['observed_output'],
                'interpretation': 'Independent comparison only; endpoint and timing differ. Oracle pass does not identify model weights as cause.'}
                if comparison else {'status': 'no_matching_oracle_observation'})
    groups = defaultdict(Counter)
    for row in rows:
        groups[row['route']][row['status']] += 1
    return {'planned': len(requests), 'completed_records': len(rows), 'missing_records': absent,
            'reported_cost_usd': str(total_cost), 'records_without_reported_cost': unknown_cost,
            'counts_by_route': {k: dict(v) for k, v in groups.items()}, 'rows': rows,
            'oracle_policy': key['role_interpretation']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--partial', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report = evaluate(args.run, args.partial)
    if args.out:
        with args.out.open('x') as stream:
            json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','missing_records')}, indent=2))
    for row in report['rows']:
        if row['status'] != 'passed':
            print(row['id'], row['route'], row['case'], row['prompt'], row['strict'], row['budget'], row['status'], row['observed_output'])


if __name__ == '__main__':
    main()
