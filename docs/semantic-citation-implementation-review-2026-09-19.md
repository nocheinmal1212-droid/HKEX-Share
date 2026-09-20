# Independent offline review — header citation implementation 1.1

**Decision: one reproduced P2 implementation defect; make a bounded offline correction before preparing a confirmation packet.** The defect loses supported coverage when a recognized continuation wrapper is nested inside a context group. No unsupported operational annotation or research promotion was demonstrated. Saved-IR semantic acceptance and Milestone 2 remain open.

This review inspected the actual modified and untracked files, not only the Git diff. HEAD is exactly `e8000e2c001983f1f65fac75de97945c628a2287`; the ancestry check succeeds. All 12 file hashes in `implementation-bindings.json` match, as do the operation, attempt, literal prompt bytes, schema, configuration, policy and runtime identities. There is no implementation-target discrepancy.

No runtime, contract, frozen expectation, original evidence or existing review was changed. No commit, dependency installation, credential access, network/provider/model-completion call or agent delegation was performed. Only this report and separately identified diagnostics under `runs/semantic-citation-review-2026-09-19/` were added. Inputs were retained selected-source packets, exposed authored fixtures and the explicitly selected corrupted saved IR. No PDFs, native corpus exports, clean counterparts, injector metadata, evaluation operands or held-back outcomes were read.

## Findings, ordered by severity

### 1. [P2] Recognized nested presentation wrappers are counted twice in the child partition

**Location:** `src/hkex_audit/header_support.py::analyze_headers`, lines **106–112, 128–150**, especially **129–134 and 140–144**. The presentation occurrence is removed from `potential` and recorded in `presentation_refs`, but the child-building loop still inserts it into its nearest potential ancestor. The actual headers below that wrapper are inserted into the same ancestor too. The partition therefore counts the wrapper's columns and those same columns again through its children.

**Contract:** operation 1.1 lines 31–37 classifies whole-label continuation wrappers as presentation context. Revised plan §2.3 steps 2–4 requires the complete recovered partition and says a recognized presentation marker never establishes contributor membership. This is a recognized, laminar presentation wrapper over an otherwise unchanged branch, not an unknown group, an extra accounting branch, a missing role or a crossing source layout.

**Minimal reproduction:** start with exposed S01's authored source. Insert exactly this row between its revenue group and the timing/subtotal row:

```html
<tr><td colspan="3">Continued</td></tr>
```

Increase the existing unit, lease and outer-total row spans from 2 to 3. The revenue category still covers the same three literal roles; the two timing headers and `合計` remain siblings. All amounts, literal roles and column positions are otherwise unchanged. The generated IR validates with a resolved grid.

- Base source SHA-256: `55cc55a33fbf28723651602107ecbc8f98a08e7f7c9094ab7ec10619539a6ec2`.
- Transformed source SHA-256: `895c7e11847950ccd9c26b448bfc240604bb2c51b6e22c694f8af7a9fd50f13e`.
- Transformed IR SHA-256: `137ff68fb2db6e7026413170684a25dcc227fcfd5eb5022b7ebc3861f21dc640`.
- **Expected before execution:** eligible; subtotal + lease with revenue-group support; continuation optional.
- **Actual:** the control is eligible; the transformed source returns `blocked_scope`, with `non_laminar_or_incomplete_hierarchy`, `unsupported_header_group` and `unresolved_subtotal_scope`. No summary witness survives. `Continued` is nevertheless correctly recorded in `presentation_refs`.

The group interval is `[1,4)`. Its computed children include both the `[1,4)` continuation cell and all three `[1,2)`, `[2,3)`, `[3,4)` leaf cells. Each column is counted twice. **Consequence:** a supported header relation becomes a zero-call blocked opportunity solely because of known presentation structure. This is a coverage defect, not evidence of false financial findings. Existing S06 only places `Continued` outside every accounting group, so its passing test does not exercise this interaction.

