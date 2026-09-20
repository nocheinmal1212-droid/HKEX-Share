# Evaluation Data Format Specification

**Version: 2.0.0 — reconciled 2026-09-09.** Replaces
[version 1.0.0](../docs/archive/2026-09-09/eval/eval_format_spec.md).
This is a contract to implement. A working migration, record validator, and CI gates are still
Milestone 0 work; this document does not claim that they already exist.

[SCORING.md](SCORING.md) owns eligibility, matching, metrics, split assignment, and publication.
[The taxonomy](../spec/taxonomy.yaml) owns category meanings.
[PLAN.md](../PLAN.md) owns implementation status and sequencing.

## 1. Sources and ownership

Preserve delivered inputs in corpus/ byte-for-byte. The current source is error_detail.jsonl:
48 records, eight per scored category, accompanying clean and corrupted 228-page PDFs.
Both MinerU exports are present. There is no established 54-record legacy set, magnitude sweep,
spreadsheet source, or negative-fixture collection to migrate.

Canonical records are a reviewed interpretation of that delivery, not a replacement for it.

| Path | Role | Status after this reconciliation |
|---|---|---|
| corpus/ | Original PDFs, injection metadata, native extractor artifacts | Supplied; immutable inputs |
| spec/taxonomy.yaml | Single runtime-safe nine-code vocabulary | Reconciled |
| schemas/taxonomy.schema.json | Vocabulary validation | Reconciled |
| eval/records/<bundle_id>/<variant_id>.jsonl | Canonical ground truth | Planned |
| schemas/error_record.schema.json | Canonical record validation | Planned |
| eval/manifests/<bundle_id>.json | Source hashes, provenance, review status | Planned |
| eval/locations/<bundle_id>.json | Source-to-evaluation location mapping | Planned |
| eval/splits/<bundle_id>.json | Site groups, assignments, salt and exposure record | Planned |
| eval/negatives/ | Reviewed benign and known-anomaly fixtures | Planned |
| runs/<run_id>/ | Frozen inputs, intermediate artifacts, results and run manifest | Planned |

One batch application and JSON/JSONL artifacts suffice. Generated enums, Parquet, spreadsheets,
prompt-file generators, and a general build framework are optional future conveniences, not PoC
prerequisites. Derived views never become another source of truth.

Runtime detection receives explicit document/extractor paths and runtime-safe configuration.
It must not discover corpus files by unrestricted globbing: corpus/error_detail.jsonl is ground
truth even though it sits beside PDFs. Evaluation records, mappings, split annotations, and
counterpart-derived operand lists stay outside the detector and prompt builder. The harness may
read them after collecting detections. Import checks alone are insufficient; test file access too.

## 2. Encoding and identity

Canonical text uses UTF-8 without BOM, LF, one final newline, spaces for indentation, and no
trailing whitespace. Preserve Chinese source text literally. JSONL has one compact object per
line, no blank lines, and records sorted by error_id. Do not apply these formatting rules to raw
delivered files. Do not split a logical record merely to meet an arbitrary nesting or line limit.

Exact financial values, scales, coefficients, residuals, and tolerances are decimal strings.
Parse them using exact decimal arithmetic. Counts and indices are integers. Geometry and optional
model confidence may use finite JSON numbers; they are not financial arithmetic.
Reject non-finite values. Preserve source parentheses, dashes, separators, and malformed tokens
in raw text; a normalized decimal must not overwrite them.

An absent optional field is not supplied or not applicable as its contract specifies.
A required nullable field uses null for unknown, with a reason in review_notes.
Do not substitute zero, false, an empty string, or a fabricated default for unknown information.
Empty source text is allowed in explicitly raw text fields; canonical identifiers are nonempty.

Identifiers are nonempty opaque strings, stable within their declared namespace. Retain the supplied
HL-ERR-* identifiers if unique; do not renumber merely to satisfy the former ERR-##### convention.
Never reuse retired IDs. A schema or semantic validator checks uniqueness bundle-wide.
Changing extraction engines can change their IDs; evaluation mapping handles that explicitly.

## 3. Taxonomy contract

The sole canonical vocabulary is spec/taxonomy.yaml. The former full and six-category files are
retired into the dated archive. There is no independently edited scored subset.
SCORING.md is authoritative for the six scored and three descoped codes.

Top-level keys, in order: spec_version, taxonomy_version, categories.
Category keys: code, revision, name, status, scope, description, examples (optional).
Use two-space YAML indentation and folded-strip prose for multiline descriptions.
No anchors or aliases. Category ordering is for reading, not an execution dependency graph.

