# Independent API model selection — 17 September 2026

**Model-choice verdict: no deployment candidate is selected. Evidence-sufficiency verdict: insufficient for a Flash default, a non-Flash default, or automatic fallback.** Preserve the owner's Flash-first preference for the next experiment. This is a completed bounded evaluation with an inconclusive selection outcome, not a recommendation to deploy incumbent Pro.

All eight supplied candidates were called under their exact IDs. None was excluded by name, generation or size. Seven had incomplete coverage after transport failures; GLM-5.3 completed the screen but made four unsupported selections. Gemini-3.8 Flash passed the source-backed screen and its separate confirmation, but is an external reference outside the deployment candidate group. No production designation, pipeline milestone, scoring gate, corpus file or historical artifact changed.

The [frozen design](../runs/milestone2/model-selection-2026-09-17/design.md), [exact configurations](../runs/milestone2/model-selection-2026-09-17/configurations.json), [evaluation including every attempt](../runs/milestone2/model-selection-2026-09-17/final-evaluation.json), and [SHA-256 inventory](../runs/milestone2/model-selection-2026-09-17/final-hashes.json) make the decision reproducible. This is **fixture-mode evidence**: English authored logical sources, not native financial statements, saved production IR, or an end-to-end audit.

## Configurations and verified access

Fresh official metadata was saved before inference: [ten successful public GETs](../runs/milestone2/model-selection-2026-09-17/metadata/fetch-log.json), including the model catalogue and all nine exact endpoint listings. An earlier sandboxed GET failed DNS resolution; it made no inference call. All IDs existed; each had an advertised route supporting `max_tokens`, `response_format` and `structured_outputs`. All nine initial requests returned a structurally valid selection with matching API-reported model/provider identity.

| Exact requested ID | Frozen primary provider tag | Reported provider on answers | Advertised input / output USD per million tokens |
|---|---|---|---:|
| `moonshotai/kimi-k3` | `deepinfra/bf16` | DeepInfra | 2.85 / 14.25 |
| `z-ai/glm-5.3` | `morph/fp8` | Morph | 0.8925 / 2.805 |
| `qwen/qwen3.8-2.4t-a95b` | `novita` | Novita | 2 / 6 |
| `deepseek/deepseek-v4-pro-0813` | `baidu/fp8` | Baidu | 1.32 / 3.96 |
| `deepseek/deepseek-v4-flash-0731` | `open-inference/fp8` | OpenInference | 0.03 / 0.13 |
| `minimax/minimax-m3` | `coreweave/fp4` | CoreWeave | 0.23 / 0.96 |
| `deepseek/deepseek-v4.1-flash` | `deepinfra/fp8` | DeepInfra | 0.20 / 0.60 |
| `z-ai/glm-5.3-flash` | `wafer` | Wafer | 0.10 / 0.35 |
| `google/gemini-3.8-flash` — oracle only | `google-ai-studio` | Google AI Studio | 0.75 / 3.75 |

