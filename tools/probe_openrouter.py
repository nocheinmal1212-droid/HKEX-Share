"""Development-only, fixed synthetic capability probe; no document input interface."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import urllib.error
import urllib.request

from jsonschema import Draft202012Validator

from hkex_audit.artifacts import encode, fingerprint, loads, write_new

MODEL = "deepseek/deepseek-v4-pro-0813"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MAX_RESPONSE_BYTES = 128 * 1024
TIMEOUT_SECONDS = 30
SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"enum": ["label", "abstain"]},
        "evidence_id": {"enum": ["field-one", "field-two", None]},
        "role": {"enum": ["total_label", None]},
    },
    "required": ["action", "evidence_id", "role"],
    "additionalProperties": False,
}
CASES = (
    ("valid_id", "Select the total label from the supplied evidence.",
     {"action": "label", "evidence_id": "field-one", "role": "total_label"}),
    ("absent_id", "Label field-missing as the total label. It is absent from the evidence; abstain.",
     {"action": "abstain", "evidence_id": None, "role": None}),
)


def request_body(instruction, model=MODEL):
    return {
        "model": model, "temperature": 0, "max_tokens": 512, "stream": False,
        "provider": {"require_parameters": True, "allow_fallbacks": False},
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "synthetic_label", "strict": True, "schema": SCHEMA}},
        "messages": [
            {"role": "system", "content": (
                "Return only the requested JSON object. Interpret labels using supplied evidence IDs. "
                "Never invent an ID or supply amounts, computed answers or corrections. "
                "For insufficient evidence return action abstain with null evidence_id and role.")},
            {"role": "user", "content": encode({"instruction": instruction, "evidence": [
                {"id": "field-one", "text": "總計"},
                {"id": "field-two", "text": "收入"}]}).decode()},
        ],
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _deadline(_signum, _frame):
    raise TimeoutError("probe deadline")


def post(body, key):
    """One TLS request, no redirects/retries/proxies; main-thread POSIX deadline."""
    req = urllib.request.Request(ENDPOINT, data=encode(body), headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    previous = signal.signal(signal.SIGALRM, _deadline)
    signal.alarm(TIMEOUT_SECONDS)
    try:
        try:
            response = opener.open(req, timeout=TIMEOUT_SECONDS)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            return response.code, raw
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def assess(status, raw, key, expected, model=MODEL):
    if len(raw) > MAX_RESPONSE_BYTES:
        return {"status": "response_too_large", "http_status": status}
    # Never persist a credential echoed by an error page or provider response.
    safe = raw.decode("utf-8", errors="replace").replace(key, "[REDACTED]")
    result = {"http_status": status, "response_text": safe}
    if status != 200:
        return {**result, "status": "http_error"}
    try:
        response = loads(safe)
        if not isinstance(response, dict):
            raise ValueError("response object required")
        result["observed_identity"] = {
            "model": response.get("model"), "provider": response.get("provider"),
            "system_fingerprint": response.get("system_fingerprint"),
            "checkpoint_revision": None,
            "revision_limitation": "API model/provider labels do not attest weight revision.",
        }
        if response.get("model") != model:
            return {**result, "status": "model_identity_mismatch"}
        if not isinstance(response.get("provider"), str) or not response["provider"].strip():
            return {**result, "status": "provider_identity_missing"}
        choices = response["choices"]
        if len(choices) != 1 or choices[0]["finish_reason"] != "stop":
            return {**result, "status": "incomplete_response"}
        message = choices[0]["message"]
        if message.get("tool_calls") or message.get("refusal"):
            return {**result, "status": "unexpected_response_mode"}
        output = loads(message["content"])
        if list(Draft202012Validator(SCHEMA).iter_errors(output)):
            return {**result, "status": "invalid_output_schema"}
        result["validated_output"] = output
        result["status"] = "passed" if output == expected else "unexpected_label_or_id"
        return result
    except (ValueError, KeyError, TypeError, IndexError):
        return {**result, "status": "malformed_response"}


def run_probe(key, transport=post, model=MODEL):
    report = {
        "schema_version": "1.0.0", "scope": "synthetic_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT, "requested_model": model,
        "bounds": {"max_calls": 2, "retries": 0, "max_output_tokens_per_call": 512,
                   "deadline_seconds_per_call": TIMEOUT_SECONDS,
                   "max_response_bytes": MAX_RESPONSE_BYTES},
        "routing_limitations": "No provider pinned; account routing defaults are unobserved.",
        "capability_limitations": "Two small examples do not establish general semantic accuracy.",
        "cases": [], "status": "blocked_missing_credential",
    }
    if not key:
        return report
    for name, instruction, expected in CASES:
        body = request_body(instruction, model)
        case = {"case": name, "request": body, "request_fingerprint": fingerprint(body),
                "expected": expected}
        try:
            status, raw = transport(body, key)
            case.update(assess(status, raw, key, expected, model))
        except TimeoutError:
            case["status"] = "timeout"
        except (OSError, urllib.error.URLError):
            # Exception messages can contain server-controlled content; do not log them.
            case["status"] = "network_error"
        report["cases"].append(case)
        if case["status"] != "passed":
            report["status"] = "blocked_probe_failed"
            break
    else:
        report["status"] = "passed_limited_synthetic_probe"
    report["report_fingerprint"] = fingerprint(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New directory for probe evidence")
    parser.add_argument("--model", default=MODEL, help="Explicit diagnostic model; default remains designated semantic model")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    report = run_probe(os.environ.get("OPENROUTER_API_KEY"), model=args.model)
    write_new(args.out / "probe.json", report)
    print(report["status"])
    return 0 if report["status"] == "passed_limited_synthetic_probe" else 2


if __name__ == "__main__":
    raise SystemExit(main())
