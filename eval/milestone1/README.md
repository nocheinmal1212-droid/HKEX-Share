# Milestone 1 evidence handoff

**Active boundary:** selected MinerU output is the source of truth. `prepare.py` verifies native-to-IR
preservation only. It neither loads PDF-derived review text/images nor runs source/OCR-quality
comparisons. Review inputs reject PDFs, image/text exports and symlinks before opening them;
native selections additionally use the runtime input restrictions. Historical packets remain
unchanged and do not define current acceptance requirements. The active guide is
[native-review-guide.md](native-review-guide.md).

**Owner accepted R4 on 2026-09-11 within its limited native-evidence scope.** The
[approval record](approvals/r4.owner-2026-09-11.json) binds the exact packet fingerprint, eight primary
mappings and six fixtures with every existing qualification retained. Milestone 1 is complete within
this scope. The sealed packet remains unchanged; its pending fields describe its state when prepared.

**Accepted handoff: [native-only packet r4](reviews/r4/index.html)**, with its
[decision template](reviews/r4/review-guide.md), [review data](reviews/r4/review.json) and
[approval manifest](reviews/r4/packet-manifest.json). It contains no PDF-derived comparison or image
inputs. Its 25 bundled files and 29 original inputs verified before Task A corrections; preparation succeeds with PDFs and
PDF-derived text/images inaccessible. Approval is scoped to native-to-IR mappings, displayed evidence
limitations and the six qualified fixture expectations. Headline scoring remains UNGATED.

R1–r3 and their audit/erratum materials are preserved as history. Their PDF-related narratives are
not current acceptance requirements. Approval must name r4's **approval_fingerprint** and the accepted
items; it does not automatically carry forward from any older packet.

The acceptance-era verification passed 26 portable evidence/packet tests (19 original plus seven review regressions),
26 retained intake tests and full source-backed native/IR checks. Installed-wheel replay with the
adapter absent remains historical evidence, inspected but not rerun during this correction.
No detector, model or OCR execution is included. All results remain UNGATED.

The full artifacts are saved locally under `runs/milestone1-r1/` (gitignored). Each variant retains
228 pages, 132 table regions and 6,415 cells. Clean has 129 resolved and 3 partial grids; corrupted
has 128 resolved and 4 partial grids. These are HTML recovery states, not source-fidelity or
accounting-completeness decisions. Native/PDF image descriptions and unsupported inline content
remain visible limitations. No raw PDF or injector-record read was needed for this implementation.

From the repository root:

```sh
make evidence-check
make evidence-local-check
```

The first target uses portable synthetic fixtures. The second verifies the frozen ready selector,
generates native runs independently in a temporary directory, checks every native literal pointer,
repeats ingestion, runs guarded IR-only replay and probes forbidden file access. It does not promote
fixture labels or run the old PDF-reading intake validation command.

To persist a new review revision after an implementation change:

```sh
PYTHONPATH=src:tools/eval-format-tools tools/eval-format-tools/.venv/bin/python \
  eval/milestone1/validate.py --output runs/<new-run>
PYTHONPATH=src:tools/eval-format-tools tools/eval-format-tools/.venv/bin/python \
  eval/milestone1/prepare.py --runs runs/<new-run> --output eval/milestone1/reviews/<new-revision>
```

Use new paths. Never overwrite a reviewed packet or its run artifacts. Approval must name the packet's
outer approval fingerprint and accepted/rejected items; retain the pending packet as historical evidence.
The source inventory, canonical records, frozen split and existing approvals remain unchanged.

Verify the sealed R4 packet against the recorded owner fingerprint:

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python eval/milestone1/packet.py \
  --packet eval/milestone1/reviews/r4 \
  --expected-fingerprint c17c4855a026deaec52e0c6bbf7b92a3b5ee0236856f928f8e621a0fb97f0bf4
```

For a new packet, use both `--check-inputs` and the separately recorded owner fingerprint before
adoption. R4 remains sealed: Task A changed active tooling and this guide, so its original-input
check now fails on those changed paths. Their approved snapshots remain bundled in R4. Run
`PYTHONPATH=src tools/eval-format-tools/.venv/bin/python eval/milestone1/reconciliation-2026-09-18/verify.py --check-inputs`
to verify the approval bindings and distinguish those documented changes from unexpected source
drift. This does not renew or extend approval. See [Task A results](../../docs/milestone1-cleanup-results-2026-09-18.md)
for current commands, evidence and portability limits. Integrity checks do not grant approval. Review packet schema 2.0.0
supersedes the incomplete r1 review binding; runtime evidence schema remains 1.0.0 unchanged.

**Historical only:** the second auditor used one documented targeted clean-PDF inspection. R3 preparation reuses its
hash-verified text/image/inspection artifacts without another PDF read. No fixture native values,
qualified labels, primary mappings or runtime code changed. The original r2 packet verifies offline;
its original-input check detects intentional changes to active generation documents.

Historical scripts in `review-support/`, R1–R3 tooling and the independent M0 review must not be
executed in this workflow. Their PDF-related observations and obsolete pending decisions remain
dated evidence. See [the archival inventory](reconciliation-2026-09-18/historical-inventory.json)
for retained PDF-derived attachment paths and provenance; no raw PDF is bundled.
