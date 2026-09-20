"""Offline probe contract and failure checks; no real network calls."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

from hkex_audit.artifacts import encode

SPEC = importlib.util.spec_from_file_location(
    "openrouter_probe", Path(__file__).resolve().parents[1] / "tools/probe_openrouter.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)
KEY = "synthetic-test-secret"


def response(output, **changes):
    value = {"model": probe.MODEL, "provider": "Test provider", "choices": [{
        "finish_reason": "stop", "message": {"content": encode(output).decode()}}]}
    value.update(changes)
    return encode(value)


class ProbeTests(unittest.TestCase):
    def test_two_fixed_requests_and_identity(self):
        calls = []

        def transport(body, key):
            self.assertEqual(key, KEY)
            calls.append(body)
            return 200, response(probe.CASES[len(calls) - 1][2])

        report = probe.run_probe(KEY, transport)
        self.assertEqual(report["status"], "passed_limited_synthetic_probe")
        self.assertEqual(len(calls), 2)
        for body in calls:
            self.assertEqual(body["model"], probe.MODEL)
            self.assertEqual(body["provider"], {"require_parameters": True, "allow_fallbacks": False})
            self.assertEqual(body["max_tokens"], 512)
            self.assertNotIn("models", body)
            self.assertNotIn(KEY, encode(report).decode())

    def test_explicit_model_preserves_request_and_checks_identity(self):
        model = "diagnostic-model"
        original = probe.request_body(probe.CASES[0][1])
        changed = probe.request_body(probe.CASES[0][1], model)
        self.assertEqual(changed, {**original, "model": model})
        calls = []

        def transport(body, key):
            self.assertEqual(body["model"], model)
            calls.append(body)
            return 200, response(probe.CASES[len(calls) - 1][2], model=model)

        report = probe.run_probe(KEY, transport, model=model)
        self.assertEqual(report["requested_model"], model)
        self.assertEqual(report["status"], "passed_limited_synthetic_probe")
        wrong = probe.assess(200, response(probe.CASES[0][2]), KEY, probe.CASES[0][2], model)
        self.assertEqual(wrong["status"], "model_identity_mismatch")
        self.assertEqual(probe.MODEL, "deepseek/deepseek-v4-pro-0813")

    def test_missing_credential_never_calls(self):
        with patch.object(probe, "post") as transport:
            report = probe.run_probe(None, transport)
        transport.assert_not_called()
        self.assertEqual(report["status"], "blocked_missing_credential")

    def test_http_error_redacted_and_no_retry(self):
        with patch.object(probe, "post", return_value=(401, KEY.encode())) as transport:
            report = probe.run_probe(KEY, transport)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(report["cases"][0]["status"], "http_error")
        self.assertNotIn(KEY, encode(report).decode())

    def test_identity_failures(self):
        for changes, expected in [({"model": "another-model"}, "model_identity_mismatch"),
                                  ({"provider": None}, "provider_identity_missing")]:
            result = probe.assess(200, response(probe.CASES[0][2], **changes), KEY, probe.CASES[0][2])
            self.assertEqual(result["status"], expected)

    def test_unknown_ids_and_amounts_rejected(self):
        for output in [{"action": "label", "evidence_id": "unknown", "role": "total_label"},
                       {**probe.CASES[0][2], "amount": "10"}]:
            self.assertEqual(probe.assess(200, response(output), KEY, probe.CASES[0][2])["status"],
                             "invalid_output_schema")

    def test_schema_valid_wrong_role_or_id_fails(self):
        self.assertEqual(probe.assess(200, response(probe.CASES[0][2]), KEY, probe.CASES[1][2])["status"],
                         "unexpected_label_or_id")

    def test_malformed_duplicate_and_truncated(self):
        for raw in [b"{", b"[]", b'{"model":"x","model":"y"}',
                    response({}, choices=[{"finish_reason": "length"}])]:
            self.assertNotEqual(probe.assess(200, raw, KEY, probe.CASES[0][2])["status"], "passed")

    def test_response_bound(self):
        self.assertEqual(probe.assess(200, b"x" * (probe.MAX_RESPONSE_BYTES + 1), KEY, {})["status"],
                         "response_too_large")

    def test_network_failure_and_timeout_are_visible(self):
        for exc, expected in [(OSError(KEY), "network_error"), (TimeoutError(KEY), "timeout")]:
            with patch.object(probe, "post", side_effect=exc) as transport:
                report = probe.run_probe(KEY, transport)
            self.assertEqual(transport.call_count, 1)
            self.assertEqual(report["cases"][0]["status"], expected)
            self.assertNotIn(KEY, encode(report).decode())

    def test_redirect_denied(self):
        self.assertIsNone(probe.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other/"))


if __name__ == "__main__":
    unittest.main()
