# Milestone 1 native-evidence review

Selected MinerU output is the source of truth for extracted evidence. Review the adapter's literal
preservation, IDs/spans, table recovery, missing evidence and declared limitations against that
selected native input. Do not read raw PDFs, compare against PDF-derived text/images, judge OCR
quality, or repair extracted values. Unsupported native evidence remains unresolved.

The packet contains four proposed primary mappings in both independent variants, additional native
regions, and six qualified synthetic fixture expectations. Runtime never compares the variants.
Fixture inputs and evaluator expectations remain separate; no detector performance is claimed.

Within a generated packet, use its sibling `index.html` to review each item and `review.json`
for its traces. Record the `approval_fingerprint` from `packet-manifest.json` with your reviewer
name, date, accepted/rejected items, exclusions and requested corrections. Integrity checks grant no
approval. Prior packets' PDF-oriented narratives are historical and are not acceptance prerequisites.

Review the eight primary occurrences, the preserved unsupported cell and context rejection,
and each synthetic fixture's stated qualification. Secondary IR mappings, relationship selection,
semantic execution and comparison plans remain separate work. OCR quality is outside scope.
R4 was accepted on 2026-09-11 in the separate owner decision at
`eval/milestone1/approvals/r4.owner-2026-09-11.json`, with its existing qualifications.
This active guide is a template for new revisions, which require their own decision; it does not
replace the guide sealed in R4 or transfer that approval. Headline status remains UNGATED.

## What the four cases mean

These are existing clean/corrupted native inputs, not edits the adapter is asked to make.
Each variant is ingested independently. Approval confirms the exact occurrence is preserved in IR.

| Case | Existing clean / corrupted tokens | Proposed mapping |
|---|---|---|
| HL-ERR-0006 | `15%` / `15` | Percent-token occurrence at native page index 184. |
| HL-ERR-0017 | `2(a)` / `3(a)` | Revenue-reference cell at native page index 158, row 1 / column 1. |
| HL-ERR-0025 | `6,527` / `6,537` | Subtotal cell at native page index 158, row 3 / column 2; blank label retained. |
| HL-ERR-0041 | `9,950` / `9,960` | Total cell at native page index 179, row 5 / column 4. |

Rows and columns are zero-based. Approval does not mean a detector has found these differences,
selected accounting relationships, corrected values or been evaluated for accuracy.

The review tooling now binds exact fixture inputs and report bytes, exposes the reference fixture's
supporting text, and shows unsupported content in the selected partial table. Historical PDF-wording
corrections are outside this native-only approval scope. No OCR-quality decision is requested.

## Decision template

Record a decision separately; never edit the sealed packet. Partial acceptance is allowed.

```text
Reviewer:
Date:
Packet revision: <new revision; R4 already has its separate owner decision>
Approval fingerprint: <copy approval_fingerprint from packet-manifest.json>

HL-ERR-0006, clean and corrupted primary mappings: accept / corrections
HL-ERR-0017, clean and corrupted primary mappings: accept / corrections
HL-ERR-0025, clean and corrupted primary mappings: accept / corrections
HL-ERR-0041, clean and corrupted primary mappings: accept / corrections
Displayed native evidence limitations and unsupported-content handling: accept / corrections
Six fixture expectations with their stated qualifications: accept / specify exceptions
Milestone 1 native-evidence handoff: accept within stated scope / corrections required
Comments / exclusions:
```

Approval covers the eight primary mappings, displayed native evidence handling, and the six
qualified fixture expectations. It does not cover OCR quality, raw-PDF fidelity, detector performance,
secondary IR mappings, scoring readiness or future model behavior. Broader gates remain separate.
