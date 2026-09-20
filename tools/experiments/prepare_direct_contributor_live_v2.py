"""Freeze one live pass plus one late-write fault; keep evaluator answers outside runtime."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from direct_contributor_live_v2 import wire_request
from direct_contributor_attempt_v2 import encode, sha

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT / 'runs/milestone2/direct-contributors-2026-09-17'
RUN = ROOT / 'runs/milestone2/direct-contributor-live-v2-2026-09-17'
STAGE = Path('/private/tmp/audit-direct-contributor-live-v2-2026-09-17')


def write(path, value):
    with path.open('xb') as stream:
        stream.write(encode(value))


def main():
    RUN.mkdir(exist_ok=False)
    STAGE.mkdir(exist_ok=False)
    output = RUN / 'attempts'
    output.mkdir()
    prompt = (PRIOR / 'prompt.txt').read_text()
    answers = json.loads((PRIOR / 'evaluator-key.json').read_bytes())['cases'][:14]
    attempts, evaluator = [], []
    for index, answer in enumerate([*answers, answers[0]], 1):
        selected = json.loads((PRIOR / 'prepared' / (answer['case'] + '.json')).read_bytes())
        source, job = selected['source'], selected['job']
        body = wire_request(job, job['payload'], prompt)
        id = f'call-{index:03d}'
        fault = 'late_result_write' if index == 15 else None
        config = {'mode': 'live_logical_fixture_v2', 'wire_request': body,
                  'wire_request_sha256': sha(encode(body)), 'deadline_seconds': 30,
                  'max_response_bytes': 131072, 'retries': 0, 'fault': fault}
        attempts.append({'id': id, 'source': source, 'identity': job['identity'], 'job': job,
                         'configuration': config, 'fault': fault})
        evaluator.append({**answer, 'id': id, 'fault': fault, 'repetition': 1})
        (output / id).mkdir()
    protected = [str(ROOT / '.env'), str(ROOT / 'corpus/error_detail.jsonl'),
                 str(ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json'),
                 str(ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json'),
                 str(RUN / 'evaluator-key.json'), str(PRIOR / 'evaluator-key.json')]
    manifest = {'version': 'direct-contributor-live-v2-2026-09-17', 'prompt': prompt,
                'attempts': attempts, 'protected_paths': protected}
    write(RUN / 'manifest.json', manifest)
    shutil.copyfile(RUN / 'manifest.json', STAGE / 'manifest.json')
    write(RUN / 'evaluator-key.json', {'cases': evaluator})
    code = ['direct_contributor_live_v2.py', 'direct_contributor_attempt_v2.py',
            'direct_contributor_boundary.py', 'direct_contributor_worker.py']
    for name in code:
        shutil.copyfile(ROOT / 'tools/experiments' / name, STAGE / name)
    profile = '(version 1)\n(allow default)\n(deny file-read-data (subpath ' + json.dumps(str(ROOT)) + '))\n'
    profile += '(allow file-read-data (subpath ' + json.dumps(str(output)) + '))\n'
    profile += '(deny file-write*)\n(allow file-write* (subpath ' + json.dumps(str(output)) + ') (subpath "/dev"))\n'
    (STAGE / 'sandbox.sb').write_text(profile)
    (RUN / 'sandbox.sb').write_text(profile)
    write(RUN / 'execution-plan.json', {
        'authorized_by': 'Send live calls through the fixed dispatcher as the first honest end-to-end check.',
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'planned_calls': 15,
        'ordinary_cases': 14, 'live_late_write_cases': 1,
        'model': 'deepseek/deepseek-v4-pro-0813', 'requested_provider': 'fireworks',
        'expected_response_provider': 'Fireworks', 'max_tokens': 2048, 'temperature': 0,
        'deadline_seconds': 30, 'retries': 0, 'fallbacks': False, 'concurrency': 1,
        'order': 'S01 through S14 once, then S01 again with a late result-write fault; no adaptive changes.',
        'scope': 'First live connected logical-fixture dispatch/transport/validation/persistence/replay check; not production IR or financial audit end-to-end.',
        'acceptance': 'All 14 ordinary attempts commit their actual terminal outcomes and replay exactly with zero replay model calls; live late-write attempt persists response/result but has no completion and replays incomplete. Report semantic grading separately, retaining unavailable outcomes.',
        'semantic_grading': 'Reuse frozen prior expectations: exact action/target/unordered contributors, reason and required support coverage; one sample per fixture, no independent new label review.',
        'stop_policy': 'Bound to 15 transport invocations; no retries or automatic reruns; unexpected uncaught exceptions stop the batch with partial artifacts retained.',
        'hashes': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [
            *[ROOT / 'tools/experiments' / name for name in code],
            ROOT / 'tools/experiments/prepare_direct_contributor_live_v2.py',
            ROOT / 'tools/experiments/launch_direct_contributor_live_v2.py',
            ROOT / 'tests/test_direct_contributor_live_v2.py',
            RUN / 'manifest.json', RUN / 'evaluator-key.json', RUN / 'sandbox.sb', PRIOR / 'prompt.txt']}})
    print('Frozen 14 ordinary live attempts and one live late-write injection; zero network calls.')


if __name__ == '__main__':
    main()
