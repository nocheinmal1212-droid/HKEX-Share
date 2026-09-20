# Scoring Contract

**Version: 2.0.0 — reconciled 2026-09-09.** Supersedes 1.1.0, preserved in
[the archive](../docs/archive/2026-09-09/eval/SCORING.md). Results are not comparable across versions.
This is the contract to implement; no matcher or scoring gates are claimed to exist yet.

This document owns scoring scope, matching, metrics, and publication rules.
[The format contract](eval_format_spec.md) owns record representations.
[The taxonomy](../spec/taxonomy.yaml) owns category meanings, not execution dependencies.

## 1. Delivered benchmark and scoring scope

The current delivery is the Chinese-language Hang Lung Properties FY2025 annual report:
228 pages, one clean PDF, one PDF containing 48 injections, and 48 raw records, eight per
scored category. Clean and corrupted MinerU exports are present. The corpus is not the previously
described 54-record bundle plus magnitude sweeps. No descoped injections, negative fixtures,
canonical records, or assigned splits have been established in this delivery.

Scored codes:

- primary_statement_articulation
- internal_note_reconciliation
- statement_to_note_articulation
- disclosure_reference_verification
- document_wide_consistency
- formatting_typography_validation

Descoped codes remain in the nine-code taxonomy: inter_note_articulation,
table_structural_integrity, textual_semantic_integrity. Future descoped ground truth must be
retained and matched as neutral. Do not manufacture records for presumed historical injections.
Taxonomy status active means a valid vocabulary term, not an implemented or scored detector.

## 2. Evaluation modes and prerequisites

- **frozen_ir:** evaluates downstream behaviour against recorded extraction artifacts.
- **pdf_end_to_end:** evaluates a recorded PDF/extraction/adapter/interpretation/check configuration.
  Extraction may be a separately executed, attested step; freeze both exports and their provenance.
- **fixture:** uses manually reviewed evidence, annotations, or plans to diagnose individual stages.

Always label the mode. Fixture inputs cannot substitute for generated inputs in end-to-end results.
Separate runs and gate evidence by mode; an IR transformation does not certify PDF extraction.
End-to-end publication requires confirmed input hashes and equivalent clean/corrupt extraction
settings, including known differences introduced by the injector. Equal tool-version strings alone
do not establish that equivalence.

Raw inputs remain unchanged. Canonical ground truth, source mappings, fixture selection, and split
assignment belong to evaluation preparation. Runtime detection never reads ground truth, the clean
counterpart as an oracle, or benchmark-authored operand lists.

## 3. Ground-truth eligibility

A canonical record must have reviewed document/variant identity, source mapping, category/revision,
site and split group, locations, status, scoring scope, and detectability assessment.
Use ingestion_status pending or ready separately from record status active or retired.
Raw status open is not a canonical retirement/eligibility decision.

For numeric relationships, report three bands separately: above_tolerance, boundary,
within_tolerance. Non-numeric errors use not_applicable and have a separate non-numeric recall.
Unknown numeric bands remain unknown; never relabel them non-numeric or silently remove them.

Band computation and relation-specific rounding are defined in the format contract. A band describes
perturbation size relative to the justified tolerance, not a promise of universal detectability.
expected_detectable requires review; propagation, cancellation, or an untestable relationship may
make a corruption undetectable by the intended checks. Low detector coverage is not a reason to
mark an otherwise detectable error excluded.

Active, ready, scored, expected_detectable=true records in above_tolerance, boundary, or
not_applicable form the primary evaluation population. within_tolerance is a separate stretch set.
Retired records and reviewed expected_detectable=false records are excluded with reasons.
Pending, unknown-band, and unknown-detectability counts must be reported and block headline
publication for the selected split until resolved. A missing relationship cannot disappear from
the intake inventory. Descoped records never enter recall denominators.

## 4. Result records and source addressing

A scoreable finding contains finding_id, doc_id, variant_id, category_code, location,
nonempty evidence_refs, check_id, and a structured claim identifying its operands or source spans.
plan_id is required for planned numerical comparisons; direct token/reference checks may use null.
Financial calculations include their residual and tolerance policy/result.
Calibrated confidence is not required. Optional confidence cannot control matching or publication.

Locations identify a table_id or section_id within a document variant. Optional row_key and
column_key support cell-level scoring. Page-only alerts are diagnostic, not eligible detections.
Cell geometry is optional: a logical cell address and a container anchor can be sufficient.
The evaluation-only mapping reconciles source anchors and re-extracted IDs without exposing answers
to the detector. Do not assume translated labels or OCR-generated IDs survive extraction unchanged.

Use exact canonical identifiers after mapping. Do not strip punctuation from opaque IDs and
accidentally collapse distinct locations. Lexical normalization belongs in reviewed mapping rules.

