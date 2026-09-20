# Independent retrospective review of Milestone 0

Reviewed 2026-09-10 America/New_York (2026-09-11 UTC), by Codex in a fresh review
requested by the project owner. Baseline: `5e30566e939a404975d0efdfcff53c8d55745fe0`;
closure: `0b2a712`; current HEAD: `18c6722780d7d6646cf3685499a1cff688af3967`.
The current working tree also contains pre-existing Milestone 1 review corrections.
This is a retrospective recommendation, not a new owner approval or Milestone 1 acceptance.

**Conclusion: retain Milestone 0's limited closure and the four ready development records.**
I found no unsupported source change, incorrect operand, rounding miscalculation, missed
cancellation in the two approved equations, or changed approval-bound input that requires
reopening that closure. I found no evidence that a Milestone 0 error has corrupted the inspected
Milestone 1 occurrence mappings. This does not certify an implemented detector: none ran.

The pre-closure packet left propagation unknown; the closure commit supplied the explicit
source-review decisions and bound revised records to the owner's authorization. It did not contain
an independent review. The present review supplies that missing second assessment; it does not
backdate one. The user's approval, now confirmed in this task, is not being inferred solely from
the repository's self-reported approval text.

## Four-case decisions

Physical page numbers below are one-based. Their printed labels are two lower; canonical page
indices are one lower. Full-page images, surrounding rows and headings were inspected, alongside
saved character probes and native/IR text. Numerical results were recomputed using Decimal code.

| Case | Source, endpoints and relationship | Decision |
|---|---|---|
| HL-ERR-0006 | Physical 185 / printed 183 / index 184. In note 7(d), the first minimum effective tax rate changes from `15%` to `15`. The later minimum-rate occurrence still contains `%`. The section address and source rectangle identify the affected occurrence. | Support ready, non-numeric, expected detectable. This is a missing percentage unit in rate prose; no financial tolerance applies. No separate endpoint is needed for this token-format discrepancy. |
| HL-ERR-0017 | Physical 159 / printed 157 / index 158, revenue-reference cell: `2(a)` becomes `3(a)`. Physical 179 / printed 177 contains note 2(a), 收入分項, the reviewed secondary endpoint. Physical 181 / printed 179 contains note 3, 其他收入淨額. Subjects establish the reference problem without matching amounts. | Support ready, non-numeric, expected detectable. Preserve the exact subsection: note 3 exists, but the inspected source shows no 3(a) subdivision before note 4. This case must not be presented as proof of detecting a wrong reference whose **complete** target exists. Its current broad category/description remain correct. |
| HL-ERR-0025 | Physical 159, 2025 HKD-million column. Revenue + signed direct costs − the immediately following subtotal. The subtotal's source row label is blank; “gross profit” is an evaluator interpretation supported by row order and rules, not extracted text. Source tokens are revenue `9,950`, costs `(3,423)` / `-3,423`, subtotal `6,527` / `6,537`. | Support ready and above-tolerance for this local equation. Independent code gives original residual 0, corrupted residual −10, change −10 and bound 1.5 HKD million. The cost notation change preserves its negative value. Administrative costs and later rows do not belong in this first subtotal. |
| HL-ERR-0041 | Physical 180 / printed 178 / index 179, note 2(b), income total under the merged 2025 header and 總額 column: `9,950` becomes `9,960`. The secondary endpoint is statement revenue on physical 159, still `9,950`. Units are HKD million; exclude comparative and reference-RMB columns. | Support ready and above-tolerance for the reviewed intended comparison. Independent code gives original residual 0, corrupted residual −10, change −10 and bound 1.0 HKD million. Runtime context resolution remains a prerequisite, described below. |

The numerical bounds include every operand, including unchanged operands and the total. Integer
HKD-million presentation supports step 1. Independent nearest rounding remains the explicitly
accepted evaluation assumption; the images do not prove the issuer's internal rounding process.
The two discrepancies exceed twice their respective bounds, so their recorded bands are correct.

## Propagation decisions

- **0006: none in the reviewed relationship.** The second rate occurrence retains its percent sign.
  The neighboring tax-table edit is a separate discrepancy; it does not propagate the omitted unit.
- **0017: none in the reviewed reference relationship.** The intended revenue-note subject and
  note-3 subject remain identifiable. No consistent renumbering accompanies this reference edit.
- **0025: linked edits confirmed.** The source statement shows the recorded changes at 0026–0029:
  both operating-profit subtotals, profit before tax and the first annual-profit occurrence.
  The statement hierarchy supports the links independently of matching changes. The later
  attribution total remains unchanged. Propagation therefore is partial, not a globally balanced
  restatement. Those downstream edits are outside the three-operand gross-profit equation and
  cannot cancel its −10 residual. Later subtotal equations must include all their own changed
  operands; the four pending linked cases are not individually promoted or reclassified here.