The pre-execution meaning and expected boundary are in [probe-plan.md](../runs/semantic-citation-review-2026-09-19/probe-plan.md); [probe_headers.py](../runs/semantic-citation-review-2026-09-19/probe_headers.py) is the offline reproduction, and [header-probes.json](../runs/semantic-citation-review-2026-09-19/header-probes.json) records actual results. Original and transformed source/IR/query files are retained in separate `control/` and `p1_continued/` directories. These are reviewer-authored, post-exposure diagnostics, not newly independent semantic confirmation.

**Smallest justified next action:** separately authorize a bounded correction to presentation-aware partition construction. Preserve the wrapper in source/trace, but do not count it and its wrapped partition as competing membership branches. First review this new source transformation and freeze its expectation in a new regression packet. Verify both outer and subtotal targets, mandatory category support, and continued rejection of missing/extra/unknown/crossing branches. Do not fix this by loosening complete-partition checks, adding fixture IDs or granting generic subtotal semantics. Bind corrected runtime bytes in new evidence; preserve this implementation packet and historical freezes. No correction was applied here.

### 2. Scope observation: host acceptance does not certify the contributor set

**Location:** `header_support.py::analyze_headers` lines **103–110**, `candidate_in_branch` lines **179–189**, and `semantic.py::validate_answer` lines **95–111**.

On unchanged S01, an authored answer selecting the single-column `港幣百萬元` occurrence plus the lease header, with target and both selected IDs cited, passes host validation. Its semantic selection is wrong: the display unit is not a revenue contributor. The single-column unit is not added to `presentation_refs`, which only collects spanning wrappers with lower occurrences. This is probe P2 in the same pre-execution declaration/results.

**Classification: scope question/known semantic limit, not a second established implementation blocker.** Operation 1.1 explicitly declines to certify completeness/correctness of every otherwise valid contributor set. The plan's presentation-membership wording could support an additional deterministic exclusion, but this review does not silently expand that requirement. Keep this counterexample when describing the gate: citation presence is not semantic certification. Any proposed exclusion needs a bounded source-role decision, not a general natural-language validator.

### Intentional limits and unverified claims

Unknown spanning groups, unsupported scale labels, unresolved possible subtotals, missing/duplicate timing roles, extra memo branches, and innocuous associated prose intentionally lose coverage. Split caption occurrences block even with distinct ordinals. Those outcomes conform to the finite profile and are not defects merely because a person could interpret the source.

Inline-cell notes, outside-table associations, extractor association fidelity, arbitrary leaf-label interpretation, numerical prerequisites and future plan/finding isolation remain outside demonstrated behavior. Fresh model compliance, eligible semantic abstention behavior and generalization beyond these exposed sources remain unverified. Source-only agent review is not human/accounting-domain approval; this implementation review is not an untouched confirmation experiment.

## Verification matrix