Record all opportunities in checks.jsonl: check_id, opportunity_id, document/variant, location,
category_code, optional plan_id, state, and reason. States are passed, failed, abstained,
not_applicable, or crashed. Here:
- abstained means a relevant opportunity lacks evidence or an unambiguous interpretation;
- not_applicable means the check is genuinely irrelevant, with an explicit reason;
- failed means a discrepancy was found and links to the corresponding finding.

abstentions.jsonl is a derived view of abstained records, not the only evidence of attempted work.
Adapter or planner failures must remain visible as stage failures and unresolved opportunities.

## 5. Matching and adjudication

**L2:** table_id, row_key, and column_key match after source mapping.
**L1:** table_id or section_id matches. L1 is the primary detection level.
The category prediction does not affect eligibility; classify matched detections separately.
For paired discrepancies, any reviewed primary or secondary endpoint is eligible.
Attribution is scored only when the corrupted endpoint is known.

Within each document variant, maximize eligible match cardinality, then prefer L2 over L1.
Resolve remaining ties lexicographically by sorted (error_id, finding_id) pairs.
Implement optimal assignment, not output-order-dependent greedy matching.
One finding matches at most one GT, and one GT receives at most one detection.

Assignment is performed across all splits before selecting split-specific recall. Ground truth
outside the selected split is not an unexplained false alarm. First match the primary population;
then match remaining findings to the stretch set, reviewed exclusions, and descoped records,
in that order. A finding already assigned cannot be reused in another population.

Extra findings may be NEUTRAL_SURPLUS only when they support the same documented discrepancy
relationship as an already matched finding. Sharing a table alone is insufficient. Preserve all
emissions for workload reporting. Other unmatched findings on injected documents are UNMATCHED
diagnostics, not a calibrated precision estimate.

A TP is an assigned primary-population record; an unmatched primary record is FN.
Stretch detections and matches to exclusions or descoped records are reported separately.
A malformed emitted finding is never a TP and still counts as an alert on a clean run.
For a GT with no hit, classify misses using the opportunity ledger:
crashed if a mapped relevant stage/check failed; otherwise attempted if any relevant check ran;
otherwise abstained if a relevant opportunity was blocked; otherwise no_check.
A whole-document crash or timeout gives all its eligible records FN/crashed, regardless of partial
outputs. A partial failure marks affected records and the run degraded; unrelated valid hits remain.

## 6. Metrics and clean-document workload

Publish separate pooled L1 recall for above_tolerance, boundary, and non-numeric/not_applicable.
Publish within_tolerance only as a stretch diagnostic. Never blend the bands into one GPR or F1.
For every rate provide numerator, denominator, n_records, n_sites, and n_split_groups.
Zero denominator means null/not_available, never zero or perfect performance.
Per-category recall is diagnostic; do not impose unsupported category targets.

**Clean alert rate = all emitted alert records / (page count / 100).**
It measures reviewer workload, not precision. Count malformed, duplicate, grouped-for-display,
and known-real-anomaly alerts too; visual grouping cannot reduce the gate's count.
Freeze duplicate-emission handling in the system before evaluation, not in the score renderer.
Every clean page must finish within the runtime budget; an incomplete clean run fails the gate.

Negative/distractor fixtures are reviewed evaluation artifacts, not runtime suppression lists.
Report confirmed false alerts, distractor hits, and known-real-anomaly matches separately when
reviewed labels exist. Until then do not label all clean alerts false positives.
Retire the old triple-weighted FP gate: the operational budget now uses the raw rate.
Classification accuracy uses matched primary TPs and the nine-code confusion matrix.
L2 localization and known-endpoint attribution are separate diagnostics.

Coverage reports:
- resolved logical tables / inventoried table regions, including unresolved regions;
- resolved contexts or labels / required contexts or labels, with the inventory definition;
- lexicon resolutions / all resolutions;
- executed opportunities (passed + failed) / relevant opportunities;
- abstained and crashed opportunities / that same denominator;
- unresolved regions, planner failures, and opportunities that could not be enumerated.

A genuinely not_applicable check is outside the relevant denominator, with counts and reasons
reported. Do not define relevance by whether prerequisites succeeded. Missing table detection
cannot be measured solely by the detector's own region list: use annotated fixtures for that gap.
Coverage is always alongside recall; abstention is not a detection and earns no recall credit.

## 7. Site groups, splits, and statistical limits

Assign stable site_id values to physical/logical injection sites. Repeated magnitudes share a site.
Assign split_group_id to connected sites with shared propagation, comparison relationships, or
interacting injections in the same table/container. Unrelated sites may remain separate groups.
This prevents a single table's ground-truth relationships from straddling development and holdout.