- **0041: none across the reviewed revenue endpoints.** Statement revenue and the note-2(a)
  revenue-disaggregation total remain unchanged. Other segment-profit edits are separate
  relationships, not propagated revenue-total replacements.

These conclusions concern observed relationship-linked edits, not historical injector execution
order or proof that no other changes exist anywhere. That matches the explicit scope of
[the closure propagation review](../promotion-source-review.json).

## Downstream trace and remaining qualifications

**1. Conflicting period evidence must remain visible before numerical comparison.** The corrupted
statement heading says 2026 while its financial column says 2025. Note 2(a)'s heading also says
2026; note 2(b)'s column says 2025. This conflict was already disclosed in the pre-closure packet
and canonical review notes. It does not defeat the same-column gross-profit equation. For the
cross-page revenue comparison, however, the future interpreter must establish compatible periods
from the corrupted input alone or abstain. The approved evaluator period is not permission to
inject a corrected date into runtime. Owner: audit/domain-review roles, interim project user;
resolve during Milestone 2 relationship validation before claiming an executed comparison.

**2. Primary mappings are supported; secondary IR mappings remain unfinished.** All eight primary
candidate objects in Milestone 1 r2 match saved IR IDs, source fragments, pointers, page indices,
text and token offsets. I also checked all ten clean/corrupted operand occurrences for the two
equations. But the secondary evaluation locations are copied with `secondary_ir_mapping_status:
not_proposed`; they are not complete paired IR mappings. Before scoring paired-endpoint results,
map those endpoints and independently generate supported runtime relationships. Owner: evaluation
and audit teams, interim project user. This is a disclosed unfinished handoff item, not evidence
that Milestone 0's PDF/logical addresses are wrong.

**3. An existing Milestone 1 review erratum remains actionable.** Current r2 guidance still claims
the source uses 採取 while native text uses 採用. The already present
[second independent Milestone 1 review](../../../milestone1/reviews/independent-r2-2026-09-10.md)
retracts that claim; the saved source image also reads 採用. This was introduced by the later
Milestone 1 review, not Milestone 0 or the adapter. Correct it in a new sealed packet, or explicitly
exclude it in an owner decision, as that review recommends. No new raw-PDF inspection was needed
here. Owner: review-packet maintainer, interim project user.

No current runtime code inspected copies the canonical amounts, evaluator operands or corrected
period into a detector. The implemented consumer reports inventory and builds literal context;
it does not execute financial checks. The passing access tests support the current adapter/IR
boundary, not future model/prompt/detector isolation or resistance to malicious native code.

## Verification and preservation

[Machine-readable results](checks.json) and [reproduction script](verify.py) record:

- All 788 manifest-listed source hashes match. PDFs were hashed as opaque bytes, not parsed.
- All 18 saved packet-image hashes match; their bytes, packet HTML, image inventory, character
  probes and source manifest are unchanged from the supplied pre-closure commit.
- Current canonical records, locations, split and approval bytes equal the closure commit and
  match the ready selector. Source-backed semantic validation passes: 48 records, four ready,
  44 pending; owner fingerprints and source/coordinate/split references validate.
- Frozen salt, algorithm, bootstrap seed and all assignments are unchanged from pre-closure.
  One development group remains; this review creates no holdout or independent clusters.
- Independent Decimal calculations reproduce both relations and bands, without using the
  intake calculation function. Eight primary IR candidates and ten operand occurrences agree.

Fresh commands passed on the current working tree:

- `make evidence-check`: 25 tests.
- `make -C tools/eval-format-tools check PYTHON=.venv/bin/python`: formatting, schemas and 26 tests.
- `make evidence-local-check`: both full native runs, literal inventory, repeat ingestion,
  guarded IR replay and forbidden-access probes. Each has 228 pages, 132 tables and 6,415 cells;
  clean has 129 resolved / 3 partial grids, corrupted 128 / 4.

The 192 schema-validated historical record instances represent 48 IDs across four revisions.
Tests do not establish source fidelity or detector accuracy. Existing PDF-correspondence renders
were not regenerated; no OCR, model, detector, fresh licensing investigation or scored run occurred.
The existing Milestone 1 packet corrections were inspected but not reimplemented or accepted.

The approved deferrals remain appropriate: 44 pending records, historical extraction metadata,
model capability/identity probing and unset alert/runtime budgets have named owners. They remain
prerequisites for the relevant integration/scored claims. Headline status stays **UNGATED**.
This review adds only its own report, reproduction evidence and a development-log note; historical
approvals, evaluation revisions, runtime code and unrelated working-tree changes are preserved.
