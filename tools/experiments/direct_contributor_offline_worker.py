"""Isolated logical-source + frozen-response replay. No network, fixture-key or IR claim."""
import base64
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_inputs.guard import install
from direct_contributor_boundary import Store, dispatch, encode, parse, sha


def main():
    payload = json.load(sys.stdin)
    names = ('source.json', 'request.json', 'started.json', 'response.json', 'result.json', 'access.json')
    output = Path(payload['output'])
    reads = [Path(payload[k]) for k in ('source_path', 'job_path', 'response_path')]
    # Code is preloaded/trusted; only these explicit data files are readable after the guard.
    # Dispatch verifies its freshly persisted request before transport starts.
    attempts = install([*reads, output / 'request.json'], [output / name for name in names])
    denials = []
    for path in payload['forbidden']:
        for method in ('read_bytes', 'os_open'):
            try:
                if method == 'read_bytes':
                    Path(path).read_bytes()
                else:
                    descriptor = os.open(path, os.O_RDONLY)
                    os.close(descriptor)
            except PermissionError:
                denials.append({'path': path, 'method': method, 'denied': True})
            else:
                raise RuntimeError('isolation failure')
    source = parse(reads[0].read_bytes())
    job = parse(reads[1].read_bytes())
    saved = parse(reads[2].read_bytes())
    raw = base64.b64decode(saved['body_base64'], validate=True)
    assert sha(raw) == saved['body_sha256']
    transport_calls = []
    def transport(body):
        transport_calls.append(sha(encode(body)))
        return {'transport_status': saved['transport_status'], 'http_status': saved['http_status'], 'body': raw}
    result = dispatch(source, payload['identity'], job, transport, Store(output),
                      {'mode': 'frozen_response_replay', 'model': 'offline_stub'})
    Store(output).write('access.json', encode({'attempts': attempts.copy(), 'protected_reads': denials,
                                              'stub_transport_calls': len(transport_calls),
                                              'network_calls': 0, 'result_state': result['state']}))
    print(json.dumps({'state': result['state'], 'denials': len(denials), 'stub_calls': len(transport_calls)}))
    return 0 if result['persisted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
