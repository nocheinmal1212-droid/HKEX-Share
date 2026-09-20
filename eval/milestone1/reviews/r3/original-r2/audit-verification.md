# Verification of the independent Milestone 1 audit

Date: 2026-09-10. This follow-up verifies the supplied audit and corrects its three packet findings.
**All three findings are confirmed. All eight primary occurrence mappings are supported.**
The source-fidelity caution is also correct, with a small clarification to its quoted wording below.
This is an implementation/review recommendation, not owner acceptance.

## Claim-by-claim findings

| Audit claim | Independent follow-up evidence | Result / correction |
|---|---|---|
| Fixture input bytes do not affect r1's approval fingerprint | A temporary copy changed rounding total `3` to `30`. Both fingerprints exactly matched r1: `8e1c3ff054c3f9ff6ab96e4fbaa0d7a3ed2912e7cbaa14367108043ce3d249d5`. HTML changed. Decimal residual magnitudes were `1` and `28`, against bound `1.5`. Repository fixtures were untouched. | Confirmed. r2 binds exact input bytes, generated fixture IR and qualified expectations in review.json; its outer manifest also binds the HTML, images and every bundled review file. |
| Valid-reference display omits supporting note text | The full input has second-block text `附註甲 收入分項`; r1 HTML lacks it because the renderer reads only its first table. | Confirmed. r2 displays all supporting literal sources and their pointers/IR IDs/spans, and includes complete native and adapted fixture files. |
| Incomplete-table handling is not demonstrated | r1 contains no `Grid: partial`. Saved corrupted IR at `/pdf_info/123/preproc_blocks/0` is partial; r1 c1 is unsupported, with `unsupported_cell_content` and table `unsupported_inline_content`. Clean is resolved. | Confirmed presentation gap. r2 displays both independent variants, content states, preserved raw markup, limitations and capabilities. A context probe rejects the unsupported cell. Dependent future checks must abstain; no detector was executed. |
| Other partial tables occur at indices 88, 125, 221 | Enumerated table nodes from both saved IR files. Clean partial indices: 88, 125, 221. Corrupted: 88, 123, 125, 221. | Confirmed. Full inventories remain 129 resolved / 3 partial clean and 128 / 4 corrupted. |
| All eight primary occurrence mappings match saved IR and native evidence | Rechecked each candidate ID, native pointer, literal text, full cell markup span, fragment list, unique token offset and expected token; checked selected native and saved IR hashes. Native pointer strings resolve exactly. Inspected both variants of four existing source pages. | Confirmed. See [machine-readable mapping checks](audit-mapping-verification.json) and the displayed cases. Primary occurrences only; copied secondary evaluation locations are not a complete new IR mapping. |
| Tests passed: 19 evidence, 26 intake, both full native/replay checks | Reran those commands successfully before correction. The intake schema check covers 192 historical record instances across four revisions, representing 48 distinct injections. Full independent runs each retain 228 pages, 132 table regions and 6,415 cells. | Confirmed. After adding six packet regression tests, all **25 evidence/packet tests** pass. See [check summary](audit-checks.json) and [current test output](audit-test-output.txt). |
| The six fixture expectations are reasonable with qualifications | Inspected all six complete native inputs, local labels and the stated assumptions. Recomputed the rounding example with Decimal. | Supported only within the qualifications shown beside every fixture and in the guide. Labels remain proposed. No detector execution, negative benchmark adequacy or false-alert claim follows. |
| Percentage surrounding native prose is nonverbatim to the page | Hash-verified saved page-185 images show `採取`; selected native/IR contains `採用`. The `15%` / `15` occurrences and offsets are correct. | Confirmed. **Clarification:** `雙重機制` also appears on the page, split across a line break. The audit's shorter source quotation should not be read as evidence that this phrase was invented. Whole-paragraph fidelity is not approved. |
| Installed-wheel replay passed historically, but was not rerun in the audit | Inspected the saved run: consumer complete, adapter_imported false, data reads limited to selected corrupted evidence/manifest; historical summary records adapter directory unavailable and identical context. | Historical evidence is consistent. This follow-up also did not rebuild/rerun the installed-wheel experiment or re-audit runtime licensing. |
| Original packet, approvals and milestone status were unchanged by the independent audit | Initial working tree contained only its new report and appended development log. Frozen artifacts and r1 hashes were captured before this follow-up. | Confirmed. r1, canonical records/locations/splits, source manifest, scoring/format contracts and existing owner approval remain untouched. This correction updates only review tooling/materials and pending-status handoff links. |

## Integrity regression coverage

Six portable tests exercise amount mutation; expectation and HTML binding; changed native/IR/report
bytes; original-input drift; snapshot mismatches; complete reference text display; partial-content
visibility and escaping; deterministic packet bytes; overwrite refusal; and symlink/path rejection.
A changed fixture changes both content and approval fingerprints. A changed rendering changes the
approval fingerprint even if the content fingerprint stays fixed. Verification against a previously
recorded owner fingerprint rejects a newly rehashed packet. Verification alone grants no approval.

The final r2 generation validates the full saved IR against each selected native input before
extracting review regions, verifies source hashes, and validates each adapted synthetic fixture.
`packet.py --check-inputs` verifies the sealed files and their original source inputs after generation.
The outer manifest avoids a circular hash: HTML links to the manifest; it does not embed its own
approval fingerprint. The final owner decision must retain that exact external fingerprint.

[r1 mutation reproduction](audit-reproduction.json) preserves the observed before/after fingerprints
and independent arithmetic. It also records a complete corrected-generator mutation probe:
changing only the temporary rounding fixture changes both fingerprints, while identical-input
regeneration produces identical sealed bytes. The corrected [regression tests](tooling/test_review_packet.py) and
[generator](tooling/prepare.py) are included as hashed provenance snapshots.

## Scope retained

No new PDF read/render, raw injector metadata read, OCR, model call, detector tuning, scoring or
new annotation of the 44 pending answers occurred. Existing native outputs and fixture inputs
remain unchanged. The eight copied images were previously rendered and hash-verified; incidental
neighboring content was not used to design rules or new labels. The review is evaluator-only.

Owner review remains required for new mappings, evidence limitations and the qualified fixture
expectations. Further semantic capability probing, dated budgets and independent evaluation groups
remain later work. Four ready development cases, 44 pending, no independent holdout; **UNGATED**.
