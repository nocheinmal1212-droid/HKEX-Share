# Approved Flash context test — 17 September 2026

**Model-choice verdict: prefer `deepseek/deepseek-v4.1-flash` through Together for the next controlled PoC development work. Evidence-sufficiency verdict: provisional success on these logical fixtures, not validation for real-report auditing.** No production configuration or designation changed; no automatic fallback is recommended.

The owner approved the four-call discrimination proposed in the [selection report](independent-model-selection-results-2026-09-17.md), including its conditional continuation. V4.1 passed both context cases and advanced to the four additional cases. V4 Flash 0731 did not advance. The experiment finished with **eight scored calls and three separate explanation calls**.

## Frozen setup

[Design and limits](../runs/milestone2/flash-context-check-2026-09-17-r2/design.md), [configurations](../runs/milestone2/flash-context-check-2026-09-17-r2/configurations.json), [source expectations](../runs/milestone2/flash-context-check-2026-09-17-r2/evaluator-key.json), and [verified results](../runs/milestone2/flash-context-check-2026-09-17-r2/verification.json) are retained with exact request/response hashes. No expected answer entered model requests.

| Requested model | Frozen route | Fresh advertised USD per million input/output tokens |
|---|---|---:|
| `deepseek/deepseek-v4-flash-0731` | `deepinfra/fp8` — DeepInfra | 0.06 / 0.18 |
| `deepseek/deepseek-v4.1-flash` | `together` — Together | 0.30 / 1.20 |

Both exact IDs and routes advertised required schema/parameter support in fresh [official endpoint snapshots](../runs/milestone2/flash-context-check-2026-09-17-r2/metadata/fetch-log.json). All ten complete response envelopes reported the requested model/provider. The remaining attempt received HTTP 200 headers but no complete body, so its served identity is unknown. These are API assertions, not independent weight attestation.

These routes differ from the previous OpenInference and DeepInfra routes. They were selected and frozen before calls to avoid repeatedly using failed configurations. Results therefore compare **model plus provider plus prompt/schema plus inference budget**; they cannot isolate a generation or provider effect.

Prompt, evidence payloads and strict output vocabulary were unchanged. Temperature 0, native default reasoning with no effort override, 4,096 total completion-token request cap, 60-second deadline, 128-KiB response bound, one concurrent call, fresh conversations, no retries or rerouting. Core order was V4/S08, V4.1/S08, V4.1/S11, V4/S11. A model needed two verified full passes to advance. The continuation used unchanged S09/S10/H01/H02 once each, with no tuning.

The ceiling was 18 calls including conditional continuation and explanations, 61,440 requested completion tokens, USD1 reserved and 20 minutes of dispatch. Only 11 calls were needed. Two public metadata GETs were separate from inference. No new Gemini call was made: oracle agreement below uses the earlier frozen Gemini responses, not a contemporaneous comparison.

## Scored outcomes

| Model and stage | Correct selection | Correct abstention | Unsupported selection | Timeout | Full passes / attempts | Source correct / usable |
|---|---:|---:|---:|---:|---:|---:|
| V4 Flash 0731 / DeepInfra — core | 0 | 0 | 1 | 1 | **0/2** | **0/1** |
| V4.1 Flash / Together — core | 0 | 2 | 0 | 0 | **2/2** | **2/2** |
| V4.1 Flash / Together — continuation | 1 | 3 | 0 | 0 | **4/4** | **4/4** |

Across all eight scored attempts: unnecessary abstentions **0/8**, invalid contract output **0/8**, refusals **0/8**, truncations **0/8**, HTTP errors **0/8**, and other transport errors **0/8**. The one timeout remains in the all-attempt denominator. Valid usable decisions were **7/8**; full source/reason/support/identity passes **6/8**. Persistence completed **8/8**, which is separate from semantic success.

V4.1/Together passed all six scored cases:

- **S08:** correctly abstained on the 2024 contributor versus 2025 target.
- **S11:** correctly preserved unknown Group/Company allocation.
- **S09/S10:** correctly abstained on currency and original/restated conflicts.
- **H01:** selected `a-sub` and `b-dist`, resolving the distributed Group header and excluding the Company occurrence, grandchildren and included memo; all required support IDs were present.
- **H02:** abstained after the single panel-key change made Group/Company allocation unknown. Additional citations addressed the competing occurrences and scopes and were relevant.

This is **one supported selection and five supported abstentions**, with one observation per case. H01/H02 are a correlated synthetic pair; the other cases are exposed development fixtures. No selected production IR, Chinese-language capability, amount invariance or independently human-adjudicated label set was tested.

V4 Flash's [S11 response](../runs/milestone2/flash-context-check-2026-09-17-r2/flash-r2-core/attempts/call-004/result.json) selected `r01` and `r04`. But r04's `s06` says “Group / Company (allocation not identified)”, while the target uses the Group header. It cited s01–s05 and omitted the decisive ambiguous header. The explicit breakdown names the category; it does not resolve this occurrence's consolidation scope. This is a source-backed unsupported relationship despite valid IDs and schema, not a conclusion derived from Gemini's answer.

V4 Flash's [S08 transport record](../runs/milestone2/flash-context-check-2026-09-17-r2/flash-r2-core/attempts/call-001/response.json) records **HTTP 200, `timeout`, `read_response`, 60.004 seconds**. The deadline expired while reading the body, after response headers arrived. This rules out “no connection established” for this observation but does not distinguish backend queueing, slow generation, network delivery or another cause. No completed semantic decision or cost was available.

