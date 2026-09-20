# Bounded offline deadline correction and successor preparation

**The execution blocker is corrected; the two-query development test is GO pending explicit live
approval and its immediate prelaunch binding check. No live run was executed.** The successor is
[preflight v2](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/README.md).
Its [freeze](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/freeze.json) and separate
[final digest/checker receipt](../runs/semantic-citation-confirmation-2026-09-19/freeze-checks-v2/verification-receipt.json)
identify the concrete approval target. The original no-go packet and digest remain intact.

## Change and version

[Exact correction patch](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/correction.patch),
[implementation bindings](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/implementation-bindings.json),
and [execution contract 1.2](../spec/paired-semantic-attempts-1.2.md) describe the change. The monotonic
clock begins at `run` entry, before preparation. A parent supervisor owns one process session for
source/output preparation, metadata, dispatch, response persistence, primary consumption and waiting
executor tasks. It cancels the owned group and reaps its child; receipt-file writing is itself bounded
inside the same deadline. Per-stage limits remain 180 seconds for source consumers and 60 seconds
for transports, shortened to remaining time. Cleanup reserves one second *within* a 600-second
budget; it is not an extra grace period.

The runtime checks expiry after reservations and launch-intent persistence, before transport process
creation, at transport entry and after DNS before the HTTP boundary. Launch intent does not prove an
issued request. Missing/partial return evidence remains unknown, at most one call, rather than zero.
Known pre-dispatch expiry is zero. Reservations remain conservative; no retry or repair occurs.
Completed attempt markers and annotation/provenance bytes are not overwritten; partial JSON and
uncommitted attempts remain incomplete. The evaluator separately reports unavailable consumption.

Attempt/batch identities change to 1.2.0, and runtime identity includes `semantic_deadline.py`.
Operation, prompt, four-field response schema, vocabulary, header analysis and provider/model
configurations are unchanged. Old replay is explicit through retained snapshots, never automatic
rebinding. README/PLAN/log updates describe execution only; no M2 checkbox was completed.

## Verification actually rerun

- The [final controlled-environment transcript](../runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2/tests-controlled-environment.txt)
  records 52 selected tests, including deadline subcases and the existing budget/persistence/replay,
  role isolation, header and nested-presentation regressions. The Python process is launched with a
  cleared environment; test transports are authored offline replacements. The existing environment
  is used directly, without installation, downloads or a wheel rebuild.
- [Real cancellation and artifact/accounting evidence](../runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2/final-results-controlled.json)
  covers preparation; first/second metadata; paired completions; response persistence; consumption;
  the second query; and slow research after committed primary. Recorded owned worker, authored
  transport and descendant PIDs are absent after launcher return. Three-second cancellation cases
  return inside three seconds; the longer real-consumer cases have separately declared test ceilings.
  A 0.15-second measurement allowance was declared for short tests, but collected successful elapsed
  values are inside their nominal ceilings. It never enlarges the proposed 600 seconds.
- The original virtual 730-second schedule now stops at **599 seconds from entry**, without a
  successful batch summary, reserving cleanup inside 600. Preparation and consumption both count.
  Separate virtual cases cover expiry before/between metadata, between queries and after reservation.
- [Edge checks](../runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2/edge-checks-controlled/results.json)
  establish zero HTTP dispatch at entry/post-DNS expiry, zero after launch-journal failure, bounded
  cancellation of a stuck receipt writer, and rejection without modifying a pre-existing output.
- [Budget/evaluator/isolation transcript](../runs/semantic-citation-confirmation-2026-09-19/deadline-diagnostics-v2/evaluator-budget-isolation-followup.txt)
  and [baseline evaluation](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v2-followup/baseline-evaluation.json)
  retain two authored successes per role, six reservations, two completions per role and $3.65958
  conservative reservation. Missing route, mismatched metadata identity, over-cap pricing, timeout,
  cost, HTTP and role caps block applicable calls without replacement. These budget controls run
  the actual batch body with authored transports; real supervisor timing is tested separately.
- The [ten-variant evaluator matrix](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v2-followup/case-matrix.json)
  preserves missing-group, wrong-period, contradictory-abstention, timeout, truncation, schema and
  identity failures. **Single-column unit plus lease still passes schema/host/citation presence but
  fails exact reviewed contributor agreement.** It remains an overall failure, not a widened policy.
