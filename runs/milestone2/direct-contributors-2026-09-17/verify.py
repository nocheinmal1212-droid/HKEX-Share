"""Independent raw-result tally and exact evaluator replay; no model calls or writes."""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
sys.path.insert(0, str(ROOT / 'tools/experiments'))
from evaluate_direct_contributor_run import evaluate


def read(path):
    return json.loads(path.read_bytes())


def main():
    saved = read(RUN / 'evaluation.json')
    assert evaluate(RUN) == saved
    key = read(RUN / 'evaluator-key.json')['cases']
    tally = Counter()
    support_observations = []
    truncations = []
    for answer in key:
        r = read(RUN / 'responses' / (answer['id'] + '.json'))
        if r['transport_status'] != 'received':
            tally[r['transport_status']] += 1
            continue
        assert r['http_status'] == 200
        raw = base64.b64decode(r['response_base64'], validate=True)
        assert hashlib.sha256(raw).hexdigest() == r['response_sha256']
        b = json.loads(raw)
        assert b['model'] == 'deepseek/deepseek-v4-pro-0813' and b['provider'] == 'Fireworks'
        c = b['choices'][0]
        if c['finish_reason'] != 'stop':
            assert c['finish_reason'] == 'length'
            assert b['usage']['completion_tokens'] == 2048
            content = c['message']['content']
            if content is not None:
                try:
                    json.loads(content)
                except ValueError:
                    pass
                else:
                    raise AssertionError('Unexpected complete JSON in this saved truncation; inspect without accepting it.')
            truncations.append({'call_id': answer['id'], 'case': answer['case'],
                                'content': content, 'completion_tokens': b['usage']['completion_tokens'],
                                'reasoning_tokens': b['usage']['completion_tokens_details']['reasoning_tokens']})
            tally['truncated'] += 1
            continue
        assert not c['message'].get('refusal')
        o = json.loads(c['message']['content'])
        e = answer['expected']
        correct = (o['action'] == e['action'] and o['target_id'] == e['target_id']
                   and set(o['contributor_ids']) == set(e['contributor_ids']))
        if correct:
            assert o['reason'] == e['reason']
            assert set(answer['support_requirements']['required_ids']) <= set(o['support_ids'])
            tally['full_pass'] += 1
        else:
            tally['wrong_relation'] += 1
        assert set(o['support_ids']) <= set(answer['job']['selected_ids'])
        support_observations.append({'call_id': answer['id'], 'case': answer['case'],
                                     'support_ids': o['support_ids'], 'relation_correct': correct})
    assert tally['full_pass'] == saved['full_passes']
    assert tally['wrong_relation'] == saved['relation_mismatches']
    assert sum(tally.values()) == saved['recorded'] == 42
    boundaries = read(RUN / 'boundaries-r2/summary.json')
    assert boundaries['passed'] == boundaries['executed_subcases_and_controls'] == 30
    assert all(row['passed'] for row in boundaries['rows'])
    isolation = {}
    for path, field in [('responses/preflight-v2.json', 'checks'), ('responses/isolation.json', 'checks'),
                        ('isolated-offline-replay-r3/access.json', 'protected_reads')]:
        records = read(RUN / path)[field]
        assert len(records) == 10 and all(r['denied'] for r in records)
        isolation[path] = len(records)
    result = {'exact_evaluation_replay': True, 'independent_raw_tally': dict(tally),
              'boundary_subcases_and_controls_passed': 30, 'protected_read_denials': isolation,
              'support_observations': support_observations,
              'truncations': truncations,
              'credential_redacted_records': sum(read(RUN / 'responses' / (a['id'] + '.json')).get('credential_redacted', False) for a in key),
              'limitations': ['Same-agent expectation/support review; no independent human adjudication.',
                              'No production IR integration or amount-invariance execution.'],
              'files_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(RUN.rglob('*')) if p.is_file() and not p.name.startswith('verification')}}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
