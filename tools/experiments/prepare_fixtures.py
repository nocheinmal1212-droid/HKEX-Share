"""Offline preparation: network request manifest and separate evaluator key."""
import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/milestone2/hypothesis-fixtures-2026-09-15'
STAGE = Path('/private/tmp/audit-fixtures-2026-09-15-v1')


def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, obj):
    with path.open('xb') as f:
        f.write(encode(obj))


def build_body(fixture, case, model, tag, prompt, strict=True, budget=512):
    schema = deepcopy(fixture['schema_template'])
    schema['properties']['evidence_id']['enum'] = [e['id'] for e in case['input']['evidence']] + [None]
    body = {'model': model, 'messages': [
        {'role': 'system', 'content': fixture['prompts'][prompt]},
        {'role': 'user', 'content': encode(case['input']).decode()}],
        'max_tokens': budget, 'temperature': 0, 'stream': False,
        'provider': {'only': [tag], 'allow_fallbacks': False, 'require_parameters': True}}
    if strict:
        body['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'synthetic_label', 'strict': True, 'schema': schema}}
    return body, schema


def main():
    fixture_path = ROOT / 'spec/diagnostics/hypothesis-fixtures-v1.json'
    fixture = json.loads(fixture_path.read_text())
    roles = {'pro': 'subject', 'flash': 'subject', 'glm': 'subject', 'gemini': 'oracle'}
    route_defs = [('pro', 'baidu/fp8'), ('flash', 'open-inference/fp8'),
                  ('glm', 'deepinfra/fp4'), ('gemini', 'google-ai-studio'), ('pro_secondary', 'ionstream')]
    routes = {}
    for name, tag in route_defs:
        short = name.split('_')[0]
        metadata = json.loads((RUN / 'metadata' / (short + '.json')).read_text())['data']
        choices = [e for e in metadata['endpoints'] if e.get('tag') == tag and e.get('status') == 0]
        assert len(choices) == 1, (name, tag)
        endpoint = choices[0]
        assert {'temperature', 'max_tokens', 'response_format', 'structured_outputs'} <= set(endpoint['supported_parameters'])
        routes[name] = {'model': metadata['id'], 'tag': tag, 'provider_name': endpoint['provider_name'],
                        'role': roles[short], 'endpoint_metadata': endpoint}
    by_case = {c['id']: c for c in fixture['cases']}
    common = ['zh_total', 'no_total', 'missing_target']
    requests, answers = [], []

    def add(route, case_id, prompt, strict=True, budget=512, repetition=1, groups=()):
        r = routes[route]
        case = by_case[case_id]
        body, schema = build_body(fixture, case, r['model'], r['tag'], prompt, strict, budget)
        raw = encode(body)
        identifier = f'call-{len(requests) + 1:03d}'
        requests.append({'id': identifier, 'body_base64': base64.b64encode(raw).decode(), 'sha256': sha(raw)})
        answers.append({'id': identifier, 'route': route, 'role': r['role'], 'model': r['model'],
                        'provider_name': r['provider_name'], 'requested_endpoint_tag': r['tag'],
                        'case': case_id, 'prompt': prompt, 'strict': strict, 'budget': budget,
                        'repetition': repetition, 'groups': list(groups), 'expected': case['expected'], 'schema': schema})

    # Fixed case/model order; first P00/P11 repetitions are interleaved and reused.
    for case in common:
        for route in roles:
            add(route, case, 'P00', groups=['H1', 'H2', 'H4_first'])
            add(route, case, 'P11', groups=['H1', 'H2', 'H3_strict', 'H4_first', 'core'])
            add(route, case, 'P10', groups=['H1', 'H2'])
            add(route, case, 'P01', groups=['H1', 'H2'])
    for case in by_case:
        if case not in common:
            for route in roles:
                add(route, case, 'P11', groups=['core', 'H6'])
    for case in common:
        for route in roles:
            add(route, case, 'P11', strict=False, groups=['H3_unconstrained'])
    for repetition in (2, 3):
        for case in common:
            for route in ('pro', 'flash', 'glm'):
                for prompt in ('P00', 'P11'):
                    add(route, case, prompt, repetition=repetition, groups=['H4_repeat'])
    for repetition in (1, 2, 3):
        for case in common:
            for prompt in ('P00', 'P11'):
                add('pro_secondary', case, prompt, repetition=repetition, groups=['H4_provider'])
    for case in ('zh_total', 'no_total'):
        for route in ('pro', 'gemini'):
            for budget in (512, 2048):
                add(route, case, 'P00', strict=False, budget=budget, groups=['H5_budget'])
    assert len(requests) == 146
    STAGE.mkdir(exist_ok=False)
    (RUN / 'responses').mkdir(exist_ok=False)
    (RUN / 'sentinels').mkdir(exist_ok=False)
    write(RUN / 'evaluator-key.json', {'cases': answers, 'role_interpretation':
        'DeepSeek and GLM are subjects; Gemini is a blind independent comparison oracle. Reviewed expected outputs remain authoritative. Oracle success does not alone locate subject failure in model weights.'})
    manifest = {'version': 'approved-fixtures-2026-09-15-v1', 'requests': requests,
                'bounds': {'max_calls': 146, 'retries': 0, 'deadline_seconds': 30, 'max_response_bytes': 131072}}
    write(STAGE / 'requests.json', manifest)
    shutil.copyfile(STAGE / 'requests.json', RUN / 'requests.json')
    shutil.copyfile(Path(__file__).with_name('fixture_worker.py'), STAGE / 'fixture_worker.py')
    protected = [str(RUN / 'evaluator-key.json'), str(fixture_path), str(ROOT / '.env'), str(ROOT / 'README.md')]
    for name in ('corpus.pdf', 'native.json', 'evidence-ir.json', 'ground-truth.json', 'clean.json', 'corrupted.json'):
        path = RUN / 'sentinels' / name
        path.write_text('SYNTHETIC ISOLATION SENTINEL; NOT REPORT EVIDENCE\n')
        protected.append(str(path))
    write(STAGE / 'isolation-paths.json', protected)
    runtime = str(Path(sys.base_prefix).resolve())
    allow = [runtime, '/System', '/usr', '/bin', '/sbin', '/Library/Apple',
             '/opt/homebrew/Cellar', '/opt/homebrew/opt', '/opt/homebrew/etc/openssl@3',
             '/private/etc', '/private/var/db/timezone', '/dev', str(STAGE)]
    profile = '(version 1)\n(allow default)\n(deny file-read*)\n'
    profile += '(allow file-read* ' + ' '.join('(subpath ' + json.dumps(x) + ')' for x in allow) + ')\n'
    profile += '(deny file-write*)\n(allow file-write* (subpath ' + json.dumps(str(RUN / 'responses')) + '))\n'
    profile += '(deny process-fork)\n(deny process-exec)\n(allow process-exec (literal ' + json.dumps(str(Path(sys.executable).resolve())) + '))\n'
    (STAGE / 'sandbox.sb').write_text(profile)
    shutil.copyfile(STAGE / 'sandbox.sb', RUN / 'sandbox.sb')
    write(RUN / 'execution-plan.json', {
        'version': manifest['version'], 'approved_at': '2026-09-15', 'frozen_at': datetime.now(timezone.utc).isoformat(),
        'source_fixture_sha256': sha(fixture_path.read_bytes()), 'manifest_sha256': sha(encode(manifest)),
        'worker_sha256': sha((STAGE / 'fixture_worker.py').read_bytes()),
        'sandbox_sha256': sha((STAGE / 'sandbox.sb').read_bytes()),
        'evaluator_key_sha256': sha((RUN / 'evaluator-key.json').read_bytes()),
        'subject_models': [routes[r]['model'] for r in ('pro', 'flash', 'glm')],
        'oracle_model': routes['gemini']['model'], 'routes': routes, 'calls': 146,
        'changes_from_proposal': ['Owner approval received; DeepSeek/GLM subjects and Gemini comparison oracle.',
          'GLM included in factorial and repeated-call diagnostics as a subject.',
          'Gemini receives each distinct primary configuration including budget controls, independently; it sees no subject answers.',
          'Three repetitions for subject P00/P11 strict common cases, one oracle observation per distinct condition.',
          'Execute optional pinned Ionstream Pro comparison; first route Baidu/fp8.'],
        'limits': manifest['bounds'], 'concurrency': 1, 'automatic_retries': 0,
        'freeze_policy': 'No adaptive prompt changes, no output repair, no additional calls; every planned outcome retained.',
        'provider_limits': 'Endpoint tags are pinned in requests; response provider names checked. Exact served endpoint revision/weights remain unknown. Provider comparison blocks also differ in time.',
        'isolation': 'OS file-read allowlist excludes project, corpus, evaluator key and .env. Only staged request data/code and system runtime are readable; writes limited to new responses directory. Bootstrap loads credential outside worker and injects sanitized environment.',
        'observation': 'Exact transmitted JSON bytes; bounded response bytes, redacting only a credential if echoed. Observation never adds model instructions or modifies requests.'})
    print(f'Frozen {len(requests)} requests; answers separate; staged at {STAGE}.')


if __name__ == '__main__':
    main()
