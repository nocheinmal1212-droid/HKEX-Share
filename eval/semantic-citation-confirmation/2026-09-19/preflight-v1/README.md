# Two-query development confirmation — preflight v1

**NO-GO for live execution.** The cases, requests, source expectations and evaluator are prepared offline. The current launcher fails the proposed **600-second total** boundary. This packet preserves that result and must not be launched. No live authorization exists. `check_freeze.py` defaults to rejecting this no-go packet even when all identity checks pass.

The final `freeze.json` binds this review material, runtime-only prepared artifacts, exact source-tree bytes, selected input hashes and diagnostics. A later correction needs a separate versioned packet; never refresh this freeze to admit changed bytes. `launch-proposal.json` records exact proposed argv, not an executable authorization. The live directory is reserved and nonexistent:

`runs/semantic-citation-confirmation-2026-09-19/live-v1` — nonce `live-v1`.

## Cases and source expectations

Exactly `total`, then `period_groups`, both from the selected corrupted IR with `mask_body_amounts_v1`. Selection IDs are in runtime-only `prepared-v1/queries.json`; full IDs, literal text, spans, fragments and source pointers are in evaluator-only `expectations.json`. All 230 selected-source packet nodes match the selected IR. Projections contain 44 and 186 items respectively and reconstruct exactly; both gates are eligible under analysis 1.0.1. Both role requests have equal semantic payloads and distinct role/attempt identities. Only fresh requests were generated for `live-v1`; none was dispatched.

| Order | Case | Reviewed immediate contributors | Required source support beyond target/contributors | Claim the proposed model response could test |
|---|---|---|---|---|
| 1 | `total` | 合計 and 租賃(HKFRS 16) | 來自與客戶合約之收入(HKFRS 15) | Prefer the immediate subtotal to its summarized timing components and cite the contributor-side revenue group. |
| 2 | `period_groups` | 物業租賃, 酒店, 物業銷售 within 2025 | 2025 | Select the three target-period occurrences, exclude 2024 peers and cite the necessary group. |

The common 港幣百萬元 display unit is optional in both cases. Timing headers are optional corroboration for `total`; 2024 is optional corroboration for `period_groups`. The unchanged four-field schema contains no prose rationale field. Extra support does not excuse a wrong contributor set. The literal 截至2026年12月31日止年度 caption remains unedited. No amount equation selects contributors.

These judgments come from `eval/semantic-citation-investigation/2026-09-19/independent-source-review.json`, whose cited occurrences were freshly checked against the selected source packet and IR. That review was an independent source-only agent review, not human/domain approval. This migration is by the same exposed preparation agent, not a new independent or blind adjudication. The review's “descendants” language for timing components describes semantic summary membership; 合計 and both timing headers are physical siblings. Operation 1.1's finite summary rule supplies the relationship. Common units became optional because they do not determine membership in this operation, never because historical responses failed to cite them. No new semantic judgment was needed for these two cases.

These are exposed development cases, not a holdout or statistical accuracy estimate. They do not test the new nested-Continued source live. G3, G4 revision 2 and G5 remain separate `blocked_scope` zero-call controls with source judgments `missing_evidence`, `ambiguous`, and `incompatible_context`. Their retained correction results are cited, not rerun on new source IR here. Blank target is freshly rerun as local `missing_evidence`, zero calls and no annotations. There is no independently reviewed eligible abstention case in this packet. Do not bypass the prose gate or add a third query to create that coverage.

## Execution and evaluator separation

`execution-identity.json` records the explicit existing Python interpreter, executable hash, Python/ABI/virtual-environment identities, five dependency inventories, actual source module locations, operation/attempt/batch/policy versions, prompt/schema hashes and all 33 source/schema/config files. A byte-verified source snapshot is retained under runtime-only `prepared-v1/runtime-snapshot/`; it was used for zero-call replay. No old wheel was used, built or installed. Literal UTF-8 prompt bytes and the unchanged schema are separately retained.

Runtime allowances contain only explicitly selected IR/manifest and the appropriate attempt's files. Expectations, `evaluate.py`, old evaluator and authored evaluation reports are outside those allowances and absent from model payloads. `evaluate.py` reuses the unchanged historical evaluator's exact-set/support-subset comparison, with a new adapter for current completion replay, independent raw candidate diagnostics and primary persistence checks. Every live result must satisfy current host validation **and** reviewed state/contributor equality **and** required citation sufficiency. Parseable content in a rejected host response is diagnostic only. Truncated text never becomes an answer.