Agreement with the **frozen** Gemini reference is V4.1 **6/6** usable relationships and reasons; V4 Flash **0/1**, with its other case unavailable. Source correctness was graded independently. Previous successful V4 Flash controls on OpenInference do not repair this new failure; nor does this prove every route fails.

## Separate explanation follow-ups

The predeclared policy sampled the earliest completed full-contract failure/refusal and earliest correct abstention per model in the core, then at most one continuation response. [Sampling records](../runs/milestone2/flash-context-check-2026-09-17-r2/diagnostic-sampling.json) preserve three selected parents, three qualifying omissions and the unavailable S08 timeout.

- V4 Flash was asked about its wrong S11 answer without a gold answer or WA label. Its explanation ended `length`, with null content. **No usable explanation was obtained**; it was not retried or treated as a correction.
- V4.1's S08 and S09 explanations both passed the diagnostic schema and literal item-ID/excerpt checks. They identify the actual period and currency conflicts. Their suggestions to recover or clarify compatible evidence remain hypothetical; no source value or association was changed. These explanations support a source-grounded reading, not a causal account of model internals.

Thus explanations were **2/3 usable**, with one truncation and no refusal, timeout or HTTP failure. The two explanation objects are marked invalid by the deliberately unchanged *semantic* validator, then accepted under the separate diagnostic schema. They are not semantic invalid-output failures and never replace an initial score.

Two V4 Flash usage records have unreconciled accounting: S11 reports 750 completion versus 760 reasoning tokens; its diagnostic reports 2,048 completion versus 2,217 reasoning tokens. [Exact observations](../runs/milestone2/flash-context-check-2026-09-17-r2/usage-observations.json) are preserved. Do not infer a precise reasoning share or silently normalize those fields. Reported cost and requested limits are not independently attested billing/token accounting.

## Cost, implementation and verification

Reported cost for all 11 calls was **USD 0.015112560**, with **one unknown-cost timeout**. V4.1's six scored responses cost **USD 0.011139768**; median latency **12.18 seconds**, maximum **29.08 seconds**, combined **98.20 seconds**. V4's one completed scored answer cost 0.00018864 and took 13.95 seconds; its other scored attempt consumed the 60-second deadline. Explanations cost 0.003784152. These tiny samples do not estimate tail latency or production cost.

First-to-last dispatch took **227.31 seconds**. Requested completion caps totaled 38,912. Reported usage totaled 10,154 prompt and 14,116 completion tokens, excluding unknown usage and retaining the inconsistencies above.

The new [transport extension](../tools/experiments/model_selection_worker_v3.py) keeps the v2 wire and completion contracts. It records fixed failure categories, integer errno and phase only; exception messages, repr, URLs, headers and credentials are not logged. It retains an HTTP status received before a body-read error. Four offline regressions cover safe classification, wrapped timeout/no retry, read failure after headers and preservation of HTTP errors. The [full suite passed 86 tests](../runs/milestone2/flash-context-check-2026-09-17-r2/full-tests.txt).

The first isolated preflight exposed a missing trusted-module path under Python `-I`; **zero inference calls** had occurred. That [failed preparation](../runs/milestone2/flash-context-check-2026-09-17/launch-failure.json) remains immutable. A fresh r2 run adds an explicit [entry bootstrap](../tools/experiments/model_selection_worker_v3_entry.py). All four core wire requests remained byte-identical across the fix. The original frozen transport module was not edited in place.

Three zero-call preflights and three live batches each verified **14 denied protected reads**. The OS sandbox and exact-file guard remained enabled; `.env` was read only by the authorized parent bootstrap. All **11/11 completion records** and source/request/response bindings replay correctly, with zero replay model calls. All **413 prior inventory hashes** still match. No PDF, OCR, clean counterpart or benchmark answers entered inference. No production code or designation changed.

Reproduce without inference:

```sh
make evidence-check
tools/eval-format-tools/.venv/bin/python runs/milestone2/flash-context-check-2026-09-17-r2/run.py replay
tools/eval-format-tools/.venv/bin/python runs/milestone2/flash-context-check-2026-09-17-r2/verify.py
```

[Final artifact hashes](../runs/milestone2/flash-context-check-2026-09-17-r2/final-hashes.json) bind the evidence and new code. Do not rerun execution into dated directories.

## Decision

V4.1/Together earned the conditional continuation and passed it. **Use this exact configuration as the preferred candidate for the next controlled semantic PoC work.** Its success is stronger evidence than Flash branding or the incumbent Pro designation. This is a recommendation; no model was wired into runtime.

V4 Flash 0731/DeepInfra did not satisfy the context requirements. There is no supported automatic fallback to it, to Pro, or to another candidate. The schema-valid wrong selection remains an unobservable error for the current structural validator; no trigger-driven cascade was tested. Correct missing-evidence abstention must continue to stop the check.

The next step that could strengthen the V4.1 recommendation is a small independently reviewed selected-IR slice with compatible and incompatible counterparts, plus a positive/missing-evidence control on the **same Together route**. Its previous S03/S04 successes were on DeepInfra and should not be combined into a same-configuration success rate. Real-IR fidelity, source-amount invariance, independent label review and business error budgets remain open. No additional experiment or future retry is scheduled.

**Final verdict: V4.1 Flash / Together is the provisional development choice; no production model or automatic fallback is validated by this test.**
