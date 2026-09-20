# Second independent review of Milestone 1 packet r2

Date: 2026-09-10. Reviewer: Codex, responding to the owner's request for a second independent review.
This report records recommendations, not owner acceptance.

Reviewed [packet r2](r2/index.html), [guide](r2/review-guide.md),
[claim-by-claim verification](r2/audit-verification.md) and the supplied portable ZIP.
All recommendations below refer to this exact **approval_fingerprint**:

`b66851423dbb940414cfd7a6ab1289a723afcaa93ab95884c6f10f1a8561440a`

**Outcome: all three original packet findings are resolved. The eight primary mappings and six
qualified fixture expectations remain supported. One factual correction remains in the fidelity
explanation; it originated in my first review, not in the adapter.** Correct that explanation in a
new sealed revision before unqualified whole-packet acceptance, or explicitly exclude it and cite
this erratum in a partial owner decision. No runtime or mapping correction is indicated by this finding.

## Remaining finding — correct the quoted source wording

Priority: P2, acceptance-document accuracy.

The [guide, line 29](r2/review-guide.md), the HTML banner, case guidance and
[audit-verification.md, line 19](r2/audit-verification.md) say that the source uses `採取` while
native/IR uses `採用`. **The source also uses `採用`.** The source contains `雙重機制`, split
across a line break, as r2 correctly clarifies.

I take responsibility for the incorrect source quotation and substantive-paraphrase claim in
the first independent review. The follow-up carried that error forward. Those assertions are
withdrawn by this report; the earlier report and r2 remain unchanged as historical evidence.

The existing 120-DPI image appeared to contradict the review narratives. Because the exact
source word remained uncertain and native JSON cannot independently attest PDF wording, I
recorded a targeted inspection plan before reading the clean source PDF. I then inspected only
physical page 185 (index 184), paragraph (d), using its existing text layer and a 300-DPI Poppler
render of the paragraph. Both unambiguously show `該法案採用收入納入規則` and the phrase
`當地最低稅雙重機制`. The supplied PDF hash matched the previously recorded source identity:
`8ee217c98b2a3684987601f5e5811af9c837fc909ffd2302075455f476617890`.

For this clean paragraph, the extracted PDF text and native text agree after removing whitespace
and treating fullwidth/ASCII parentheses as equivalent in a diagnostic comparison. The remaining
literal formatting differences do not support a claim of substantive paraphrasing. No evidence
or source strings were normalized or overwritten. This local check does not certify the whole
document, all extractor prose, or all source typography.

The pre-inspection rationale, exact extraction/render scope, source identity, results and derived
artifact hashes are saved in
[inspection-result.json](../../../runs/milestone1-independent-r2/inspection-result.json).
Unlike the first review and r2's preparation, **this second review did perform one justified,
targeted raw-PDF read and render**. It did not run OCR.

Recommended correction: replace the specific `採取`/`採用` claim with an accurate account of the
limited source check, retain the general distinction between native preservation and PDF fidelity,
and attach an explicit erratum to the first review's claim. Update the generation inputs and
banner together, then create a new packet and approval fingerprint. Do not edit sealed r2 or
silently replace its historical audit copy.

## Disposition of the three original findings

| Original finding | Second-round evidence | Disposition |
|---|---|---|
| Fixture inputs/report bytes not bound | Independently recomputed content and approval hashes. Regenerated all 47 packet files byte-for-byte. Changed the rounding total from `3` to `30` through a temporary in-memory file-read substitution while leaving repository inputs untouched: both fingerprints changed. Verification against r2's original approval fingerprint rejected the changed packet. Appending bytes to a temporary rendered report also failed verification. | Resolved. |
| Valid-reference supporting text omitted | Complete native and validated fixture IR are bundled. The visible report shows `附註甲 收入分項`, its pointer `/pdf_info/0/preproc_blocks/1/lines/0/spans/0/content`, and expandable IR IDs/spans. Browser screenshot inspection confirmed it is readable. | Resolved. |
| No incomplete-table example | Both variants of page index 123 are displayed. Corrupted r1 c1 is visibly unsupported, with partial grid status, both limitation reasons and dependent-check abstention guidance. Its retained region matches the full IR. Re-executing the context probe rejected the unsupported cell. Browser screenshots confirmed the table and explanations render. | Resolved. |

The full-generator mutation produced these diagnostic fingerprints; the changed packet was temporary
and is not a proposed revision:

| Binding | Original r2 | Mutated rounding fixture |
|---|---|---|
| content | `31c0cada7596228b2f4056bb3caa72c1352d39afcd5168787493e14803cfc25f` | `675b7664554057a7ba0545fb98e364810e1f5f0b1457db0e0db819718c7e609b` |
| approval | `b66851423dbb940414cfd7a6ab1289a723afcaa93ab95884c6f10f1a8561440a` | `5c52d74ad67799e7738b6f28f44cf0d4d721fbcd9ef8bc464787bbf32f930b8c` |

