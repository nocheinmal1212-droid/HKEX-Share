# Evaluation Data Format Specification

**Bundle:** HKEX Annual Report Audit — Hang Lung Properties (00101.HK) error benchmark
**Spec version:** 1.0.0
**Status:** normative. CI enforces every rule marked **MUST**.

---

## 0. Reading this document

- **MUST** / **MUST NOT** — CI-enforced. A violating commit fails the build.
- **SHOULD** — enforced by review, not by machine. Deviations need a one-line justification in the PR.
- **MAY** — permitted, no obligation.

Two artifacts are hand-authored: `taxonomy.yaml` and `errors/**/*.jsonl`. Everything else in the
bundle is generated from those two by `make`. If you find yourself editing a generated file, the
generator is wrong — fix the generator.

---

## 1. Layer model

The bundle carries the same data in several formats. Each copy has exactly one purpose, one
producer, and one editability rule. Confusing the layers is the single most likely way this bundle
rots.

| Layer | Artifact | Format | Producer | Git | Hand-editable |
|---|---|---|---|---|---|
| **L1 Canonical** | `taxonomy.yaml` | YAML 1.2 | human | tracked | **yes** |
| | `errors/<bundle>/<variant>.jsonl` | JSONL | human + injector | tracked | **yes** |
| | `bundle.lock.json` | JSON | `make lock` | tracked | no |
| **L2 Contract** | `schemas/taxonomy.schema.json` | JSON Schema 2020-12 | human | tracked | **yes** |
| | `schemas/error_record.schema.json` | JSON Schema 2020-12 | human | tracked | **yes** |
| **L3 Machine** | `build/taxonomy.json` | JSON | `make json` | ignored | no |
| | `build/taxonomy_codes.py` / `.ts` | codegen enum | `make codegen` | ignored | no |
| | `build/errors.parquet` | Parquet | `make parquet` | ignored | no |
| **L4 Prompt** | `build/prompt/taxonomy_brief.txt` | pipe-delimited | `make prompt` | ignored | no |
| | `build/prompt/category_<code>.txt` | plain text | `make prompt` | ignored | no |
| **L5 Human** | `build/taxonomy.md` | Markdown | `make docs` | ignored | no |
| | `build/coverage.md` | Markdown | `make docs` | ignored | no |
| | `build/errors_review.xlsx` | XLSX | `make xlsx` | ignored | no |

### 1.1 Layer rules

- L3–L5 **MUST** be reproducible from L1 alone. `make clean && make` on a fresh clone reproduces
  every generated artifact byte-for-byte.
- Generated artifacts **MUST** carry a first-line or metadata banner:
  `GENERATED FROM taxonomy.yaml@<sha256[:12]> BY <tool>@<version> — DO NOT EDIT`.
- `build/` **MUST** be in `.gitignore`. If a downstream consumer needs a committed copy, commit it
  under `dist/` with a CI check that `dist/` matches a fresh `build/`.
- `errors_review.xlsx` exists so finance and audit reviewers can read the ground truth. It is a
  **view**, never a source. The previous arrangement (JSONL derived from `hksa_*.xlsx`) **MUST** be
  inverted before any other work lands, because a binary source of truth cannot be diffed, merged,
  schema-validated, or reviewed line by line.

### 1.2 Leakage boundary

Ground truth **MUST NOT** be reachable from any code path that builds an LLM prompt.

```
eval/
  errors/          <- ground truth. Read only by harness/ and tools/.
  base/            <- documents under test. Read by pipeline/ and harness/.
  taxonomy.yaml    <- read by everyone.
pipeline/          <- MUST NOT import from, glob into, or resolve paths under eval/errors/.
```

CI **MUST** run `tests/test_no_leakage.py`, which imports every module under `pipeline/` with a
filesystem shim that raises on any open under `eval/errors/`. A recall number produced by a pipeline
that can see the answers is not a measurement.

---

## 2. Universal encoding rules

Applies to every text artifact in L1 and L2.

- Encoding **MUST** be UTF-8 without BOM.
- Line endings **MUST** be LF. Enforce with `.gitattributes`: `* text=auto eol=lf`.
- Every file **MUST** end with exactly one trailing newline.
- Trailing whitespace **MUST NOT** appear on any line.
- Indentation **MUST** be spaces. Tabs are forbidden everywhere.
- Non-ASCII characters **MUST** be written literally, not as `\uXXXX` escapes. Company names and
  Chinese-language content appear in this corpus; escaping them makes diffs unreadable.

