# Two-query confirmation preparation — offline results

**The two cases and evaluator are prepared, but live execution is NO-GO.** The current launcher cannot enforce the proposed **600-second total** ceiling. A predeclared virtual-time probe completed normally at 730 seconds while the dispatcher reported 560 seconds, excluding preparation. No runtime change or live call was made. The smallest next action is a bounded deadline correction and a successor preparation freeze; requesting live approval for this known-failing execution binding would be premature.

## Frozen preparation and exact cases

The [preflight v1 packet](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/README.md), [final freeze](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/freeze.json), [reviewed expectations](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/expectations.json), and [query/request bindings](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/query-bindings.json) preserve the concrete proposal. Final verification receipts are recorded separately under `runs/semantic-citation-confirmation-2026-09-19/freeze-checks-v1/`; they do not amend the freeze.

Exactly these two existing queries were freshly prepared, in this order:

| Case | Reviewed selection | Required context citation | Intended model-behavior test |
|---|---|---|---|
| `total` | Immediate 合計 subtotal plus 租賃(HKFRS 16) | 來自與客戶合約之收入(HKFRS 15), in addition to target and both contributors | Subtotal preference and contributor-side conditional citation. |
| `period_groups` | 物業租賃, 酒店 and 物業銷售 in the target's 2025 group | 2025, in addition to target and all three contributors | Contextual occurrence selection, support and exclusion of 2024 peers. |

Both use the same explicitly selected corrupted [IR selection](../runs/semantic-citation-confirmation-2026-09-19/prepared-v1/selection.json) and retained `mask_body_amounts_v1` specifications. Full table/target/contributor/support IDs and literal source occurrences are retained in the linked JSON, not sent as evaluator lists to either model. All **230** retained source-packet nodes match the selected IR; the fresh projections contain **44** and **186** items, reconstruct exactly and are both eligible under `header-source-analysis-1.0.1`. Each role pair has equal semantic input and distinct attempt identity. The literal **截至2026年12月31日止年度** caption and common **港幣百萬元** units are preserved.

Expectations carry forward the [existing independent source-only review](../eval/semantic-citation-investigation/2026-09-19/independent-source-review.json). Its source citations were checked against both the retained packet and selected IR. No new semantic judgment was required. This is a same-agent, post-exposure migration, not new independent/blind adjudication or human/domain approval. Common units are optional because they do not establish membership in this operation; prior failing support counts are not the migration rationale. 合計 and the timing headers are physical siblings under the revenue group; the finite summary rule supplies their semantic relationship.

These are exposed development cases, not a holdout or accuracy estimate. They do not constitute a live test of the new nested-Continued fixture. G3, G4 revision 2 and G5 remain separate zero-call controls, with reviewed source states `missing_evidence`, `ambiguous` and `incompatible_context`; the runtime blocks all three as `blocked_scope`. Their prior correction evidence is cited, not relabeled as a fresh source run. Blank target was freshly checked as a zero-call `missing_evidence` control. None can establish live model abstention behavior. No eligible reviewed abstention source or third live case is proposed.

## Execution binding and proposal

[Execution identity](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/execution-identity.json) records the existing explicit `tools/eval-format-tools/.venv/bin/python` interpreter, executable hash, Python/ABI/virtual-environment identities, five installed dependency inventories, actual imported module locations, all **33** source/schema/config files and a byte-verified source snapshot. The snapshot successfully replays both authored primary annotation/provenance pairs byte-for-byte. The older installed wheel was not used, rebuilt or installed.

The fresh [runtime-only preparation](../runs/semantic-citation-confirmation-2026-09-19/prepared-v1/) contains literal prompt bytes, unchanged four-field response schema, configurations, two queries and four role requests. Evaluator expectations and authored evaluation reports stay outside it and outside operational file allowances. No `started.json`, response or completion exists in the reserved live attempt path.

| Binding | Value |
|---|---|
| Operation / attempt | `direct-contributor-headers-1.1.0` / `paired-semantic-attempt-1.1.0` |
| Analysis / vocabulary policy | `header-source-analysis-1.0.1` / `header-support-policy-1.0.0` |
| Prompt SHA-256 | `bf071b1efd8bcf4b7c4d7dca848c979ba01ccf835da7d7e151568e965011258c` |
| Response schema fingerprint | `9019af0a893fb8e998d4ddd78d65e709085da332dd2fd364e70bc5ea24c46cd4` |
| Runtime identity | `763e67e891af0d5d7e5ae08d7b6a6bca46a3884b2775f0785f1312c6165f06ea` |
| Reserved nonce | `live-v1` |
| Reserved output, still nonexistent | `runs/semantic-citation-confirmation-2026-09-19/live-v1` |