| Evidence class / review question | What was checked or rerun | Result and boundary |
|---|---|---|
| Deterministic source qualification and support | All 10 `test_header_support.py` tests, including the 24 frozen source cases, every required-support omission, optional support, G1/G2/variation, nested/disjoint groups, unknown/conflicting groups, order/amount variation and branch-local unit rejection | Pass: 9 eligible and 15 blocked frozen S cases. Runtime reads source IDs and finite policy, not fixture identifiers or evaluator support arrays. New nested-presentation probe exposes Finding 1 outside that coverage. |
| Separate subtotal scope | Retained selected packet confirms revenue group at row 0, columns 1–3; timing/timing/`合計` are row-1 siblings. Reran all three mixed subtotal/component selections and exhaustive small subset check against the separately authored relationship | All three reject through `validate_summary_selection`/`summary_scopes`, not containment. Missing/duplicate roles, two totals, extra branches and unknown summary scope block. The target is exempt from the possible-contributor scope test; period containment does not create summary edges. |
| Full-interval containment | New P3 widens a copied timing occurrence beyond its category interval in a pure-header diagnostic | Crossing occurrence receives no category path; partition analysis blocks. This deliberately is not valid IR and establishes only the helper's whole-interval behavior. Operational grid validity is tested separately. |
| Prose profile | Reran whole/null-ordinal caption, split/null/distinct/duplicate ordinal, appended restriction, separate note and innocuous-prose cases. New S14-derived nonliteral formula-caption probe; edited S18 projection with recomputed metadata/query ID | Unsupported caption remains blocked despite caption-looking characters; all five answer states fail annotation. Original-IR verification and annotation reject the edited projection. Direct helper inputs are not an authenticated replacement for guarded source preparation/consumption. |
| G3–G5 local operation | Fresh runs from exact saved authored-IR selections, separate primary/research replay; credential lookup/bootstrap/transport mocked to raise | All three remain `blocked_scope`, zero HTTP/completion reservations, no annotations, byte-identical primary replay. Reviewed semantic states remain respectively `missing_evidence`, `ambiguous`, `incompatible_context`. These are zero-call controls, not model abstention tests. |
| Mixed eligible/local accounting | New two-table authored source combining S01 and G3; local query first. Offline available-metadata and unavailable-metadata mocks | Available: 2 metadata + 2 eligible completions mocked, one completion reservation per role, only eligible primary links. Unavailable: 2 metadata mocks, zero completions, eligible `unavailable`, local still blocked. Local cost/completion reservations remain zero. Primary annotation/provenance replay bytes match both modes. |
| Current attempt/role isolation | All 19 `test_semantic_integration.py` tests | Pass: actual persisted failure/abstention with accepted research, completion/configuration binding, early/late writes, promotion mutation, file-access guards, and synchronized slow research. Accepted primary persists before research finishes. Failure has no annotation; semantic abstention has no links. No claims about unimplemented plans/findings. |
| Historical v1 replay and isolation | All 3 `test_pinned_semantic_replay.py` tests; additional independent disposable copies with missing research directory, corrupt response under intact research manifest, missing manifest, malformed manifest | Valid primary retains all five annotation/provenance pairs byte-for-byte in every research variant. Separate research verification fails before output. No research manifest/directory is needed by the primary launcher/consumer. |
| Historical fail-closed binding | Existing selected-primary-file deletion/corruption, shared batch corruption, changed selection and extra pin-file tests; new primary-manifest, query-binding and pinned-code mutations | Reject as expected, with no output for these precheck failures. Current runtime rejects v1 batches/operation bindings. Launcher offers only replay commands and rejects changed frozen query bindings; there is no v1 new-query dispatch fallback. Manifests remain trusted reviewed inputs, not a hostile-code security boundary. |
| Historical research meaning | Fresh intact research replay in exact pinned environment | Original three truncations, invalid abstention (`invalid_output`) and local blank-target `missing_evidence` preserved. No usable research agreement result is created. |
| Independent semantic expectations | Read source-only review, all 24 literal header/prose inventories, fixture freeze, separate G overlay and prior investigation; compare support/scope rationale to active contract | Existing finite timing premise is supported by source meaning, not amounts. This review saw implementation and prior outcomes; its new probes are exposed diagnostics. Neither the old review nor this one supplies human/domain approval. |
| Packaging | Inspected retained wheel contents/hash and six installed runtime/resource files; reran actual installed consumer against existing authored accepted attempt | Policy is packaged. Retained wheel hash matches `e828f0cb9013c80fe6c575231634827988c0990fd9691d429c74deb5705f6673`; installed consumption reproduces exact annotation/provenance bytes. No rebuild or installation performed. |
| Future model behavior | No inference | Unverified. Stronger prompt wording and passing deterministic tests do not establish model citation compliance or semantic acceptance. |