### 2.1 Identifier and naming conventions

- Field names: `snake_case`, ASCII, no abbreviations except the whitelist below.
- Enum values: `snake_case`, lowercase.
- Whitelisted abbreviations: `id`, `ocr`, `pdf`, `fy`, `ir`, `hk`, `sha256`.
- Identifier fields end in `_id`. Timestamps end in `_at` and are ISO 8601 UTC with `Z`.
- Counts start with `n_`. Booleans are affirmative adjectives or `is_` / `has_` prefixed; never
  negated (`is_detectable`, never `is_not_detectable`).
- Arrays are plural nouns. Scalars are singular.

### 2.2 Numeric rules

- **Monetary and any exactness-critical values MUST be strings holding a decimal literal**, e.g.
  `"12345.6"`, not `12345.6`. Rationale: JSON numbers are IEEE 754 doubles in most parsers, and this
  bundle exists to test arithmetic to the last digit. A footing check that fails because of float
  representation is an artifact you will spend a week misdiagnosing. Parse with `decimal.Decimal`.
- Counts, indices, and revisions **MUST** be JSON integers.
- `NaN`, `Infinity`, `-Infinity`, and leading-`+` numbers **MUST NOT** appear.
- Negative decimals use a leading `-`. Parenthesised negatives belong in the document, never in the
  ground truth.

### 2.3 Null semantics

Exactly one meaning each, **MUST** be observed:

| Encoding | Meaning |
|---|---|
| key absent | Not applicable to this record type. |
| `null` | Applicable, value genuinely unknown, and that is a recorded fact. |
| `""` | **MUST NOT** be used. Use `null` or omit. |

Example: `n_addends` is absent on a typography error (arithmetic is not applicable) and `null` on an
arithmetic error whose addend count could not be determined from a mangled table (applicable,
unknown — and that is itself worth knowing).

---

## 3. `taxonomy.yaml`

### 3.1 Why YAML here and JSONL there

The taxonomy is ~9 hand-authored prose-bearing entries reviewed by people. It needs comments,
readable multi-line strings, and whole-file review. YAML wins.

Error records are hundreds of machine-generated, machine-validated, independently-editable rows.
They need line-scoped diffs, streaming reads, shardability, and surgical single-record edits. JSONL
wins. Do not unify them.

### 3.2 File-level rules

- **MUST** begin with `---` on line 1.
- Indentation **MUST** be exactly 2 spaces per level.
- Sequences under a mapping key **MUST** be indented (not flush-left).
- Anchors (`&`) and aliases (`*`) **MUST NOT** be used. They do not survive JSON conversion legibly
  and they hide duplication from reviewers.
- Multi-line prose **MUST** use the folded-strip scalar `>-`. Single-line strings are unquoted
  unless they contain `:`, `#`, or leading/trailing spaces.
- Comments **SHOULD** be used, placed on their own line immediately above the block they annotate.
  Comments explaining *why* a category boundary sits where it does are the main reason this file is
  YAML.
- Categories **MUST** be ordered by pipeline dependency (dependencies before dependents), not
  alphabetically. The file then reads as the execution order.

### 3.3 Key order

Within each category, keys **MUST** appear in this order. The formatter enforces it.

```
code, revision, name, status, superseded_by, scope, description,
detection_strategy, depends_on, rounding_sensitive, requires_ir_features,
precision_target, recall_target, positive_fixtures, negative_fixtures, examples
```

### 3.4 Field contract

