"""Narrow OpenRouter subprocess: one HTTPS request, no runtime file access, no retries."""
import base64
import http.client
import json
import os
import socket
import ssl
import sys
import time
import encodings.idna  # load before file guard
from .artifacts import encode
from .semantic_attempt import CONFIGS

HOST = 'openrouter.ai'


def install_transport_guard(addresses):
    def guard(event, args):
        if event in {'open','os.listdir','os.scandir','subprocess.Popen','os.system','os.exec','os.posix_spawn','os.fork','ctypes.dlopen'}:
            raise PermissionError('transport file/execution access denied')
        if event == 'socket.getaddrinfo' and (args[0] != HOST or args[1] != 443):
            raise PermissionError('transport host denied')
        if event == 'socket.connect' and (args[1][0] not in addresses or args[1][1] != 443):
            raise PermissionError('transport endpoint denied')
    sys.addaudithook(guard)


def main():
    job = json.load(sys.stdin)
    deadline = job['deadline_monotonic']
    if time.monotonic() >= deadline:
        print(json.dumps({'transport_status':'budget_exhausted','request_started':False})); return
    role = job['role']; config = CONFIGS[role]
    mode = job['mode']
    if mode == 'metadata':
        path = '/api/v1/models/' + config['model'] + '/endpoints'; data = None
    elif mode == 'completion':
        payload = job['payload']
        assert payload['model'] == config['model']
        assert payload['provider']['only'] == [config['route']]
        assert payload['provider']['allow_fallbacks'] is False
        path = '/api/v1/chat/completions'; data = encode(payload)
    else:
        raise ValueError('unknown transport mode')
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        print(json.dumps({'transport_status': 'unavailable', 'reason': 'credential_absent'})); return
    # Trust TLS/encoding bootstrap, then deny all files and external execution. Network is
    # restricted to resolved OpenRouter addresses on 443; no arbitrary URL or redirect support.
    context = ssl.create_default_context()
    addresses = {i[4][0] for i in socket.getaddrinfo(HOST, 443, type=socket.SOCK_STREAM)}
    install_transport_guard(addresses)
    start = time.monotonic()
    request_started = False
    try:
        connection = http.client.HTTPSConnection(HOST, 443, timeout=min(config['deadline_seconds'], max(.001, deadline-time.monotonic())), context=context)
        if time.monotonic() >= deadline:
            print(json.dumps({'transport_status':'budget_exhausted','request_started':False})); return
        request_started = True  # an exception after this boundary has unknown remote acceptance
        connection.request('GET' if data is None else 'POST', path, data,
                           {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        response = connection.getresponse(); raw = response.read(2_000_001)
        if len(raw) > 2_000_000: raise ValueError('response exceeds byte bound')
        # Never persist a credential even if a remote error echoes it.
        raw = raw.replace(key.encode(), b'[REDACTED]')
        result = {'transport_status': 'ok' if response.status == 200 else 'transport_error', 'http_status': response.status,
                  'body_base64': base64.b64encode(raw).decode(), 'elapsed_seconds': time.monotonic() - start}
        connection.close()
    except (TimeoutError, socket.timeout):
        result = {'transport_status': 'timeout', 'elapsed_seconds': time.monotonic() - start}
    except Exception:
        result = {'transport_status': 'transport_error', 'elapsed_seconds': time.monotonic() - start}
    result['request_started'] = request_started
    print(json.dumps(result))

if __name__ == '__main__':
    main()
