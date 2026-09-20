"""Selected logical sources -> v2 dispatcher -> live OpenRouter -> committed replay.

Run in a separate OS sandbox. No evaluator imports, answers, retries or fallback.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import ssl
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from direct_contributor_attempt_v2 import Store, dispatch, encode, parse, precheck, replay, sha
from direct_contributor_boundary import output_schema
from direct_contributor_worker import ENDPOINT, MAX_BYTES, NoRedirect, deadline, verify_isolation

MODEL = 'deepseek/deepseek-v4-pro-0813'
NAMES = ('source.json', 'request.json', 'started.json', 'response.json', 'result.json',
         'completion.json', 'observation.json')


def wire_request(job, payload, prompt):
    return {'model': MODEL, 'messages': [{'role': 'system', 'content': prompt},
            {'role': 'user', 'content': encode(payload).decode()}],
            'temperature': 0, 'max_tokens': 2048, 'stream': False,
            'provider': {'only': ['fireworks'], 'allow_fallbacks': False, 'require_parameters': True},
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'direct_contributors', 'strict': True, 'schema': output_schema(job)}}}


class LiveTransport:
    def __init__(self, job, prompt, configuration, key, opener):
        self.job, self.prompt, self.configuration = job, prompt, configuration
        self.key, self.opener = key, opener
        self.network_attempts = 0

    def __call__(self, payload):
        raw = encode(wire_request(self.job, payload, self.prompt))
        if sha(raw) != self.configuration['wire_request_sha256']:
            raise ValueError('dispatch payload differs from frozen wire request')
        result = {'wire_request_sha256': sha(raw), 'started_at': datetime.now(timezone.utc).isoformat()}
        started = time.monotonic()
        signal.alarm(30)
        try:
            request = urllib.request.Request(ENDPOINT, data=raw, headers={
                'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
            self.network_attempts += 1
            try:
                response = self.opener.open(request, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                body = response.read(MAX_BYTES + 1)
                result['http_status'] = response.code
            result['transport_status'] = 'received' if len(body) <= MAX_BYTES else 'response_too_large'
            if len(body) > MAX_BYTES:
                body = body[:MAX_BYTES]
                result['response_truncated_for_storage'] = True
            safe = body.replace(self.key.encode(), b'[REDACTED]')
            result.update(body=safe, credential_redacted=safe != body)
        except TimeoutError:
            result['transport_status'] = 'timeout'
        except (OSError, urllib.error.URLError):
            result['transport_status'] = 'transport_error'
        finally:
            signal.alarm(0)
        result['elapsed_seconds'] = round(time.monotonic() - started, 6)
        return result


class LateResultFailure(Store):
    def write(self, name, raw):
        super().write(name, raw)
        if name == 'result.json':
            raise OSError('planned failure after result bytes were written')


def install_guard(stage, output, entries):
    allowed = {str((stage / name).resolve()) for name in
               ('manifest.json', 'direct_contributor_live_v2.py', 'direct_contributor_attempt_v2.py',
                'direct_contributor_boundary.py', 'direct_contributor_worker.py')}
    writes = {str((output / name).resolve()) for name in ('preflight.json', 'batch.json', 'access.json')}
    for entry in entries:
        own = {str((output / entry['id'] / name).resolve()) for name in NAMES}
        allowed.update(own)
        writes.update(own)
    runtime = [Path(sys.base_prefix).resolve(), Path('/opt/homebrew/etc/openssl@3').resolve()]
    accesses = []
    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.exec', 'os.posix_spawn',
                     'ctypes.dlopen', 'os.listdir', 'os.scandir', 'os.remove', 'os.rename', 'os.link', 'os.symlink'):
            raise PermissionError('worker discovery or external execution forbidden')
        if event == 'urllib.Request' and args[0] != ENDPOINT:
            raise PermissionError('worker endpoint is fixed')
        if event == 'open':
            target, mode, flags = args
            if isinstance(target, int):
                raise PermissionError('descriptor opens forbidden')
            path = Path(os.fsdecode(target))
            if any(p.is_symlink() for p in [path, *path.parents]):
                raise PermissionError('symlink access forbidden')
            path = path.resolve()
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)) or bool(mode and any(c in mode for c in 'wax+'))
            permitted = str(path) in writes if writing else (str(path) in allowed or any(p == path or p in path.parents for p in runtime))
            accesses.append({'path': str(path), 'access': 'write' if writing else 'read', 'allowed': permitted})
            if not permitted:
                raise PermissionError('unselected file access')
    sys.addaudithook(audit)
    return accesses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    manifest_raw = args.manifest.read_bytes()
    manifest = parse(manifest_raw)
    entries = manifest['attempts']
    assert len(entries) == 15 and len({e['id'] for e in entries}) == 15
    assert [e['id'] for e in entries] == [f'call-{i:03d}' for i in range(1, 16)]
    assert [e['fault'] for e in entries] == [None] * 14 + ['late_result_write']
    for entry in entries:
        assert precheck(entry['source'], entry['identity'], entry['job'])['state'] == 'eligible'
        body = wire_request(entry['job'], entry['job']['payload'], manifest['prompt'])
        assert body == entry['configuration']['wire_request']
        assert sha(encode(body)) == entry['configuration']['wire_request_sha256']
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    accesses = install_guard(args.manifest.parent, args.out, entries)
    checks = verify_isolation(manifest['protected_paths'])
    if args.preflight:
        Store(args.out).write('preflight.json', encode({'checks': checks, 'network_calls': 0,
                              'manifest_sha256': sha(manifest_raw), 'planned_attempts': len(entries)}))
        print('Preflight passed; zero network calls.', flush=True)
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('Credential unavailable')
    signal.signal(signal.SIGALRM, deadline)
    observations = []
    for entry in entries:
        directory = args.out / entry['id']
        transport = LiveTransport(entry['job'], manifest['prompt'], entry['configuration'], key, opener)
        store = (LateResultFailure if entry['fault'] else Store)(directory)
        result = dispatch(entry['source'], entry['identity'], entry['job'], transport, store, entry['configuration'])
        replayed = replay(directory)
        observation = {'id': entry['id'], 'fault': entry['fault'], 'dispatch': result, 'replay': replayed,
                       'network_attempts': transport.network_attempts}
        Store(directory).write('observation.json', encode(observation))
        observations.append({'id': entry['id'], 'dispatch': result['state'], 'replay': replayed['state'],
                             'persisted': result['persisted'], 'network_attempts': transport.network_attempts})
        print(json.dumps(observations[-1]), flush=True)
    Store(args.out).write('batch.json', encode({'manifest_sha256': sha(manifest_raw), 'checks': checks,
                         'observations': observations, 'completed_at': datetime.now(timezone.utc).isoformat()}))
    Store(args.out).write('access.json', encode(accesses))


if __name__ == '__main__':
    main()
