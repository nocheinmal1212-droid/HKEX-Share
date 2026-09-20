"""Versioned synthetic prompt/schema diagnostic; no report inputs."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import urllib.error

import probe_openrouter as probe
from hkex_audit.artifacts import encode, fingerprint, loads, sha, write_new

VERSION = 'prompt-schema-v1'
MODELS = (probe.MODEL, 'deepseek/deepseek-v4-flash-0731')
CLARIFICATION = (
    ' This is text-label classification only, not verification of an accounting total. '
    'No amounts or surrounding table are needed to recognize a total label. '
    'The role total_label means text explicitly naming a total. '
    'When the requested label is supported, return action label, its supplied evidence_id, '
    'and role total_label. When the requested ID is absent or no text names a total, '
    'return action abstain with null evidence_id and role. '
    'Return a JSON object with exactly action, evidence_id, and role; no other text.'
)
CASES = (*probe.CASES, ('no_total', probe.CASES[0][1], probe.CASES[1][2]))


def request(model, prompt, strict, case):
    body = probe.request_body(case[1], model)
    if prompt == 'clarified':
        body['messages'][0]['content'] += CLARIFICATION
    if not strict:
        del body['response_format']
    if case[0] == 'no_total':
        payload = loads(body['messages'][1]['content'])
        payload['evidence'][0]['text'] = '成本'
        body['messages'][1]['content'] = encode(payload).decode()
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=MODELS, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('Credential unavailable')
    args.out.mkdir(exist_ok=False, parents=True)
    requests = [dict(prompt=prompt, strict_schema=strict, case=case[0],
                     expected=case[2], request=request(args.model, prompt, strict, case))
                for prompt in ('original', 'clarified') for strict in (True, False) for case in CASES]
    plan = {'version': VERSION, 'model': args.model, 'created_at': datetime.now(timezone.utc).isoformat(),
            'bounds': {'max_calls': 12, 'retries': 0, 'deadline_seconds': 30, 'max_tokens': 512},
            'scope': 'synthetic_only', 'stop_policy': 'Execute all predeclared independent cases, including after failures.',
            'routing': 'Unpinned, original provider policy. Provider changes confound comparisons.',
            'limitations': 'One observation per cell. Original unconstrained arm removes the API schema without adding a textual substitute; semantic content and format failures must be distinguished.',
            'harness_sha256': sha(Path(__file__).read_bytes()),
            'base_harness_sha256': sha(Path(probe.__file__).read_bytes()), 'requests': requests}
    write_new(args.out / 'plan.json', plan)
    for index, item in enumerate(requests):
        result = {**item, 'request_fingerprint': fingerprint(item['request']),
                  'created_at': datetime.now(timezone.utc).isoformat()}
        try:
            status, raw = probe.post(item['request'], key)
            result.update(probe.assess(status, raw, key, item['expected'], args.model))
        except TimeoutError:
            result['status'] = 'timeout'
        except (OSError, urllib.error.URLError):
            result['status'] = 'network_error'
        result['fingerprint'] = fingerprint(result)
        write_new(args.out / f'{index:02d}-{item["prompt"]}-{item["strict_schema"]}-{item["case"]}.json', result)
        print(args.model, item['prompt'], item['strict_schema'], item['case'], result['status'],
              result.get('validated_output'), flush=True)


if __name__ == '__main__':
    main()