| Field | Type | Req | Notes |
|---|---|---|---|
| `code` | enum string | yes | Canonical key. `snake_case`. **Immutable once merged.** |
| `revision` | integer ≥ 1 | yes | Bump on any change to detection semantics. See §3.5. |
| `name` | string | yes | Human display name. |
| `status` | `active` \| `deprecated` \| `retired` | yes | |
| `superseded_by` | code | no | Required iff `status != active`. |
| `scope` | enum | yes | `financial_statements`, `cross_statement_and_notes`, `single_note`, `cross_notes`, `global`, `tables`, `cross_references`, `presentation`, `narrative`. |
| `description` | string `>-` | yes | Detection criteria, not marketing prose. |
| `detection_strategy` | `deterministic` \| `hybrid` \| `llm` | yes | Drives which checks the harness expects to fire. |
| `depends_on` | list[code] | yes | May be `[]`. Encodes the dependency graph — see §3.6. |
| `rounding_sensitive` | boolean | yes | If true, findings **MUST** carry a tolerance bound. |
| `requires_ir_features` | list[enum] | yes | e.g. `note_reference_column`, `row_hierarchy`, `cell_bbox`. Lets you compute up front which categories are blocked by IR gaps. |
| `precision_target` | decimal string | yes | Acceptance threshold on the negative corpus. |
| `recall_target` | decimal string | yes | Acceptance threshold on the positive set. |
| `positive_fixtures` | list[error_id] | yes | ≥ 1. CI checks each exists. |
| `negative_fixtures` | list[distractor_id] | yes | ≥ 1. CI checks each exists. |
| `examples` | list[string] | no | Human illustration only. Never consumed by code. |

`category_id` (the `ERR_SCREAMING_CASE` form) **MUST NOT** be stored. It duplicates `code` and will
drift. Generate it in `make json` if a consumer wants it.

### 3.5 Revision discipline

- Bump `revision` when the definition changes what counts as a hit: scope boundary moved, criteria
  tightened, a subtype reassigned to another category.
- Do **not** bump for typo fixes, `examples` edits, or `name` changes.
- Every scored result **MUST** be keyed on `(code, revision)`. The harness **MUST** refuse to
  aggregate or compare results across differing revisions and **MUST** say so loudly rather than
  silently averaging. Comparing a month-one number against a month-four number under a changed
  definition is the quietest way to fake progress.
- A `revision` bump **MUST** be accompanied by a row in `CHANGELOG.md` naming the affected
  `error_id`s.

### 3.6 Dependency graph

`depends_on` **MUST** form a DAG; CI fails on a cycle. It exists because categories interfere: a
dangling note reference breaks statement-to-note articulation, and a structural parse failure
manufactures phantom arithmetic errors. The harness uses this graph to attach
`upstream_failed: true` to findings whose prerequisites did not resolve, so a cascade counts as one
root failure rather than five independent misses.

### 3.7 Example entry

```yaml
---
spec_version: 1.0.0
taxonomy_version: 2.0.0
categories:
  # Runs before articulation checks: a broken reference invalidates any
  # statement-to-note reconciliation that resolves through it.
  - code: disclosure_reference_verification
    revision: 1
    name: Disclosure and Reference Verification
    status: active
    scope: cross_references
    description: >-
      Erroneous, dangling, or nonexistent cross-references to note numbers, page
      numbers, exhibits, or sections. A reference is in scope when it names a
      target that does not exist, or names a target that exists but does not
      contain the referenced subject matter.
    detection_strategy: deterministic
    depends_on: []
    rounding_sensitive: false
    requires_ir_features:
      - note_index
      - page_index
      - inline_reference_spans
    precision_target: "0.95"
    recall_target: "0.90"
    positive_fixtures:
      - ERR-00007
      - ERR-00019
    negative_fixtures:
      - DIS-00003
    examples:
      - Statement item references Note 15, but the disclosure appears under Note 16.
      - Table of contents cites a page number beyond the document extent.
```

---

## 4. `errors/**/*.jsonl`

### 4.1 File-level rules

- One JSON object per line. **MUST NOT** be pretty-printed. No blank lines. No comments (JSONL has
  none — use the `notes` field or a sibling `<variant>.notes.md`).
- Separators **MUST** be `,` and `:` with no spaces (`json.dumps(..., separators=(",", ":"))`).
- Records within a file **MUST** be sorted ascending by `error_id`.
- Soft line-length cap of 4000 characters. Exceeding it means the record is over-nested — split it
  into two records sharing an `error_group_id`.
- Nesting depth **MUST NOT** exceed 3 levels below the record root.

### 4.2 Sharding

One file per document variant: `errors/v2/var07.jsonl`. Reasons: merge conflicts stay local to a
variant; a single corrupt line costs one variant, not the bundle; and the harness can run one
variant without parsing the rest.

`errors/v1/legacy54.jsonl` holds the original 54 records, frozen. It **MUST NOT** be merged into v2
statistics.