- spec_version is this format version; taxonomy_version identifies the vocabulary release.
- code is an immutable category identifier. revision changes when its meaning or boundary changes.
- status active means a usable vocabulary term, including descoped terms. It does not promise an
  implemented detector, an acceptance target, or inclusion in a metric.
- scope and description define the discrepancy. Examples illustrate it without benchmark IDs.
- All nine codes occur exactly once. The schema rejects unknown fields and duplicate/missing codes.

Version 2 resets the operational category contracts explicitly; all category revisions are 2.
Future prose-only corrections do not require a semantic revision. Versioned results must retain
their category revisions; changed definitions need a migration note before results are compared.

Capabilities, prerequisite handling, tolerance policy, and execution strategy belong to individual
checks and plans. Precision targets, split assignments, and positive/negative fixture IDs belong
to evaluation. None belong in the runtime vocabulary. A structural extraction failure is an
engineering limitation, not a mandatory upstream taxonomy detector.

## 4. Canonical ground-truth records

The following fields define the proposed version-2 record schema. Implement that schema during
Milestone 0; pending records must remain representable without inventing metadata.

| Fields | Representation and rule |
|---|---|
| schema_version | "2.0.0" |
| error_id, bundle_id, variant_id, doc_id | Stable identity; doc_id identifies the document, variant_id its clean/corrupted form |
| source_ref | Raw relative path, sha256, original record ID and one-based JSONL line number |
| status | active or retired; retirement requires a reason |
| ingestion_status | pending or ready; readiness is separate from record lifecycle |
| category_code, category_revision | Current taxonomy code and integer revision; retain original taxonomy metadata in source_ref or review_notes |
| scoring_status | scored or descoped, derived from the scoring contract |
| site_id, split_group_id, split | Nullable until reviewed; ready records require identities and dev/test assignment |
| location, secondary_locations | Primary address and zero or more related endpoints; pending unresolved primary is null |
| original_text, injected_text | Unmodified source values from metadata; nullable if unavailable, not automatically numeric |
| original_value, injected_value, value_delta | Nullable exact decimal strings for the changed fact, when normalization is justified |
| relation | Nullable reviewed numeric relation described below; absent arithmetic uses null |
| detectability_band | above_tolerance, boundary, within_tolerance, not_applicable, or unknown |
| expected_detectable | Boolean or null; review rationale required, especially for false |
| injection_stage | pre_ocr_pdf, post_ocr_ir, post_ocr_markdown, or unknown |
| injector_version, seed | String/integer respectively, or null when unavailable; record why |
| propagated, propagation_sites | Boolean or null; source addresses of linked changes, empty only when reviewed none |
| description, review_notes | Description and explicit review decisions, uncertainties, exclusions and mapping notes |
| created_at, updated_at | Known UTC timestamps or null; do not fabricate source creation times |

Use this table's order for serialization; within each group use the displayed order.
Ground-truth completeness is validated semantically as well as structurally.
Ready scored records require confirmed identity, location, group/split, category revision,
detectability decision and known band. Retired and descoped records remain inventoried and require
enough reviewed mapping to support any matching claimed for them.
Unknown historical seed/version may remain null with an explicit limitation; that prevents a claim
of exact injection regeneration, not necessarily evaluation of a frozen, attested PDF.

Raw status open is not canonical active by spelling substitution: review lifecycle.
Raw document_id names the clean source even for injected records; resolve document/variant identity
from the PDF manifest. Raw confidence and expected/actual prose are not canonical eligibility.
Preserve them in the raw source rather than using them as detection output or a calibrated label.

## 5. Locations and provenance

A reviewed location contains a physical page index (zero-based), table_id or section_id, and optional
row_key, column_key and source anchors. Source anchors may include a PDF rectangle, raw extractor
pointer, or text span. Store coordinate units, origin, rotation, page dimensions, and source artifact
identity with the mapping. Printed page labels are separate from physical indices.

Do not assume the delivered pdf_page numbering or bbox convention; confirm before conversion.
A container anchor plus logical cell IDs can support L1/L2 without exact cell geometry.
Unresolved cell mapping is not fixed by inventing a bounding box.

Evaluation addresses are stable within a frozen bundle and mapping revision. They are not guaranteed
to survive re-extraction. Record each mapping from native/IR IDs to canonical evaluation IDs, including
ambiguous or unmapped cases. Hashes detect source changes; they do not establish semantic equivalence.
Never strip punctuation from opaque IDs to force a match.

