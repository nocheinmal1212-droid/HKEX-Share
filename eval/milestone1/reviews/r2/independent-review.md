Navigation-adjusted copy; [original bytes](inputs/independent-review.original.md).

# Independent review of Milestone 1 packet r1

Review date: 2026-09-10. Reviewer: Codex, in a separate review requested by the project owner.
This is a recommendation, not owner acceptance or milestone closure.

Reviewed packet: [r1/index.html](original-r1/index.html), with review-record content fingerprint
`8e1c3ff054c3f9ff6ab96e4fbaa0d7a3ed2912e7cbaa14367108043ce3d249d5`.

**Recommendation: request a corrected packet before accepting the entire handoff.** The eight
primary occurrence mappings (four cases, two variants) are supported. The synthetic expectations
are reasonable within the qualifications below. However, r1 does not securely bind the fixture
inputs and omits evidence needed for two parts of its requested acceptance scope.

## Findings requiring correction before whole-packet acceptance

### 1. High priority: the approval fingerprint does not bind fixture inputs

[prepare.py lines 61–71](tooling/prepare-r1.py) reads each fixture to render the report, but fingerprints
only the proposals file containing its path and expected behavior. Neither the fixture bytes nor
the generated HTML are included in that fingerprint.

Reproduced without modifying repository inputs: copied the selected configuration, ready selector,
proposals and six fixtures into a temporary directory; used the existing verified intake result and
frozen r1 runs; generated two packets, changing only the rounding fixture's total from `3` to `30`
between generations. The first generation reproduced r1's fingerprint exactly. The second produced
different HTML with **the same fingerprint**. Decimal arithmetic gives residual magnitudes `1` and
`28`, respectively, against the same `1.5` bound. A substantive reversal of the label's validity is
therefore invisible to the requested approval identifier.

Required correction: bind each fixture's exact input hash and its expectation in the review record;
verify those hashes before rendering and later adoption. Bind the report bytes in a separate manifest
or make all displayed review content reproducible from authenticated packet content. Include a
regression probe showing that a changed fixture invalidates or changes the approval binding.
Publish a new revision; preserve r1.

### 2. Medium priority: the valid-reference example hides its supporting evidence

[prepare.py lines 62–64](tooling/prepare-r1.py) renders only the first table in each synthetic input.
The reference fixture also contains the separate text block `附註甲 收入分項`, which supports the
reference `收入（附註甲）`. That supporting block is absent from r1's HTML. The underlying fixture
supports the proposed label, but the displayed packet asks the owner to trust the description
instead of showing the evidence that makes it valid.

Required correction: display the supporting block and its source pointer alongside the reference,
and include the fixture's adapted IR/source trace. Preserve runtime input and evaluator expectation
as separate records. No detector execution is required for this correction.

### 3. Medium priority: incomplete-evidence handling is requested for approval but not demonstrated

The packet's acceptance scope explicitly includes incomplete/ambiguous table handling. Nevertheless,
every displayed real table says `Grid: resolved`. [prepare.py line 60](tooling/prepare-r1.py) renders
additional regions from the clean variant only, and its table renderer does not show cell content
states or region limitation reasons.

The already selected page index 123 provides a concrete omitted example: clean is resolved, while
corrupted is partial. In corrupted IR, row 1, column 1 has `unsupported_cell_content`, and its table
has `unsupported_inline_content`. Both retain source evidence. The current report shows only the
resolved clean counterpart. Other partial tables occur at page indices 88, 125 and 221; none is
displayed. The full inventories correctly report 3 partial clean tables and 4 partial corrupted
tables, so this is a review-presentation gap rather than evidence that the adapter dropped them.

Required correction: show a source-linked partial example, preferably both variants of the already
selected region, with unsupported cell states, retained raw content and consequences for dependent
checks. Display relevant capabilities/limitations rather than just a grid status. No new PDF read
or expansion into the remaining 44 answers is needed.

## Mapping decisions supported by this review

Each candidate's evidence ID, page, native pointer, text, source span, fragment and token offset was
checked against the saved IR and selected native JSON. All eight had a unique expected occurrence.
The corresponding tokens and positions were also inspected in existing, hash-verified source-page
images from the owner-reviewed intake packet. Physical page numbers below are one-based; IR indices
are zero-based. Printed labels were read from the images, not extrapolated by runtime.

| Case | Physical page / IR index / printed label | Clean → corrupted | Recommendation |
|---|---|---|---|
| HL-ERR-0006 | 185 / 184 / 183 | `15%` → `15` at paragraph offsets `[203,206)` / `[203,205)` | Support the token correspondence. |
| HL-ERR-0017 | 159 / 158 / 157 | `2(a)` → `3(a)` in the revenue reference cell, row 1 / column 1 | Support the occurrence mapping. |
| HL-ERR-0025 | 159 / 158 / 157 | `6,527` → `6,537`, row 3 / column 2, 2025 HKD millions | Support the occurrence mapping; the row label correctly remains blank. |
| HL-ERR-0041 | 180 / 179 / 178 | `9,950` → `9,960`, row 5 / column 4, 2025 total | Support the occurrence mapping; the merged year header covers this column. |

