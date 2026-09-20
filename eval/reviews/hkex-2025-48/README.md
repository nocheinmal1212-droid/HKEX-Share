# Milestone 0 review handoff

Milestone 0 is closed. The owner approved all four selected cases, which are now `ready` in
record revision 3; the other 44 remain pending. [Closure evidence](milestone-0-closure.json)
records the successful checks. [Closure re-verification](closure-verification-2026-09-10.json)
records the fresh 2026-09-10 checks. [Ready development selection](ready-development.json) identifies
the exact records, mappings, split and approval file for Milestone 1.

The [development review packet](packet-r2/index.html) is preserved as immutable pre-approval evidence;
its pending labels describe that earlier snapshot. [Readiness](readiness.r5.json) names owners and
next steps for unresolved extraction/model metadata, budgets and publication prerequisites.

## What is established

- Immutable inventory: 788 files, including both supplied PDFs, raw metadata and both native exports.
- All 48 raw records retained, with eight records per scored category and unchanged IDs/source text.
- Four reviewed PDF/logical mappings and 44 explicit candidate mappings; the ready subset includes
  two reviewed, computed relationships.
- One conservative group hashes to development with the preselected salt. No test set, untouched
  holdout or independent-group confidence interval exists. Splits were not rerolled.
- Raw pdf_page is one-based physical numbering. All 48 original and injected tokens were recovered
  by character-center checks in the corresponding rectangles, in PDF points from the top left.
  Printed labels were visually checked on selected pages, not assumed for the whole report.
- Both exported origin PDFs differ in bytes from the supplied sources. After correcting numeric
  geometry comparison, all 228 pages of each pair agree in page geometry, decoded content and
  extracted text; all 228 low-resolution page renders per pair are identical. This strongly
  corroborates source correspondence, without proving clean/corrupt OCR settings equivalence.
- Visual review of physical pages 159, 180 and 185 confirms the selected source changes and reveals
  injection artifacts: white redaction patches, typography differences and removed title characters.
  Extraction layout text can reorder replacement tokens. Do not classify that reordering as another
  authored source discrepancy or claim artifact-only performance is at chance.

## Accepted development review

The owner approved the percent-token, revenue-reference, gross-profit and statement-note revenue
cases. Source locations, counterparts, numeric relationships, current-period interpretation and
rounding assumptions in the packet were accepted. Source-backed propagation review is recorded
separately in [promotion-source-review.json](promotion-source-review.json): gross profit has linked
changes in its downstream statement subtotal chain; the other three cases have no propagated edit
within their reviewed discrepancy relationships. Historical injector execution order remains unknown.

[Owner approval](owner-approval.json) binds the exact promoted records with their mapping and split
hashes. Four PDF/logical mappings are reviewed. Native candidate IDs remain candidate links until the
Milestone 1 adapter supplies actual IR correspondence; no completed adapter is implied.

The gross-profit proposal has residual change -10 and tolerance 1.5; the revenue-pair proposal has
residual change -10 and tolerance 1.0, in displayed HKD millions. Values were read from source
characters by code. Operand roles were selected by table structure/context, not by numerical fit.
Those are owner-approved evaluator-only annotations, not runtime comparison plans.

The six minus-for-parentheses injections need local-convention review; a valid negative style is
not automatically a discrepancy. Other arithmetic sites may involve cancellation among linked
subtotal changes. Their raw descriptions are hypotheses, not ready eligibility decisions.

## Provenance and licensing

[Dependency evidence](dependency-licenses.json) records installed package versions, declared
licenses, local license-file hashes and requirements. The tested intake dependency graph uses
MIT/BSD-3-Clause notices. Retain those notices on redistribution. This covers the intake Python
packages, not an uninstalled OCR engine or future semantic serving stack.

The separate source-character investigation used bundled pdfplumber 0.11.9; packet rendering used
external Poppler. These review tools are not shipped into the proprietary runtime. Their use here
does not establish that embedding, modifying or redistributing them is compliant; review any such
change under the project's constraints. A process boundary alone is not a license clearance.

Current [MinerU source licensing](https://github.com/opendatalab/MinerU/blob/master/LICENSE.md)
uses an Apache-2.0-based license with additional commercial/attribution conditions. The published 3.2.2 wheel was downloaded without installation and its license, source entrypoints
and declared dependency sets were inspected; see [package review](mineru-package-review.json) for
the wheel/license hashes. Its license has the same additional commercial/attribution conditions.
This does not identify the exact build, checkpoint or serving backend used for the supplied exports.
Weights and actual backend dependency closure remain unreviewed; extraction licensing is pending.

The current owner-selected development model is `deepseek/deepseek-v4-pro-0813` through
OpenRouter. Availability, observed provider/model identity, capabilities and revision-pinning limits
remain to be probed. Earlier readiness revisions preserve Flash documentation evidence as history;
it does not establish capabilities or identity for the newly selected Pro model. No model call was
made for this change. See [current readiness](readiness.r5.json).

## Revisions and verification

`revisions.json` identifies the first three record revisions; `milestone-0-closure.json` and
`ready-development.json` identify the owner-approved revision 3. Mapping/split revision 3 preserves
all site/group assignments and the original frozen salt/seed. Every re-import requires
unchanged source hashes and byte-identical output, or a new revision path. The original geometry
comparison report is retained alongside its corrected revision and rationale.

Portable `make check` validates formatting, schemas and synthetic regression cases; local
`eval-intake validate` additionally checks source integrity and provenance. Initial isolation passed
for built-in, pathlib, io and os.open access, including forbidden symlink targets. No real detector,
adapter or prompt-builder isolation is claimed. No scored runs or headline results exist.