## Item-level recommendations for the owner

Each recommendation is attached to r2's approval fingerprint above and excludes the refuted
source-wording claim. These are not recorded approvals.

| Item | Recommendation and scope |
|---|---|
| HL-ERR-0006 clean / corrupted | Support both primary token mappings, `15%` / `15`. Withdraw the claimed word substitution in surrounding prose. |
| HL-ERR-0017 clean / corrupted | Support both primary reference occurrences, `2(a)` / `3(a)`; no runtime target-selection approval. |
| HL-ERR-0025 clean / corrupted | Support both subtotal occurrences, `6,527` / `6,537`; preserve blank row label; no generated equation approval. |
| HL-ERR-0041 clean / corrupted | Support both total occurrences, `9,950` / `9,960`; no secondary mapping or comparison-plan approval. |
| Displayed limitations / incomplete content | Support retained unsupported content, visible limitation states and the demonstrated context rejection. Actual detector abstention remains future behavior to implement and test. |
| rounding | Support under the stated complete-sum, independent-nearest-rounding assumptions. Decimal residual magnitude `1` is within bound `1.5`, including the total's uncertainty. |
| contexts | Support the group/parent scope incompatibility example only. |
| reference | Support the benign expectation with the now-visible matching note subject. |
| negative-style | Support the locally declared parentheses/minus conventions only. |
| percentage | Support the minimal valid-token example; broader narrative/convention coverage remains absent. |
| ambiguity | Support conservative abstention for insufficient evidence; this remains a minimal example. |
| Whole Milestone 1 evidence handoff | Supported within these limits, with the fidelity narrative corrected or explicitly excluded in the owner's decision. No unconditional endorsement of every statement in r2. |

All eight candidate objects are unchanged from r1 and match the full saved IR, expected token offsets,
source fragments and page-local positions. I rechecked the packet's selected-region nodes and sources
against the complete IR, including all ten additional variant regions. Complete fixture IRs validate
against their bundled native inputs. Secondary locations remain explicitly `not_proposed` as IR mappings.

## Fresh verification and portability

- `make evidence-check`: 25 tests passed, including all six packet regression tests.
- `make -C tools/eval-format-tools PYTHON=.venv/bin/python check`: formatting/schema checks and
  26 intake tests passed. Schema count remains 192 record instances across four revisions.
- `make evidence-local-check`: both independent native runs, literal-pointer inventories, repeated
  ingestion, guarded IR-only replay and forbidden-access probes passed. Each variant retains
  228 pages, 132 tables and 6,415 cells; clean is 129 resolved / 3 partial, corrupted 128 / 4.
- Packet verification with `--check-inputs` and the explicit r2 fingerprint passed for all 46
  manifest-listed bundled files and 49 original input entries. A separate standard-library hash
  calculation reproduced the content and approval fingerprints.
- The ZIP has exactly those 46 files plus the packet manifest: all 47 entries match the packet
  directory byte-for-byte, with no extra file or duplicate archive path. ZIP SHA-256:
  `567f490ede4048f69c397fa0c8643da6f8db2c1eeb3a1f5a0c165b468d04ac79`.
- Full regeneration from the current inputs reproduced every r2 file exactly before the temporary
  mutation. The regenerated fixture mutation and changed-rendering rejection were independently
  executed rather than accepted from the bundled audit summary.
- Browser inspection succeeded using a temporary loopback-only HTTP preview of the packet. I
  inspected the reference fixture, partial-table rendering, unsupported-cell label and limitation
  explanations. The earlier local-file URL obstacle did not block this review. The preview was
  temporary; no report was published externally.

The ZIP is self-contained for review of the selected excerpts, images and fixtures. Reproduction of
the complete native pipeline and original-input checking still require the external source and run
files, as the guide discloses. Integrity checks authenticate the reviewed bytes against the retained
fingerprint; they are not a signature, source-fidelity proof or owner approval.

## Remaining limits and preservation

I did not rerun the installed-wheel experiment or perform a full implementation/licensing audit.
No model call, OCR, detector execution, scoring, raw injector metadata read, or new label for the
44 pending cases occurred. The source-PDF exception above was confined to the clean page's disputed
paragraph and was documented before inspection. No runtime tuning used it.

The r1/r2 packets, original independent report, frozen evaluation records, approvals, runtime code
and PLAN.md were preserved. This second report and a development-log addendum record the new review
and retract the earlier erroneous fidelity claim. Owner acceptance remains pending and headline
status remains UNGATED.