These are primary occurrence mappings. The packet copies secondary evaluation locations but does
not assign all of them new IR IDs. Acceptance must not be interpreted as approval of a complete
runtime equation, reference-target selection or statement-note comparison plan. Those remain
separate downstream work; canonical mapping adoption requires the separately reviewed revision
already specified in PLAN.md.

There is also a concrete reason to retain the narrow fidelity claim. In the saved page-185 image,
the paragraph contains `該法案採取收入納入規則和當地最低稅`; native/IR text instead contains
`該法案採用收入納入規則和當地最低稅雙重機制`. The adapter faithfully preserves the native string,
but that paragraph is not a verbatim transcription of the page. This does not invalidate the
verified `15%`/`15` token mapping. It does mean that owner acceptance should not grant fidelity to
the whole paragraph or authorize treating all surrounding extractor prose as source-verified.
No raw PDF inspection was needed to observe this difference.

## Fixture-label recommendations

| Fixture | Independent assessment | Acceptance qualification |
|---|---|---|
| rounding | With coefficients `+1,+1,-1`, unit rounding steps and independent nearest rounding, `abs(1+1-3)=1`; including the total gives bound `1.5`. The stated benign expectation is correct. | Accept only with the explicitly stated complete-sum and rounding assumptions. The table alone does not establish the rounding policy. |
| contexts | Group and parent scope labels do not justify an equality check between `20` and `12`. | Accept for scope incompatibility. It does not test period, scale or presentation-basis differences. |
| reference | The separate `附註甲 收入分項` block supports the revenue reference. | The label is supported by the full input; expose that block in the corrected packet. |
| negative-style | The two local labels explicitly support parentheses and minus notation. | Accept the narrow expectation that notation alone is not an error; this is not approval of every mixed-style document. |
| percentage | `有效稅率` with `15%` is a valid literal percentage example. | Accept as a minimal token fixture. It lacks the repeated conventions and full narrative proposed in the benign-fixture plan. |
| ambiguity | Neither candidate has enough concept/scope/period support to establish an equality with revenue; matching `10` must not select a target. | Accept the conservative abstention expectation. Generic candidate names make this a minimal insufficient-evidence case, not a strong test of choosing between two semantically plausible notes. |

These are fixture expectations, not executed detector results or an adequate negative benchmark.
No evidence here establishes false-alert rates, interpretation accuracy or generalization.

## Verification performed

- `make evidence-check`: all 19 tests passed.
- `make evidence-local-check`: passed for both full native documents, all literal-pointer
  inventories, repeat ingestion, guarded IR-only replay and forbidden-access probes. Each variant
  retained 228 pages, 132 tables and 6,415 cells. Resolved/partial counts matched r1: 129/3 clean,
  128/4 corrupted.
- `make -C tools/eval-format-tools PYTHON=.venv/bin/python check`: formatting/schema checks and
  all 26 retained tests passed. Schema validation covered 192 historical record instances across
  four revisions, not 192 distinct injections.
- Independently recomputed the review-record fingerprint and hashes of its referenced ready
  selector, selection, verification file, proposals, both saved IR files and selected native inputs.
  Checked all eight candidate fields and native source strings rather than relying on token search
  or successful schema validation alone.
- Verified all hashes in the existing intake packet-r2 image inventory; visually inspected eight
  full-page images covering both variants of physical pages 159, 179, 180 and 185.
- Ran the temporary-copy fingerprint mutation described in finding 1. Confirmed the supporting
  reference text, partial-grid status and unsupported-cell limitation details are absent from r1 HTML.

The installed-wheel replay record was inspected; the historical wheel experiment was not rerun.
This review did not re-audit the full runtime implementation or dependency licensing. No OCR,
model call, raw PDF read, raw injector-record read, detector execution or scoring occurred. The
review selected only the four ready cases; incidental neighboring content in existing page images
was not used to develop labels for the remaining 44 cases. No runtime rules were tuned.

## Recommended owner decision

Retain milestone closure as pending. Request a new packet addressing the three findings, carrying
forward these supported primary mappings and the qualified fixture expectations. Review the new
fingerprint before owner acceptance. Preserve the documented limits on source fidelity, secondary
mappings, property roll-forward interpretation and future detector behavior. Budgets, model probing
and wider scoring gates remain later dependencies, not additional blockers introduced by this review.

Existing r1 artifacts, source evidence, frozen evaluation records, approvals and PLAN.md were not
modified by this review. Headline status remains UNGATED.
