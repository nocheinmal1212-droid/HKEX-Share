# Task A results — committed Milestone 1 foundation

Task A reconciled and committed the pending Milestone 1 work. The existing September 11 R4
acceptance remains limited to native-to-IR preservation and qualified fixtures. No new acceptance,
OCR assessment, model experiment, detector result or publication gate is claimed. No raw PDF or
credential was opened; no OCR ran. Gemini 3.8 Flash primary / DeepSeek V4.1 Flash research-only
through OpenRouter remains the closed model policy, with no automatic fallback.

The stable implementation/evidence/guidance boundary is
**`88608d7c7c2fdbd25a58d42cbe11bd08b8acac53`**. It was tested from a clean `git archive` export using
existing installed Python dependencies, without copying pending code. The subsequent report commits
add this handoff and verification records only. Task B should start from the final report commit,
verify the foundation below, and follow the [paired integration handoff](paired-semantic-integration-handoff-2026-09-18.md).

| Commit | Reviewed scope |
|---|---|
| `5bf960e35c71c4801820a4c374513b32dc82b509` | Active native-only preparation, packet binding/verification, input guards, guide and ten packet regression tests |
| `dc1a3bba4bf8e35f4439681c6675e70978f1fc95` | Exact R4 approval, sealed R2–R4 packets, audit/erratum history and historical independent M0 review |
| `88608d7c7c2fdbd25a58d42cbe11bd08b8acac53` | Strict no-PDF guidance, qualified M1 status, ignore protections, supplied Task A/B handoffs and reconciliation evidence |

No existing commits were rewritten and nothing was pushed. The four model-policy/experiment
commits `2584415`, `fcd40f0`, `2c50596`, `f539e9d` remain ancestors. Runtime code, schemas,
evidence/scoring/format contracts, diagnostic fixtures, experimental code and tracked model runs
have no diff from the starting HEAD. Both final experiment inventories verify: **413 + 123 = 536 hashes**.

## Inventory and disposition

The [starting manifest](../eval/milestone1/reconciliation-2026-09-18/starting-manifest.json) records
HEAD `f539e9de1f93cc6a33b6d8c332f912411f11ab50`, exact initial status and 207 pending paths. No files
were initially staged. [Attribution](../eval/milestone1/reconciliation-2026-09-18/attribution.json)
identifies Task A edits separately from the inherited work.

All 207 starting paths were accounted for and committed: active tooling/tests/guidance, the existing
owner decision, sealed review evidence, dated audits/obsolete tools and the supplied handoffs.
Historical PDF-derived attachments were first inventoried by path and recorded provenance, then
hashed solely for archival preservation. They were not visually inspected, compared to native text,
or loaded by active native verification. R2 has 46 sealed members, R3 has 103, and R4 has 25;
all match their manifests. The [historical inventory](../eval/milestone1/reconciliation-2026-09-18/historical-inventory.json)
records the 26 derived attachments, including nested copies. There are no raw PDF members or native
corpus exports in these added packets; bundled native fixture files are the six synthetic examples.

Historical review scripts and `review-guide.md` remain evidence, superseded by the active native guide
and current README/AGENTS instructions. Do not execute the old M0 verifier: it hashes raw PDFs.
Do not rerun R1–R3 generators or silently repair archived conclusions. The separate source-wording
erratum remains intact. Two archived whitespace defects and the raw failing-test log's trailing
space were deliberately preserved; the commit-range whitespace check therefore reports those
three files, not a clean blanket pass.

`.gitignore` now protects both `.env`/`.env.*` and `APIKEY.txt`, while preserving `/corpus` and
`/runs/`. `git check-ignore` confirms all five representative paths. No credentials were opened.
Pattern scans of each staged scope reported no matches and no credential/source-PDF/corpus paths;
this is a pattern-based check, not proof against every possible secret format. Existing explicitly
tracked experiment snapshots remain tracked and unchanged.

## Defects and corrections

The seven pending review regressions passed at the start. Independent review then reproduced:

1. Packet original-input verification opened image/text exports and followed original-input symlinks.
2. Resolving the packet directory before checking it concealed a symlink.
3. Preparation's intake helper attempted to open a prohibited selector before the review guard.

