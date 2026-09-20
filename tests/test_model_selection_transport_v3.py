"""Safe transport failure classification with no network or artifact dependency."""
import http.client
import json
from pathlib import Path
import socket
import ssl
import sys
import unittest
import urllib.error
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools/experiments'))
from model_selection_worker_v3 import Transport, classify_exception
import test_model_selection_v2 as fixtures

class ClassificationTests(unittest.TestCase):
    def test_fixed_categories_without_exception_text(self):
        cases = [(urllib.error.URLError(socket.gaierror(-2,'SECRET')), 'dns_resolution'),
                 (ssl.SSLCertVerificationError(1,'SECRET'), 'tls_certificate'),
                 (ConnectionResetError(54,'SECRET'), 'connection_reset'),
                 (PermissionError(13,'SECRET'), 'permission_denied'),
                 (http.client.IncompleteRead(b'SECRET',20), 'incomplete_http_read'),
                 (urllib.error.URLError('SECRET'), 'unclassified_url_error')]
        for exc, expected in cases:
            detail = classify_exception(exc)
            self.assertEqual(detail['kind'], expected)
            self.assertNotIn('SECRET', json.dumps(detail))

    def fixture(self):
        t=fixtures.ComparisonTests();t.setUp();return t

    def test_wrapped_timeout_one_call(self):
        f=self.fixture();op=Mock();op.open.side_effect=urllib.error.URLError(TimeoutError('SECRET'))
        t=Transport(f.e,f.prompt,'SECRET',op);r=t(f.e['job']['payload'])
        self.assertEqual(r['transport_status'],'timeout')
        self.assertEqual(r['transport_exception']['phase'],'open_connection')
        self.assertEqual(t.network_attempts,1);self.assertEqual(op.open.call_count,1)
        self.assertNotIn('SECRET',json.dumps(r))

    def test_http_status_survives_read_failure(self):
        f=self.fixture()
        class BrokenReply(fixtures.Reply):
            def read(self,n):raise ConnectionResetError(54,'SECRET')
        op=Mock();op.open.return_value=BrokenReply(b'')
        r=Transport(f.e,f.prompt,'SECRET',op)(f.e['job']['payload'])
        self.assertEqual(r['http_status'],200)
        self.assertEqual(r['transport_exception']['phase'],'read_response')
        self.assertEqual(r['transport_exception']['kind'],'connection_reset')
        self.assertEqual(r['transport_status'],'transport_error')
        self.assertNotIn('SECRET',json.dumps(r))

    def test_http_error_is_preserved_as_http(self):
        import io
        f=self.fixture();op=Mock()
        op.open.side_effect=urllib.error.HTTPError('https://openrouter.ai/api/v1/chat/completions',429,'SECRET',{},io.BytesIO(b'{"error":"limited"}'))
        r=Transport(f.e,f.prompt,'SECRET',op)(f.e['job']['payload'])
        self.assertEqual(r['http_status'],429);self.assertEqual(r['transport_status'],'received')
        self.assertNotIn('transport_exception',r)
        self.assertEqual(op.open.call_count,1)

if __name__=='__main__':unittest.main()
