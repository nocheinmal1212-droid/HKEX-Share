"""Freeze authorized interpretation experiment; source proposals remain immutable."""
from datetime import datetime, timezone
import base64
import json
from pathlib import Path
import shutil

from direct_contributor_boundary import encode, sha, freeze, precheck, output_schema
from check_direct_contributor_fixtures import check

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/milestone2/direct-contributors-2026-09-17'
STAGE = Path('/private/tmp/audit-direct-contributors-2026-09-17-v1')
VERSION = 'direct-contributors-2026-09-17-v1'
PROMPT = '''Return only a JSON object for the typed operation select_direct_addends.
Use the supplied literal evidence IDs and header_refs; never invent or normalize an ID.
For the requested target, select its nearest directly contributing additive children only.
Do not flatten a subtotal into its children, count both an included row and its parent, add a memo
row marked as already included, or substitute a different total. This is an expense-breakdown
relationship task, not an arithmetic task. Do not return amounts, signs, coefficients, calculated
answers, corrections or code. Explicit supporting relationship evidence is required: a total
label, row order, plausible accounting names or a rectangular table alone do not prove directness
or completeness. If the intended contributor set cannot be identified completely, abstain.
Use the literal header text and associations to check the target and contributors for compatible
entity/consolidation scope, period, currency and presentation basis. A conflicting context blocks
the proposed relationship; a candidate's ambiguous context is unknown, not a match. Do not perform
currency conversion. A shared unspecified currency/scale within the same explicit local breakdown
does not alone prevent identifying contributors; this does not establish arithmetic readiness.
Apply limitations to the relevant container and source region; an unrelated table limitation does
not block a supported local relationship. Preserve missing evidence as unknown rather than guessing.
Return exactly action, target_id, contributor_ids, support_ids, reason. target_id must equal the
requested target even when abstaining. action is exactly select or abstain. For select return the
nonempty set of unique supplied candidate_ids which are direct addends, cite the relationship note
and all target/contributor header IDs needed to support the claim in support_ids, and use reason
supported_direct_breakdown. Relevant additional supplied support IDs are permitted. For abstain
return an empty contributor_ids array, available relevant support_ids (possibly empty), and the
most specific reason: missing_evidence for an unrecovered required source occurrence;
ambiguous_relationship when available labels do not establish the direct relationship;
incompatible_context for an explicit conflict; unknown_context when a candidate's context cannot
be resolved. Arrays contain literal unique source IDs only. Never put explanations outside these
keys or inside the ID arrays. A structurally valid response remains subject to independent review.'''


def write(path, value):
    with path.open('xb') as stream:
        stream.write(encode(value))