Three new test methods produced five failing assertions before correction; see the retained
[reproduction](../eval/milestone1/reconciliation-2026-09-18/defect-reproduction.txt).
Shared evaluator-only readers now check permitted extensions, credential paths, regular files and
symlink components before opening. Intake and original-input verification use them; packet and
preparation directories are checked before resolution. Synthetic test roots resolve the macOS
system temporary-directory alias before constructing their intentional test symlinks.

The pending `.gitignore` replacement would also have removed `APIKEY.txt` protection; that is fixed.
Active README/PLAN passages still implying M1 had not begun, allowing exceptional PDF reads, or
requesting PDF-quality work were reconciled. Historical dated narratives were retained. No financial
value, source string, evidence ID, pointer, accepted fixture label or runtime contract was repaired.

A fresh packet generated from selected saved IR/native inputs under a Python audit hook rejecting
PDFs, images and text exports made **zero prohibited read attempts**. Its candidates, additional
evidence, fixtures, guidance and acceptance scope equal R4 exactly. This unapproved tooling check is
local at `runs/milestone1-cleanup-2026-09-18/fresh-packet/`; its
[manifest/check result](../eval/milestone1/reconciliation-2026-09-18/guarded-preparation.json) and
[field comparison](../eval/milestone1/reconciliation-2026-09-18/fresh-packet-comparison.json) are retained.
It is not a replacement approval packet.

## Approval integrity and versions

[The existing owner decision](../eval/milestone1/approvals/r4.owner-2026-09-11.json) still binds R4's
approval fingerprint:

`c17c4855a026deaec52e0c6bbf7b92a3b5ee0236856f928f8e621a0fb97f0bf4`

The actual packet tool verified all 25 files and 29 original inputs against that fingerprint before
Task A edits. Independent checks also verify the approval record fingerprint, packet manifest hash,
review content fingerprint, exact eight primary mapping IDs and all six fixture hashes, expectations
and qualifications. See [approval verification](../eval/milestone1/reconciliation-2026-09-18/approval-verification.json).

After correction, **25 original inputs remain unchanged; four active tooling/guide inputs differ**:
`prepare.py`, `packet.py`, `native-review-guide.md` and `test_review_packet.py`. Their original bytes
remain bound in R4's snapshots. Consequently `packet.py --check-inputs` against R4 now fails as it
should; do not reseal R4, replace its approved fingerprint or claim the active generator reproduces
approved bytes. The reconciliation verifier reports this exact drift without altering approval.
The sealed packet's historical pending fields remain unchanged.

Acceptance covers native preservation, displayed limitations/unsupported handling and six qualified
fixture expectations. It excludes OCR/raw-PDF fidelity, runtime relationship/operand selection,
secondary mapping adoption, model correctness, detector performance, wider negative adequacy and
headline readiness. The rounding example retains its explicit completeness/rounding assumptions;
percentage and ambiguity examples remain minimal. All results remain **UNGATED**.

Versions are unchanged: runtime evidence/selection/manifest/pipeline schemas **1.0.0**, identity
policy **1**, review content **2.0.0**, packet manifest and approval record **1.0.0**, evaluation
format/scoring/taxonomy **2.0.0**. Path-guard corrections change no wire representation or accounting
semantics, so no contract migration or reinterpretation of frozen artifacts was needed.

## Commands and observed results

Run from the repository root using the existing `tools/eval-format-tools/.venv/bin/python`:

| Command/check | Observed result |
|---|---|
| `make evidence-check` | Starting workspace 86 tests; final workspace and clean committed export **89 passed** |
| `PYTHONPATH=src tools/eval-format-tools/.venv/bin/python -m unittest discover -s tests -p test_review_packet.py -v` | **10 passed**, including seven inherited and three added regression methods |
| `make -C tools/eval-format-tools PYTHON=.venv/bin/python check` | Formatting/schema checks and **26 tests passed**; 192 retained record instances, not distinct injections |
| `make evidence-local-check` | Both explicitly selected full native variants passed literal inventories, repeat ingestion, guarded IR-only replay and denied-access probes |
| Starting HEAD clean export, `make evidence-check` | **79 passed**, independently reproducing the starting observation |
| Clean export, existing saved IR via `launch('inspect', ...)` | Both variants reproduced byte-identical context; only selected evidence/manifest read; adapter unimported |
| Saved experiment evaluators in clean export | Historical interface, original direct-contributor, connected live-v2, 46 model-selection completions and 11 follow-up completions replayed successfully; no inference |