Prices above are the frozen **endpoint** rates, not catalogue minimums, future quotations or account billing totals. Cache prices and complete parameter inventories are retained in each [metadata file](../runs/milestone2/model-selection-2026-09-17/metadata). The exact oracle variant was served; no generation substitution occurred. Gemini responses report the default service tier. Provider slug and tier semantics follow [OpenRouter's routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection). Model/provider fields and catalogue canonical slugs do not independently attest weights or endpoint revision; underlying serving identity remains a limitation.

All scored calls used the unchanged explicit [operation prompt](../runs/milestone2/model-selection-2026-09-17/prompt.txt), the existing strict per-case JSON schema, temperature 0, 4,096 total completion tokens, a 60-second deadline, and a 128-KiB response bound. Native default reasoning was retained: metadata lists Kimi/GLM/GLM Flash default max, Qwen xhigh, DeepSeek high, Gemini medium; MiniMax's default effort is unspecified. These labels are not equal compute budgets. No reasoning parameter was silently forced across models. Strict schema support was both advertised and exercised, with host validation retained; it never implied correct interpretation. See [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs) and [reasoning token accounting](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

The design offered every truncating model one 8,192-token arm. No scored response truncated, so no budget arm ran. Every model passed initial availability, so no secondary-route probe ran. Later failures invoked the predeclared stop rule; this deliberately limits what can be concluded. There were no route changes, retries, output repairs or selected best repetitions. API account limits/provider terms remain applicable; synthetic evidence here establishes no suitability for confidential report processing.

## Capability coverage and source review

The frozen six-case screen uses exposed development fixtures. I checked their exact source text, header associations and expectations before fresh outputs. That is a new agent review, **not independent human adjudication**.

| Required capability | Test and source-backed distinction | What remains unmeasured |
|---|---|---|
| Direct children, grandchildren, memo exclusion | S03: s05 specifies the complete outer breakdown; payroll/premises belong inside administration; r06 is included. Select r01/r04. | Implicit relationships in actual statements; new models on the old S02 target-switch control. |
| Incomplete evidence | S04: distribution is required by s05 but its occurrence is absent; preserve unresolved-region limitation and abstain `missing_evidence`. | Native projection loss versus extraction absence. |
| Period, currency/unit, presentation basis | S08/S09/S10: r04 references s06 instead of the target's corresponding header. Abstain `incompatible_context`. | Scale conversion and arithmetic; shared unknown-unit control S12 was mapped but not repeated. |
| Entity/consolidation uncertainty | S11: group target, candidate header “Group / Company (allocation not identified)”. Abstain `unknown_context`. | General entity resolution; old S07 explicit scope conflict was not repeated. |
| Distributed context with same-label alternatives | New H01/H02: linked panel headers, nested administration subtotal, included memo and two Distribution occurrences. Only one scope-key text changes. | Chinese variation, genuine cross-note matching and production IR consumption. |
| Invariance and local prerequisites | Existing S06/S13/S14 cover unrelated limitations, order and IDs historically. | These were not fresh candidate tests. No financial-amount invariance was executed. |

The minimal harder-test condition **was met**: the existing payload and validator could carry linked headers without an adapter, benchmark framework or annotation campaign. [H01/H02 and source hashes](../runs/milestone2/model-selection-2026-09-17/selected-cases.json) and [separate expectations](../runs/milestone2/model-selection-2026-09-17/evaluator-key.json) were frozen before any candidate output. H01's panel key resolves Group and supports `a-sub`/`b-dist`; `c-dist` is Company. H02 makes that key ambiguous, requiring abstention. The pair differs only in `panel-key` text. It is two synthetic cases with correlated repetitions, not genuine saved IR or independent accuracy samples.

No deployment candidate advanced to this pair. Only Gemini ran it: H01 selection 2/2; H02 abstention 2/2; repeated S11 abstention 2/2. All six met relationship, reason and required-support expectations. This confirms useful oracle observations on the pair, **not candidate capability on harder evidence**.

## All-attempt results

Screen rows below count actual dispatches, including failures. Every model had six planned screen cases; stopped cases remain explicitly untested. Correct abstention here means the action/contributor decision is correct; reason and support are scored separately.

| Configuration | Attempted / planned | Correct selections | Correct abstentions | Unnecessary abstentions | Unsupported selections | Timeouts | Other transport errors | Full passes / attempts | Source correct / usable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Kimi K3 / DeepInfra | 2/6 | 1 | 0 | 0 | 0 | 1 | 0 | 1/2 | 1/1 |
| GLM-5.3 / Morph | 6/6 | 1 | 1 | 0 | 4 | 0 | 0 | 1/6 | 2/6 |
| Qwen3.8 / Novita | 2/6 | 1 | 0 | 0 | 0 | 0 | 1 | 1/2 | 1/1 |
| DeepSeek V4 Pro / Baidu | 3/6 | 1 | 1 | 0 | 0 | 1 | 0 | 2/3 | 2/2 |
| DeepSeek V4 Flash 0731 / OpenInference | 3/6 | 1 | 1 | 0 | 0 | 0 | 1 | 2/3 | 2/2 |
| MiniMax M3 / CoreWeave | 3/6 | 1 | 1 | 0 | 0 | 0 | 1 | 2/3 | 2/2 |
| DeepSeek V4.1 Flash / DeepInfra | 3/6 | 1 | 1 | 0 | 0 | 0 | 1 | 2/3 | 2/2 |
| GLM-5.3 Flash / Wafer | 3/6 | 1 | 1 | 0 | 0 | 0 | 1 | 1/3 | 2/2 |
| Gemini-3.8 Flash / Google AI Studio | 6/6 | 1 | 5 | 0 | 0 | 0 | 0 | 6/6 | 6/6 |

For **every screen row**, invalid output = 0/N, refusal = 0/N, truncation = 0/N and HTTP service error = 0/N, where N is its attempted count. The five “other transport errors” ended without an HTTP response. Their saved generic exception category does not distinguish DNS, TLS, connection, OS or upstream causes; attribution to a provider pool would be unjustified. Two additional calls timed out. Ten-second/one-second transport failures are not evidence of fast model inference.

Total screen: **31/54 dispatched; 23 untested after stopping; 24/31 usable; 20/24 source-correct; 18/31 full passes.** Valid contract output is 24/31; completion persistence is 31/31. Reasons match 19/24 usable answers. Required-support coverage is 23/24, but this alone says little when a wrong selection cites contradictory evidence and an expected abstention has no mandatory citation list. Manual source review found relevant extra item citations; it does not rehabilitate the four incompatible relationships.

The separate six oracle confirmation attempts were all full passes: two selections and four abstentions, with zero invalid outputs, refusals, truncations, timeouts or service errors. No candidate confirmation, tuned configuration or automatic cascade was measured.

Candidate–oracle relationship agreement on matched usable screen cases: Kimi 1/1, GLM 2/6, Qwen 1/1, Pro 2/2, V4 Flash 2/2, MiniMax 2/2, V4.1 Flash 2/2, GLM Flash 2/2. Reason agreement is identical except GLM 1/6. These are small, selectively available pairs. Oracle agreement is reported independently of source correctness; Gemini did not supply evaluator labels.

## Disagreements and explanations

GLM's completed selections are unsupported on four distinct context cases within this related fixture family:

- [S08 period conflict](../runs/milestone2/model-selection-2026-09-17/screen-s08/attempts/call-006/response.json): r04 is linked to 2024 while target r05 is 2025. GLM selected r01/r04 and omitted the conflicting s06 from support. Gemini abstained; the literal header binding resolves the disagreement.
- [S11 ambiguous scope](../runs/milestone2/model-selection-2026-09-17/screen-s11/attempts/call-001/response.json): GLM cited s06 yet selected its ambiguously scoped occurrence. Valid IDs and even a relevant citation do not establish compatible scope.
- S09 and S10 repeat unsupported selection with US$/HK$ and restated/original conflicts. These are source-backed errors, not an inference from Gemini's confidence.

Two further contract-fidelity failures are distinct: GLM used `ambiguous_relationship` on S04 despite missing required evidence; GLM Flash correctly selected S03 contributors but omitted all four required header IDs. The latter is a support omission, not an incorrect contributor set.

Nine separately frozen [diagnostic follow-ups](../runs/milestone2/model-selection-2026-09-17/diagnostics/manifest.json) produced six schema-valid explanations and three HTTP 429s (Pro, V4.1 Flash and the GLM Flash support-omission follow-up). The sampling rule selected earliest full-contract failure and earliest full-pass abstention per model, plus an eligible confirmation response. It omitted eleven qualifying decisions, including GLM's four later unsupported selections; [every omission and seven unavailable initial decisions](../runs/milestone2/model-selection-2026-09-17/diagnostic-sampling.json) is listed. Thus no explanation of those four wrong selections was obtained. No diagnostic is a replacement score or a production step.

GLM's S04 explanation recognizes that distribution is absent but still defends the ambiguity label. Source inspection supports missing evidence; its speculation that the note might represent a different structure does not override the explicit relationship. V4 Flash, MiniMax and GLM Flash also identify incompleteness; that supports their abstention rationale but supplies no causal explanation for other failures. MiniMax asks for a missing value even though values are unnecessary for this operation.

Only **2/6 explanations pass a strict evidence-item-ID citation check**. Four cite limitation metadata outside that item namespace: `limitations`, `limitations:unresolved_region`, `limitations[0]`, or Gemini's real container ID `t01`. Their limitation excerpts are present in the supplied payload, so these are citation-address failures/namespace ambiguity, not four fabricated source facts. The diagnostic schema permits string IDs; literal membership is checked separately. Gemini's H02 explanation cites valid item IDs and the decisive unresolved panel scope. Self-explanations remain post hoc hypotheses, never proof of model internals.

## Costs, timing and verification

| Screen configuration | Reported USD subtotal | Attempts missing cost | Median all-attempt seconds |
|---|---:|---:|---:|
| Kimi | 0.00723045 | 1/2 | 43.57 |
| GLM | 0.0047866475 | 0/6 | 7.16 |
| Qwen | 0.00696000 | 1/2 | 14.54 |
| Pro | 0.00939048 | 1/3 | 17.81 |
| V4 Flash 0731 | 0.00016841 | 1/3 | 32.17 |
| MiniMax | 0.00054586 | 1/3 | 3.08 |
| V4.1 Flash | 0.001084472 | 1/3 | 14.94 |
| GLM Flash | 0.00023175 | 1/3 | 5.21 |
| Gemini | 0.02263125 | 0/6 | 6.33 |

Total: **46 inference attempts**, USD **0.089131708 reported**, **10 unknown-cost attempts**. Screen cost is 0.0530293195; oracle confirmation 0.02753925; diagnostics 0.0085631385. Reported usage is 36,351 prompt and 18,909 completion tokens; failed requests may have unreported usage. Requested completion caps total 169,984. First-to-last dispatch wall time was 681.91 seconds; summed attempt latency 560.51 seconds. All stayed below the frozen 117-call / 1-million-completion-token / USD35 / 120-minute ceilings. Input allowance was conservative planning, not a tokenizer-attested hard bound. No API call was spent on a budget arm, alternate route, weight download, OCR or local serving.

On the **same two usable controls only**, V4 Flash cost 0.00016841 and took 49.79 seconds combined; V4.1 cost 0.001084472 and took 33.21 seconds; MiniMax cost 0.00054586 and took 7.14 seconds; Pro cost 0.00939048 and took 35.09 seconds. These observations motivate further Flash and MiniMax assessment; they do not establish sufficiency or reliable latency tails. Native reasoning, caching, providers and transient transport are confounded.

Verification evidence:

- Historical [interface replay](../runs/milestone2/model-selection-2026-09-17/historical-interface-review.json) reproduced September 15/16 evaluations, 388 recorded hashes, all 90 prompt-only pairs, Pro B0/B1 outcomes and the original 60 Fireworks Flash HTTP 429s. The PDF-named synthetic sentinel hash was deliberately skipped. The [original direct-contributor replay](../runs/milestone2/model-selection-2026-09-17/historical-direct-review.json) reproduced 31 passes, one wrong relationship, five timeouts and five truncations. [Connected live v2 replay](../runs/milestone2/model-selection-2026-09-17/historical-live-review.json) reproduced its two usable answers, twelve ordinary 429s and correctly incomplete late-write probe. Earlier prose conclusions were not used as scores.
- The existing 77 tests passed before extension; the [final portable suite](../runs/milestone2/model-selection-2026-09-17/final-tests.txt) passed **82 tests**. New checks cover request/model binding, payload mutation before network, successful and late-failed persistence, credential redaction, and timeout/no retry. No live successful-answer late-write experiment was added; that historical gap remains.
- All **46/46 completion records**, raw response hashes, source/request snapshots and configuration bindings replay exactly. All 36 HTTP 200 envelopes, including diagnostic responses, report requested model/provider identity. The six explanation-shaped outputs are intentionally `invalid_output` under the unchanged semantic validator, then validated under the separate diagnostic schema; they are excluded from semantic invalid-output counts.
- Eight zero-call preflights and eight live batches each recorded **14 denied reads**, using both pathlib and os.open for seven protected files. OS sandbox plus exact read guard excluded keys, root `.env`, raw injection metadata and unstaged fixture files. Worker staging contained selected sources and requests only. The outer sandbox initially refused nested sandbox launch; escalated launch retained the inner OS sandbox. No approval rejection, source repair or isolation bypass occurred.
- Frozen v1/v2 modules and previous artifacts remain unchanged. Completion is terminal persistence, not semantic correctness. The transport extension is an experiment wrapper, not deployment or a new general evaluation platform. Its generic network-error capture limits causal diagnosis; safe exception-kind reporting belongs in a future version.

Read-only reproduction, from the repository root:

```sh
make evidence-check
PYTHONPATH=tools/experiments tools/eval-format-tools/.venv/bin/python tools/experiments/evaluate_model_selection.py availability screen-s04 screen-s08 screen-s11 screen-s09 screen-s10 confirmation diagnostics
```

The final inventory contains exact request/schema/prompt/code hashes, evaluator keys, expectations and raw response records. Do not rerun dated preparation or launch scripts into existing directories. The finalizer uses exclusive writes; the evaluator command above is the repeatable no-inference replay. No scored population, alert budget or runtime production budget was invented; headline audit status remains UNGATED.

## Selection decision and next discriminating experiment

**Default:** none validated. V4 Flash 0731 now has two usable direct-contributor observations, so it is no longer wholly unassessed as in the historical Fireworks run. Its context-conflict behavior remains unobserved. V4.1 is separately unvalidated; its generation cannot fill those gaps. GLM Flash has an additional measured citation omission. The Flash-first preference remains sensible as a testing priority, not an accepted runtime policy.

**Fallback:** no automatic cascade. There is no measured trigger-driven improvement in coverage, cost or latency. A service failure is observable, but candidate cross-provider failures and three diagnostic 429s do not validate a reliable fallback. A valid-ID wrong selection may be invisible to the current host validator. Gold-label routing would falsely suggest repair. Missing source evidence requires recovery or abstention, not a larger model's guess.

**Debugging:** Gemini is a useful external reference on these frozen logical cases (12/12 scored full passes), with the observed diagnostic citation caveat. Among deployment candidates, MiniMax merits a controlled debugging comparison based on two correct, relatively quick responses; it has not earned that role yet. Pro receives no preference: its fresh two correct answers do not erase historical ambiguous-scope error and truncations. GLM/Morph's four source-backed errors rule out this tested configuration as a sufficient default despite good completion availability.

The smallest next discrimination is **four new, separately frozen scored calls**: V4 Flash 0731 and V4.1 Flash each on S08 and S11, with safe transport-exception classification and a declared provider choice, plus the same bounded explanation policy. This could change which Flash deserves full confirmation; it cannot by itself establish production sufficiency. Do not automatically rerun the ambiguous historical calls or reuse their completion IDs. If usable context decisions are correct, complete the remaining currency/basis cases and the untouched-for-candidates H01/H02 pair before considering a provisional fixture default. Real-IR integration, independent expectation adjudication, amount invariance and business error budgets would still be required for a broader claim.

**Final model-choice verdict: no selected default and no automatic fallback. Final evidence-sufficiency verdict: bounded comparative evidence obtained, sufficient to reject GLM-5.3/Morph's tested semantic configuration, insufficient to validate any deployment candidate for the real audit task.**