Secondary locations describe the other endpoints of a discrepancy. Explicitly identify the corrupted
endpoint when known; array order is not an attribution convention. The harness may match either
reviewed endpoint under SCORING.md.

The bundle manifest records original and corrupted PDF hashes separately, native export hashes,
engine/backend/version, checkpoint and settings when known, and source PDF correspondence.
Both present exports report MinerU VLM 3.2.2 and 228 pages; this does not identify a checkpoint or
prove settings equivalence. MinerU's exported origin PDF may differ in bytes from the supplied PDF.
Record both hashes and how correspondence was verified, rather than declaring them identical.

Injection provenance includes stage and propagation review. The raw redaction/replace method
supports investigation of a PDF-stage injection; do not infer a missing generator revision or seed.
For PDF-mode evaluation, verify selected injected text visually in the source as well as its extraction.
Consistent propagation can cancel a residual, but propagation alone does not prove undetectability.

## 6. Numeric relationships, tolerance and bands

Numeric records describe a reviewed relationship with operands, signed coefficients, compatible
context, and rounding policy. These are evaluator-only annotations; runtime plans must be produced
independently. Financial normalization is code-derived and reviewed, never supplied by a language
model as a corrected value.

For an additive relation, write the residual as sum(a_i * x_i), including the total as an operand.
With independently nearest-rounded displayed values and rounding steps u_i, the conservative bound is:

~~~text
tolerance_bound = sum(abs(a_i) * u_i / 2)
residual_change = sum(a_i * (injected_i - original_i))
~~~

Coefficients, values and steps use compatible units before computation. Include unchanged operands'
rounding uncertainty. For n unit-weight addends and an equally rounded total, the bound is
(n + 1) * u / 2. The former n * u / 2 formula omitted the total.
Other operations require an explicit justified policy; do not force them into this additive rule.

Store relation operands with source references, coefficients, original/injected normalized values
and rounding steps, plus rounding_policy, tolerance_bound and residual_change.
The single-site value_delta remains useful provenance but cannot replace residual_change when
several changes propagate or cancel. Unknown contributors, precision, or policy leave the relation
assessment pending; increasing tolerance is not a remedy for incomplete relationships.

Compute bands from magnitude = abs(residual_change):

~~~text
magnitude <= tolerance_bound       -> within_tolerance
magnitude <= 2 * tolerance_bound   -> boundary
otherwise                         -> above_tolerance
~~~

At zero tolerance, zero change is within_tolerance and any nonzero change is above_tolerance.
Non-numeric reference/token discrepancies use not_applicable; unknown numeric assessments use unknown.
The band measures perturbation size, not a guarantee that the actual corrupted residual exceeds
tolerance. Review expected_detectable against the intended relationship, original/corrupted residuals
and evidence. A within-tolerance case remains a stretch diagnostic even if independently detectable.

## 7. Grouping, splits and output contract

site_id groups repeated versions of the same injection site. split_group_id connects sites sharing
propagation, comparison relationships, or interacting injections in one container.
Use the exact SHA-256 assignment in SCORING.md; never split by error_id or reroll after seeing results.
Store the grouping rationale, salt, algorithm, assignments, source hashes and prior-exposure note
in the split manifest. The delivered records have not yet been assigned.

Runtime artifacts are evidence, annotations, comparison plans, checks.jsonl, findings.jsonl,
a derived abstentions.jsonl, coverage and manifests. Their schemas belong to pipeline contracts
and remain implementation work. SCORING.md defines the minimum finding and check fields.

All relevant opportunities appear in the check ledger, including blocked ones.
Use passed, failed, abstained, not_applicable and crashed consistently.
Abstained means missing/ambiguous prerequisites; not_applicable means genuinely irrelevant.
Optional confidence never substitutes for prerequisites or controls scoring.
Run results reference exact evaluation, taxonomy, schema, mapping and split versions.

## 8. Validation and migration work

Milestone 0 must implement and demonstrate:

1. An explicit, lossless raw-to-canonical importer preserving all 48 records and source pointers.
2. Taxonomy and record schema validation, decimal parsing, identities, references and readiness rules.
3. Reviewed page/coordinate mapping, site groups, splits and provenance manifests.
4. Recomputed numeric bands using whole relationships; non-numeric and unknown handling.
5. Runtime file-access isolation from ground truth and clean counterpart answers.
6. Small positive/benign fixtures for the first vertical slice and an injection-artifact inspection.
   A balanced, labeled fixture set is needed before claiming an artifact-only baseline is at chance.