The three focused test commands used the existing `tools/eval-format-tools/.venv/bin/python`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src`, and `unittest discover -s tests -p NAME -q`. **32 tests were rerun and passed** (10 + 19 + 3). [Header](../runs/semantic-citation-review-2026-09-19/header-tests.txt), [integration](../runs/semantic-citation-review-2026-09-19/integration-tests.txt), and [pinned replay](../runs/semantic-citation-review-2026-09-19/pinned-tests.txt) transcripts are retained. The implementation packet's transcript reports **123 tests passing**; that full-suite run was inspected, not repeated or relabeled as this review's execution.

New diagnostic results: [batch accounting and local controls](../runs/semantic-citation-review-2026-09-19/batch-probes.json), [prose](../runs/semantic-citation-review-2026-09-19/prose-probes.json), [replay isolation](../runs/semantic-citation-review-2026-09-19/replay-probes.json), [installed consumption](../runs/semantic-citation-review-2026-09-19/installed-probe.json). Their source meanings and expected boundaries were written before execution. The original batch declaration bytes are preserved as `batch-probe-plan-initial.md`; the later prose declaration adds a new probe without changing any prior expectation. Scripts intentionally use new output paths and are not in-place regeneration tools for existing packets.

## Preservation and reconciliation of claims

[Integrity verification](../runs/semantic-citation-review-2026-09-19/integrity.json) independently rehashed:

- All **127 original retained artifacts**, with the inventory matching the original retained-artifact manifest.
- All **119 prior-investigation members**, plus its report.
- All **139 protected current files**; preserved v1 contracts, original review/freeze/evaluator and schema resources also match Git objects at the base commit.
- All **123 fixture-freeze members**, **327 implementation artifact bindings**, **12 implementation file bindings**, and **31 pinned runtime/schema/package files**. Pin bytes also match the named commit's objects.
- All four recorded inputs to the implementation's source-only agent review.

All match. The four-field schema fingerprint remains `9019af0a893fb8e998d4ddd78d65e709085da332dd2fd364e70bc5ea24c46cd4`. The three intentionally versioned runtime modules differ from HEAD as expected and retain their original bytes in the pin. The prompt binding is SHA-256 of literal UTF-8 prompt bytes; the initial diagnostic also tried JSON-string fingerprinting, which is a different representation. [Clarification](../runs/semantic-citation-review-2026-09-19/integrity-clarifications.json) records both and confirms the literal-byte match; this is not a binding discrepancy.

The exact pinned Python/dependency environment was available and successfully verified by the launcher. No hashes were refreshed to accommodate an environment change. The installed-wheel evidence was corroborated with a new consumer run; the original wheel build process itself was not rerun. `git diff --check` passed.

The original Task B result remains **4/4 matching contributor sets and 0/4 complete frozen support sets**. Its three research truncations and invalid research abstention remain failures. The packet's new-policy checks of saved answers are **post-exposure diagnostic re-evaluation**; preserved hashes and replay do not turn them into repaired historical passes. The revised plan labels itself planning-only, while the dated results explicitly supersede that status for implemented scope; this is documented historical sequencing, not evidence that the new code is absent.

## Next-step decision and confirmation boundary

Proceed with the bounded offline correction described in Finding 1, followed by focused regression and a new implementation binding/review. Preserve the approved gate, finite vocabulary, role separation and all old expectations. Do not broaden note handling, change schema/model/provider policy or start inference to compensate for this defect.

**A live confirmation design is deferred until that correction is reviewed.** Existing eligible sources could later test specific claims: the outer-total source tests subtotal preference and contributor-side category citations; G2 tests measurement-group selection/citation; a distinct reviewed amount/order contrast could test that selected membership is invariant. These are candidates, not a selected or frozen packet, and need not consume three query slots.

There is no independently reviewed eligible abstention case in this packet supporting a fresh missing-evidence/ambiguity/incompatible-context model-behavior claim. G3–G5 and the blank target are local controls and cannot fill that gap. Authored abstention responses on eligible sources test host shape/persistence only. Do not bypass the gate or widen natural-language scope to manufacture live abstention coverage.

Any later confirmation must separately freeze source identities, selected cases, operation, prompt/schema/policy/runtime bindings and independently reviewed expectations **before** inference, then obtain an explicit call/time/cost budget. The earlier tentative two metadata GETs plus at most three paired eligible queries is only a ceiling to reconsider. Task B's exhausted budget is not reusable. All such work remains development evidence, and neither saved-IR semantic acceptance nor M2 is complete.