### 4.3 Key order

Records **MUST** serialise keys in this fixed logical order — **not** lexicographic. Lexicographic
sorting is machine-canonical but scatters related fields across the line and makes hand-review
miserable. A fixed order enforced by the formatter gives the same diff determinism with none of the
readability cost.

```
schema_version, error_id, error_group_id, bundle, variant, status,
category_code, category_revision, subtype,
doc_id, location, secondary_locations,
original_value, injected_value, value_delta, unit, rounding_step,
n_addends, tolerance_bound, detectability_band,
injection_stage, injector_version, seed, propagated, propagation_sites,
split, expected_detectable, depends_on_error_ids,
description, rationale, notes, created_at, updated_at
```

### 4.4 Identity rules

- `error_id` format: `ERR-#####`, zero-padded to 5 digits. **MUST** be globally unique across the
  bundle, immutable, and **never reused** — even after retirement.
- Deletion is forbidden. Retire with `status: "retired"` and a `notes` explanation. A benchmark whose
  records vanish cannot be compared against its own history.
- `error_group_id` links records describing one logical injection that needed several rows.

### 4.5 Location addressing

`location` **MUST** be semantic, not positional. Line numbers and character offsets break the moment
the base markdown is regenerated with a different OCR version, and it will be regenerated.

```json
"location":{
  "table_id":"note_21_cash_and_cash_equivalents",
  "row_key":"bank_balances_and_cash",
  "column_key":"FY2024",
  "cell_content_hash":"sha256:9f2a1c...",
  "page":142
}
```

- `table_id`, `row_key`, `column_key` are canonical and survive re-extraction.
- `cell_content_hash` is a drift tripwire. `make verify` recomputes it against the base document and
  fails when the ground truth has silently detached from the corpus.
- `char_span` **MAY** appear as a convenience field. If present it **MUST** be regenerated by
  `make spans` and **MUST NOT** be hand-edited.
- `secondary_locations` is an array of the same shape, used for cross-articulation errors where the
  discrepancy has two ends. Order is `[the-side-that-is-wrong, the-side-that-is-right]` when known.

### 4.6 Rounding and detectability fields

Every record with `rounding_sensitive: true` on its category **MUST** carry:

| Field | Type | Definition |
|---|---|---|
| `unit` | enum | `HKD_million`, `HKD_thousand`, `HKD`, `CNY_million`, `percent`, `count`, `none` |
| `rounding_step` | decimal string | Smallest presented increment at the site, e.g. `"1"` for HK$m with no decimals. |
| `n_addends` | integer \| null | Count of components summing to the affected total. |
| `value_delta` | decimal string | `injected_value - original_value`, signed. |
| `tolerance_bound` | decimal string | `0.5 × rounding_step × n_addends`. Worst-case linear bound. |
| `detectability_band` | enum | See below. |

`detectability_band` **MUST** be computed, never hand-assigned:

```
|value_delta| <= tolerance_bound              -> "within_tolerance"
|value_delta| <= 2 * tolerance_bound          -> "boundary"
otherwise                                      -> "above_tolerance"
```

The harness **MUST** report recall per band and **MUST NOT** publish a blended figure. Records in
`within_tolerance` are excluded from headline recall and reported as a stretch set: no deterministic
check can separate them from legitimate rounding residue, and pretending otherwise sets a target that
can only be hit by destroying precision.

### 4.7 Provenance fields

- `injection_stage` — `pre_ocr_pdf` | `post_ocr_markdown`. **MUST** be present on every record. If
  the value is `post_ocr_markdown` for a `table_structural_integrity` or
  `formatting_typography_validation` record, the harness **MUST** emit a warning that the record does
  not exercise the real pipeline.
- `injector_version`, `seed` — **MUST** be present for machine-generated records, `null` for
  hand-authored ones. Together with `bundle.lock.json` they make the corpus regenerable.
- `propagated` / `propagation_sites` — real misstatements appear in several places. Records with
  `propagated: true` and a complete site list are undetectable by internal consistency alone and
  exist to define the ceiling, not to be scored as ordinary misses.

### 4.8 Split control

`split` **MUST** be `dev` or `test`, assigned once at generation time by hashing `error_id` against a
fixed salt so the assignment is stable and unarguable. Re-splitting after seeing results **MUST NOT**
happen. `expected_detectable` is a boolean the bundle owner sets deliberately; it lets you distinguish
"the system missed this" from "nothing could catch this".

