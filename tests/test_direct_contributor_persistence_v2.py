"""Commit visibility, late failures, corrupt artifacts and isolated offline replay."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools/experiments'
with patch.object(sys, 'path', [str(TOOLS), *sys.path]):
    import direct_contributor_attempt_v2 as boundary
    import run_direct_contributor_persistence_v2 as runner
    from run_direct_contributor_boundaries import envelope


class PersistenceV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def dispatch(self, name='attempt', transform=None, response=None, store_class=boundary.Store):
        directory = self.root / name
        directory.mkdir()
        source, identity, job, saved = runner.inputs()
        if transform:
            transform(source, identity, job)
        calls = []
        def transport(payload):
            calls.append(payload)
            return saved if response is None else response
        result = boundary.dispatch(source, identity, job, transport, store_class(directory), {'model': 'offline_stub'})
        return directory, result, calls

    def test_42_write_timing_cases(self):
        result = runner.run(self.root / 'matrix')
        self.assertEqual(result['cases'], 42)
        self.assertEqual(result['passed'], 42, [(r['file'], r['fault']) for r in result['rows'] if not r['passed']])

    def test_terminal_outcomes_replay_without_transport(self):
        cases = [
            ('selected', None, None, 'structure_accepted', 1),
            ('timeout', None, {'transport_status': 'timeout'}, 'transport_failure', 1),
            ('abstain', None, envelope({'action': 'abstain', 'target_id': 'r05', 'contributor_ids': [],
              'support_ids': ['s05'], 'reason': 'missing_evidence'}), 'model_abstention', 1),
            ('bad_identity', lambda s, i, j: i.update(evidence_sha256='0' * 64), None, 'rejected_input', 0),
            ('bad_request_version', lambda s, i, j: j.update(version='invalid'), None, 'rejected_input', 0),
            ('missing_target', lambda s, i, j: j['request'].update(target_id='absent'), None, 'precondition_abstention', 0),
        ]
        for name, transform, response, state, count in cases:
            with self.subTest(name=name):
                directory, result, calls = self.dispatch(name, transform, response)
                replay = boundary.replay(directory)
                self.assertTrue(result['persisted'])
                self.assertEqual((result['state'], replay['state']), (state, state))
                self.assertEqual((len(calls), replay['historical_model_calls'], replay['model_calls']), (count, count, 0))

    def test_missing_or_changed_dependencies_invalidate_commit(self):
        for name in runner.FILES:
            for action in ('remove', 'change'):
                with self.subTest(name=name, action=action):
                    directory, _, _ = self.dispatch(name + action)
                    path = directory / name
                    if action == 'remove':
                        path.unlink()
                    else:
                        path.write_bytes(b'{}')
                    self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')

    def test_invalid_marker_inventory_is_not_dereferenced(self):
        markers = [None, [], {'version': 'old', 'artifacts': {}},
                   {'version': boundary.VERSION, 'artifacts': {'../protected.json': '0' * 64}},
                   {'version': boundary.VERSION, 'artifacts': dict.fromkeys(runner.FILES[:2] + ('result.json',), 'invalid')}]
        for index, marker in enumerate(markers):
            directory, _, _ = self.dispatch(str(index))
            (directory / boundary.COMPLETION).write_bytes(boundary.encode(marker))
            original = boundary.Store.read
            reads = []
            def read(store, name):
                reads.append(name)
                return original(store, name)
            with patch.object(boundary.Store, 'read', read):
                self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')
            self.assertEqual(reads, [boundary.COMPLETION])

    def test_rehashed_but_inconsistent_bindings_fail(self):
        mutations = [lambda r: r.update(model_calls=0), lambda r: r.update(model_calls=True),
                     lambda r: r.update(source_snapshot_sha256='0' * 64),
                     lambda r: r.update(request_sha256='0' * 64),
                     lambda r: r.update(configuration={'model': 'different'}),
                     lambda r: r.update(response_record_sha256='0' * 64)]
        for index, mutate in enumerate(mutations):
            directory, _, _ = self.dispatch(str(index))
            result = boundary.parse((directory / 'result.json').read_bytes())
            mutate(result)
            raw = boundary.encode(result)
            (directory / 'result.json').write_bytes(raw)
            marker = boundary.parse((directory / boundary.COMPLETION).read_bytes())
            marker['artifacts']['result.json'] = boundary.sha(raw)
            (directory / boundary.COMPLETION).write_bytes(boundary.encode(marker))
            self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')

    def test_fsync_error_never_commits_result_bytes(self):
        real = boundary.os.fsync
        count = 0
        def fsync(fd):
            nonlocal count
            count += 1
            if count == 5:  # source, request, started, response, result
                raise OSError('injected result fsync failure')
            real(fd)
        with patch.object(boundary.os, 'fsync', fsync):
            directory, result, _ = self.dispatch()
        self.assertEqual(count, 5)
        self.assertEqual(result['state'], 'persistence_failure')
        self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')

    def test_readback_failure_never_commits(self):
        class BrokenReadback(boundary.Store):
            def read(self, name):
                if name == 'result.json':
                    raise OSError('injected result readback error')
                return super().read(name)
        directory, result, _ = self.dispatch(store_class=BrokenReadback)
        self.assertEqual(result['state'], 'persistence_failure')
        self.assertFalse((directory / boundary.COMPLETION).exists())
        self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')

    def test_reuse_refused_without_overwriting_or_resending(self):
        directory, _, _ = self.dispatch()
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        source, identity, job, _ = runner.inputs()
        def forbidden(_):
            self.fail('reuse must not call transport')
        result = boundary.dispatch(source, identity, job, forbidden, boundary.Store(directory), {})
        self.assertEqual(result['state'], 'attempt_conflict')
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})
        self.assertEqual(boundary.replay(directory)['state'], 'structure_accepted')

    def test_frozen_v1_folders_are_not_implicitly_migrated(self):
        import direct_contributor_boundary as v1
        source, identity, job, response = runner.inputs()
        directory = self.root / 'v1'
        directory.mkdir()
        result = v1.dispatch(source, identity, job, lambda _: response, v1.Store(directory), {})
        self.assertTrue(result['persisted'])
        self.assertEqual(v1.replay(directory)['state'], 'structure_accepted')
        self.assertEqual(boundary.replay(directory)['state'], 'incomplete_attempt')

    def test_mutation_result_only_replay_is_detected(self):
        original = boundary.replay
        def weak(directory):
            path = Path(directory) / 'result.json'
            try:
                return {**boundary.parse(path.read_bytes()), 'model_calls': 0}
            except (OSError, ValueError):
                return original(directory)
        with patch.object(boundary, 'replay', weak):
            result = runner.run(self.root / 'mutant')
        self.assertFalse(next(r for r in result['rows'] if r['file'] == 'result.json' and r['fault'] == 'late')['passed'])

    def test_isolated_v2_dispatch_and_replay(self):
        directory, _, _ = self.dispatch()
        output = self.root / 'isolated'
        output.mkdir()
        _, identity, _, _ = runner.inputs()
        payload = {'source_path': str(directory / 'source.json'), 'job_path': str(directory / 'request.json'),
                   'response_path': str(directory / 'response.json'), 'identity': identity, 'output': str(output),
                   'forbidden': [str(ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json'),
                                 str(self.root / 'unselected.json')]}
        proc = subprocess.run([sys.executable, '-I', '-B', str(TOOLS / 'direct_contributor_offline_worker_v2.py')],
                              input=json.dumps(payload), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        access = boundary.parse((output / 'access.json').read_bytes())
        self.assertEqual((access['result_state'], access['replay_state']), ('structure_accepted', 'structure_accepted'))
        self.assertEqual((access['stub_transport_calls'], access['network_calls']), (1, 0))
        self.assertEqual(len(access['protected_reads']), 4)
        self.assertTrue(all(r['denied'] for r in access['protected_reads']))


if __name__ == '__main__':
    unittest.main()