Authored responses are exclusively in `diagnostics-v1`, with diagnostic nonces. Their persisted annotations retain the runtime schema's `method=model` field, but directory identities and evaluation records explicitly identify every such response as authored, not inferred. The reserved live requests were never reused as diagnostic attempts. The source snapshot replay uses the diagnostic attempt's original nonce and completion bytes; it is not a new attempt.

## Budget and stopping contract

The proposed ceilings are six HTTP calls total (two metadata GETs, four completions), two completions per role, 600 seconds total, 60 seconds per attempt, $8 conservative reservation, 4096 output tokens per completion, no retries or fallback. Preserve the exact primary/research route, model, native reasoning and provider configuration in `configurations.json`. Prior Task B budget remains exhausted and unrelated. The four request reservations sum to **$3.65958**, using the existing conservative formula and frozen route price ceilings; this is not an actual price or availability quote.

Metadata remains unknown until a separately authorized run. Each role needs exact advertised model/route/provider identity, availability and required controls, finite nonnegative prompt/completion prices within current caps and no unsupported charge. Metadata itself consumes the HTTP/time budget. Invalid/unavailable metadata prevents that role's completion calls; the current dispatcher can continue the other eligible role. A completion identity mismatch is recorded and rejected. Exhaustion yields visible unavailable/budget outcomes, never alternate routing, retries, larger token caps, changed native reasoning or substituted cases. All two primary and two research case slots stay visible; no selective denominator or repair.

Research is reported independently, never fallback, consensus, veto or annotation input. Each primary case is a success only if the reviewed contributor set and required support both pass along with host validation and intact completion/persistence bindings. Host acceptance alone is insufficient. Report missing, invalid, timed-out, truncated, unavailable and incomplete outcomes separately. Primary abstention produces no contributor links; accepted research cannot promote it.

### Blocking budget result

`semantic_cli.run` prepares before starting its clock (lines 157 and 170), uses time only for dispatch admission (173 and 211–212), and consumes primary output through a separate worker with its default 180-second timeout (226; `isolated` at 32). The predeclared virtual-time probe uses preparation 170s, two metadata requests of 55s, two concurrent completion pairs of 55s, and two consumers of 170s. All individual durations respect existing timeouts. The unmodified dispatcher makes all six mock calls and returns success at **730s total**, reporting **560s** after preparation. This falsifies the hard total ceiling; it is not a real latency measurement.

The smallest next action is a separately authorized bounded correction that enforces one deadline from launch entry across preparation, metadata, paired work, consumption and child-process cleanup, with no post-deadline dispatch and no retry. Keep semantic scope and model settings unchanged. Rerun the boundary probe and relevant budget/isolation checks, then create a successor freeze before asking for live approval. Merely lowering or relabeling the requested ceiling, or refreshing this packet's hashes, is not a correction.

## Offline check and eventual launch sequence

`check_freeze.py --freeze <absolute freeze.json> --expected-sha256 <approved digest>` is a read-only check with no credential, network or transport action. It verifies all frozen files, complete runtime inventory, environment dependencies and module locations, reprojects both queries from the selected IR in memory, compares all four requests byte-equivalently, checks eligible gates and verifies the reserved live path is absent. Any drift fails; nothing is rewritten. `--bindings-only` is explicitly diagnostic and must never be used as a launch permission gate. The default readiness check rejects this packet's known time blocker.

A future ready packet's successful default check must occur immediately before its exact launch argv, in an unchanged workspace and environment. Do not invoke this v1 proposal directly or bypass the check. There are no automatic calls following preparation. Credentials are neither inspected nor bootstrapped by these preparation/evaluator helpers; the eventual authorized CLI requires its configured environment credential as documented by the existing dispatcher.

**Live approval is deferred because the essential execution check failed.** The intended approval scope, once a successor freeze is ready, remains exactly the six-call/600-second/$8 two-case proposal above, with 60-second attempts, 4096 output tokens and zero retries/fallback. The approval request must identify that successor freeze's hash, nonce and output path. Approval of preparation is not approval of this proposed run.

Historical **0/4 complete frozen support**, three research truncations and invalid research abstention remain unchanged. No saved model answers were rescored. No numerical compatibility, general natural-language certification, downstream financial isolation, semantic acceptance or M2 completion is claimed.
