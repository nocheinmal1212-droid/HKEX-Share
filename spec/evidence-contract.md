# Document evidence contract

Version **1.0.0**, identity policy **1**. These are executable Milestone 1 interfaces, independent
of the frozen evaluation format/scoring version 2.0.0. README section 3.1 owns the architecture;
PLAN owns milestone status. Schemas in `schemas/` own wire fields and required/nullability rules.

## Selection and execution

`audit_input.schema.json` accepts `native` and `ir` modes. Both declare one document/variant and
source provenance. Native mode selects exactly one `middle_json` role with an explicit path and
SHA-256. IR mode selects evidence and manifest files with expected hashes. The evaluator-owned
projection can copy the selected source PDF hash from the inventory without opening the PDF.
That hash is supplied provenance, not runtime attestation of the PDF or variant semantics.
Native artifacts do not independently identify their variant: the caller must use a trusted
selection. The evaluation launcher verifies membership against the frozen inventory.

The obsolete `{pdf, native_artifacts, configuration}` interface is rejected. The historical example
remains preserved, but current commands require a versioned selection. Relative paths resolve against
the selection file. Final data paths must be regular files with no symlink components; PDFs,
evaluation paths and credentials are forbidden. File contents resembling a renamed PDF also fail.
IR provenance/image paths are inert identifiers and are never followed.

Run from the repository root with Python 3.13 and `PYTHONPATH=src`:

```sh
python -m hkex_audit ingest --selection <native-selection.json> --output <new-run-directory>
python -m hkex_audit inspect --selection <ir-selection.json> --output <new-replay-directory>
```

Every CLI invocation requires a new output directory. This is deliberately stricter than the low-level
byte-idempotent artifact writer: execution timing records are immutable too. Exit 0 means structurally
valid evidence, possibly partial; exit 2 means invalid input/contract; exit 1 means execution failure.
Accepted ingestion outputs evidence, manifest, inventory, bounded context and an execution record.
Stage exceptions persist `stage-failure.json` and a failed run record; launch failures report on stderr.
An absent successful run record must not be interpreted as completed ingestion.

Before source reads, a fresh worker preloads its selected code/schema/dependency resources and installs
an exact-file Python audit guard. Runtime permits only selected data reads and named output writes.
It denies discovery, unselected reads, external execution, network and subsequent dynamic library
loading. The launcher uses an isolated interpreter and closes inherited nonstandard descriptors.
Preloaded Python/native dependencies, ordinary Python memory access and raw `os.read` on already-open
descriptors remain trusted. This is tested accidental-access isolation, not hostile-code containment.
Actual access logs contain selected paths and denied-operation reasons, not forbidden file contents.

## Evidence and identity

`evidence.schema.json` defines ordered pages, a flat parent-linked node inventory, source fragments,
capabilities and limitations. Page/block/table/cell identities are opaque hashes, not semantic names.
Document identity hashes the declared document provenance and selected artifact identities. Source
artifact identity is its SHA-256. Occurrence identity hashes identity-policy version, document ID,
kind, native pointer and optional HTML anchor ordinal. A source fragment's identity hashes artifact
identity and its native pointer. Paths, timestamps and numerical agreement never select identity.

Identical relocated native bytes retain evidence identities and content. A changed export has a new
artifact/document namespace; stable identities across extraction revisions are not promised. Distinct
source occurrences remain distinct even when their text agrees. Cell anchors are enumerated once;
rowspan/colspan coverage does not create duplicate cells. Evaluation mapping remains outside runtime.

Literal JSON text and complete native HTML are preserved without trimming, Unicode normalization or
source correction. Text fragment offsets are half-open Unicode-code-point indices into a source string.
HTML entities have explicit decoding markers; the original spelling remains in the source string.
Each logical cell also has a complete markup span, including empty cells. Joining text fragments adds
no whitespace. Layout/discretionary line separators belong to presentation, never raw source fields.
A blank cell has empty text; an absent or unsupported cell is not fabricated. Dashes, zero and malformed
financial tokens remain literal. Numeric parsing and all exact-decimal arithmetic are Milestone 2.