### 4.9 Complete example record

Shown wrapped for readability. On disk this is **one line**.

```json
{"schema_version":"1.0.0","error_id":"ERR-00031","bundle":"v2","variant":"var07",
"status":"active","category_code":"statement_to_note_articulation","category_revision":2,
"subtype":"note_total_mismatch","doc_id":"00101_FY2024",
"location":{"table_id":"note_21_cash_and_cash_equivalents","row_key":"total",
"column_key":"FY2024","cell_content_hash":"sha256:9f2a1c4e","page":142},
"secondary_locations":[{"table_id":"consolidated_statement_of_financial_position",
"row_key":"cash_and_cash_equivalents","column_key":"FY2024",
"cell_content_hash":"sha256:11bd77a0","page":98}],
"original_value":"6420.0","injected_value":"6510.0","value_delta":"90.0",
"unit":"HKD_million","rounding_step":"1","n_addends":4,"tolerance_bound":"2.0",
"detectability_band":"above_tolerance","injection_stage":"pre_ocr_pdf",
"injector_version":"0.4.1","seed":178432,"propagated":false,"split":"dev",
"expected_detectable":true,"depends_on_error_ids":[],
"description":"Note 21 total inflated by 90; statement face left unchanged.",
"rationale":"Tests articulation without a collaborating footing error.",
"notes":null,"created_at":"2026-09-01T04:11:07Z","updated_at":"2026-09-01T04:11:07Z"}
```

---

## 5. Prompt rendering (L4)

`build/prompt/taxonomy_brief.txt` is the taxonomy re-rendered for LLM consumption. JSON in a prompt
spends tokens re-stating keys on every record and reads no better to a model than a delimited table.
Render pipe-delimited, one category per line, header row first:

```
code|scope|strategy|criteria
statement_to_note_articulation|cross_statement_and_notes|hybrid|Face-of-statement amount disagrees with the corresponding note breakdown total.
```

Rules:

- Fields containing `|` **MUST** be escaped as `\|`.
- Only `code`, `scope`, `detection_strategy`, and a one-sentence criteria line are included.
  `examples`, targets, and fixtures **MUST NOT** be rendered — they are review material and, in the
  case of fixtures, ground-truth pointers.
- Per-category files `category_<code>.txt` carry the full description for narrow, single-category
  prompts. Prefer these over the whole brief.
- JSON belongs on the LLM's **output** side, paired with constrained decoding against
  `schemas/llm_finding.schema.json`. Reminder from the architecture decision: that output schema
  **MUST NOT** contain any numeric value field. The model emits row keys, table ids, and concept
  labels; code reads the figures from the IR. Numeric hallucination then becomes structurally
  impossible rather than merely unlikely.

---

## 6. Analysis rendering (L3)

`build/errors.parquet` is the flat, columnar view for calibration work: rounding-residual
distributions, magnitude sweeps, per-band recall.

- Flatten `location` to dotted columns: `location.table_id`, `location.row_key`, ...
- Decimal-string fields **MUST** map to Parquet `DECIMAL(28,6)`, never `DOUBLE`.
- Arrays map to Parquet `LIST`; do not join them into strings.
- Include a `_source_line` column carrying the originating file and line number so any analytical
  finding can be traced back to a canonical record.

DuckDB reads the JSONL directly, so Parquet is an optimisation rather than a dependency. Build it
once the negative corpus makes scans slow enough to notice.

---

## 7. CI gates

`make check` **MUST** run all of these, and **MUST** be green before merge.

**Format**
1. `fmt --check` is idempotent on `taxonomy.yaml` and every `.jsonl` (formatter output equals input).
2. Encoding, LF, trailing newline, no trailing whitespace, no tabs.
3. Key order matches §3.3 and §4.3.

**Schema**
4. `taxonomy.yaml` validates against `schemas/taxonomy.schema.json`.
5. Every JSONL line validates against `schemas/error_record.schema.json`.
6. No `NaN`/`Infinity`; every monetary field parses as `Decimal`; no empty strings.

