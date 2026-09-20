"""Transport diagnostics extension; frozen v2 wire and completion contracts unchanged.

Exception descriptions, URLs, headers and repr/tracebacks never enter artifacts.
"""
from datetime import datetime, timezone
import http.client
import signal
import socket
import ssl
import time
import urllib.error
import urllib.request
import model_selection_worker_v2 as base
from direct_contributor_attempt_v2 import encode, parse, sha
from direct_contributor_worker import ENDPOINT, MAX_BYTES


def classify_exception(error):
    """Only fixed categories and integer errno; do not serialize exception text."""
    inner = error.reason if isinstance(error, urllib.error.URLError) else error
    classes = [(socket.gaierror, 'dns_resolution'),
               (ssl.SSLCertVerificationError, 'tls_certificate'),
               (ssl.SSLError, 'tls_error'),
               (TimeoutError, 'timeout'),
               (ConnectionRefusedError, 'connection_refused'),
               (ConnectionResetError, 'connection_reset'),
               (ConnectionAbortedError, 'connection_aborted'),
               (BrokenPipeError, 'broken_pipe'),
               (PermissionError, 'permission_denied'),
               (http.client.IncompleteRead, 'incomplete_http_read'),
               (http.client.HTTPException, 'http_protocol'),
               (OSError, 'other_os_error')]
    kind = next((label for cls, label in classes if isinstance(inner, cls)),
                'unclassified_url_error' if isinstance(error, urllib.error.URLError) else 'unexpected_exception')
    number = getattr(inner, 'errno', None)
    return {'kind': kind, 'wrapped_url_error': isinstance(error, urllib.error.URLError),
            'errno': number if type(number) is int else None}


class Transport(base.Transport):
    def __call__(self, payload):
        e = self.entry
        raw = encode(base.wire_request(e['job'], payload, self.prompt, e['settings'], e.get('diagnostic')))
        if sha(raw) != e['configuration']['wire_request_sha256'] or parse(raw) != e['configuration']['wire_request']:
            raise ValueError('wire binding mismatch')
        result = {'wire_request_sha256': sha(raw), 'started_at': datetime.now(timezone.utc).isoformat()}
        started = time.monotonic()
        phase = 'request_build'
        signal.alarm(60)
        try:
            req = urllib.request.Request(ENDPOINT, data=raw, headers={
                'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
            phase = 'open_connection'
            self.network_attempts += 1
            try:
                response = self.opener.open(req, timeout=60)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                result['http_status'] = response.code
                phase = 'read_response'
                body = response.read(MAX_BYTES + 1)
            result['transport_status'] = 'received' if len(body) <= MAX_BYTES else 'response_too_large'
            if len(body) > MAX_BYTES:
                body = body[:MAX_BYTES]
                result['response_truncated_for_storage'] = True
            safe = body.replace(self.key.encode(), b'[REDACTED]')
            result.update(body=safe, credential_redacted=safe != body)
        except Exception as error:
            detail = classify_exception(error)
            result.update(transport_status='timeout' if detail['kind'] == 'timeout' else 'transport_error',
                          transport_exception={**detail, 'phase': phase})
        finally:
            signal.alarm(0)
        result['elapsed_seconds'] = round(time.monotonic() - started, 6)
        return result


if __name__ == '__main__':
    base.Transport = Transport
    base.main()
