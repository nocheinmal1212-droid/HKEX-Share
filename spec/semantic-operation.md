# Direct contributor headers, version 1.0.0

This operation selects **column-header occurrences immediately contributing to a named total
header**, in one explicitly selected saved-IR table. It does not choose numerical operands or
assert accounting completeness. A later planner must independently establish row applicability,
entity, period, unit, basis, completeness and arithmetic prerequisites.

Success: `selected` with the complete set of immediate contributor header IDs, target ID and
literal support IDs. Prefer a subtotal over its descendants to avoid double counting. Same
column meaning with incompatible period/scope is not a contributor. Hierarchy comes from literal
labels together with recovered HTML row/column spans; coordinates alone do not establish roles.
The model must cite the target, each contributor, and contextual/group headers used. No amounts,
calculations, coefficients, corrected text or free-form explanations are returned.

Supported abstentions: `missing_evidence`, `ambiguous`, `incompatible_context`, `not_a_total`.
A blank/missing target or unresolved/partial grid blocks dispatch locally as missing evidence or
invalid extraction. Unknown IDs, wrong parent/table, edited projections, omitted table descendants,
unsupported transforms and oversized context are invalid caller inputs, not source abstentions.
A structurally valid selection is not certified source-correct; independent review checks meaning.

Projection includes the entire selected table's descendant inventory with literal parent links,
cell anchors/spans, states, source fragment references and applicable limitations. Header-band
cells intersecting rows through the target's bottom edge retain literal text. Body numerical cells
are either amount-masked or amount-varied in explicitly versioned derived projections; dates,
units, labels, captions and notes remain literal. Original evidence is immutable. Missing text
stays null. No neighboring section/note association is invented. Unassociated context is unknown.
Bounds: one table, 256 descendants, 120,000 UTF-8 bytes. These are engineering limits, not
accounting adequacy criteria. Output IDs must belong to the header band; same-table/span
checks reject known geometric group conflicts, while semantic compatibility still needs review.

Failures remain distinct: refusal, truncation, invalid output/identity, timeout, transport error,
persistence failure, incomplete attempt and commit_unknown. No retries or research promotion.
The paired attempt and operational provenance contract is additive; frozen M1 schema bytes and
historical experimental attempt versions remain unchanged.
