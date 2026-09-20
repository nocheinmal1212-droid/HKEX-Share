"""Transport-only synthetic worker. Runs inside a separate macOS read/write sandbox.

No evaluator imports, expected answers, fixture reasoning or adaptive retries.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import ssl
import time
import urllib.error
import urllib.request

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MAX_BYTES = 131072


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open('xb') as stream:
        stream.write(encode(value))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def deadline(signum, frame):
    raise TimeoutError('deadline')


def check_manifest(manifest):
    assert set(manifest) == {'version', 'requests', 'bounds'}
    assert manifest['version'] == 'approved-fixtures-2026-09-15-v1'
    assert len(manifest['requests']) == manifest['bounds']['max_calls']
    assert len({r['id'] for r in manifest['requests']}) == len(manifest['requests'])
    for entry in manifest['requests']:
        assert set(entry) == {'id', 'body_base64', 'sha256'}
        raw = base64.b64decode(entry['body_base64'], validate=True)
        assert digest(raw) == entry['sha256']
        body = json.loads(raw)
        assert set(body) <= {'model', 'messages', 'temperature', 'max_tokens', 'stream', 'provider', 'response_format'}
        assert len(body['messages']) == 2
        assert [m['role'] for m in body['messages']] == ['system', 'user']
        assert body['max_tokens'] in (512, 2048) and body['temperature'] == 0 and body['stream'] is False
        assert body['provider']['allow_fallbacks'] is False
        assert body['provider']['require_parameters'] is True and len(body['provider']['only']) == 1
        assert set(json.loads(body['messages'][1]['content'])) == {'instruction', 'evidence'}


def verify_isolation(paths):
    checks = []
    for path in paths:
        for method in ('path_read', 'os_open'):
            try:
                if method == 'path_read':
                    Path(path).read_bytes()
                else:
                    fd = os.open(path, os.O_RDONLY)
                    os.close(fd)
            except PermissionError:
                checks.append({'path': path, 'method': method, 'denied': True})
            else:
                raise RuntimeError('isolation failure: protected read was not denied')
    return checks


def install_read_guard(stage, out):
    """Defense in depth for this trusted Python worker; OS blocks project reads."""
    allowed = [stage.resolve(), Path(sys.base_prefix).resolve(),
               Path('/opt/homebrew/etc/openssl@3').resolve()]
    def within(path, roots):
        return any(path == root or root in path.parents for root in roots)
    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.exec', 'ctypes.dlopen'):
            raise PermissionError('worker cannot launch processes or foreign code')
        if event == 'urllib.Request' and args[0] != ENDPOINT:
            raise PermissionError('worker endpoint is fixed')
        if event in ('open', 'os.listdir', 'os.scandir'):
            target = args[0]
            if isinstance(target, int):
                raise PermissionError('unapproved file descriptor read')
            path = Path(os.fsdecode(target)).resolve()
            mode = args[1] if event == 'open' else 'r'
            flags = args[2] if event == 'open' else 0
            writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)) or bool(mode and any(c in mode for c in 'wax+'))
            if writing:
                if not within(path, [out.resolve()]):
                    raise PermissionError('write outside response directory')
            elif not within(path, allowed):
                raise PermissionError('read outside worker allowlist')
    sys.addaudithook(audit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--isolation-paths', type=Path, required=True)
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    install_read_guard(args.manifest.parent, args.out)
    isolation = verify_isolation(json.loads(args.isolation_paths.read_text()))
    manifest_raw = args.manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    check_manifest(manifest)
    save(args.out / ('preflight-v2.json' if args.preflight else 'isolation.json'), {
        'checked_at': datetime.now(timezone.utc).isoformat(), 'checks': isolation,
        'manifest_sha256': digest(manifest_raw), 'worker_sha256': digest(Path(__file__).read_bytes()),
        'credential_source': 'OPENROUTER_API_KEY environment only',
        'network_calls': 0 if args.preflight else 'recorded individually'})
    if args.preflight:
        print('Isolation and manifest preflight passed; zero network calls.', flush=True)
        return
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise SystemExit('Credential unavailable')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    signal.signal(signal.SIGALRM, deadline)
    for index, entry in enumerate(manifest['requests']):
        raw = base64.b64decode(entry['body_base64'], validate=True)
        result = {'id': entry['id'], 'request_sha256': digest(raw),
                  'started_at': datetime.now(timezone.utc).isoformat()}
        save(args.out / (entry['id'] + '.started.json'), result)
        started = time.monotonic()
        signal.alarm(30)
        try:
            req = urllib.request.Request(ENDPOINT, data=raw, headers={
                'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
            try:
                response = opener.open(req, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                payload = response.read(MAX_BYTES + 1)
                result['http_status'] = response.code
            if len(payload) > MAX_BYTES:
                result['transport_status'] = 'response_too_large'
                payload = payload[:MAX_BYTES]
                result['response_truncated_for_storage'] = True
            else:
                result['transport_status'] = 'received'
            safe = payload.replace(key.encode(), b'[REDACTED]')
            result['credential_redacted'] = safe != payload
            result['response_base64'] = base64.b64encode(safe).decode()
            result['response_sha256'] = digest(safe)
        except TimeoutError:
            result['transport_status'] = 'timeout'
        except (OSError, urllib.error.URLError):
            result['transport_status'] = 'transport_error'
        finally:
            signal.alarm(0)
        result['elapsed_seconds'] = round(time.monotonic() - started, 6)
        save(args.out / (entry['id'] + '.json'), result)
        print(f"{index + 1}/{len(manifest['requests'])} {entry['id']} {result['transport_status']} HTTP {result.get('http_status')}", flush=True)
    save(args.out / 'completed.json', {'calls': len(manifest['requests']),
                                      'completed_at': datetime.now(timezone.utc).isoformat()})


if __name__ == '__main__':
    main()
