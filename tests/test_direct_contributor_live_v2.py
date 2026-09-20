"""Transport adapter checks; no external requests or real credentials."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

TOOLS = Path(__file__).resolve().parents[1] / 'tools/experiments'
with patch.object(sys, 'path', [str(TOOLS), *sys.path]):
    import direct_contributor_live_v2 as live
    from run_direct_contributor_persistence_v2 import inputs


class Response(io.BytesIO):
    code = 200


class LiveV2Tests(unittest.TestCase):
    def transport(self, body=b'{}', error=None):
        source, identity, job, response = inputs()
        wire = live.wire_request(job, job['payload'], 'test prompt')
        config = {'wire_request': wire, 'wire_request_sha256': live.sha(live.encode(wire))}
        opener = Mock()
        opener.open.side_effect = error
        opener.open.return_value = Response(body)
        transport = live.LiveTransport(job, 'test prompt', config, 'unit-test-secret', opener)
        return source, identity, job, response, config, transport, opener

    def test_wire_request_is_bound_to_dispatch_payload(self):
        _, _, job, _, _, transport, opener = self.transport()
        with self.assertRaises(ValueError):
            transport({**job['payload'], 'target_id': 'changed'})
        self.assertEqual(transport.network_attempts, 0)
        opener.open.assert_not_called()

    def test_response_bound_and_secret_redacted(self):
        _, _, job, _, config, transport, opener = self.transport(b'unit-test-secret')
        with patch.object(live.signal, 'alarm'):
            result = transport(job['payload'])
        self.assertEqual(result['body'], b'[REDACTED]')
        self.assertTrue(result['credential_redacted'])
        self.assertEqual(result['wire_request_sha256'], config['wire_request_sha256'])
        self.assertEqual(opener.open.call_args.args[0].data, live.encode(config['wire_request']))
        self.assertEqual(transport.network_attempts, 1)

    def test_timeout_is_one_attempt_without_retry(self):
        _, _, job, _, _, transport, opener = self.transport(error=TimeoutError())
        with patch.object(live.signal, 'alarm') as alarm:
            result = transport(job['payload'])
        self.assertEqual(result['transport_status'], 'timeout')
        opener.open.assert_called_once()
        self.assertEqual(alarm.call_args.args, (0,))

    def test_response_limit_preserves_explicit_failure(self):
        _, _, job, _, _, transport, _ = self.transport(b'x' * (live.MAX_BYTES + 1))
        with patch.object(live.signal, 'alarm'):
            result = transport(job['payload'])
        self.assertEqual(result['transport_status'], 'response_too_large')
        self.assertEqual(len(result['body']), live.MAX_BYTES)

    def test_adapter_to_dispatch_to_replay_and_late_fault(self):
        for fault in (False, True):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                source, identity, job, response, config, transport, opener = self.transport()
                opener.open.return_value = Response(response['body'])
                store = (live.LateResultFailure if fault else live.Store)(tmp)
                with patch.object(live.signal, 'alarm'):
                    result = live.dispatch(source, identity, job, transport, store, config)
                self.assertEqual(result['state'], 'persistence_failure' if fault else 'structure_accepted')
                self.assertEqual(live.replay(tmp)['state'], 'incomplete_attempt' if fault else 'structure_accepted')
                self.assertEqual(transport.network_attempts, 1)


if __name__ == '__main__':
    unittest.main()
