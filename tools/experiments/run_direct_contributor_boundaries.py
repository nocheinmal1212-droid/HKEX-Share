"""Execute authored boundary fault scenarios against the experimental dispatcher, offline."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock

import direct_contributor_boundary as boundary

ROOT = Path(__file__).resolve().parents[2]


def envelope(output=None, *, finish='stop', refusal=None, tool_calls=None, content=None):
    message = {'content': json.dumps(output) if content is None else content, 'refusal': refusal}
    if tool_calls:
        message['tool_calls'] = tool_calls
    return {'transport_status': 'received', 'http_status': 200,
            'body': boundary.encode({'choices': [{'finish_reason': finish, 'message': message}]})}


class FaultStore(boundary.Store):
    def __init__(self, directory, fail=None, tamper=False):
        super().__init__(directory)
        self.fail = fail
        self.tamper = tamper

    def write(self, name, raw):
        if name == self.fail:
            raise OSError('injected persistence failure')
        if name == 'request.json' and self.tamper:
            value = json.loads(raw)
            value['payload']['evidence'][0]['text'] = 'tampered after freezing'
            raw = boundary.encode(value)
        super().write(name, raw)


def run(output):
    output = Path(output)
    output.mkdir(exist_ok=False)
    fixtures = json.loads((ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json').read_bytes())
    key = json.loads((ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json').read_bytes())
    base = fixtures['cases'][0]
    requirements = {s['id']: s for s in key['boundary_scenarios']}
    good = {'action': 'select', 'target_id': 'r05', 'contributor_ids': ['r01', 'r04'],
            'support_ids': ['s05', 's01', 's02', 's03', 's04'], 'reason': 'supported_direct_breakdown'}
    abstain = {'action': 'abstain', 'target_id': 'r05', 'contributor_ids': [],
               'support_ids': ['s05'], 'reason': 'missing_evidence'}
    variants = [('D01', ''), ('D02', ''), ('D03', ''),
                *[('D04', x) for x in ('doc_id', 'variant_id', 'evidence_sha256')],
                ('D05', ''), ('D06', 'overflow'), ('D06', 'exact_multibyte_control'),
                ('D07', ''), ('D08', ''), ('D09', ''), ('D10', ''),
                ('D11', 'parseable'), ('D11', 'null_content'), ('D12', ''), ('D13', ''),
                ('D14', ''), ('D15', ''), ('D16', 'response_write'), ('D16', 'result_write'),
                ('D17', ''), ('D18', ''), ('D19', ''),
                *[('D20', x) for x in ('duplicate', 'nonfinite', 'envelope', 'tool_calls')],
                ('C01_selected', ''), ('C02_model_abstention', '')]
    observations = []
    for id, variant in variants:
        name = id + ('_' + variant if variant else '')
        directory = output / name
        directory.mkdir()
        source, request = deepcopy(base['source']), deepcopy(base['request'])
        expected = deepcopy(requirements.get(id, {}))
        response = envelope(good)
        store = FaultStore(directory)
        if id == 'D02':
            request['target_id'] = 'absent'
        elif id == 'D03':
            source['items'].append(deepcopy(source['items'][0]))
        elif id == 'D05':
            store.tamper = True
        elif id == 'D07':
            next(i for i in source['items'] if i['id'] == 'r05')['text'] = ''
        elif id == 'D08':
            next(i for i in source['items'] if i['id'] == 'r05')['content_state'] = 'unsupported'
        elif id == 'D10':
            response = envelope(good, refusal='synthetic refusal')
        elif id == 'D11':
            response = envelope(good, finish='length')
            if variant == 'null_content':
                value = json.loads(response['body'])
                value['choices'][0]['message']['content'] = None
                response['body'] = boundary.encode(value)
        elif id == 'D12':
            response = envelope({**good, 'contributor_ids': ['s01']})
        elif id == 'D13':
            response = envelope({**good, 'contributor_ids': ['unseen']})
        elif id == 'D14':
            response = envelope({**good, 'contributor_ids': ['r01', 'r02']})
        elif id == 'D15':
            store.fail = 'request.json'
        elif id == 'D16':
            store.fail = 'response.json' if variant == 'response_write' else 'result.json'
        elif id == 'D19':
            source['limitations'].append({'container_id': 't01', 'code': 'unresolved_region',
                                         'description': 'Required source evidence is unresolved.'})
        elif id == 'D20':
            if variant == 'duplicate':
                response = envelope(content='{"action":"select","action":"abstain"}')
            elif variant == 'nonfinite':
                response = envelope(content='{"action":NaN}')
            elif variant == 'envelope':
                response = {'transport_status': 'received', 'http_status': 200, 'body': b'{"choices":[null]}'}
            else:
                response = envelope(good, tool_calls=[{'id': 'not-requested'}])
            expected['expected_reason'] = {'duplicate': 'malformed_json', 'nonfinite': 'malformed_json',
                                           'envelope': 'malformed_response', 'tool_calls': 'unexpected_response_mode'}[variant]
        if id in ('C01_selected', 'C02_model_abstention') or (id == 'D06' and variant == 'exact_multibyte_control'):
            expected = {'expected_state': 'structure_accepted', 'expected_reason': 'semantic_correctness_unverified', 'expected_model_calls': 1}
            if id == 'C02_model_abstention':
                response = envelope(abstain)
                expected.update(expected_state='model_abstention', expected_reason='model_abstained')

        if id == 'D06':
            payload = boundary.project(source, request, [i['id'] for i in source['items']])
            extra = boundary.MAX_CONTEXT_BYTES - len(boundary.encode(payload))
            source['items'][0]['text'] += '漢' * (extra // 3) + 'x' * (extra % 3)
            if variant == 'overflow':
                source['items'][0]['text'] += 'x'
        identity = {'doc_id': 'synthetic', 'variant_id': 'sample', 'evidence_sha256': boundary.sha(boundary.encode(source))}
        job = boundary.freeze(source, request, identity)
        if id == 'D01':
            job = boundary.freeze(source, request, identity, selected_ids=[i['id'] for i in source['items'] if i['id'] != 'r05'])
        elif id == 'D04':
            job['identity'][variant] = 'foreign'
        elif id == 'D19':
            job['payload']['limitations'] = []
            job['payload_sha256'] = boundary.sha(boundary.encode(job['payload']))
        before = deepcopy(job)
        spy = Mock(return_value=deepcopy(response))
        if id == 'D09':
            spy.side_effect = TimeoutError('injected timeout')
        elif id == 'D18':
            response = envelope({**good, 'contributor_ids': ['s01']})
            def mutate(payload):
                payload['candidate_ids'].append('s01')
                return deepcopy(response)
            spy.side_effect = mutate
        if id == 'D17':
            store.write('request.json', boundary.encode(job))
            store.write('started.json', boundary.encode({'request_sha256': boundary.sha(boundary.encode(job))}))
            result = boundary.replay(directory)
        else:
            result = boundary.dispatch(source, identity, job, spy, store,
                                       {'model': 'offline_stub', 'operation_version': boundary.VERSION})
        checks = {
            'state': result['state'] == expected['expected_state'],
            'reason': result['reason'] == expected['expected_reason'],
            'spy_calls': spy.call_count == expected['expected_model_calls'],
            'recorded_calls': result['model_calls'] == expected['expected_model_calls'],
            'caller_unchanged': job == before,
        }
        if result.get('persisted'):
            checks['terminal_record_exists'] = (directory / 'result.json').is_file()
            if checks['terminal_record_exists']:
                checks['terminal_record_matches'] = json.loads(store.read('result.json')) == {k: v for k, v in result.items() if k != 'persisted'}
        if id in ('D15', 'D16', 'D17'):
            checks['no_completion_record'] = not (directory / 'result.json').exists()
        if spy.call_count and id not in ('D09',) and store.fail != 'response.json':
            record = json.loads(store.read('response.json'))
            checks['raw_response_preserved'] = record['body_sha256'] == boundary.sha(response['body'])
        if id == 'D14':
            checks['semantic_error_still_visible'] = set(result['model_output']['contributor_ids']) != {'r01', 'r04'}
        if id in ('C01_selected', 'C02_model_abstention'):
            replay = boundary.replay(directory)
            checks['replay_no_call_same_outcome'] = (replay['model_calls'] == 0 and replay['historical_model_calls'] == 1
                                                    and replay['state'] == result['state'])
        observation = {'id': id, 'variant': variant, 'passed': all(checks.values()),
                       'checks': checks, 'observed': result, 'expected': expected,
                       'payload_bytes': len(boundary.encode(job['payload'])), 'artifacts': str(directory)}
        observations.append(observation)
    summary = {'scope': 'Experimental logical-source dispatcher; no real IR or production integration.',
               'scenarios': 20, 'executed_subcases_and_controls': len(observations),
               'passed': sum(r['passed'] for r in observations), 'network_calls': 0,
               'rows': observations}
    (output / 'summary.json').write_bytes(boundary.encode(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))
    for row in result['rows']:
        if not row['passed']:
            print(row['id'], row['variant'], row['checks'], row['observed'])
    raise SystemExit(0 if result['passed'] == result['executed_subcases_and_controls'] else 1)