7. A report of unresolved intake fields and coverage rather than fabricated ready records.

The existing tools/eval-format-tools package implements the old formatting assumptions.
It is not a version-2 validator, corpus importer, or working pipeline.
Align its paths, field order and validation boundary before using it on canonical version-2 files;
do not run it on raw corpus exports or take an empty default file discovery as a successful check.
Preserving YAML comments remains desirable; formatting is not semantic validation.

No current CI enforcement is claimed. Pin only dependencies actually used and review their code,
weights and transitive license obligations under the README constraint. A hard-coded license-name
denylist does not establish compliance. Optional analysis/export libraries need not be installed now.

## 9. Milestone 0 implementation profile (2026-09-09)

Version 2.0.0 now has an executable intake profile. The formerly proposed top-level record
contract is unchanged. The schemas specify the previously unspecified nested shapes:

- `review_notes` is an array of field, reason, reviewer, nullable UTC reviewed_at, and
  evidence_refs. A null top-level field and an `unknown` assessment need a field-specific reason.
- `propagation_sites: null` means unknown and accompanies `propagated: null`; `[]` means reviewed
  none and accompanies false. True requires linked locations. This explicitly clarifies the
  previously ambiguous nullable propagation representation; do not treat historical empty arrays
  as reviewed absence without evidence.
- Locations include nullable logical row/column keys, source anchors and an explicit nullable
  corrupted_endpoint flag. Anchors identify an inventoried artifact hash and PDF `page:N` pointer
  or JSON Pointer. Rectangles use `[x0, top, x1, bottom]`; page coordinate definitions belong to
  the mapping manifest. Unknown primary mapping remains null; candidate mappings stay proposed.
- Numeric relations use signed_sum, complete operands and independent_nearest rounding. Each
  operand has literal original/injected text, decimal values, coefficient, positive scale to
  the relation's common unit, rounding_step in the operand's displayed unit, role and location.
  Include at least one total operand. Record original and injected residuals as well as their
  difference. Unsupported policies remain pending instead of using an unjustified formula.
- The intake decimal implementation accepts plain decimal strings up to 1,000 characters and
  traps inexact arithmetic. It does not accept exponent notation, non-finite values or model-
  supplied normalization. Token parsing distinguishes missing, blank, dash and malformed values.
- Supporting artifacts have bundle/revision identity, nullable predecessor hash and revision
  reason. Initial artifacts use revision 1. Changed outputs require a new revision path; existing
  files are byte-idempotent and never overwritten by intake commands. A frozen grouping includes
  its complete edge/rationale record. Group IDs hash sorted component site IDs; splits use the
  scoring contract unchanged. Conservative whole-bundle grouping is explicitly labeled and its
  reduced statistical utility must be reported.
- Owner review decisions bind the exact proposed canonical record's content fingerprint with
  ingestion_status=pending, plus source, mapping and split file hashes. `approve` can promote only
  a fully validated record whose mapping is reviewed. A proposal or agent inspection is not an
  owner approval. Reviewer names are an audit trail, not cryptographic authentication.

Revision paths may append `.initial` or `.rN` to artifact filenames. Only the explicitly selected
record revision enters validation/evaluation; formatting may visit multiple retained revisions.
The source manifest remains the immutable observed inventory; correspondence inspection and later
attestations are separate, hash-linked review evidence, not an alteration of the original observation.

`eval-intake validate` returns success for structurally and semantically valid pending intake;
`--require-ready` additionally returns exit 3 when records remain pending. Invalid inputs return
exit 2. Publication status remains UNGATED: no intake command certifies later runtime, invariance,
or clean-run gates. Empty discovery is an error. Portable tests use synthetic sources; local source
hash and raw-record checks additionally require the explicitly selected immutable corpus.

The initial runtime consumer interface accepts one PDF, a list of native-artifact paths and empty
configuration. The evaluation harness checks that selected native artifacts belong to that PDF's
variant. It instruments Python file access in a fresh process, including resolved symlink targets.
This tests accidental answer access, not malicious code or native-library/subprocess containment.
Extend the probes to actual adapter, semantic prompt and detector modules when they exist.

Migration note: there are no pre-existing frozen version-2 scoring runs. The original intake
revision preserves unresolved metadata; subsequent mapping/proposal revisions retain all 48 IDs.
Legacy formatter tests and rules are replaced by this profile; raw files and archived contracts
are never reformatted. This clarification does not change category meanings or scoring bands.
