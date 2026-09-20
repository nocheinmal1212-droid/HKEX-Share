# Nested presentation partition correction — offline results

**The approved P2 correction is implemented and verified offline.** A recognized `Continued`
wrapper nested inside a revenue group no longer blocks an otherwise supported relationship by
counting its columns twice. The four new regression tests and 32 existing focused tests pass.
Saved-IR semantic acceptance and Milestone 2 remain open; no live confirmation was performed.

## Change and bounded review

The change follows Finding 1 of the
[independent implementation review](semantic-citation-implementation-review-2026-09-19.md), approved
by the owner with “Approved.” The revised implementation changes only
`header_support.py::analyze_headers` membership-child construction: skip occurrences already
classified as presentation wrappers. Their wrapped headers still undergo the original exact
partition, qualification, context and summary checks. Source occurrences, fragments, spans and
projection inventory remain intact. No geometry-only summary, new vocabulary or fixture-specific
runtime rule was introduced. Finding 2's single-column unit/contributor scope observation is unchanged.

The [source review and expectations](../eval/semantic-citation-implementation/1.1.1/source-review.md)
were frozen before editing runtime or executing new candidate-answer tests. The original P1 source
and IR bytes were copied exactly. Additional authored variants exercise repeated wrappers,
order/amount variation, missing/duplicate timing roles, extra memo content, unknown wrappers and
crossing contextual groups. The [freeze](../eval/semantic-citation-implementation/1.1.1/fixture-freeze.json)
binds eight sources, thirteen target expectations and the pre-correction package. These are exposed
regressions based on the approved review, not a new independent or human/domain source adjudication.
No additional agent was launched.

A same-agent follow-up inspection confirms that the patch excludes only occurrences already in
`presentation_refs`. It does not change presentation classification, hide unknown branches, bypass
blank/unsupported content checks, change complete-partition equality or alter the three-role
summary matcher. Existing missing-discriminator and prose gates remain intact. Both outer-total and
subtotal answers still require their category citation, and every subtotal-plus-component overlap
is rejected. This inspection and its tests address the reproduced defect; they do not certify all
possible semantic selections or replace an independent review of the new bindings.

## Verification actually performed

| Check | Result |
|---|---|
| New regression tests before correction | Failed as intended: all six positive target cases were incorrectly blocked; support/persistence checks could not proceed; old analysis identity differed. Original transcript retained. |
| New regression tests after correction | 4 tests pass across all 13 frozen target cases: 6 eligible, 7 blocked. Both outer/subtotal relations, repeated wrappers, amount/order variation, required support, optional wrappers, wrapper-as-contributor rejection, three overlap combinations and old-query rejection are covered. |
| Existing header support suite | 10 tests pass; all 24 original S fixtures and existing G expectations remain unchanged. |
| Existing semantic integration suite | 19 tests pass, including role binding, primary failure/abstention with accepted research, guarded reads, write faults, promotion rejection and slow-research synchronization. |
| Existing pinned v1 suite | 3 tests pass in the available pinned environment, including research deletion/corruption independence, primary/shared failures and current v1 rejection. No pin refresh. |
| New persisted authored outputs | Outer and subtotal selections produce two primary links each. Separate consumption and replay produce identical annotation/provenance bytes. Guard records contain no adapter import or research reads. Mock responses are explicitly authored, not provider completions. |
| G3, G4 revision 2, G5 | Fresh all-local batches retain `blocked_scope`, zero HTTP/completion reservations and empty annotations. Credential lookup/bootstrap/transport were configured to fail if attempted. Their reviewed semantic states remain separate. |
| Prior 1.1 runtime preservation | All 33 package/schema/config files match the pre-edit baseline. The preserved runtime replays an original authored accepted attempt with byte-identical annotation/provenance. Corrected runtime refuses an old 1.1 batch before creating output. |

The commands used the existing local Python environment with `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH=src`, running `unittest discover -s tests -p FILE -q` for
`test_presentation_partition.py`, `test_header_support.py`, `test_semantic_integration.py` and
`test_pinned_semantic_replay.py`. **36 focused tests passed.** The full 123-test historical suite was
not rerun or claimed as a new result. The corrected wheel was not rebuilt or installed; packaging
configuration and the policy resource are unchanged. No new installed-package validation is claimed.

[Offline results](../eval/semantic-citation-implementation/1.1.1/offline-results.json) retain the
source-derived analyses, query identities, persisted annotations/provenance and guard records.
Transcripts and source/attempt outputs are under `runs/semantic-citation-correction-1.1.1/`;
[artifact integrity](../eval/semantic-citation-implementation/1.1.1/artifact-integrity.json) binds them.
Existing generation scripts and frozen output paths were not reused.

## Version and preservation

[Analysis revision 1.0.1](../spec/header-source-analysis-1.0.1.md) makes the correction explicit in
host/query identity. Operation, prompt, response schema, vocabulary policy, attempt/batch formats,
provider/model settings and research roles retain their prior versions and bytes. The new analysis
identity and runtime hash deliberately reject old queries/batches in current consumption. Old
completions are never reinterpreted or rebound automatically.

[New implementation bindings](../eval/semantic-citation-implementation/1.1.1/implementation-bindings.json)
identify the corrected tree. The old twelve-file binding intentionally differs only at
`src/hkex_audit/header_support.py`; its exact old bytes are preserved in the new packet's
`runtime-before` snapshot. All other old binding members match. Old packet metadata is unchanged.

[Preservation verification](../eval/semantic-citation-implementation/1.1.1/preservation-verification.json)
checks all 127 original retained hashes, 119 investigation members, 139 protected files, 327 original
implementation artifact members and the review's recorded artifacts. Original contracts, reviews,
expectations, schema resources and original implementation/result packets remain unchanged.
`git diff --check` passes. No unrelated work was reset, cleaned or committed.

The historical outcome remains **0/4 complete frozen support**, alongside matching contributor
sets, three research truncations and an invalid research abstention. No saved model answers were
rescored here. All new responses are authored offline controls; no network/provider calls,
credentials, raw PDFs, native corpus exports, clean counterparts, injector metadata, held-back
outcomes, OCR or dependency installation were used.

## Next boundary

The bounded correction is ready for review of its new bindings. After that review, a confirmation
packet may be prepared separately with frozen selected sources, source-reviewed expectations and
operation/prompt/schema/policy/runtime identities. A live run still requires explicit call/time/cost
approval; the prior tentative ceiling is neither authorization nor a target to fill.

G3–G5 remain zero-call controls and cannot be counted as live abstention tests. This packet supplies
no independently reviewed eligible abstention source. Preserve that coverage limit instead of
bypassing the gate or widening natural-language scope. No semantic acceptance or M2 completion is
claimed from this correction.
