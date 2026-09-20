# Erratum: withdrawn source-wording claim in the Milestone 1 reviews

Date: 2026-09-10. Applies to the first independent review, its follow-up verification and sealed r2
(approval fingerprint `b66851423dbb940414cfd7a6ab1289a723afcaa93ab95884c6f10f1a8561440a`).

**The clean source paragraph uses `採用`, matching native/IR. It does not use `採取`.**
Both contain `雙重機制`; the source phrase crosses a line break.

The first independent review misquoted the low-resolution source image. The follow-up incorrectly
endorsed that reading and repeated it in r2's guide, HTML banner, case guidance, verification report
and final response. Those specific assertions, including the claim of substantive paraphrasing in
this paragraph, are withdrawn. This is an error in the review explanation, not in the adapter.

The second independent reviewer documented a narrow inspection rationale, read only the clean
physical page 185 (IR index 184), paragraph (d), using its existing PDF text layer, and rendered
that paragraph at 300 DPI. Its source identity matches the frozen clean-source identity. This
follow-up verified the saved artifact hashes, visually read the high-resolution image and compared
the saved source text with the selected native/IR paragraph. Both unambiguously contain `採用`.
No additional PDF read, rendering or OCR was needed for this follow-up.

The saved clean-source text and native paragraph agree after removing whitespace and treating
fullwidth/ASCII parentheses as equivalent **in a diagnostic comparison only**. Their literal bytes
are not equal. Nothing was normalized in the evidence, runtime input or fixture files. This local
observation does not certify the corrupted paragraph in full, source typography, other extractor
prose or whole-document fidelity.

All eight primary token mappings and six qualified fixture expectations remain unchanged and
pending owner acceptance. No runtime, adapter, source value, secondary mapping or comparison-plan
change is indicated. The first and second audit originals, r1 and r2 remain immutable historical
records. Revision r3 binds this erratum and the saved inspection evidence in a new approval
fingerprint; prior approval must not be inferred or transferred.

Inspection artifacts are bundled under `source-inspection/` in r3: inspection-plan.json,
inspection-result.json, source-paragraph.txt and source-paragraph.png. The original inspection
artifacts remain under `runs/milestone1-independent-r2/`. The second auditor's original report is
`eval/milestone1/reviews/independent-r2-2026-09-10.md`.
