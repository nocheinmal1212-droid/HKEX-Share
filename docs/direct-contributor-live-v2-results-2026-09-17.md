# First live v2 dispatcher check — 2026-09-17

**Verdict: the connected logical-fixture path works for a live selection, a live abstention,
provider failures, and the injected late-write failure. Semantic coverage is severely limited
by upstream rate limiting. This is not production-IR or financial-audit end-to-end validation.**

The user authorized live calls through the [fixed v2 dispatcher](direct-contributor-persistence-fix-2026-09-17.md).
This run connects selected logical evidence → frozen request/prechecks → actual Pro HTTP call →
response validation → result/completion persistence → replay. The earlier experiment ran live
transport and stubbed dispatcher persistence separately; this run removes that separation.

## Frozen design

The [execution plan](../runs/milestone2/direct-contributor-live-v2-2026-09-17/execution-plan.json)
was saved before inference: one attempt each for S01–S14, then one additional S01 attempt with
an error injected immediately after writing complete result bytes. The latter is a persistence
probe and is excluded from the ordinary semantic denominator. There are no retries or fallback,
one concurrent call, a 30-second deadline and 131,072-byte response limit.

All 15 outbound request bodies are byte-identical to their corresponding requests in the prior
frozen experiment: same explicit prompt, model `deepseek/deepseek-v4-pro-0813`, Fireworks-only route,
temperature 0, strict output schema, and 2,048 output-token cap. Configuration records bind the
full outbound request and its hash; the transport reconstructs it from the actual dispatched
payload and refuses a mismatch before sending. The source, request, configuration, response and
terminal result remain separately traceable through the v2 completion record.

## Observed results

| Population | Observed behavior |
|---|---|
| 14 ordinary attempts | **14/14 terminal outcomes committed and replayed exactly**, with zero replay model calls |
| S03 | HTTP 200; correct direct-contributor selection; correct reason and required support |
| S04 | HTTP 200; correct missing-evidence abstention; correct reason and required support |
| Other 12 ordinary cases | HTTP 429; explicitly persisted/replayed as `transport_failure`; no usable semantic answers |
| Additional S01 late-write probe | HTTP 429, then injected result-write error; dispatch `persistence_failure`, no completion record, replay `incomplete_attempt` |

Thus **15/15 persistence expectations pass**, while only **2/14 ordinary cases have a usable,
fully matching semantic answer**. Zero observed wrong relationships among two usable answers is
not an accuracy estimate. S08 and S11 remain unanswered in this run, and their earlier failures
are not superseded. The full [evaluation](../runs/milestone2/direct-contributor-live-v2-2026-09-17/evaluation.json)
retains unavailable outcomes rather than dropping them from the denominator.

The successful [S03 observation](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/call-003/observation.json)
selects `r01` and `r04`, with the relationship note and all four context headers as support. The
source explicitly names administrative and distribution expenses as direct children of operating
expenses; payroll and premises costs belong inside administrative expenses. The included
depreciation memo row is correctly excluded. The
[S04 observation](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/call-004/observation.json)
abstains because the distribution row is absent and an unresolved region is recorded. Its extra
support IDs `r01` and `r05` refer to the available contributor and target; they do not introduce an
unsupported selection. These source checks are same-agent review of authored fixtures, not
independent adjudication or real-report evidence.

Both HTTP 200 envelopes identify DeepSeek-V4-Pro-0813 and Fireworks and finish with `stop`.
Exact underlying weights/endpoint revision are not independently attested. All thirteen HTTP 429
envelopes identify the error source as `upstream_provider_shared_pool`, with Fireworks named in
error metadata. They say the requested model is temporarily rate-limited upstream. This is an
availability result for this run, not evidence of incorrect model reasoning.

The [late-write observation](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/call-015/observation.json)
shows that a real HTTP error response and complete result bytes cannot masquerade as a committed
attempt. Because that call received 429, **late-write failure after a successful live model answer
remains untested**. The previous offline tests cover that successful-response fault combination;
this live run does not replace it with stronger evidence.

Reported API cost totals **USD 0.00690096** for the two usable responses. Thirteen HTTP errors
have no reported usage cost; their cost is unknown, not asserted to be zero. Exactly 15 HTTP
transport invocations were recorded. No additional calls were made after observing rate limits.

## Verification and isolation

- New [live adapter](../tools/experiments/direct_contributor_live_v2.py),
  [preparation](../tools/experiments/prepare_direct_contributor_live_v2.py), and
  [credential bootstrap](../tools/experiments/launch_direct_contributor_live_v2.py) connect the
  existing v2 dispatcher without modifying it. Root `.env` bootstrap was already authorized;
  only `OPENROUTER_API_KEY` enters the worker environment. No credential is saved in configuration,
  request bodies, results or logs. The worker cannot read `.env` itself.
- The outer workspace sandbox initially refused to launch `sandbox-exec` (`Operation not
  permitted`). The same zero-call preflight then passed with escalated launch permission, with
  the worker's own OS sandbox retained. This setup failure made no network calls.
- [Preflight](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/preflight.json)
  and [live batch](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/batch.json)
  each record **12 denied protected reads**: `.env`, raw evaluation metadata, fixture inputs,
  fixture expectations, and old/new evaluator keys, each through two file-opening APIs.
  The worker reads only its selected staged manifest, trusted runtime files, and named attempt
  artifacts. The [access log](../runs/milestone2/direct-contributor-live-v2-2026-09-17/attempts/access.json)
  preserves those accesses. This is isolation evidence for trusted experiment code, not hostile
  native-code containment.
- Five new [adapter tests](../tests/test_direct_contributor_live_v2.py) cover frozen wire binding,
  secret redaction, timeout/no retry, response limits, and adapter→dispatcher→replay with a late
  write fault. The [full suite](../runs/milestone2/direct-contributor-live-v2-2026-09-17/tests.txt)
  passes **77 tests**. Those tests use synthetic responses; the live observations above are
  separate evidence.
- The offline [verifier/evaluator](../tools/experiments/evaluate_direct_contributor_live_v2.py)
  checks frozen hashes, source/request preservation, wire-request equality, response hashes,
  recomputed validation, exact caller/result/replay correspondence, and isolation counts. It
  runs in a fresh process and performs no inference. A separate raw tally and completion-hash
  check are recorded in the [verification summary](../runs/milestone2/direct-contributor-live-v2-2026-09-17/verification.json).
  Original v1 and fixed-v2 implementation hashes remain unchanged.

## Decision

Retain the v2 dispatcher and this live adapter as experimental integration candidates. The first
connected live check succeeds for the outcomes actually observed. Do not claim a completed audit
pipeline, production readiness, or improved semantic accuracy. Real selected-IR consumption,
financial verification/findings, amount invariance and independent expectation review remain open.

The next live experiment should be separately frozen when capacity is available: obtain usable
responses for the twelve unavailable cases and a successful-response late-write probe. A provider
comparison would be a distinct experiment; this run did not silently reroute or alter the budget.
