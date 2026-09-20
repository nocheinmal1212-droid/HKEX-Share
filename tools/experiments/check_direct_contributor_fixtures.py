"""Offline proposal consistency checks; does not implement or grade model interpretation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check():
    paths = [ROOT / 'spec/diagnostics' / name for name in
             ('direct-contributors-inputs-v1.json', 'direct-contributors-expectations-v1.json')]
    inputs, key = [json.loads(p.read_bytes()) for p in paths]
    cases = {c['id']: c for c in inputs['cases']}
    answers = {c['id']: c for c in key['cases']}
    assert len(cases) == len(inputs['cases']) == len(answers) == len(key['cases']) == 14
    assert cases.keys() == answers.keys()
    assert inputs['execution']['inference_calls'] == 0
    assert inputs['execution']['production_dispatch'] is False
    assert key['status'] == 'proposed_expectations_not_independently_reviewed'
    sizes = []
    for id, case in cases.items():
        source, request = case['source'], case['request']
        items = {item['id']: item for item in source['items']}
        assert len(items) == len(source['items'])
        assert request['operation'] == inputs['operation']
        assert request['target_id'] in items
        assert len(request['candidate_ids']) == len(set(request['candidate_ids']))
        assert all(i in items for i in request['candidate_ids'])
        assert request['target_id'] not in request['candidate_ids']
        for item in items.values():
            assert isinstance(item['text'], str)
            assert all(ref in items and items[ref]['kind'] == 'header'
                       for ref in item.get('header_refs', []))
        answer = answers[id]['expected']
        assert answer['target_id'] == request['target_id']
        assert answer['action'] in inputs['action_vocabulary']
        assert answer['reason'] in inputs['reason_vocabulary']
        contributors = answer['contributor_ids']
        assert len(contributors) == len(set(contributors))
        assert set(contributors) <= set(request['candidate_ids'])
        assert bool(contributors) == (answer['action'] == 'select')
        assert all(i in items for i in answers[id]['support_requirements']['required_ids'])
        assert answers[id]['author_review_status'] == 'proposed_not_independently_reviewed'
        # This is a draft logical payload size, not a production IR context-bound assertion.
        sizes.append(len(json.dumps({'source': source, 'request': request},
                                    ensure_ascii=False, sort_keys=True).encode('utf-8')))

    # Independently stated transformations: compare exact input changes, not just answers.
    base = cases['S01']
    reordered = deepcopy(cases['S13'])
    reordered['source']['items'].reverse()
    assert reordered['source'] == base['source'] and reordered['request'] == base['request']
    shared_unknown = deepcopy(cases['S12']['source'])
    header = next(i for i in shared_unknown['items'] if i['id'] == 's03')
    assert header['text'] == 'Currency and scale not stated'
    header['text'] = 'HK$ million'
    assert shared_unknown == base['source']
    mapping = answers['S14']['evaluation_only_id_map']
    inverse = {v: k for k, v in mapping.items()}
    renamed = deepcopy(cases['S14'])
    for item in renamed['source']['items']:
        item['id'] = inverse[item['id']]
        if 'header_refs' in item:
            item['header_refs'] = [inverse[i] for i in item['header_refs']]
    renamed['request']['target_id'] = inverse[renamed['request']['target_id']]
    renamed['request']['candidate_ids'] = [inverse[i] for i in renamed['request']['candidate_ids']]
    assert renamed['source'] == base['source'] and renamed['request'] == base['request']
    assert {inverse[i] for i in answers['S14']['expected']['contributor_ids']} == {'r01', 'r04'}
    for id in ['S03', 'S06', 'S12', 'S13']:
        assert answers[id]['expected'] == answers['S01']['expected']
    assert answers['S02']['expected']['contributor_ids'] == ['r02', 'r03']
    for id in ['S04', 'S05', 'S07', 'S08', 'S09', 'S10', 'S11']:
        assert answers[id]['expected']['action'] == 'abstain'

    forbidden = {'expected', 'expected_model_output', 'contributor_ids', 'evaluation_only_id_map',
                 'support_requirements', 'author_review_status'}
    def inspect_input(value):
        if isinstance(value, dict):
            assert not (value.keys() & forbidden)
            for child in value.values():
                inspect_input(child)
        elif isinstance(value, list):
            for child in value:
                inspect_input(child)
    for case in cases.values():
        inspect_input(case)
    scenarios = key['boundary_scenarios']
    assert len({s['id'] for s in scenarios}) == len(scenarios) == 20
    assert all(s['execution_status'] == 'not_executed' for s in scenarios)
    assert key['future_source_transform']['status'] == 'not_instantiated'
    return {
        'status': 'proposal_consistency_checks_passed',
        'interpretation_cases_prepared': len(cases),
        'boundary_scenarios_specified_not_executed': len(scenarios),
        'interpretation_cases_executed': 0,
        'model_calls': 0,
        'production_integration': False,
        'max_draft_logical_payload_bytes': max(sizes),
        'files_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in paths},
        'limitation': 'Static references/control checks only. No semantic correctness, real IR fidelity, '
                      'runtime isolation, dispatch, persistence, amount invariance or provider acceptance claim.'
    }


if __name__ == '__main__':
    print(json.dumps(check(), indent=2, sort_keys=True))