def main():
    check()
    fixtures = json.loads((ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json').read_bytes())
    expectations = json.loads((ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json').read_bytes())
    metadata_raw = Path('/private/tmp/direct-contributors-pro-endpoints.json').read_bytes()
    metadata = json.loads(metadata_raw)['data']
    assert metadata['id'] == fixtures['model']
    endpoint = next(e for e in metadata['endpoints'] if e['tag'] == 'fireworks' and e['status'] == 0)
    assert {'structured_outputs', 'response_format', 'max_tokens', 'temperature'} <= set(endpoint['supported_parameters'])
    RUN.mkdir(exist_ok=False); STAGE.mkdir(exist_ok=False)
    (RUN / 'responses').mkdir(); (RUN / 'prepared').mkdir()
    (RUN / 'endpoint-metadata.json').write_bytes(metadata_raw)
    (RUN / 'prompt.txt').write_text(PROMPT)
    requests, answers = [], []
    keys = {c['id']: c for c in expectations['cases']}
    # Rotate case order between repetitions; no adaptive order, prompt or budget changes.
    for rep, offset in [(1, 0), (2, 5), (3, 10)]:
        cases = fixtures['cases'][offset:] + fixtures['cases'][:offset]
        for case in cases:
            source = case['source']
            identity = {'doc_id': 'synthetic-direct-contributors', 'variant_id': case['id'],
                        'evidence_sha256': sha(encode(source)), 'evidence_mode': 'logical_fixture'}
            job = freeze(source, case['request'], identity)
            assert precheck(source, identity, job)['state'] == 'eligible'
            if rep == 1:
                write(RUN / 'prepared' / (case['id'] + '.json'), {'source': source, 'job': job})
            body = {'model': fixtures['model'], 'messages': [
                {'role': 'system', 'content': PROMPT},
                {'role': 'user', 'content': encode(job['payload']).decode()}],
                'temperature': 0, 'max_tokens': 2048, 'stream': False,
                'provider': {'only': ['fireworks'], 'allow_fallbacks': False, 'require_parameters': True},
                'response_format': {'type': 'json_schema', 'json_schema': {
                    'name': 'direct_contributors', 'strict': True, 'schema': output_schema(job)}}}
            raw = encode(body); id = f'call-{len(requests)+1:03d}'
            requests.append({'id': id, 'sha256': sha(raw), 'body_base64': base64.b64encode(raw).decode()})
            answers.append({'id': id, 'case': case['id'], 'repetition': rep, 'job': job,
                            'expected': keys[case['id']]['expected'],
                            'support_requirements': keys[case['id']]['support_requirements']})
    manifest = {'version': VERSION, 'bounds': {'max_calls': 42, 'retries': 0,
                'deadline_seconds': 30, 'max_response_bytes': 131072}, 'requests': requests}
    write(STAGE / 'requests.json', manifest); shutil.copyfile(STAGE / 'requests.json', RUN / 'requests.json')
    write(RUN / 'evaluator-key.json', {'cases': answers})
    original = (ROOT / 'tools/experiments/interface_worker.py').read_text()
    worker = original.replace('interface-boundaries-2026-09-16-v1', VERSION).replace(
        "{'instruction', 'evidence'}", "{'operation', 'container_id', 'target_id', 'candidate_ids', 'evidence', 'limitations'}")
    worker_path = ROOT / 'tools/experiments/direct_contributor_worker.py'
    with worker_path.open('x') as f:
        f.write(worker)
    shutil.copyfile(worker_path, STAGE / 'direct_contributor_worker.py')
    protected = [str(RUN / 'evaluator-key.json'), str(ROOT / '.env'), str(ROOT / 'README.md'),
                 str(ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json'),
                 str(ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json')]
    write(STAGE / 'isolation-paths.json', protected)
    profile = '(version 1)\n(allow default)\n(deny file-read-data (subpath ' + json.dumps(str(ROOT)) + '))\n'
    profile += '(deny file-write*)\n(allow file-write* (subpath ' + json.dumps(str(RUN / 'responses')) + ') (subpath "/dev"))\n'
    (STAGE / 'sandbox.sb').write_text(profile); (RUN / 'sandbox.sb').write_text(profile)
    write(RUN / 'execution-plan.json', {
        'version': VERSION, 'authorized_by': 'User: Execute those tests, record observations, and output a verdict on their effectiveness.',
        'frozen_at': datetime.now(timezone.utc).isoformat(), 'model': fixtures['model'],
        'provider': endpoint['provider_name'], 'provider_tag': 'fireworks', 'planned_calls': 42,
        'repetitions': 3, 'prompt_arms': 1, 'max_tokens': 2048, 'temperature': 0,
        'deadline_seconds': 30, 'max_response_bytes': 131072, 'retries': 0, 'fallbacks': False,
        'order': 'Fixture order rotated by 0, 5, 10 positions over three fresh-conversation repetitions.',
        'grading': 'Report exact action/target/unordered-contributor match, reason match, and required support coverage separately; full pass requires all. Unexpected abstention, wrong selection, schema/refusal/truncation/transport failure remain distinct. Inspect extra support manually.',
        'review': 'Expected contributor sets rechecked against explicit synthetic source prose before execution; S04/S05 missingness and S07-S11 conflicts retained; S12 shared-unknown control retained. Same-agent review, not an independent human or second-agent review.',
        'budget_rationale': '2048 output tokens for five fields and multi-ID support on a richer new operation. No claim of comparability with earlier 512-token lexical experiments.',
        'scope': 'Fixture-only interpretation; preparation prechecks and offline output checks. Transport worker does not implement production dispatch. No valid IR, amount invariance or financial accuracy claim.',
        'hashes': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [
            ROOT / 'spec/diagnostics/direct-contributors-inputs-v1.json',
            ROOT / 'spec/diagnostics/direct-contributors-expectations-v1.json',
            ROOT / 'tools/experiments/direct_contributor_boundary.py', worker_path,
            RUN / 'requests.json', RUN / 'evaluator-key.json', RUN / 'prompt.txt',
            RUN / 'endpoint-metadata.json', RUN / 'sandbox.sb']}})
    print('Frozen 42 Pro/Fireworks attempts; no inference yet.')


if __name__ == '__main__':
    main()