The [exact launch proposal](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/launch-proposal.json) is an argv array using `-I -B`, the explicit existing interpreter and the corrected repository's absolute `src` import path. Its CLI arguments are `run`, the new selection/query files, the reserved output, `--max-http-calls 6 --max-role-calls 2 --max-seconds 600 --max-cost 8`. It does not use credential bootstrap. **Do not execute this no-go proposal.**

The [read-only checker](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/check_freeze.py) requires an externally specified freeze digest, verifies frozen content and complete runtime inventory, interpreter/dependency identities, module locations, source hashes and regenerated in-memory projections/requests, and checks that the reserved output does not exist. Drift causes failure without overwriting or regenerating approved files. Its default readiness check deliberately rejects this packet. `--bindings-only` is diagnostic and is not a launch gate. The immediately-before-launch check remains a required future action against a ready successor freeze; the check performed now is an offline rehearsal, not a claim that a future workspace is unchanged.

## Findings and smallest next action

**Execution blocker — total time is not enforced.** In [`semantic_cli.py::run`](../src/hkex_audit/semantic_cli.py#L152), preparation runs at line 157 before the clock starts at line 170. Checks at 173 and 211–212 admit transport work, while consumption at 226 uses `isolated`'s separate 180-second worker timeout. There is no enclosing total-deadline supervisor.

The [probe plan](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/probe-plan.md) fixed the meaning and expected boundary before execution: total elapsed includes preparation and consumption. The [actual dispatcher diagnostic](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v1/budget-total_time.json) uses virtual preparation 170s, two metadata requests of 55s each, two concurrent completion pairs of 55s each and two primary consumers of 170s each. Every individual duration is below its existing timeout. All six mocked calls are admitted; the function returns normally at **730s from entry**, with **560s reported elapsed**. No real waiting or provider traffic is represented by those durations.

The smallest justified correction is one total deadline from launch entry covering preparation, metadata, paired dispatch, consumption and child-process termination, preserving partial artifacts and preventing post-deadline dispatch. Keep model settings, semantic scope, expectations and the two-case selection unchanged. This correction is **not implemented or authorized here**. It needs its own regression, offline review and successor binding/freeze. Changing the interpretation of “total,” lowering a CLI parameter without a guaranteed bound, or refreshing this freeze's hashes would not resolve the finding.

**Known host coverage limit, successfully handled by the evaluator.** A single-column unit plus lease remains schema/host-valid even with the full reviewed citation set. The independent contributor comparison rejects it. This is the previously retained scope limitation, not a new reason to widen runtime policy or patch it during preparation. Host acceptance and citation presence do not certify general semantic correctness or natural-language interpretation.

## Verification actually performed

The evaluator is [evaluate.py](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/evaluate.py), which preserves the [historical evaluator](../eval/semantic-integration/validate.py) and reuses its exact contributor/support comparison. Its current-format adapter separately reports availability, schema validity, host validation, exact reviewed contributor/state agreement, citation sufficiency, and completion-bound primary persistence. Parseable host-rejected answers remain evaluator-only diagnostics; truncated text is never promoted. Both evaluator identities are frozen.

| Verification class | Freshly performed | Result / limit |
|---|---|---|
| Corrected tree and source | 18 corrected binding files; runtime/prompt/schema/policy/config identities; actual module paths; 230 source nodes; both projections and four requests | Match; both cases eligible, equal semantic inputs, role identities distinct. |
| Correct authored lifecycle | Actual paired dispatcher, four authored completion transports, real guarded primary consumers and evaluator CLI | Both cases pass each role's host, exact contributor and support checks; actual primary annotations/provenance retained. This is authored development evidence, not model success. |
| Missing group citations | Both cases, same correct contributor sets | Host rejects; independent contributor checks remain true; required support checks fail. |
| Wrong period / contradictory abstention | 2024 occurrences with complete reviewed citations; ambiguous state with contributors retained | Host rejects; independent contributor/state check fails. |
| Known semantic counterexample | Single-column unit plus lease, including full required reviewed support | Schema and host accept, citation presence passes, independent contributor-set comparison fails. Overall failure retained. |
| Failed response outcomes | Timeout, length truncation, schema-invalid output, wrong served model identity | Distinct host failures, no primary annotations, no repair. Accepted research does not replace primary. |
| Primary abstention | Authored empty-contributor abstention with accepted research | Primary abstention record has no contributor links; cannot count as expected selection success. |
| Role isolation and corruption | Remove/corrupt research in disposable copies; corrupt primary completion; separate research replay | Primary bytes unchanged by research changes, while separate research replay fails. Primary corruption blocks primary and does not invalidate accepted research. Guard logs exclude evaluator/research reads from primary. |
| Snapshot replay | Replay both authored primary cases using the retained corrected source snapshot | Annotation and provenance bytes identical, zero calls. |
| Budget admission | Exact baseline and missing route, wrong metadata identity, over-cap price, metadata timeout, cost cap, HTTP cap, role cap and elapsed admission controls | Baseline reserves 6 calls, 2 completions/role and $3.65958; negative cases block applicable calls without alternate routes or retries. This does not prove the hard total-time ceiling. |
| Hard total-time ceiling | Predeclared virtual-time boundary, unchanged dispatcher | **FAIL: 730s total / 560s reported**, the live blocker. |
| Local controls | Blank target freshly dispatched/consumed offline; G3/G4 revision 2/G5 correction records inspected | Blank target: zero calls and no annotations. G controls: cited retained zero-call evidence, no fresh extra source IR read. |
| Preservation | Repeat five inventories and source/runtime comparisons | 18 corrected files, 183 correction artifacts, 68 fixture-freeze members, 127 original retained hashes and 119 investigation members match. |
| Future model behavior | None | No completion, metadata GET, provider availability or pricing check; no statistical/semantic acceptance claim. |

See the [authored case matrix](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v1/case-matrix.json), [baseline evaluation](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v1/baseline-evaluation.json), [role isolation results](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v1/role-isolation-followup.json), [snapshot replay verification](../runs/semantic-citation-confirmation-2026-09-19/snapshot-replay-v1/snapshot-replay-verification.json), and [preservation verification](../eval/semantic-citation-confirmation/2026-09-19/preflight-v1/preservation-verification.json). Reproduction helpers and all generated diagnostic members are bound by the freeze. The first diagnostic script encountered a reporting-only `KeyError` after successful research replay; a separately retained follow-up helper completed the same checks in new paths. No expected outcome, runtime file or existing output was changed to hide that interruption.

The previously reported 4 partition + 10 header tests, correction's 36 focused tests, original 123-test suite and installed-wheel verification are **cited historical evidence, not rerun claims** here. Fresh verification instead addresses these selected sources, fresh requests, evaluator boundaries, persistence/isolation and the exact proposed budget. No old saved model answer was rescored.

## Success, stop criteria and approval status

Every proposed primary result needs intact request/completion bindings, host acceptance, exactly the reviewed contributor set and all required source support. Research is independently recorded, never fallback, consensus, veto or annotation input. The denominator remains two cases per role even for missing, invalid, truncated, timed-out or unavailable outcomes. There is no repair, retry, case substitution, third case, altered reasoning setting or increased research token cap.

The contemplated ceiling remains **6 HTTP calls: 2 metadata GETs + 2 primary and 2 research completions; 600 seconds total; 60 seconds per attempt; $8 conservative reservation; 4096 output tokens per completion; zero retries/fallback.** Provider availability and actual pricing remain unknown. Authorized metadata would consume this same budget and must validate exact current routes, models, providers, controls and price caps. Failure blocks the affected role as the current dispatcher specifies; another eligible role may continue, without replacement calls. A completion identity mismatch is a rejected outcome. Task B's exhausted budget is not reused.

**No live approval is requested for this failing freeze.** The instruction to stop when an essential execution check fails applies: first authorize and review the bounded deadline correction, then prepare a successor freeze. Only after that should one concrete live approval request identify its exact digest, nonce, output and the unchanged six-call/600-second/$8 ceiling. This is an explicit unresolved prerequisite, not silent expansion of this handoff's runtime authority.

The workspace remains uncommitted at the verified ancestor `e8000e2c001983f1f65fac75de97945c628a2287`; modified and untracked implementation files were included, and unrelated work and old packets were preserved. No PDFs, native corpus exports, clean counterpart, injector metadata, evaluation numeric operand lists, held-back outcomes, credentials, network, downloads or agent delegation were used.

Historical **0/4 complete frozen support**, three research truncations and the invalid research abstention remain unchanged. Saved-IR semantic acceptance and Milestone 2 remain open. Empty downstream outputs do not establish financial isolation, and these header tests establish no numerical compatibility.