The observed MinerU profile is VLM 3.2.2 middle JSON. It translates `preproc_blocks` and
`discarded_blocks`, including nested text and page furniture. Paragraph-view differences are recorded;
its cross-page merges do not move page-local cells. No second-engine or cross-version compatibility
is claimed. Generic downstream code uses this IR, not alternate MinerU fields or an installation.

Native page sizes/boxes remain in a named native frame. Units, origin and page rotation are unknown
unless supported; block angle is separate. Printed labels are literal evidence references, never
extrapolated from physical indices. Cell/character geometry, fonts and semantic headers are unavailable
or unknown. Generated image descriptions, charts/equations and unsupported inline content are labeled
and cannot enter the ordinary literal text context payload.

The conservative HTML parser supports explicit table/row/cell structure, spans and common inline text
markup. Images/equations stay in raw HTML with local unsupported status. Broken structure, invalid
spans and overlap yield unresolved grids without repaired cells; rectangular holes preserve surviving
cells with a partial grid. Native source fragments retain the unaccepted content. Concatenated numeric
tokens are never split. Parser bounds: JSON 64 MiB, HTML 2,000,000 characters, 50,000 cells per HTML
body, 500,000 occupied grid positions and native depth 64. Limit breaches fail the stage visibly.

## Validation and replay

The manifest binds evidence bytes, selected inputs, adapter code/version, schema definitions,
configuration, producer metadata and nullable checkpoint/settings with reasons. Timestamps and timing
live in the run record. Schemas resolve offline. Unknown fields, duplicate JSON keys, non-finite values,
unsupported versions, dangling IDs, parent cycles, invalid spans and overlapping grids fail validation.
Native adaptation additionally verifies all persisted source fragments against their original pointers.
An independent evaluator check compares the complete native literal-pointer inventory with IR sources.
IR-only validation verifies embedded fragments, identities and manifest hashes without native reads.
The loader currently requires exact schema-definition hashes; compatibility changes require an explicit
new contract/migration rather than silently accepting an unknown revision.

The inventory counts all detected table regions, resolved/partial/unresolved grids and limitation
regions. A resolved grid means recovered HTML occupancy, not faithful PDF extraction, complete
accounting relationships or a correct report. Detection opportunities/check states are not fabricated
at this stage. Missing table detection requires independently reviewed fixtures; the native inventory
alone cannot measure what the extractor omitted. `native_fidelity` describes literal transfer only.

## Downstream interfaces and review boundary

`pipeline_artifacts.schema.json` defines separate annotation, plan, check, finding and stage-failure
records. `pipeline_contracts.validate_bundle` checks identities and cross-record references without
executing them. Model annotations allow labels/links/support IDs only; supplied permitted vocabulary
is required for model label validation. Plans contain referenced operands, code-assigned decimal
coefficients, allowed operation, justification, completeness and tolerance policy. Arithmetic is absent.
Check states and finding requirements follow SCORING.md; accepted category codes must come from the
canonical taxonomy. Fixtures cannot grant runtime access to evaluator-owned operands.

The bounded evidence-context builder selects existing node IDs, literal fragments and limitations;
it accepts no file paths or evaluation records. It is not a model prompt. Real prompt/request isolation
and the selected OpenRouter model capability probe must be tested when Milestone 2 implements them.
The evidence-only commands require no credential; the additive live semantic entry point below uses the environment-only credential boundary.

New IR mappings and benign/ambiguous fixture labels require owner acceptance of the exact review
packet fingerprint. An existing approved evaluation record is not approval of generated evidence.
`eval/milestone1/` contains these proposals and review tools; `runs/` contains local runtime artifacts.
Neither updates frozen records, mappings, splits or approvals. Headline status remains UNGATED.

## Additive semantic integration (2026-09-18)

The selected-IR [paired semantic interface](paired-semantic-attempts.md) now implements one
bounded header relationship operation. It uses the existing annotation wire contract unchanged,
with a separately versioned provenance companion and independent role-bound completion records.
It adds a narrow transport subprocess; the existing evidence workers remain network-denied.
No schema hashes, scoring semantics, M1 approvals or historical attempts are migrated.
