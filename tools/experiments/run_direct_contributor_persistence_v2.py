"""Offline fault timing matrix for the v2 attempt commit contract; no model calls."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

import direct_contributor_attempt_v2 as boundary
from run_direct_contributor_boundaries import envelope

ROOT = Path(__file__).resolve().parents[2]
FILES = ('source.json', 'request.json', 'started.json', 'response.json', 'result.json', 'completion.json')
MODES = ('before', 'partial', 'late', 'interrupted', 'partial_interrupted', 'omitted', 'corrupted')


class Interrupted(BaseException):
    """Simulates process interruption without being caught as a recoverable write error."""


class FaultStore(boundary.Store):
    def __init__(self, directory, target, mode):
        super().__init__(directory)
        self.target, self.mode = target, mode

    def write(self, name, raw):
        if name != self.target:
            return super().write(name, raw)
        if self.mode == 'before':
            raise OSError('injected before write')
        if self.mode == 'omitted':
            return
        if self.mode in ('partial', 'partial_interrupted'):
            super().write(name, raw[:len(raw) // 2])
        elif self.mode == 'corrupted':
            super().write(name, b'{}')
            return
        else:
            super().write(name, raw)
        if self.mode in ('interrupted', 'partial_interrupted'):
            raise Interrupted('injected interruption')
        raise OSError('injected after bytes written')


def inputs():
    base = json.loads((ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json').read_bytes())['cases'][0]
    source, request = deepcopy(base['source']), deepcopy(base['request'])
    identity = {'doc_id': 'persistence-fixture', 'variant_id': 'synthetic',
                'evidence_sha256': boundary.sha(boundary.encode(source))}
    job = boundary.freeze(source, request, identity)
    good = {'action': 'select', 'target_id': 'r05', 'contributor_ids': ['r01', 'r04'],
            'support_ids': ['s05', 's01'], 'reason': 'supported_direct_breakdown'}
    return source, identity, job, envelope(good)


def run(output):
    output = Path(output)
    output.mkdir(exist_ok=False)
    rows = []
    for target in FILES:
        for mode in MODES:
            directory = output / (target.removesuffix('.json') + '_' + mode)
            directory.mkdir()
            source, identity, job, response = inputs()
            calls = []
            def transport(payload):
                calls.append(boundary.sha(boundary.encode(payload)))
                return response
            try:
                result = boundary.dispatch(source, identity, job, transport,
                                           FaultStore(directory, target, mode), {'model': 'offline_stub'})
            except Interrupted:
                result = {'state': 'interrupted', 'persisted': None}
            replay = boundary.replay(directory)
            interrupted = mode in ('interrupted', 'partial_interrupted')
            expected_state = ('interrupted' if interrupted else
                              'commit_unknown' if target == 'completion.json' else 'persistence_failure')
            # Only a COMPLETE marker published after all verified dependencies commits.
            expected_replay = ('structure_accepted' if target == 'completion.json'
                               and mode in ('late', 'interrupted') else 'incomplete_attempt')
            expected_calls = 0 if target in FILES[:3] else 1
            expected_persisted = None if interrupted or target == 'completion.json' else False
            passed = (result['state'] == expected_state and result['persisted'] is expected_persisted
                      and replay.get('state') == expected_replay and len(calls) == expected_calls
                      and replay.get('model_calls') == 0)
            if target != 'completion.json':
                passed = passed and not (directory / 'completion.json').exists()
            rows.append({'file': target, 'fault': mode, 'dispatch': result, 'replay': replay,
                         'stub_transport_calls': len(calls), 'expected_state': expected_state,
                         'expected_replay': expected_replay, 'passed': passed})
    summary = {'scope': 'synthetic logical-source persistence only', 'network_calls': 0,
               'cases': len(rows), 'passed': sum(r['passed'] for r in rows), 'rows': rows}
    (output / 'observations.json').write_bytes(boundary.encode(summary))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('new_output', type=Path)
    args = parser.parse_args()
    result = run(args.new_output)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['passed'] == result['cases'] else 1)