**Referential integrity**
7. Every `category_code` exists in the taxonomy with `status: active`.
8. Every `category_revision` equals the taxonomy's current revision for that code.
9. `error_id` unique bundle-wide; no reuse against `retired_ids.txt`.
10. Every `positive_fixtures` / `negative_fixtures` entry resolves.
11. Every category has ≥ 1 positive and ≥ 1 negative fixture.
12. `depends_on` is a DAG.
13. `depends_on_error_ids` resolve within the same variant.

**Semantic**
14. `detectability_band` matches the recomputed value from `value_delta` and `tolerance_bound`.
15. `tolerance_bound` matches `0.5 × rounding_step × n_addends` where `n_addends` is non-null.
16. `superseded_by` present iff `status != active`.
17. `injection_stage` present on every record.

**Corpus integrity**
18. `make verify` — every `cell_content_hash` matches the current base document.
19. `bundle.lock.json` matches the on-disk base documents and injector version.

**Safety**
20. `tests/test_no_leakage.py` passes (§1.2).
21. Cheater baseline: the surface-artifact-only detector scores at chance on every variant. A pass
    above chance means the injector is leaving a signature and every recall number in the bundle is
    inflated.

---

## 8. Tooling

Permissive licences only, per project guardrails. All of the following are compatible with a closed
codebase.

| Purpose | Tool | Licence |
|---|---|---|
| YAML round-trip preserving comments | `ruamel.yaml` | MIT |
| JSON Schema validation | `jsonschema` | MIT |
| Record models / codegen | `pydantic` | MIT |
| Parquet | `pyarrow` | Apache-2.0 |
| Analytical queries | `duckdb` | MIT |
| XLSX review export | `xlsxwriter` | BSD-3 |
| Exact arithmetic | `decimal` (stdlib) | PSF |

`PyYAML` is acceptable for read-only paths but **MUST NOT** be used by the formatter — it discards
comments, which is the reason the taxonomy is YAML at all.

Run `pip-licenses --fail-on="GPL;AGPL;LGPL"` in CI rather than trusting this table, including on
transitive dependencies.

---

## 9. Anti-patterns

Each of these has a specific failure mode, listed so the rule survives the person who wrote it.

| Don't | Because |
|---|---|
| Store `category_id` alongside `code` | Two names for one thing drift on the first rename. |
| Sort record keys lexicographically | Machine-canonical, human-hostile; §4.3 gets both. |
| Use line/char offsets as canonical location | Breaks on OCR re-run; you will re-run OCR. |
| Store money as JSON numbers | Float error is indistinguishable from the errors under test. |
| Delete a retired record | Destroys historical comparability of the benchmark. |
| Edit a `build/` artifact | The edit is erased by the next `make` and the divergence is silent. |
| Merge v1's 54 into v2 statistics | Different injector, different revisions, uncomparable. |
| Re-split dev/test after seeing results | Turns a measurement into a wish. |
| Put ground truth on a prompt-builder path | Produces recall numbers that are fiction. |
| Blend recall across detectability bands | Hides that the tolerance-band errors are unreachable. |

---

## 10. Migration from the current bundle

Ordered; each step is independently mergeable.

1. **Invert the xlsx dependency.** Convert `hksa_*.xlsx` to JSONL once, by hand-checked script.
   Archive the xlsx under `archive/`. Add `make xlsx` producing the review view.
2. **Split the taxonomy.** Move the current JSON to `taxonomy.yaml`; write the real
   `schemas/taxonomy.schema.json`. The current file's `$schema` key points at JSON Schema
   2020-12 but the file declares no `type`, `properties`, or `required` — validators pass it
   trivially, so today's taxonomy has the appearance of validation and none of the substance.
3. **Add operational fields** to each category: `detection_strategy`, `depends_on`,
   `rounding_sensitive`, `requires_ir_features`, targets, fixtures.
4. **Retrofit the 54 records** to schema v1 by hand. This is tedious and worth doing manually — the
   fields you cannot fill (`original_value`, `n_addends`, `injection_stage`) are exactly the
   ambiguities in the current ground truth, and a script would paper over them. Expect to go back to
   whoever generated the bundle for original values and site coordinates. If those cannot be
   recovered, §4.6 is unimplementable and the rounding problem stays unmeasured.
5. **Freeze as `errors/v1/`.** Add `retired_ids.txt`, empty.
6. **Stand up CI gates 1–13.** The rest follow once the injector and negative corpus exist.
```
