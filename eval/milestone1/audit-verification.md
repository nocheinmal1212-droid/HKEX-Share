# Verification of the second independent Milestone 1 audit

Date: 2026-09-10. The user-named `independent-2026-09-10.md` remains the first audit; the second
is `independent-r2-2026-09-10.md`. Both were read. This verification covers the second audit's
claims before changing the active review inputs.

**The remaining wording correction is confirmed.** The source says `採用`, matching native/IR.
The previous follow-up incorrectly endorsed the first auditor's misreading. The asserted word
substitution and substantive-paraphrase claim are withdrawn in the [explicit erratum](source-wording-erratum.md).
All three original packet defects are resolved; the mappings and qualified fixture expectations
remain supported. No fixture value or runtime change is required. Owner acceptance remains pending.

## Claim-by-claim verification

| Second-audit claim | Verification and disposition |
|---|---|
| Clean source uses `採用`, not the previously quoted `採取` | **Confirmed.** Visually inspected the saved 300-DPI paragraph image. The word is clearly `採用`. Independently checked all three derived artifact hashes in inspection-result.json; the saved text contains the same word. |
| `雙重機制` is present across a line break | **Confirmed** by the saved image and text; native preserves the phrase. |
| Clean paragraph agrees after ignoring whitespace and equating fullwidth/ASCII parentheses | **Reproduced.** Compared the saved text with the selected clean native/IR paragraph. Diagnostic equality is true; literal equality is false. No original string was changed. The comparison is evaluator-only. |
| Inspection was limited to clean physical page 185 / index 184 / paragraph (d), with source hash `8ee217c98b2a3684987601f5e5811af9c837fc909ffd2302075455f476617890` | **Supported by the saved inspection plan/result and matching frozen IR source identity.** The inspection record identifies one targeted PDF text-layer read and 300-DPI render, no OCR. This follow-up reused the artifacts without rereading or rehashing a PDF. The saved plan records that it preceded inspection; file contents alone do not independently prove execution chronology. |
| Fixture and report bindings are fixed | **Reproduced exactly before correction.** All 47 r2 files regenerate byte-for-byte. A temporary read substitution changes rounding `3` to `30`; both resulting fingerprints exactly match the second audit's diagnostic fingerprints. The retained r2 approval fingerprint rejects the changed packet. Appended HTML bytes also fail verification. |
| Reference supporting text/pointer/IR are included and displayed | **Confirmed** in native input, validated fixture IR and rendered HTML: `附註甲 收入分項`, pointer `/pdf_info/0/preproc_blocks/1/lines/0/spans/0/content`, with IR IDs/spans. |
| Both page-123 variants, unsupported cell and limitations are included | **Confirmed.** Corrupted r1 c1 remains unsupported, table partial, with `unsupported_cell_content` and `unsupported_inline_content`. Re-executed its context rejection probe. Actual detector abstention remains future behavior. |
| Eight candidates are unchanged from r1 and agree with full IR | **Confirmed.** Compared each candidate object, ID, native pointer, text, source span, fragments and unique token offset. All eight match; secondary IR mappings remain `not_proposed`. Full native validation separately passes. |
| All ten additional variant regions match full IR | **Confirmed.** Compared every selected node and source string, including complete region membership by native pointer. |
| Six complete fixture IRs validate against their native inputs | **Confirmed** with the current evidence validator. No native fixture bytes, expectations or generated fixture IR changed for r3. |
| Six qualified expectations remain supported | **Supported within their stated limits.** Independently read the six literal inputs. Decimal gives rounding residual magnitude `1`, bound `1.5`, conditional on complete-sum and independent-nearest-rounding assumptions. Group/parent scope differs; the reference has matching subject support; local labels permit both negative styles; percentage and ambiguity remain minimal token/insufficient-evidence examples. These are proposed labels, not detector results or a complete negative benchmark. |
| 25 evidence tests and 26 intake tests passed | **Freshly reproduced before correction.** The intake schema count is 192 historical record instances across four revisions, representing 48 injections. After adding a diagnostic-comparison regression, the evidence/packet suite has 26 passing tests. |
| Full native/replay and forbidden-access checks passed | **Freshly reproduced.** Both variants retain 228 pages, 132 table regions and 6,415 cells. Resolved/partial counts are clean 129/3 and corrupted 128/4. Literal-pointer checks, repeat ingestion and guarded replay pass. |
| R2 has 46 manifest-listed files, 49 original inputs; both fingerprints verify | **Confirmed before changing active generation documents**, including a separate standard-library digest calculation. Original r2 remains intact. Its original-input check now appropriately detects revised generation documents; offline historical verification still passes. |
| ZIP has exactly 47 entries, no duplicates or extras, all bytes match | **Confirmed**, including SHA-256 `567f490ede4048f69c397fa0c8643da6f8db2c1eeb3a1f5a0c165b468d04ac79`. Portable review material is complete; full native pipeline reproduction still requires external native/run files. |
| Browser screenshots verified reference/partial-table readability through loopback preview | **Rendering independently reproduced in the r3 preview.** A temporary loopback-only HTTP preview showed readable reference text/pointer, the corrupted partial table, unsupported-cell label, limitation/abstention explanations and saved source image. The unchanged reference/partial-table sections match r2. The second auditor's own historical screenshot files were not supplied. |
| No new owner approval, runtime correction or detector/scoring evidence follows | **Confirmed by the current artifacts and retained status.** Recommendations are not approval. Installed-wheel replay and licensing review were not rerun in this follow-up. Source inspection establishes only the narrow clean-paragraph observation. |
| Historical packets, frozen contracts, approvals and unrelated work were preserved | Captured 78 pre-change hashes covering r1/r2, both audits, frozen evaluation artifacts, selected native/fixture files and the unrelated Milestone 0 review. The completion check compares these exact hashes. Active generation documents and pending handoff links are revised separately; originals remain sealed. |

## Reproduction evidence

[Machine-readable second-round checks](audit-round2-claims.json) record the exact comparisons and
hashes. The reproduced mutated content fingerprint is
`675b7664554057a7ba0545fb98e364810e1f5f0b1457db0e0db819718c7e609b` and mutated approval fingerprint is
`5c52d74ad67799e7738b6f28f44cf0d4d721fbcd9ef8bc464787bbf32f930b8c`; neither identifies a proposed fixture.

[Current check summary](audit-checks.json), [evidence/packet test output](audit-test-output.txt),
[intake output](audit-intake-output.txt) and [full native-check output](audit-native-output.txt) are
bundled. Historical first-round reproduction and mapping traces are retained separately in
[audit-reproduction.json](audit-reproduction.json) and [audit-mapping-verification.json](audit-mapping-verification.json).

## What r3 changes

R3 corrects the banner, case guidance, review guide and current verification narrative together.
It includes the explicit erratum, both audit originals, the unchanged r1/r2 packets, and the
hash-verified saved high-resolution source image, text and inspection records. A narrow regression
ensures the diagnostic comparison can ignore formatting but cannot hide a word substitution.
No comparison normalization enters the evidence adapter or runtime.

No new raw-PDF read/render, OCR, model call, raw injector metadata read, detector tuning, scoring,
or label for any of the 44 pending cases occurred in this follow-up. The second audit did use its
recorded targeted PDF exception; this packet makes that distinction explicit. Four ready cases,
44 pending, no independent holdout; headline status remains **UNGATED**.
