# Milestone 1 corrected review — owner guide

**Decision requested: review the new evidence correspondence and qualified fixture labels.**
Revision r3 corrects the false source-wording claim in r2. The three earlier packet gaps remain resolved. All proposed items remain pending.
Prior intake approvals do not approve this packet. Nothing here claims detector performance,
complete source fidelity or headline scoring readiness.

Start with [the readable packet](index.html), then [claim-by-claim verification](audit-verification.md).
The [second audit](independent-review-r2.md) and [explicit erratum](source-wording-erratum.md)
explain the correction. The [first audit](independent-review.md) is historical. Both original audit
texts and the complete r1/r2 packets are included unchanged, alongside reading copies with local links. [review.json](review.json)
contains the source-linked regions, candidates, limitations, fixture expectations and input hashes.
The [manifest](packet-manifest.json) binds every bundled file, including the report and this guide.

## Review in this order

1. **Four cases, both variants.** Inspect the eight unique token occurrences, logical cells,
   exact native pointers, source spans and literal text. The page images are linked at the end of
   the report, with hashes and original rendering metadata in review.json.

   | Case | Physical page / IR index / printed label | Clean → corrupted |
   |---|---|---|
   | HL-ERR-0006 | 185 / 184 / 183 | `15%` → `15` |
   | HL-ERR-0017 | 159 / 158 / 157 | `2(a)` → `3(a)`, r1 c1 |
   | HL-ERR-0025 | 159 / 158 / 157 | `6,527` → `6,537`, r3 c2; blank row label |
   | HL-ERR-0041 | 180 / 179 / 178 | `9,950` → `9,960`, r5 c4; merged 2025 header |

   Rows/columns are zero-based. Primary mapping acceptance does not approve copied secondary
   locations as IR links, operand lists, equations or reference-target selection. The surrounding-prose
   wording claim in r2 is **withdrawn**: the source and native text both say `採用` and
   contain `雙重機制`. Review the [saved 300-DPI paragraph image](source-inspection/source-paragraph.png)
   and [saved source text](source-inspection/source-paragraph.txt), with the
   [inspection rationale](source-inspection/inspection-plan.json) and
   [scope/identity/result](source-inspection/inspection-result.json). The second auditor performed
   a documented targeted clean-PDF inspection; this revision reuses those artifacts without another
   PDF read. The clean paragraph agrees after a diagnostic comparison that ignores whitespace and
   equates fullwidth/ASCII parentheses. Literal formatting differences remain; no blanket PDF or
   whole-document fidelity approval follows. The eight primary mapping decisions are unchanged.

2. **Incomplete evidence and capabilities.** In “Later continued-table fragment”, page index 123
   (physical page 124), compare the independently generated runs. Clean is resolved; corrupted
   is partial. Corrupted r1 c1 is unsupported. Inspect its preserved raw HTML, source span,
   `unsupported_cell_content`, `unsupported_inline_content`, and context rejection probe.
   A future comparison requiring this content must abstain. Other cells remain individually
   traceable; a resolved grid does not prove accounting completeness. Continued pages remain
   distinct, with no inferred cross-page merge. Geometry and other missing capabilities remain
   unknown. Property movement relationships are still unreviewed.

3. **Six portable fixtures.** Each has its exact native JSON and validated IR in `fixtures/`.
   Read the expectation and qualification immediately above it. In particular, the reference now
   shows `附註甲 收入分項`, its native pointer and IR span. The rounding expectation requires
   accepted completeness/rounding assumptions. Percentage and ambiguity are minimal examples;
   this set is not an adequate negative benchmark. These are proposed labels, not executed
   detector outcomes. Runtime inputs contain no evaluator-authored expectations.

4. **Integrity and verification.** See audit-verification.md for reproduced findings, current
   test results and historical-only checks. Preserve the exact `approval_fingerprint` from
   packet-manifest.json in your decision. It binds both content and presentation. It is a digest,
   not a signature or approval. Future adoption must verify against the separately recorded
   owner fingerprint and recheck the original inputs; rehashing a changed packet does not carry
   forward approval.

## Integrity commands

From the repository root (substitute the actual revision if reviewing a later packet):

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python eval/milestone1/packet.py \
  --packet eval/milestone1/reviews/r3 --check-inputs
```

For an owner-approved adoption, add `--expected-fingerprint <value-from-owner-decision>`.
Without `--check-inputs`, the check verifies the self-contained bundled review material offline.
The copied `tooling/` scripts are bound provenance snapshots; run the repository tools above.
The historical r2 packet still verifies offline; its original-input check will detect the intentional
revision of active generation documents. That does not alter its sealed bytes or transfer approval.
The complete 228-page IR files remain local under `runs/milestone1-r1/{clean,corrupted}/` and are
hash-bound external inputs; only selected regions are copied into the review record. Native input
paths are in `inputs/{clean,corrupted}-selection.json`. Reading PDFs is unnecessary.

## Decision template

Record your decision separately; do not edit this sealed packet. A new generation/revision needs
new review of its fingerprint. Partial acceptance is allowed.

```text
Reviewer:
Date:
Packet revision: r3
Approval fingerprint: <copy approval_fingerprint from packet-manifest.json>

HL-ERR-0006 clean / corrupted: accept | reject | corrections (token only)
HL-ERR-0017 clean / corrupted: accept | reject | corrections (primary occurrence)
HL-ERR-0025 clean / corrupted: accept | reject | corrections (primary occurrence)
HL-ERR-0041 clean / corrupted: accept | reject | corrections (primary occurrence)
Source-wording erratum and limited clean-paragraph evidence: acknowledge | corrections
Evidence limitations / incomplete-content handling: accept | reject | corrections
rounding (with stated assumptions): accept | reject | corrections
contexts (scope only): accept | reject | corrections
reference (including supporting text): accept | reject | corrections
negative-style (local labels only): accept | reject | corrections
percentage (minimal token): accept | reject | corrections
ambiguity (minimal insufficient evidence): accept | reject | corrections
Milestone 1 evidence handoff: accept within stated limits | corrections required
Comments / exclusions:
```

Model availability/capability probing is later work. Dated alert/runtime budgets, broader fixture
coverage, and independently grouped evaluation evidence remain future owner decisions, not
prerequisites for inspecting this packet. Milestone closure and headline status remain pending
and UNGATED until the appropriate decisions and evidence exist.
