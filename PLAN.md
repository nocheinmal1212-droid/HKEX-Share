# Implementation Plan

**Revision 2 — closure reverified 2026-09-10. Milestone 0 complete: four owner-approved development records are ready.**
This replaces and retires the [previous plan](docs/archive/2026-09-09/PLAN.md).
The [current design](README.md), [scoring contract](eval/SCORING.md),
[format contract](eval/eval_format_spec.md) and [taxonomy](spec/taxonomy.yaml) govern this plan.
The initial proposal remains historical in [README.original.md](README.original.md).

Build one thin complete lifecycle, then extend coverage across the six scored categories.
Keep one batch application, one first extractor adapter, Gemini 3.8 Flash as primary semantic
interpreter and DeepSeek V4.1 Flash as a research-only comparison, deterministic verification,
and inspectable JSON/JSONL artifacts. The [README model policy](README.md#4-model-operation-and-licensing)
supersedes older model designations; preserve dated experiment records. The owner-approved
[2026-09-18 reconciliation](docs/model-policy-reconciliation-2026-09-18.md) closes model selection,
not runtime integration, source validation or Milestone 2.
Do not train a new OCR model or build storage/services/code-generation infrastructure for this PoC.

## 1. Ownership and current evidence

| Area | Owner | Reviewable handoff |
|---|---|---|
| Evidence and downstream contracts | Audit team with extraction-team input | Versioned schemas, validator, examples and capabilities |
| OCR selection, adaptation and adapter | Extraction team | Native artifacts, source correspondence, manifest and conforming IR |
| Interpretation, planning and verification | Audit team | Traceable plans, checks, findings and coverage |
| Context, relationships and benign cases | Domain reviewer with audit team | Reviewed development fixtures |
| Ground truth, splits and scoring | Evaluation owner | Canonical records, mappings, frozen split and scored report |
| Alert/runtime budgets | Review owner with evaluation owner | Dated values fixed before scored runs |

These are responsibility roles. The project user is the interim intake, domain-review, provenance,
readiness and budget owner; the current named assignments and next actions are in the
[readiness register](eval/reviews/hkex-2025-48/readiness.r5.json).

- [x] Reconcile design, scoring, format, taxonomy and taxonomy schema; archive superseded versions.
- [x] Confirm presence of clean/corrupted PDFs, 48 raw records, and both MinerU exports.
- [x] Establish the observed export metadata: VLM backend 3.2.2, 228 pages each.
- [x] Corroborate supplied/exported PDF correspondence through geometry, content, text and renders.
- [ ] If OCR deployment or end-to-end scope is reintroduced, confirm checkpoint/settings
  equivalence and extraction quality. Current work verifies native-to-IR preservation only.
- [x] Create canonical records, reviewed development mappings, group assignments and frozen manifests.

Delivery observations and completed intake do not establish a working detection pipeline.
The delivered records contain eight injections per scored category. No descoped records,
magnitude sweeps or reviewed negative collection have been established. Milestone 0 now records
a conservative frozen development assignment with four reviewed ready inputs and 44 pending records.

## 2. Milestone 0 — Intake and evaluation boundaries

Implement the minimum trustworthy intake; do not implement the whole detector here.

**Closure reverified 2026-09-10: complete under the minimum-intake exit below.** All 48 records validate:
four owner-approved development cases are ready and 44 remain pending. Approval fingerprints,
source hashes, propagation review and unchanged group/split assignments are recorded in
[closure evidence](eval/reviews/hkex-2025-48/milestone-0-closure.json) and
[fresh verification](eval/reviews/hkex-2025-48/closure-verification-2026-09-10.json).
See [review handoff](eval/reviews/hkex-2025-48/README.md) and
[owned readiness register](eval/reviews/hkex-2025-48/readiness.r5.json). One conservative group
remains development-only; no holdout or independent bootstrap clusters exist. The unchecked
extractor/model/budget items are owned follow-ups before relevant deployment or scoring claims;
closing intake does not mark those publication prerequisites complete.

### Sources and canonical records

- [x] Inventory and hash the original PDFs, raw error_detail.jsonl and both native exports.
  Record the distinct exported origin PDFs and verify their correspondence to the supplied sources.
- [x] Confirm page numbering and rectangle conventions across the delivery; visually review the
  selected development changes. The other records remain pending detailed domain review.
- [x] Implement schemas/error_record.schema.json and an explicit raw-to-canonical importer under
  the version-2 format contract. Preserve all 48 source records, original IDs/text and source pointers.
- [x] Separate active/retired lifecycle from pending/ready ingestion and scored/descoped scope.
  Represent unknowns explicitly; do not invent seeds, versions, geometry or numeric values.
- [x] Review selected development relationship operands, units, rounding precision and propagated effects.
  Compute tolerance including the total, bands from the net residual change, and reviewed
  expected_detectable. Keep non-numeric and unknown assessments distinct.
- [x] Create source mappings with stable evaluation IDs; record unresolved mappings explicitly.
  Do not assume native extractor IDs persist between runs.
- [x] Establish site_id and connected split_group_id assignments. Freeze the exact scoring-contract
  hash split, salt, grouping rationale and prior-exposure record before detector tuning.
- [x] Store manifests, records, mappings and splits separately from the immutable raw corpus.

### Boundaries and execution preparation

- [x] Appoint owners for pending metadata, fixture review and readiness decisions.
- [x] Define explicit detector input paths; implement an initial file-access isolation check and
  extend it when runtime code lands. Include corpus/error_detail.jsonl and clean-counterpart answers.
- [x] Align tools/eval-format-tools with canonical paths and version-2 field rules before using it.
  Add a nonempty-discovery check; formatting success must not masquerade as schema validation.
- [x] Validate the taxonomy against its schema and canonical records against their new schema;
  check references, IDs, scope/revisions, numeric recomputation and readiness semantics.
  Portable schema/synthetic checks and local source-backed validation have separate commands.
- [x] Select the first development fixture sites after split assignment; inspect injection artifacts.
  Record a small benign fixture plan instead of assuming that a negative dataset was delivered.
- [x] Freeze the evaluation bootstrap seed (`0`) separately from unknown historical injection seeds.

### Owned follow-ups — not minimum-intake exit blockers

The readiness register captures the available evidence, gaps, owner and next action. Completing
these prerequisites is required before the corresponding integration, deployment or scoring claim.

- [ ] If OCR deployment or end-to-end evaluation is reintroduced, complete extractor
  code/weights/backend licensing and settings review. Deferred from current frozen-artifact development;
  retain historical gaps. Review dependencies actually introduced by the adapter in Milestone 1.
- [x] Select OpenRouter for the provisional Gemini-primary / V4.1-research policy (2026-09-18).
- [ ] Integrate secure credential access and verify actual served identities, API capabilities and
  revision-pinning limitations for both configured roles. Historical probes do not implement this
  paired runtime boundary. Internal hosting is outside current API-only scope.
- [ ] Fix and date ALERT_BUDGET and RUNTIME_BUDGET before scored runs; alert counting already
  follows SCORING.md. Both budgets remain explicitly unset.

**Exit:** every supplied record is accounted for in validated canonical intake, including pending
records; reviewed development inputs have mappings and frozen groups/splits; provenance and isolation
checks work; unresolved publication items have named owners. Milestone 1 may use ready development
inputs while independent metadata or budget decisions remain open. Headline scoring remains blocked
until the selected population and all publication gates are ready.

## 3. Milestone 1 — Evidence contract, adapter and fixtures

**Confirmed implementation direction (2026-09-10):** adapt the existing MinerU outputs into a
versioned, validated and saved document evidence IR. Keep OCR/native translation and the main audit
pipeline in distinct layers, with the IR as their handoff. Downstream development and replay must run
without installing or rerunning MinerU. OCR work is excluded from current scope; use the supplied
clean and corrupted exports in separate runs. Treat selected native output as the extracted-evidence
source of truth; do not read raw PDFs or assess OCR quality. Validate native-to-IR preservation.
Missing evidence still blocks dependent checks. README section 3.1 owns this architecture decision. The planning-agent handoff is
[Milestone 1 intake prompt](docs/milestone-1-planning-prompt.md).

### Planning evidence and implementation boundary

Inspection on 2026-09-10 found only the Milestone 0 Python intake/formatting package and its
`audit_inputs` consumer probe. No evidence adapter, IR, semantic client or detector exists.
The portable `make check` passed all 26 tests. It validates 192 record instances across four
retained revisions, not 192 distinct injections. No new source-backed intake validation was run.

The source configuration and immutable inventory indexed the native files inspected; neither PDFs
nor raw injector records were opened. Both selected middle-JSON hashes match the inventory. Each
contains 228 sequential zero-based pages, native page sizes `[595, 841]`, and backend/version fields
`vlm`/`3.2.2`. These dimensions are not the reviewed PDFs' exact point dimensions.

Use `pdf_info[*].preproc_blocks` plus `discarded_blocks` as the first adapter's evidence view.
Each export has 132 page-local table regions containing 132 HTML strings and 6,415 HTML cells.
An exploratory span-occupancy check found no grid holes or overlaps; this is not fidelity approval.
`para_blocks` differs on page indices 122–127: it merges tables and deletes four later table bodies.
Consuming it alone would misattribute continued-table cells to earlier pages. Content-list exports
also use different coordinate scales. Do not combine those alternate views into duplicate facts.

Native captions, footnotes, page furniture, text spans, block boxes and HTML row/column spans are
available. Cell/character boxes, fonts and verified semantic headers are not. Some reference-currency
cells concatenate several numbers; some HTML cells contain images/equations. Image descriptions are
generated descriptions, not verbatim page text. Preserve these limitations explicitly.

**Milestone 1 accepted 2026-09-11 within R4’s limited native-evidence scope.**
Owner decision: [R4 approval](eval/milestone1/approvals/r4.owner-2026-09-11.json). Existing fixture
qualifications remain binding; OCR quality, detector performance and headline readiness are excluded. Evidence contract `1.0.0`,
independent of evaluation version `2.0.0`, is implemented with guarded ingestion, saved IR and
IR-only consumption. [The handoff](eval/milestone1/README.md) links the generated review packet
and verification summary. Both full native exports pass literal-pointer inventory, repeat ingestion
and isolated replay checks. Installed-wheel replay with its adapter directory unavailable is
historical evidence, not rerun by Task A. The original acceptance-era evidence/packet suite had
26 tests (19 original and seven review regressions); retained intake tests: 26. Current verification
is recorded in [Task A results](docs/milestone1-cleanup-results-2026-09-18.md). No semantic execution, detector, OCR or new
PDF fidelity approval is claimed. Existing intake approvals and frozen evaluation files are unchanged.
The planning observations above remain the pre-implementation baseline.

### 1. Establish the runtime package and contract skeleton

- [x] Add root `pyproject.toml`, `requirements-runtime.lock`, and `src/hkex_audit/` with
  `__main__.py`, `cli.py`, `contracts.py`, `evidence.py`, `artifacts.py`, `consumer.py`,
  `evidence_context.py`, and `adapters/mineru.py` plus `adapters/html_table.py`.
  Keep adapter imports lazy: IR-only consumption must not import even the local MinerU adapter.
- [x] Move the existing `audit_inputs` package from `tools/eval-format-tools/` to `src/audit_inputs/`;
  evolve `__init__.py` and `probe.py`, and add `guard.py`. Keep its import name, but replace the legacy
  mandatory-PDF selection shape. Update the intake package discovery, Makefile, README and tests to
  use the root source package. Do not leave a second competing input implementation.
- [x] Add `spec/evidence-contract.md` and schemas `evidence.schema.json`,
  `evidence_manifest.schema.json`, `audit_input.schema.json`, and `pipeline_artifacts.schema.json`
  under `schemas/`. The last contains separate definitions for annotations, plans, checks, findings
  and stage failures; it does not merge their persisted records. Package these exact schemas as
  runtime resources rather than maintaining copied definitions. Validate them with Draft 2020-12.
- [x] Use Python 3.13 as the tested execution baseline, standard-library JSON/hash/path/HTML tools,
  and existing `jsonschema==4.26.0` without extras. Pin its actual dependency closure using the
  already tested versions; record licenses, dependency edges, notice files and hashes in
  `docs/dependency-reviews/milestone-1.json`. Review binary/transitive notices as well as metadata.
  Do not pull `pypdf`, PDF review tools, MinerU, model SDKs or YAML formatting into runtime dependencies.
  Packaged MIT notices and native binary identities are recorded. Source-level Rust dependency
  closure for rpds-py remains unverified; no proprietary redistribution clearance is claimed.

### 2. Define identities, evidence and validation

- [x] Persist one `evidence.json` and `manifest.json` per selected document variant. Evidence contains
  document identity, ordered pages, blocks, text fragments, logical tables/cells, source fragments,
  capability assessments and unresolved regions. Every region is inventoried even if unreadable.
  Use explicit `available`, `unavailable` or `unknown` capability states with reasons and evidence;
  distinguish grid recovery from source fidelity and accounting completeness.
- [x] Preserve literal decoded JSON strings and complete raw HTML strings without Unicode
  normalization, trimming or numeric correction. Text fragments point to native JSON Pointers;
  HTML cell provenance adds half-open Unicode-code-point offsets into that exact HTML string.
  Retain entity spellings/markup in source fragments and map decoded text back to those spans.
  Keep individual text fragments ordered; any display separator is derived, not source text.
- [x] Cells have opaque IDs, zero-based row/column anchors, positive row/column spans, literal
  text fragments, content state and source references. Covered grid positions reference the anchor
  cell instead of creating extra occurrences. Empty cells, absent cells and unsupported content
  remain distinct. Dash and zero remain literal text; normalized amounts and parsing belong to
  Milestone 2. An absent row label stays absent, including the statement's unlabeled subtotal.
- [x] Derive source artifact IDs from SHA-256 bytes. Derive document evidence identity from the
  declared document/variant and selected artifact identities; derive occurrence IDs from that
  namespace, record kind and native pointer, plus the HTML anchor ordinal for cells. Never identify
  facts by amount, label, native `index` alone or evaluation IDs. Identity is stable for the same
  frozen input and identity-policy version, not promised across changed exports. Native indices
  remain provenance. Exact alternate-view aliases may be recorded without merging distinct occurrences.
- [x] Keep physical page index separate from literal printed-label fragments. Retain native page
  dimensions and boxes in their own named coordinate frame; units, origin and page rotation may
  be null with reasons until established. Native block `angle` does not establish PDF page rotation.
  Do not label the integer native dimensions as PDF points, infer character boxes, scale content-list
  boxes into this frame, or extrapolate printed labels. Missing geometry is valid evidence.
- [x] The manifest records schema/identity-policy versions, adapter version and code hash, selected
  input byte hashes, evidence output hash, configuration hash, engine/backend/version, nullable
  checkpoint/settings with reasons, and source-document hash with its supplied provenance status.
  Source PDF hashes are carried from preparation, never recomputed by runtime. Use immutable output
  directories; identical replay is accepted, changed outputs require a new directory/revision.
  Keep execution timestamps/timings in a separate run record so evidence bytes remain deterministic.
- [x] Reject duplicate JSON keys, non-finite numbers, unsupported schema versions, invalid identities,
  dangling/cross-document references, invalid text offsets, overlapping cell occupancy and invalid
  span dimensions. Unknown fields fail closed. Offline schema resolution must never fetch URLs.
  Native-pointer/text equality is checked during adaptation; IR-only validation checks embedded
  fragments and hashes without following provenance paths. It cannot independently re-attest native
  or PDF fidelity and must report that distinction.

### 3. Replace PDF-required selection and enforce access boundaries

- [x] Define a versioned discriminated selection: `mode: native` supplies one document/variant,
  its provenance descriptor and an explicit list of artifact role/path/hash entries; `mode: ir`
  supplies one evidence file and its manifest with expected hashes. The first native profile accepts
  exactly one selected middle JSON. Reject mixed modes, extra answer/configuration fields, missing
  files, duplicate selections, PDFs and unsupported artifact roles. Paths are resolved relative to
  the selection file by the launcher; worker inputs use validated absolute regular files.
- [x] Add evaluation-only `eval_intake/runtime_selection.py` to project the selected variant from
  the current source inventory into this minimal selection and bind its hashes. It must not copy
  record IDs, labels, mappings, split metadata, operands, counterpart paths or raw descriptions.
  Extend `eval_intake/isolation.py` and add separate native/IR selection examples; preserve the old
  example as a documented legacy fixture rejected by the new default interface. Record this local
  interface migration in the new contract/tool README, without editing hash-bound format contracts.
- [x] Run the actual adapter and IR consumer in fresh guarded Python workers. Allow only exact
  selected data files, explicit schema/code/dependency resources and designated new output files.
  Resolve paths and symlinked parents before checks; reject aliases into forbidden inputs. Deny
  all PDFs, injector metadata, evaluation artifacts, unselected native files and all other IR runs.
  Embedded provenance/image paths grant no read permission. Refuse output collisions with inputs,
  existing run artifacts and protected paths. Do not allow whole repository/corpus/site-package
  directories as blanket data-read permissions.
- [x] Extend real file-access tests across built-in `open`, pathlib, `io.open`, `os.open`, renamed
  files, symlink targets/parents and descriptor access. Deny runtime discovery, network calls,
  subprocesses and dynamic native loading after the reviewed bootstrap. Capture access attempts
  and stage failures. Treat this as accidental-access protection for the tested Python runtime,
  not hostile-code containment; review the preloaded dependency boundary explicitly.
- [x] `evidence_context.py` exposes only bounded, requested IR IDs and their literal evidence,
  captions/header candidates/context fragments and limitations. It accepts neither paths nor
  evaluator annotations. Test its actual serialized payload and all runtime imports/literals, not
  just the old dummy probe. Milestone 2 must repeat these checks on the real model prompt and
  request immediately before semantic integration; no nonexistent prompt/detector isolation pass.

### 4. Implement translation and persisted replay

- [x] Walk `preproc_blocks` and `discarded_blocks` once per page, preserving child order and native
  source pointers. Translate text/title/list/caption/footnote/page-furniture evidence. Keep image
  descriptions explicitly non-verbatim and image/chart/equation regions inventoried. Never load
  referenced images automatically. Preserve native merge hints as unverified provenance; keep
  continued table fragments on their physical pages without inferring continuation relationships.
- [x] Implement a bounded `html.parser.HTMLParser` adapter for explicit tables/rows/cells and
  row/column spans; preserve inline text/entity fragments. Require explicit consistent structure,
  rather than relying on HTMLParser's permissiveness to repair malformed tables. Mark image/equation
  content unresolved locally. Preserve surviving cells and raw fragments for incomplete grids;
  never fill missing cells, split concatenated financial tokens or infer semantic header roles.
- [x] Unsupported block kinds and recoverable malformed regions produce valid partial evidence
  with source-linked limitations. Unreadable/truncated JSON, invalid root/page identity or broken
  trusted provenance produces a stage-failure record and no accepted IR. Documented parser resource
  bounds are versioned configuration; limit breaches fail visibly rather than dropping content.
- [x] Expose `python -m hkex_audit ingest --selection <native.json> --output <new-directory>` and
  `python -m hkex_audit inspect --selection <ir.json> --output <new-directory>`. Ingest writes IR,
  manifest and structural validation/coverage; inspect uses only saved IR and writes an evidence
  inventory plus a bounded evidence-context example. Exit 0 is structurally valid evidence, possibly
  partial; exit 2 is invalid input/contract, exit 1 is execution failure. Neither command emits
  detector findings, scored results or a claim that missing evidence is correct.

### 5. Freeze the minimum downstream handoff, without executing semantics

- [x] Annotations reference existing occurrence IDs and evidence spans for concepts, roles,
  entity/scope, instant/duration, period, currency/scale and presentation basis. They record method,
  supporting references and explicit unresolved states. Model-origin annotations contain IDs and
  permitted labels/links only, not financial values, corrections, residuals or coefficients.
- [x] Comparison plans reference annotations and operands, permitted operation (`signed_sum` or
  `equality` initially), code-assigned signed coefficients, context requirements, relationship
  justification, completeness and tolerance-policy ID. Exact financial fields use decimal strings.
  Plans contain no generated code or computed answer. Runtime number parsing, relationship selection
  and arithmetic remain Milestone 2; do not import evaluator `numeric.py` into runtime.
- [x] Check/finding definitions satisfy SCORING.md's minimum fields, including source-addressable
  claims and evidence references. Preserve its five check states, local prerequisite states and
  separate stage failures. Direct checks permit null plan IDs; numerical findings require plans.
  Validate synthetic positive/negative contract examples and reference chains only. Leave check
  execution, opportunity enumeration, scoring and the findings UI for later milestones.

### 6. Prepare evaluator-owned fixtures and request concrete review

- [x] Add `eval/milestone1/prepare.py`, `validate.py` and `selection.json`. Resolve and verify
  `ready-development.json` before selecting its four records; never use historical packet selection
  as the current selector. Generate both native runs independently before the evaluator reads
  either set of outputs. Reviewed operands stay evaluator-only.
- [x] Write new `eval/milestone1/reviews/r1/` artifacts binding generated IR hashes, evidence spans,
  candidate IR-to-evaluation mappings, fixture expectations and review status. Do not alter the
  frozen r3 locations/splits or reinterpret their native candidates as approved IR links. Preserve
  ambiguous/unmapped results. Any later adoption into canonical evaluation needs a separately
  reviewed mapping revision, not a silent change to existing approvals.
- [x] Cover the four approved percent-token, reference, subtotal and statement-note cases using
  native page indices 158, 178, 179 and 184. Add page 186's property movement table as an unapproved
  roll-forward evidence candidate; pages 122–127 exercise continued tables, and page 158's separate
  reference-currency table exercises concatenated-token ambiguity. These page selections belong
  only in evaluator fixtures, never adapter rules. Do not review the remaining 44 error answers.
- [x] Add portable manually authored fixtures under `tests/fixtures/evidence/`: Unicode/entities,
  repeated occurrences, merged/continued tables, missing evidence, geometry-free pages, embedded
  images/equations, malformed grids and amount/name/order variations. Keep runtime inputs separate
  from expected annotations. Add six proposed benign/ambiguous fixtures under `eval/negatives/`
  following its existing PLAN: rounding, incompatible contexts, valid reference, valid negative
  style, valid percentage and ambiguous targets. Synthetic examples are labeled `fixture` mode.
- [x] Prepare an escaped static review report showing native text/HTML fragments alongside IR,
  logical cells, source pointers, capabilities and unresolved regions. Bind exact candidate hashes
  and record owner acceptance, rejection or requested corrections. PDF-derived review material remains historical and is not part of current acceptance.
  No new raw-PDF review or OCR quality assessment is in scope. Review native-to-IR preservation
  only; historical PDF review does not authorize new PDF reads. Prior intake approval approves no new fixtures.
  **Accepted native-only packet: eval/milestone1/reviews/r4/index.html; owner approval recorded 2026-09-11.**
  Independent review found r1 omitted fixture-byte/report binding, the supporting reference block
  and a displayed partial-table example. r2 preserves r1, binds exact fixture inputs/expectations
  plus rendered files with an outer approval fingerprint, and exposes both variants' selected
  regions, content states and limitations. `eval/milestone1/packet.py` verifies sealed bytes and
  original inputs; adoption must additionally match the separately recorded owner fingerprint.
  Six packet regressions and a complete temporary-copy mutation/replay probe verify the correction.
  R3 corrects the subsequently refuted source-wording claim: both source and native use 採用.
  It preserves r1/r2 and both audit originals, adds an explicit erratum and the saved targeted
  source inspection, and adds one regression for the evaluator-only text comparison. No native
  fixture value, qualified expectation, primary mapping or runtime code changed. At that R3 stage, owner review
  remained open; the second auditor's targeted PDF read was not repeated in r3 preparation.
  **Current boundary:** active preparation no longer loads historical images/PDF-derived text or
  performs their comparison. It validates selected native-to-IR preservation only. The historical
  comparison regression is replaced by a pre-open PDF/derived-asset/symlink rejection regression;
  the acceptance-era evidence suite had 26 tests. R1–r3 remain sealed historical artifacts.
  Task A subsequently hardens pre-open intake/original-input and symlink checks without changing
  those packets or the R4 approval; see its results for current test counts.

### 7. Demonstrate acceptance and reconcile milestone status

- [x] Add `tests/test_evidence_contract.py`, `test_mineru_adapter.py`, `test_evidence_replay.py` and
  `test_runtime_isolation.py`. Test lossless source spans, distinct IDs, grid occupancy against
  independently specified small examples, invalid references/versions, optional geometry, failed
  regions and whole-run failures. Mutation probes must reject changed hashes, shifted spans,
  duplicate IDs, overlapping cells and cross-variant file selection.
- [x] Adapt each full native document separately: account for all 228 pages and 132 inventoried
  page-local tables per artifact, reporting resolved/partial/unresolved counts. These are observed
  fixture expectations, not constants in runtime. Match every emitted literal fragment to its
  native pointer/slice. Review required accepted-case cells, surrounding context and omissions
  separately; a rectangular table alone does not establish source or relationship completeness.
- [x] Demonstrate byte-identical evidence on repeat ingestion; relocating identical selected files
  must preserve evidence IDs/content, while provenance/run-path metadata may differ. Saved-IR
  inspection must reproduce canonical inventory/context payloads with MinerU and the adapter
  unavailable and all native files/PDFs/evaluation files inaccessible. Reject incompatible versions
  before downstream processing. Repeat with each variant; attempts to use its counterpart fail.
- [x] Add root `Makefile` targets `evidence-check` and `evidence-local-check`, and extend
  `.github/workflows/intake.yml` for portable runtime tests. Preserve existing intake checks.
  `evidence-check` runs `PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v` and validates
  the new schemas/nonempty fixtures. `evidence-local-check` invokes `eval/milestone1/validate.py`
  on explicit selections in fresh temporary output directories; it reads native JSON and reviewed
  evaluation artifacts, never PDFs/raw injector metadata. Unreviewed fixtures are reported pending.
- [x] Record structural validation, native/IR fidelity review and replay/isolation as distinct
  evidence in the handoff. Claim no detector performance. Close Milestone 1 only after the interim
  owner accepts the concrete handoff and required fixture expectations; retain unresolved evidence
  with its consequences. **Structural/replay evidence and owner native-evidence/qualified-fixture acceptance
  are recorded. Milestone 1 is complete within that scope; headline scoring remains UNGATED.**

**First useful implementation slice:** steps 1–4 limited to one synthetic table and the explicitly
selected corrupted middle JSON. Produce page-local evidence, a source-span validator and an IR-only
inspection command under the access guard. Demonstrate the selected subtotal/table and percent-token
fragments without computing or identifying any discrepancy. Then broaden to the clean independent
run, alternate-layout fixtures, downstream schemas and owner review. This tests the principal
provenance/isolation risks before semantic integration.

**Commands already present:** from the repository root,
`make -C tools/eval-format-tools PYTHON=.venv/bin/python check` runs portable formatting/schema/tests
and passed during planning. `make -C tools/eval-format-tools local-check` exists for full source-backed
intake validation, but reads/hashes PDFs and raw ground truth; do not use it as the ordinary M1 native
test command. The evidence targets and CLI above are now executable; full outputs are saved under runs/milestone1-r1/.

**Owner dependencies and defaults:** an agent can implement the contracts, adapter, isolation,
fixtures and review report without further architectural approval. The owner must accept newly
generated IR correspondence and fixture labels before the reviewed-handoff exit. Alert/runtime
budgets and independent holdout evidence are later scoring decisions, not M1 blockers. Second-engine
samples and OCR provenance/deployment licensing remain deferred; adapter dependency review is not.

No M1 model call is needed. At the start of Milestone 2, before semantic integration, check only
whether `OPENROUTER_API_KEY` is available; never print or persist it. Use the selected OpenRouter
base URL and exact primary/research identities in README section 4. Before live integration,
freeze bounded checks of output constraints, valid/invalid ID handling and served identity for each
role; reuse historical evidence without representing it as fresh availability. Cap calls, time and
output tokens; preserve observed routing and unknowns. Primary unavailability blocks operational
interpretation; research unavailability is logged separately and cannot promote another model.
Credential provision is owner input only if absent. No new calls are scheduled by this plan.

**Exit:** accepted versioned evidence handoff, independently traceable native-to-IR examples,
countable limitations and demonstrated IR-only downstream consumption without MinerU or PDFs.
All 48 intake records and their frozen hashes/splits remain intact; headline scoring stays UNGATED.

## 4. Milestone 2 — First complete lifecycle

The 2026-09-19 [bounded execution correction](spec/paired-semantic-attempts-1.2.md) and
[successor preparation](docs/semantic-citation-deadline-correction-results-2026-09-19.md) address the
total-time blocker only. Live execution requires separate explicit approval. Saved-IR semantic
acceptance and all remaining M2 exit conditions remain open; no checkbox is completed here.

- [x] Close the bounded model-selection investigation with the owner-approved provisional policy
  (2026-09-18). The dated history below remains evidence, not current model-selection instructions.
  [Independent comparison](docs/independent-model-selection-results-2026-09-17.md) and
  [Flash follow-up](docs/flash-context-check-results-2026-09-17.md) support a limited development
  decision; no production model, cascade or complete semantic pipeline was validated.
  **2026-09-11:** the [probe harness and observed result](docs/openrouter-probe.md) are implemented.
  Access succeeded; OpenRouter reported the exact requested model via Ionstream. The valid-ID
  example unexpectedly abstained, so capability acceptance remains open and semantic integration
  is blocked pending investigation. The second case was not called; no model was substituted.
  **2026-09-15:** owner-approved [isolated hypothesis fixtures](docs/experimental-fixture-results-2026-09-15.md)
  executed (146 calls; DeepSeek/GLM subjects, Gemini oracle). The shared explicit strict prompt
  passed core/repeated controls on primary DeepSeek routes; GLM still has an explicit-prompt
  decision failure and service gaps. These are synthetic diagnostics; production integration and
  acceptance of the selected semantic configuration remain pending.
  **2026-09-16:** approved [interface-boundary experiment](docs/interface-boundary-results-2026-09-16.md)
  executed all 180 attempts. Pro/Fireworks passed existing explicit wording 30/30; concise wording
  passed 26/30 (two unexpected abstentions, two truncations). V4.1 Flash extension passed both
  arms 30/30; existing V4 Flash returned 60 HTTP 429 errors, leaving its comparison unassessed.
  Eleven offline boundary fixtures passed, including the deliberate semantic-error limit.
  The boundary remains experimental; production integration and selected-configuration acceptance
  are still pending. Retain explicit wording as the current candidate.
  **2026-09-17 UTC independent review:** [raw-record review and implementation decision](docs/model-interface-independent-review-2026-09-17.md)
  confirm those counts, all 90 prompt-only pairs, and exact replay of both dated fixture evaluations;
  55 portable tests pass. Keep B0 for lexical diagnostics and carry the deterministic behaviors
  into the first real semantic operation. Do not promote the unbounded lexical helper into runtime:
  selected-evidence provenance, operation-specific prerequisites, dispatch and persisted outcomes
  must be implemented together. Define that operation and its reviewed sufficiency/failure fixtures
  next. Existing-Flash availability remains a separate comparison question, not a Pro integration
  prerequisite. No production semantic path or milestone acceptance is claimed by this review.
  **Owner response: approved (2026-09-17 UTC).** Approval applies to the review's decisions,
  including deferred production integration. The next [direct-contributor fixture proposal](docs/direct-contributor-fixture-proposal-2026-09-17.md)
  now specifies one operation, 14 logical interpretation cases, and 20 unexecuted dispatch/failure
  scenarios with separate evaluator expectations. These new exact labels remain proposed;
  preparation checks are not model results or integration tests. Resolve the semantic-attempt
  record separately from the frozen M1 schema-hash inventory before implementing persistence.
  **2026-09-17 authorized fixture execution:** [results and verdict](docs/direct-contributor-results-2026-09-17.md)
  record 30/30 offline subcases/controls across 20 boundary scenarios, four detected implementation
  mutations, an isolated logical-source replay, and 61 passing portable tests. The 42 frozen
  Pro/Fireworks attempts yielded 31 full passes, one wrong relationship, five timeouts and five
  truncations. S11 ambiguous scope has no pass; S08 period conflict has no usable answer. Retain
  the diagnostic suite; do not accept this configuration for production. The new dispatcher is
  experimental and consumes logical fixtures, not production IR. Live transport and stubbed
  persistence remain separate tests; real IR integration, source-amount invariance and independent
  expectation review are still open. M1 schema hashes and previous fixture/run evidence are intact.
  An additional late-write persistence probe **failed**: dispatch reports persistence failure
  after result bytes are written, but replay accepts that leftover result. The original D16
  injections fail before writing and miss this case. The defect remains unresolved; extend
  persistence tests and define commit/completion semantics before promoting the dispatcher.
  **2026-09-17 subsequent persistence fix:** the [versioned v2 completion protocol](docs/direct-contributor-persistence-fix-2026-09-17.md)
  now rejects leftover result bytes without a valid hash-bound completion record. All 42 new
  write-timing cases and 72 total tests pass, with isolated replay verified. Completion-publication
  errors are explicitly `commit_unknown` until replay resolves them. Frozen v1 evidence remains
  unchanged; new experimental persistence work uses v2. This fixes the observed defect without
  claiming production integration or resolving the semantic experiment's remaining failures.
  **2026-09-17 first connected live v2 check:** [results](docs/direct-contributor-live-v2-results-2026-09-17.md)
  record 14/14 ordinary live outcomes committed and replayed, plus a correctly incomplete
  injected late-write attempt. Two usable Pro/Fireworks responses (S03 selection, S04 abstention)
  match frozen expectations; the other twelve ordinary cases and the fault probe receive upstream
  HTTP 429. The live fault therefore covers an HTTP error response, not a successful model answer.
  All 77 tests pass. This verifies the logical-fixture live path, not production IR or the full
  audit lifecycle; rate-limited cases remain unavailable rather than semantic passes.
- [x] Implement one selected-IR direct-contributor **header** operation with independent Gemini
  primary / V4.1 research attempts, role-bound completions, separate artifacts, guarded operational
  replay and primary annotation/provenance persistence. Additive attempt version 1.0.0 preserves
  frozen M1 and experimental v2 schemas. See [Task B results](docs/paired-semantic-integration-results-2026-09-18.md).
- [x] Prove research noninterference at the implemented annotation/provenance boundary, including
  persisted failure matrices, interrupted/late writes, promotion fault injection and synchronized
  stalled research. Plans/checks/findings remain unimplemented, so their future isolation is not proved.
- [ ] Close saved-IR semantic acceptance: four live primary selections match the frozen source-only
  agent review, but all four omit its required unit citation. Research has zero usable answers from
  four calls (three truncations, one invalid abstention). Retain this failed acceptance gate; a new
  contract/prompt version and separately bounded confirmation are the next step, not silent rescoring.
- Offline correction 1.1 implements [conditional support and source prerequisites](spec/semantic-operation-1.1.md)
  with a separately reviewed finite sibling-summary rule and [pinned role-scoped v1 replay](spec/paired-semantic-attempts-1.1.md).
  This is exposed development evidence, not closure of the acceptance item above. No live budget is
  authorized; future confirmation requires separately frozen bindings and expectations.
- The approved [nested presentation correction](spec/header-source-analysis-1.0.1.md) fixes the
  independent review's P2 partition defect with separately frozen regressions and analysis-bound
  runtime identities. [Offline results](docs/semantic-citation-partition-correction-results-2026-09-19.md)
  preserve prior artifacts and do not close semantic acceptance or authorize confirmation calls.
- [ ] Parse numbers using exact decimals, preserving raw text, parse status and rounding precision.
- [ ] Resolve explicit contexts and known vocabulary deterministically.
- [ ] Implement the [provisional paired-query plan](docs/model-policy-reconciliation-2026-09-18.md#provisional-implementation-plan--not-implemented-by-this-reconciliation)
  for unresolved concepts, roles and links: Gemini primary, V4.1 research only, independent bounded
  attempts with linked source/contract identity and independently hash-bound completion records. Outputs refer to permitted
  IDs/labels, not financial amounts, corrected values or computed answers.
- [ ] Verify that changing research responses or failures cannot change accepted primary annotations,
  plans or findings; primary failures never promote research answers. Verify file-access isolation,
  separate primary/research completion and explicit incomplete-pair accounting.
- [ ] Validate the integrated policy on a small independently reviewed selected-IR slice, including
  compatible/incompatible context, positive/missing-evidence controls and amount invariance.
  Keep source correctness separate from agreement; do not reopen model selection automatically.
- [ ] Validate response schema, referenced IDs and contexts; bound retries and record failures.
  Cache accepted responses by complete input/model/prompt/schema/configuration identity.
- [ ] Construct signed-sum and context-compatible equality plans from independently supported
  relationships. Prohibit amount matching, subset-sum search and benchmark-authored operands.
- [ ] Add direct evidence-based token/reference checks.
- [ ] Implement interval tolerances and the common opportunity ledger:
  passed, failed, abstained, not_applicable, crashed.
- [ ] Persist checks, linked findings, derived abstentions, unresolved opportunities and coverage.
  Present a simple findings table; a failed equation does not automatically identify the wrong cell.
- [ ] Run fixture and frozen_ir paths with clearly separated claims. Keep pdf_end_to_end deferred
  unless OCR/end-to-end scope is explicitly reintroduced and its provenance prerequisites are met.
  Implement minimal contract matching and diagnostic reporting for the vertical slice.

**Exit:** one command completes evidence intake → annotations → plans → checks → findings →
diagnostic evaluation on representative cases. A deliberate ambiguity abstains, an execution failure
is visible, and frozen-artifact replay reproduces canonical downstream results.

**Decision point:** re-estimate effort using observed extraction, semantic and relationship gaps.
Fix contract deficiencies before expanding coverage.

## 5. Milestone 3 — Arithmetic and contextual consistency

- [ ] Extend additive, roll-forward, matrix, comparative and maturity patterns as fixtures require.
- [ ] Implement primary-statement and internal-note checks over supported relationships.
- [ ] Handle nested totals, memo rows, transfers, contribution signs and missing contributors.
- [ ] Preserve instant/duration, group/parent, currency/scale and restatement/presentation contexts.
- [ ] Implement document-wide consistency only across compatible contexts; retain source occurrences.
- [ ] Validate rounding policies on clean development cases without tuning tolerance to suppress alerts.
- [ ] Verify that changing amounts does not change structurally justified operand selection.

**Exit:** supported relationships have reviewed completeness; unsupported cases abstain.
Failure in both comparative periods does not automatically invalidate a table. Coverage accompanies
misses, and extraction limitations are not treated as source-document structural findings.

## 6. Milestone 4 — References, typography and statement-note links

- [ ] Build note and printed-page indexes, retaining literal source references.
- [ ] Detect dangling references and supported wrong-but-existing targets.
- [ ] Implement raw-token checks with local conventions and declared evidence needs.
  Do not infer font/glyph anomalies from normalized text alone.
- [ ] Match statement lines to note facts through concept/context filtering and bounded ID selection.
- [ ] Use bounded alternative-note search for suspect references without silently replacing them.
- [ ] Exercise ambiguity, restated comparatives, multiple totals and legitimate style differences.
- [ ] Complete small positive/benign fixtures for every scored category.

**Exit:** all six scored categories have implemented paths and explicit abstention conditions.
Matching never chooses a fact simply because its amount agrees. The three descoped vocabulary
categories acquire no dedicated detector work.

## 7. Milestone 5 — Generalization and replay

- [ ] Implement the six scoring-contract invariance transforms and exemptions.
  Preserve rounding precision under rescaling and map canonical claims with multiplicity.
- [ ] Label IR versus PDF test coverage; a missing required transformation is not a pass.
- [ ] Add useful randomized synthetic relationships/corruptions, grouping related variants.
- [ ] Probe a few unfamiliar issuer tables separately; record vocabulary/pattern additions and
  check-code changes without claiming market-wide calibration.
- [ ] Verify literals, runtime file-access isolation and frozen evaluation configuration.
- [ ] Exercise malformed/truncated responses, unknown IDs, ambiguous evidence and failed stages.
- [ ] Demonstrate deterministic artifact replay; report fresh-call sensitivity separately.
- [ ] Verify primary/research isolation and configuration-bound replay across the integrated
  semantic path. Any future API route change needs a separately frozen comparison; local model
  serving and weight downloads remain outside current scope.

**Exit:** declared invariance and isolation gates pass, with supported layers and limitations stated.
Freeze only after fixes found here have been validated.

## 8. Milestone 6 — Frozen evaluation and extraction handoff

- [ ] Freeze code/configuration, prompts, vocabulary, patterns, models, extraction and manifests.
- [ ] Verify optimal one-to-one category-neutral assignment, L1/L2 preference, ties, paired endpoints,
  stretch/exclusion/descoped tiers, surplus relationships and whole/partial crash behaviour.
- [ ] Confirm all selected records are ready and modes/source mappings are comparable.
- [ ] Execute complete clean and corrupted runs with the required attested extraction provenance.
- [ ] Evaluate the declared split without lexicon updates or tuning on its outcomes.
- [ ] Report separate above-tolerance, boundary and non-numeric recall; within-tolerance stretch;
  coverage, miss reasons, raw clean alerts and exclusions/pending counts.
- [ ] Report split-group bootstrap uncertainty with record/site/group counts and small-sample limits.
- [ ] Publish headline recall only when intake, literals/isolation, invariance and the clean-alert
  gate pass. Retain UNGATED results and failures as diagnostics.
- [ ] Deliver replay instructions, source-to-finding examples, adapter contract/capability evidence,
  remaining extraction issues and a measured extension-effort estimate.

**Exit:** the complete lifecycle is demonstrated with bounded, reproducible claims.
Any tuning after held-back feedback is recorded as exposure; the same bundle is no longer an
untouched holdout. Missing budgets or provenance are unresolved gates, not implicit passes.

## 9. Verification and effort discipline

Prioritize silent-error risks: token fidelity, spans/references, numeric parsing, contributor
completeness, contextual compatibility, rounding boundaries, wrong-note selection, source mapping,
matching, missing evidence, leakage and invariance.
Use reviewed fixtures and useful properties rather than tests that merely mirror implementation.

Do not add OCR fallbacks, fine-tuning, another adapter or infrastructure without a measured need.
Track audit-team effort, extraction-team effort and integration waiting time separately.
Re-estimate after Milestone 2; the historical estimate is not a commitment for this revised plan.
