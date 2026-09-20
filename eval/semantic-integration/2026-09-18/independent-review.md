# Independent agent source review — frozen before inference

Reviewer: `/root/source_review`. Independent **AGENT** review; **not human/domain approval**. Started `2026-09-18T05:47:27Z` (first captured time immediately after initial source read); completed `2026-09-18T05:49:51Z`.

Only the operation contract and supplied source-review packet were read as task evidence. No Task B model output, implementation, clean IR, benchmark metadata, other review, PDF or native export was inspected. Packet body amounts were visible but were not used to choose relationships or calculate answers.

| Query | Frozen expected outcome | Literal source justification |
|---|---|---|
| `total` | Select `合計` + `租賃(HKFRS 16)` | The HKFRS 15 group spans columns 1–3, terminating in `合計`; leasing is the separate column 4 and `總額` is column 5. |
| `subtotal` | Select `於某一時點確認收入` + `隨時間逐步確認收入` | Both recognition categories and `合計` occupy the same HKFRS 15 group. |
| `period_groups` | Select 2025 `物業租賃`, `酒店`, `物業銷售` | Target `總額` is under the literal 2025 span; matching 2024 labels belong to an incompatible group. |
| `missing_target` | Local `missing_evidence`; no model call | Existing target occurrence is literally blank, with empty text and no text fragments. |
| `varied_total` | Same selection as `total` | Body-only amount changes cannot alter unchanged header meaning or hierarchy. |

Positive header relationships are supported for the four selection queries, conditional on faithful packet/projection preservation. This does not establish numerical operands, row applicability, accounting completeness or arithmetic correctness. Selecting a subtotal together with its descendants would double count the hierarchy. Selecting the corresponding 2024 headers for the 2025 target is unsupported. There is no unresolved dispute about these bounded expectations.

Both declared grids are resolved and fully occupied without overlapping or out-of-bounds cells: 37 cells in a 7×6 grid; 182 cells in a 21×9 grid. These are packet-internal checks, not proof that the saved IR or PDF is complete. Source identity and underlying IR hash are declarations from the packet, not independently reverified. Physical/printed page correspondence and OCR accuracy remain unverified.

The first table's associated caption literally states `截至2026年12月31日止年度`; it is retained without correction. The other table's 2025/2024 groups do not override it. Both tables contain `港幣百萬元`. Entity/consolidation scope and full presentation basis remain unknown; the operation defers those prerequisites to later planning.

Full occurrence IDs, parent links, native pointers, literal text, spans, support/exclusion sets and source-fragment citations are frozen in [independent-review.json](independent-review.json). Expected support IDs are minimum semantic citations; the table caption is reviewer context, not a required model header ID. Transform execution has not been reviewed.

- Packet SHA-256: `57a0ca40e2f19a3ec33564a2fdf549c39482d4031ca5df4283364c3190095b80`
- Operation contract SHA-256: `9dd7e84f3707de3817dff38bd06a0b13c8b559eda7fc19607f44c08434852529`
- Review JSON SHA-256: `186751559cb107900b7eb1cebee5993d43b729ed283649929a467dd51fcea789`