Each native variant retains 228 pages, 132 table regions and 6,415 cells, with clean resolved/partial
129/3 and corrupted 128/4. These are native HTML recovery results, not OCR or accounting-completeness
measurements. Workspace local checks are separate from portable checks; the clean-export IR check
uses explicitly selected local saved IR and is not advertised as corpus-free.

Exact export locations, commands and exit codes are in
[clean-export verification](../eval/milestone1/reconciliation-2026-09-18/clean-export-verification.json).
Logs include [portable](../eval/milestone1/reconciliation-2026-09-18/clean-portable.txt),
[intake](../eval/milestone1/reconciliation-2026-09-18/clean-intake.txt),
[local native](../eval/milestone1/reconciliation-2026-09-18/local-check.txt), and
[committed IR replay](../eval/milestone1/reconciliation-2026-09-18/clean-local-ir.txt).
For an export, pass the absolute installed interpreter as a shell-quoted Make variable because the
workspace path contains a space. An initial unquoted invocation failed before any test ran; the
corrected invocation and successful results are recorded. No dependency install was needed.

Read-only approval and experiment verification:

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python eval/milestone1/packet.py \
  --packet eval/milestone1/reviews/r4 \
  --expected-fingerprint c17c4855a026deaec52e0c6bbf7b92a3b5ee0236856f928f8e621a0fb97f0bf4
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python \
  eval/milestone1/reconciliation-2026-09-18/verify.py
```

Add `--check-inputs` to the reconciliation verifier for explicit local source/IR checks plus the
four documented active-input changes. It fails on missing local inputs or unexpected drift.
Never run the legacy intake `local-check` target for this workflow.

## Task B inputs, limits and remaining state

[Selection](../eval/milestone1/selection.json), [source inventory](../eval/manifests/hkex-2025-48.json),
and [ready selector](../eval/reviews/hkex-2025-48/ready-development.json) are evaluator-owned.
Original local full evidence and manifests remain separately under `runs/milestone1-r1/clean/` and
`runs/milestone1-r1/corrupted/`; R4's `inputs/verification.json` records their exact hashes and
original paths. The clean-export replay log independently checks the evidence hashes. Select one
variant's saved IR through the runtime selection contract. Do not send these evaluator selectors,
R4 mappings, fixture expectations or counterpart answers into Task B's runtime/model context.

No Task A implementation blocker remains for Task B in this workspace. A new checkout needs the
explicitly selected existing native exports or saved IR for local checks; Git intentionally contains
neither full corpus exports nor local M1 runs. Missing local inputs are a prerequisite gap, not a
portable failure or permission to read PDFs. Installed-wheel replay and source-level transitive
licensing were not re-audited; the former remains historical evidence. Optional cell geometry/fonts,
verified semantic headers, accounting relationships, secondary IR mappings, amount invariance and
semantic execution remain incomplete. Task B still needs independent source review, secure paired
transport and verified research noninterference. No detector/headline readiness follows from M1.

R4 report/guide links and all links from this results handoff resolve in both the workspace and
clean export. Across the supplied prompts and R4/results documents, all 50 local links resolve in
the workspace. The clean export resolves 49: the supplied Task A prompt
links to `runs/milestone2/model-commit-review-2026-09-18/review.md`, an optional prior local review
under ignored runs. Its absence was anticipated in that prompt; Task A independently reproduced
the relevant checks, so it is not an unresolved implementation dependency. The wider guidance
also references absent `README.original.md` and `AGENTS_template.md`; these are pre-existing,
unrelated historical/template gaps and were not fabricated or silently redirected.

At the verified foundation checkpoint `git status --short` was empty. The final report commits only
add this document and its verification records. No unrelated pending work was deleted or left
untracked. Ignored corpus, credentials, caches, local M1 runs, fresh diagnostic packet and temporary
exports remain local by design. Only selected native/IR inputs are required for local replay; caches,
old convenience ZIPs and the fresh unapproved diagnostic packet are not Task B dependencies.