Before detector tuning, hash UTF-8 (split_salt + ":" + split_group_id) with SHA-256, interpret the
hex digest as an integer, and assign test if integer modulo 3 is zero; otherwise dev.
Record salt, algorithm, assignments, and the group rationale immutably. Never reroll an awkward split.
No assignment is made by this document.

The single corrupted PDF contains all sites. Development diagnostics must hide test-site scores,
annotations, and counterpart-derived plans. Record prior exposure honestly: the bundle has already
been inspected, so a later split is not a claim that its contents were never seen. Test runs are
predeclared and logged. Tuning after test feedback converts subsequent uses to exploratory;
fresh evidence is needed for an untouched holdout claim.

Use a cluster bootstrap over split_group_id, preserving sites and records within each group.
When groups equal sites this is the original site bootstrap. Use 10,000 resamples and record the
seed; report percentile 95% intervals only when the band has at least two independent groups,
otherwise null with insufficient_clusters. Report how many bootstrap draws lack that band and omit
them from its interval calculation. Small cluster counts are explicitly qualified.
No default significance test or market-wide inference is warranted. Comparative runs use paired
group resampling, not a nominally clustered McNemar test without a specified method.
The delivered 48 sites have no established repeated-magnitude sweep; do not promise a response curve.

## 8. Publication gates and reproducibility

Headline is null and status UNGATED unless all of the following pass:
1. Canonical intake, split mapping, and provenance are ready for the selected mode/population.
2. Literals/import-boundary checks find no issuer facts or benchmark-answer access in runtime code.
3. The six declared invariance transformations pass at their declared layer.
4. A complete clean run has raw alert_rate <= the dated, frozen ALERT_BUDGET.

Invariance compares canonical claim signatures (category, mapped locations/operands, operation,
discrepancy kind), preserving multiplicity. Exclude timestamps, run IDs, prose, and optional
confidence. Convert units/operand IDs before comparing. Log all exempt-category differences.

| Transform | Exempt categories |
|---|---|
| Consistent note renumbering | none |
| Entity/name/code replacement | none |
| Unit rescaling with equivalent values and preserved rounding precision | formatting_typography_validation |
| Consistent negative-number style substitution | formatting_typography_validation |
| Approved lexicon synonyms | none |
| Independent-note reordering with mappings | disclosure_reference_verification |

A missing required transform is not a pass. Report whether each transform covers frozen IR or PDF.
Second-issuer samples are an additional diagnostic, not a recall benchmark or mandatory new corpus.

Replaying frozen extraction and accepted semantic artifacts must reproduce canonical plans/results.
A fresh model call or fresh OCR run is a different reproducibility experiment and may vary.
Do not divide categories into inherently deterministic versus hybrid for seed-median scoring:
upstream interpretation can affect any numerical check. Use one predeclared frozen run for scoring;
optional repeated-call sensitivity experiments are separate and cannot select the best result.

Record code/config hashes, taxonomy/format/scoring versions, bundle and split-map hashes,
source mappings, extraction fingerprints, model identity/revision limitations, prompts, schemas,
cache manifest, runtime budget, and actual timing. Never substitute an alias for a verified revision.

## 9. Open parameters and artifacts

ALERT_BUDGET and RUNTIME_BUDGET are unset. Their owners must fix values and dates before the
first scored run. Do not carry the old provisional 8-alert example forward as approval.
Set the alert budget from reviewer capacity before observing scored alert counts.
Bootstrap seed and split salt are also fixed and recorded during intake.

runs/<run_id>/result.json records mode, population, versions/hashes, gates, band-specific metrics,
coverage, exclusions/pending counts, misses, neutral/unmatched findings, and failures.
Raw artifacts include evidence, annotations, plans, checks, findings, abstentions, and manifests.
Result records are immutable; corrections create a new run referencing its predecessor.
No sample success scores are embedded in this contract.

For comparisons, require identical evaluation contract versions, bundle, split, mode, source mapping,
and category revisions; record system changes explicitly. Missing comparability fields block a
comparison rather than implying equivalence.

## 10. Acceptance examples

- Wrong component reported at its total in the same table: TP at L1, not necessarily L2.
- Correct paired discrepancy reported at the uncorrupted endpoint: TP; attribution may miss.
- Two genuinely distinct injections in one container and one finding: at most one TP.
- Additional finding about the same relationship: surplus diagnostic; still an alert on a clean run.
- Unrelated finding in that container: unmatched, not automatically surplus.
- Wrong predicted category at a correctly mapped site: detection hit, classification error.
- Missing prerequisites at an otherwise eligible site: FN/abstained, not excluded.
- Unknown band or incomplete source mapping: intake pending and no headline, not a smaller denominator.
- No numeric tolerance applies to a wrong note reference: non-numeric population, not within_tolerance.
- Consistent corrupted propagation cancels the tested residual: reviewed detectability decision,
  never guessed from one changed cell's magnitude.
