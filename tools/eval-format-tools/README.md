# Evaluation intake and formatting tools

Milestone 0 provides separate formatting, schema validation, source/semantic validation,
source inventory, deterministic import, frozen grouping, review packets and initial file-access
isolation. It does not implement a detector or certify headline scoring.

## Install and portable checks

From the repository root:

```sh
python3 -m venv tools/eval-format-tools/.venv
tools/eval-format-tools/.venv/bin/python -m pip install -r tools/eval-format-tools/requirements.lock
make -C tools/eval-format-tools PYTHON=.venv/bin/python check
```

The package can also be installed with `pip install -e tools/eval-format-tools`; installed entry
points are `eval-intake`, `eval-fmt`, and `fmt`. The lock pins the tested Python 3.13 dependency set.
`make check` runs formatting, schema-only checks, and synthetic tests without needing the private
corpus. The GitHub workflow runs that same portable target; it is not a publication gate.

## Local source-backed workflow

Set the module search path from the repository root when using the source checkout:

```sh
export PYTHONPATH=tools/eval-format-tools
tools/eval-format-tools/.venv/bin/python -m eval_intake inventory \
  --config eval/config/hkex-2025-48.sources.json --output eval/manifests/hkex-2025-48.json

tools/eval-format-tools/.venv/bin/python -m eval_intake validate \
  --manifest eval/manifests/hkex-2025-48.json \
  --locations eval/locations/hkex-2025-48.r3.json --splits eval/splits/hkex-2025-48.r3.json \
  --records eval/records/hkex-2025-48/corrupted.r3.jsonl \
  --review eval/reviews/hkex-2025-48/owner-approval.json

tools/eval-format-tools/.venv/bin/python -m eval_intake isolation-check \
  --manifest eval/manifests/hkex-2025-48.json --selection eval/config/runtime-inputs.example.json
```

`validate` rehashes selected source files and checks source pointers, taxonomy, mapping, frozen
assignment, numeric recomputation and readiness. Exit 0 means valid intake, which can contain pending
records; `--require-ready` returns exit 3 while pending records remain. Invalid inputs return exit 2.
All outcomes remain UNGATED because later publication gates do not exist here.

`import --config ... --manifest ... --output ...` creates pending records. Attach `--locations` and
`--splits` for the mapped revision and `--proposals` for selected complete proposed records. The current
revision uses `eval/reviews/hkex-2025-48/development-proposals.r3.jsonl` and
`--review eval/reviews/hkex-2025-48/owner-approval.json`. Unknown historical timestamps,
seeds and settings remain null with reasons. No raw file is changed.

`split-freeze --grouping ... --manifest ... --locations ... --output ...` applies the contract's hash.
A mapping-only revision uses `--previous`; it must preserve salt, bootstrap seed, assignments and
contract hashes. Existing outputs accept identical bytes only. Changed records/manifests use a new
revision path with predecessor/reason; neither command overwrites prior artifacts or rerolls a split.

## Review and promotion

The owner approved all four cases. Current records/mappings/splits are revision 3, with approvals
in `eval/reviews/hkex-2025-48/owner-approval.json` and the selected ready inputs in
`eval/reviews/hkex-2025-48/ready-development.json`. The following packet remains the immutable
pre-approval evidence; its pending labels describe its historical state.

Open `eval/reviews/hkex-2025-48/packet-r2/index.html` for four source-backed development proposals.
To replay that historical packet, use `review-packet` with the source manifest,
`eval/locations/hkex-2025-48.r2.json`, `eval/splits/hkex-2025-48.r2.json`,
`eval/records/hkex-2025-48/corrupted.r2.jsonl`, and
`--selection eval/reviews/hkex-2025-48/selection.r3.json --output <new-directory>`.
Omit `--review` for this pending snapshot. Despite its name, `selection.r3.json` binds split revision 2;
it must not be combined with current revision-3 inputs. Use `ready-development.json` to identify
current approved inputs, not as the historical packet selection argument.
`pdftoppm` must be available for rendering; it is an external review tool, not bundled into runtime.
Packets reject test/unassigned records before rendering. No network request or model call occurs.

The owner must review logical containers/endpoints, context, rounding, propagation and detectability.
The original four proposals had unresolved propagation and proposed mappings; the source-backed
review and explicit owner approval are now recorded in revision 3. For future promotions, create a mapping revision with the accepted
entries marked reviewed, preserve the split via a mapping-only revision, and create a review file
matching `schemas/intake_review.schema.json`. Each approval binds the SHA-256 content fingerprint
(`eval_intake.common.fingerprint`) of the exact pending proposed record plus manifest, mapping and
split file hashes. `import --review <file>` promotes approved records only after all validations pass.
Reviewer names are an audit trail, not authentication; never fabricate an owner's approval.

The evaluation-only `prepare_development.py` records manually chosen operand spans and reads amounts
from source characters using pdfplumber 0.11.9. It is not runtime code or an OCR adapter. It reuses the recorded review time for byte-identical replay; use a new revision and a recorded
review time for later changes rather than overwriting artifacts. PDF correspondence can be reproduced with
`python -m eval_intake.source_review --config ... --output <new-file>`.

## Formatting and boundaries

Default formatting discovery reads `spec/taxonomy.yaml` and `eval/records/**/*.jsonl`; empty discovery
fails. Explicit canonical files are accepted, but paths resolving into `corpus` are refused. Version 2
preserves Unicode and YAML comments/quotes, supports nested relationships and finite geometry, and
has no legacy dependency order or arbitrary nesting/line-length limit. Financial types and meanings
are schema/semantic checks, not formatting. Do not reformat frozen files: byte changes require an
explicit revision and updated provenance.

`audit_inputs` is the runtime-safe input interface. `eval_intake` contains evaluation-only code.
The initial consumer probe checks built-in, pathlib, io and os.open reads in a fresh Python process,
including symlink targets, with no unrestricted discovery. The harness additionally enforces native
artifact variant identity. This is accidental-access regression coverage, not a security sandbox or
proof about a future detector, native library, subprocess or prompt builder.

## Milestone 1 input migration

The runtime-safe `audit_inputs` package now lives under root `src/` with `hkex_audit`; it is no longer
packaged inside these evaluation tools. The Makefile supplies both source paths. For direct source
commands use `PYTHONPATH=src:tools/eval-format-tools` from the repository root, or install the root
runtime package separately before installing these tools. The legacy mandatory-PDF selection example
above is retained as history and is rejected by the new default interface.

Current native/IR selection and replay rules are in [the evidence contract](../../spec/evidence-contract.md).
`eval_intake.runtime_selection.project` produces a minimal native selection from an explicitly selected
inventory entry. It reads no PDF or raw record and copies no evaluator labels/operands. The strengthened
`isolation-check` probes the actual runtime guard; full adapter/consumer access traces and replay are
checked by root `make evidence-local-check`. That target requires selected native exports and the
ready-development handoff, but never reads PDFs or raw injector metadata.