- [Role isolation](../runs/semantic-citation-confirmation-2026-09-19/diagnostics-v2-followup/role-isolation.json)
  confirms identical primary bytes with research deleted/corrupted. Accepted research never promotes
  failed/abstained primary. Real slow-research cancellation preserves completed primary annotations;
  primary corruption blocks its own replay. Guard records exclude research/evaluator reads.
- [Snapshot replay](../runs/semantic-citation-confirmation-2026-09-19/snapshot-replay-v2/verification.json)
  reruns both authored cases under the retained 33-file old snapshot and the corrected 34-file
  snapshot. Both reproduce annotations/provenance byte-for-byte with zero calls.

The [same-agent review](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/review.md)
inspected deadline propagation, cancellation races, completion binding, partial artifacts, accounting
and isolation after verification. It is not independent approval. The supported process topology is
POSIX owned sessions with no detached workers; these measurements do not certify hard-real-time OS
behavior. Failure to verify cleanup never counts as success.

Initial harness failures remain in separate files: sandbox denial of process-list inspection,
insufficient fixture time for actual IR validation, and the budget helper initially patching only the
old clock namespace. Follow-up paths preserve successful checks without overwriting earlier evidence.
The earlier v1 helper's reporting-only KeyError and successful follow-up remain separate and unchanged.

## Preserved evidence and successor identity

Before editing, all **760** old freeze members, all **33** old snapshot files, and the five retained
inventories matched. HEAD remains at the verified ancestor `e8000e2c001983f1f65fac75de97945c628a2287`;
modified and untracked implementation was included. [Preservation verification](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/preservation-verification.json)
rechecks the 183 correction artifacts, 68 fixture members, 127 original retained hashes and 119
investigation members unchanged. The old freeze and 18-file correction binding each have five
intentional current-file deltas, enumerated separately with exact retained original bytes. No old
hash was refreshed to make changed working files appear unchanged. Historical launchers/pins remain.

The successor [execution identity](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/execution-identity.json)
binds the complete 34-file runtime/schema/config inventory and snapshot, actual interpreter and
installed dependency identities. [Queries/requests](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/query-bindings.json)
are freshly bound to **live-v2**, with distinct role attempt IDs. Both query bytes and all model-facing
payloads are unchanged from v1. Source-reviewed [expectations](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/expectations.json)
are byte-identical and remain outside runtime allowances/model payloads. The literal 2026 caption,
common units, amount masks and selected corrupted IR/manifest identities are preserved.

Exactly `total`, then `period_groups`: immediate 合計 plus lease with revenue-group support; then
three 2025 peers with 2025 support and exclusion of 2024 peers. G3, G4 revision 2, G5 and blank target
are cited retained zero-call controls; nested Continued is an offline regression, not a third live
case. No PDFs, native corpus exports, clean counterpart, injector data or held-back outcomes were read.

## Approval boundary

The [exact launch proposal](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/launch-proposal.json)
reserves nonexistent `runs/semantic-citation-confirmation-2026-09-19/live-v2`, nonce **live-v2**.
`live-v1` also remains nonexistent and unused. The proposed ceilings remain **6 HTTP calls** (2
metadata GETs + 2 primary + 2 research completions), **600 seconds total**, **60 seconds/attempt**,
**$8 conservative reservation**, **4096 tokens/completion**, **zero retries/fallback**. Availability
and actual pricing are unknown until separately authorized metadata checks, within this same budget.
No alternate route, substituted case, larger cap or reuse of Task B's exhausted budget is allowed.

The checker must pass against the explicit approved successor digest immediately before launch.
Its offline positive/negative rehearsal is not a guarantee that a future workspace is unchanged and
is never authorization by itself. Any changed binding stops execution without regenerating requests.
No network/provider calls, metadata GETs, dependency installation, commit or agent delegation was
performed. No live execution follows this report automatically.

Historical **0/4 complete frozen support**, three research truncations and invalid research abstention
remain unchanged. No saved-answer recheck repairs that result. These remain exposed development
cases, not holdout/statistical evidence or human/domain acceptance. Saved-IR semantic acceptance and
Milestone 2 remain open; no numerical compatibility or downstream financial isolation is claimed.
