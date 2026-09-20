# Synthetic OpenRouter probe

`tools/probe_openrouter.py` is a development tool outside the detector. It takes no report,
native-artifact, IR or evaluation input. It reads only `OPENROUTER_API_KEY` from its environment;
it does not load credential files. The owner-authorized local `.env` entry was loaded into the
execution process for the first live run, without shell evaluation or credential output.

With the environment configured, run from the repository root using a **new** output directory:

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python tools/probe_openrouter.py --out runs/milestone2/probe-new
make evidence-check
```

The probe uses the selected exact model, two fixed synthetic cases at most, 512 output tokens
per request, a 30-second deadline per request and zero retries. It stops on the first failure.
Provider fallback, HTTP redirects and environment proxies are disabled. The provider is not pinned;
account-level routing defaults remain unobserved. Requests use strict JSON Schema and require
parameter support, following [OpenRouter structured-output documentation](https://openrouter.ai/docs/guides/features/structured-outputs)
and [provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).
Local checks separately require the exact response model, an observed provider, complete output,
permitted IDs/roles and the expected synthetic decision. Schema compliance alone does not pass.

Saved evidence includes requests, expected decisions, sanitized bounded response text (including
usage and returned identities), results and fingerprints. API labels do not attest the underlying
checkpoint revision; it stays unknown. Even a successful probe would support only these tiny
examples, not financial interpretation accuracy or deterministic fresh-call replay.

No new dependency was added: HTTP, deadline and JSON handling use the Python standard library
(PSF license); schema validation uses the already-reviewed `jsonschema==4.26.0` dependency.
The deadline implementation requires a POSIX main thread, matching this development environment.
The tool is not a runtime OpenRouter client and does not relax the detector's network/file guard.

## Observed result, 2026-09-11

- R1 (`runs/milestone2/probe-2026-09-11-r1/probe.json`) records a network error in the restricted
  execution environment. No HTTP response or provider identity was observed.
- R2 (`runs/milestone2/probe-2026-09-11-r2/probe.json`), with network access, received HTTP 200.
  The returned model was `deepseek/deepseek-v4-pro-0813`, provider `Ionstream`, with no system
  fingerprint or checkpoint revision. This demonstrates credential/access success and the
  API-reported identity, without independently attesting the weights.
- The valid-ID case supplied `field-one: 總計` and `field-two: 收入`. Expected selection was
  `field-one` with role `total_label`; the response was `abstain` with both fields null.
  It passed output shape validation but failed the semantic expectation. The absent-ID case
  was consequently not called. Reported usage was 132 tokens and reported cost was USD 0.00012012.
- No substitution, retry, report evidence, raw PDF access or OCR assessment occurred. The semantic
  integration gate remains open. One unexpected abstention does not establish general model
  incapability. Next investigate prompt/vocabulary clarity and routing behavior with an explicitly
  versioned bounded synthetic diagnostic, retaining this failure rather than weakening its test.

Ten offline probe checks and all 36 portable repository tests passed. Those tests validate the
probe's acceptance/rejection behavior; they do not override the failed live capability result.

## Owner-requested model comparison, 2026-09-12

The owner explicitly authorized diagnostic calls to three alternative models. This does not
replace the designated semantic model or satisfy its integration gate. The development probe now
accepts `--model`; its default remains `deepseek/deepseek-v4-pro-0813`. Exact returned identity is
validated against the requested model. Prompts, schema, temperature, token/deadline bounds,
routing policy and stop-on-first-failure behavior are unchanged.

| Requested model | Observed provider | Total-label case | Absent-ID case |
|---|---|---|---|
| `deepseek/deepseek-v4-flash-0731` | OpenInference | Unexpected `abstain`, both fields null | Not called |
| `z-ai/glm-5.3-flash` | DeepInfra | Correct `field-one`, `total_label` | Correct abstention |
| `google/gemini-3.8-flash` | Google AI Studio | Correct `field-one`, `total_label` | Correct abstention |

Exact requests, response text, identities and validation results are saved under
[`runs/milestone2/model-comparison-2026-09-12`](../runs/milestone2/model-comparison-2026-09-12/).
The [comparison manifest](../runs/milestone2/model-comparison-2026-09-12/comparison.json) records
artifact and harness hashes. An initial restricted-network DeepSeek attempt failed before an HTTP
response; it is preserved separately. Five network-enabled calls completed, with total
API-reported cost USD 0.001121141. No retries, report evidence or PDFs were used.

Verified all first-case request objects match the historical Pro request except for the model ID;
checked report/request fingerprints and raw-response agreement with parsed outputs. All 37 local
tests passed, including the new explicit-model identity and unchanged-request regression.

The two successful models demonstrate that this prompt/schema can elicit the intended outputs
through this harness. DeepSeek Flash repeats Pro's abstention via a different reported provider,
weakening an explanation specific to Ionstream alone. This is not evidence of general DeepSeek
incapability or financial accuracy for the passing models. Models and providers both vary, and
there is one observation per executed case. Next discriminate prompt interpretation from strict
schema handling using separately versioned synthetic controls; preserve abstention on genuinely
missing evidence and retain the original failure.

## Approved prompt/schema diagnostic, 2026-09-12

The owner approved the next prompt-versus-schema comparison. The separate development harness
[`tools/diagnose_openrouter.py`](../tools/diagnose_openrouter.py), version `prompt-schema-v1`,
predeclares a 2 × 2 comparison for each DeepSeek model: original/clarified system prompt and
strict API schema present/absent. Each combination runs three synthetic cases: original total
label, original explicit absent-ID instruction, and a new no-total control (`成本`, `收入`)
with the original selection question and expected abstention. The clarification defines the task
as text classification and states the successful output vocabulary; it supplies neither the
Chinese translation nor the answer ID. It changes several related instructions together, so
individual wording effects are not isolated.

Each model's plan was saved before calls. All 12 independent cases execute even after failure,
unlike the acceptance probe; there are no retries. Each call retains the 512-token, 30-second,
128-KiB limits, temperature zero and original unpinned routing policy. Removing the API schema
from the original prompt also removes the only explicit successful-output vocabulary supplied
to the API. Consequently this arm tests that combined removal, not constrained decoding alone.
The clarified prompt supplies the same textual vocabulary in both schema modes. All outputs
still face the unchanged local schema and exact expected-answer validator.

| Prompt / API schema | Pro via Baidu | Flash via OpenInference |
|---|---|---|
| Original / strict | All 3 passed | All 3 passed |
| Original / absent | Missing-ID passed; total-label and no-total cases hit 512-token limit without a final answer | Both negative controls passed; selected correct ID but invalid action/role on total-label case |
| Clarified / strict | All 3 passed | All 3 passed |
| Clarified / absent | All 3 passed | All 3 passed |

Plans and all exact requests/responses are in
[`runs/milestone2/prompt-schema-2026-09-12`](../runs/milestone2/prompt-schema-2026-09-12/).
[Verification manifest](../runs/milestone2/prompt-schema-2026-09-12/verification.json):
24 completed calls, API-reported cost USD 0.006283129832; no retries or report/PDF reads.
All 39 local tests passed. Verified every executed request and expectation against its predeclared
plan, request/result fingerprints, raw-response re-assessment, and exact equality of original
strict positive requests to their historical counterparts. No historical evidence was overwritten.

### Interpretation and new evidence

- Both original strict positive requests now pass unchanged. Pro's provider changed from Ionstream
  to Baidu; Flash reports the same OpenInference provider and `vllm-dev-ep-2b83873d` fingerprint.
  Flash's same-request variation establishes non-repeatability across these observed calls, not
  its cause. The fingerprint is not an independently attested checkpoint.
- Inspecting the previously saved Flash failure reveals returned reasoning text that recognizes
  `總計` and proposes `field-one`, but uses `action=select`, `role=label`; the actual final response
  abstains. The fresh original/no-schema Flash output is exactly
  `{"action":"select","evidence_id":"field-one","role":"label"}`. This supports a mismatch
  between output vocabulary and schema handling as an investigative hypothesis, rather than a
  basic inability to recognize the word. Returned reasoning is generated text, not proof of the
  internal causal process. The historical Pro response has no returned reasoning.
- The identical Pro request reports 107 prompt tokens historically and 397 now. Different provider
  preprocessing/schema handling or token accounting merits inspection; counts alone cannot
  establish which occurred or whether it caused the earlier abstention.
- Clarified prompts passed all six cases per model, retaining appropriate abstention on both
  controls. Original strict prompts also passed, so this experiment does not prove clarification
  fixes the original intermittent failure or that strict schema caused it. Pro's new no-schema
  token-limit failures are distinct from its earlier normally completed abstention.

Next useful check: repeated original-versus-clarified requests with provider pinned, retaining
both negative controls and all failures. A further same-text schema-present/absent comparison
could include explicit output vocabulary in both arms. The designated model and original probe
are unchanged. Semantic integration remains pending resolution of serving/prompt repeatability;
these diagnostic passes do not establish financial interpretation accuracy or a full lifecycle.

## Approved isolated hypothesis fixtures, 2026-09-15

Executed all 146 predeclared synthetic calls: 121 subject calls (DeepSeek Pro, DeepSeek Flash,
GLM) and 25 independent Gemini oracle calls. See the
[full fixture report](experimental-fixture-results-2026-09-15.md) and
[verification manifest](../runs/milestone2/hypothesis-fixtures-2026-09-15/verification.json).
Gemini never saw subject answers; reviewed fixture expectations remain authoritative.

The common P11 prompt plus strict schema passed all nine core cases and six additional scheduled
strict repetitions on each primary DeepSeek route (Pro/Baidu and Flash/OpenInference: 15/15 each).
GLM's core suite had five passes and four HTTP 429 outcomes; a later P11 missing-target repetition
returned a schema-valid wrong selection despite the explicit absent-target rule. Its matching
Gemini oracle correctly abstained. Cross-subject acceptance is therefore not established.

Pro/Ionstream reproduced the original positive-case abstention twice; the remaining original
positive call was rate-limited. Its explicit positive prompt passed all three repetitions.
Pro/Baidu's original positive prompt passed all three, while negative-control errors depended on
scope wording. Flash's original missing-target request varied across truncation, wrong selection
and correct abstention. These observations support prompt/serving interaction without attesting
model weights or separating provider effects from timing and hidden serving changes.

Gemini passed all nine core oracle cases but produced Markdown-wrapped answers and one truncation
in no-schema diagnostic configurations. More tokens did not repair Pro's no-schema vocabulary
errors; its no-total case changed from truncation to timeout. Do not equate oracle agreement,
completion or schema conformance alone with a correct semantic decision.

Isolation: a request-only staged worker with a separate inaccessible answer key, macOS denial of
project-file content, Python read allowlisting after imports, minimal credential environment,
write-only response directory, fixed endpoint, and zero retries/fallback/adaptive prompt changes.
Twenty protected-read checks passed. Early OS allowlist startup failures occurred before calls;
final isolation layers and limitations are documented in the launch attestation. No supplied
PDF, native report, evidence IR or benchmark inputs were read. All 47 local tests passed; exact
request/response hashes, fixture preservation, provider names and offline evaluation replay were
verified. API-reported cost was USD 0.064093228 across records with usage; 22 records had no reported
cost. No production semantic prompt, designated model or integration gate was changed.

## Approved interface-boundary experiment, 2026-09-16

Completed all 180 planned attempts on Fireworks, preserving fixed prompts, strict schema, 512
output tokens and zero retries/fallback. [Full results](interface-boundary-results-2026-09-16.md)
link raw evidence and the verification manifest. This phase uses reviewed answers, with Pro as
baseline, existing V4 Flash as primary subject and V4.1 Flash as a separate extension.

Pro passed 30/30 with existing explicit P11; concise wording passed 26/30 (two unexpected
abstentions and two truncations). Both completed wrong abstentions concern C06's requested target
among two total labels; neither is a recorded refusal. V4.1 Flash passed 30/30 in both arms.
Existing V4 Flash received upstream HTTP 429 on all 60 attempts, leaving that comparison unassessed.
Retain explicit wording as the candidate; propose a separately controlled existing-Flash rerun
and a scope-only wording experiment, without changing results or adding calls to this run.

Eleven offline boundary fixtures passed, including a structurally valid semantic error that the
guard correctly does not claim to detect. All 55 local tests, protected-read checks, exact hashes,
reviewed fixture preservation and identical offline evaluation replay passed. Experimental code
remains separate from production. No supplied PDF, extractor output, IR or benchmark data used.
The designated production model and integration acceptance remain unchanged.
