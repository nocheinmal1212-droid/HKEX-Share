# Task B — paired semantic integration on selected saved IR

**Implementation works at the header-annotation boundary; research isolation passes; full saved-IR
semantic acceptance remains open.** Gemini selected the independently reviewed contributor headers
correctly in all four eligible queries, but every answer omitted the review's required unit-header
citation. DeepSeek produced no usable answers. No research output affected operational artifacts.
No numerical plans, checks, findings, detector accuracy, full Milestone 2 or scoring readiness is claimed.

## Foundation and committed scope

Started from clean `94c6b3f`, following [Task A's handoff](milestone1-cleanup-results-2026-09-18.md).
Inspected its cited implementation/review/guidance commits `5bf960e`, `dc1a3bb`, `88608d7` and report
commits `d9db19a`, `94c6b3f`. The reconciliation verifier rechecks the 25 R4 members, existing approval
bindings and 536 historical experiment hashes; [retained output](../eval/semantic-integration/2026-09-18/baseline-verification.json).
It grants no new approval and does not recheck local original inputs. No Task A work was modified
or recommitted. No raw PDF, clean counterpart, injector metadata or held-back outcome was read.

- `21bcc83`: supported semantic implementation, contracts and separation tests.
- `d83a5fe`: independent source review, frozen expectations and pre-inference bounds.
- `6b6e713`: reproduced relative-selector launch defect corrected before any API call; this is
  the implementation used for the live batch and installed-wheel replay.
- `58e210b`: evaluator correction/regressions and replay path prevalidation.
- A separate evidence/report commit retains validation artifacts and this report. These changes
  alter neither live requests nor frozen answers.

The [operation](../spec/semantic-operation.md) is immediate **column-header contributor selection**,
not numerical operand selection. Actual IR supports this limited hierarchy through literal labels,
parent links and recovered spans. The projection includes every descendant of the selected table,
source-fragment references and relevant limitations. It preserves Chinese literals and the source's
2026 caption. Missing entity/basis and external associations stay unknown. The blank target is
missing source evidence; an edited projection, unknown ID or bad caller selection is an input error.

The [additive contract](../spec/paired-semantic-attempts.md) defines operation, attempt, batch and
provenance version 1.0.0. Existing evidence/annotation schemas and their hashes remain unchanged;
no historical attempt, scoring run or approval is migrated. No new runtime dependency is introduced.
The transport uses Python's standard library. Existing dependency-license qualifications still apply.

## Independent review and frozen inputs

[Source packet](../eval/semantic-integration/2026-09-18/source-review-packet.json) and
[independent expectations](../eval/semantic-integration/2026-09-18/independent-review.json) were
reviewed by `/root/source_review`, with no implementation, model answers, clean IR or gold operands.
Review ended **2026-09-18 05:49:51 UTC**, before inference. This is independent **agent** review,
not independent human/domain approval. The review records exposure to literal body amounts; amounts
were not used to establish relationships. The main agent later verified packet nodes and descendant
completeness against the explicitly selected IR and accepted the expectations unchanged.

Selected source: `runs/milestone1-r1/corrupted/evidence.json`, SHA-256
`69595ab56b61046c3a991cd7726dbd82abde16f223d2ff9dfed362171a10bbe9`.
Manifest and source-provenance hashes are in the retained [IR selector](../runs/paired-semantic-integration-2026-09-18/selection.json).
[Pre-inference freeze](../eval/semantic-integration/2026-09-18/pre-inference-freeze.json) binds source,
review, operation, queries and limits. Packet hash:
`57a0ca40e2f19a3ec33564a2fdf549c39482d4031ca5df4283364c3190095b80`.
Review hash: `186751559cb107900b7eb1cebee5993d43b729ed283649929a467dd51fcea789`.

The five development queries were selected before new responses: total and nested subtotal on
previously exposed M1 page index 178, comparative 2025/2024 headers on index 179, a genuinely blank
target, and the total with a versioned body-amount variation. These are source development examples,
not a new benchmark split or untouched holdout. Runtime contains no page, issuer, note or expected
operand constants. Source traces retain zero-based IR page indices; no new PDF numbering/fidelity
attestation is made.

The amount contrast changes only numeric body placeholders in a derived projection
(`mask_body_amounts_v1` versus `vary_body_amounts_v1`). Original IR and semantic labels/spans remain
unchanged. Code checks verify exactly which projected fields change; the fresh paired queries test
model selection invariance separately. This is one projected contrast, not general numerical
operand invariance or evidence of repeatability across extraction revisions.

## Live invocation and bounds

From the repository root, using the existing Python 3.13 environment:

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python -m hkex_audit.semantic_cli run \
  --selection runs/paired-semantic-integration-2026-09-18/selection.json \
  --queries runs/paired-semantic-integration-2026-09-18/queries.json \
  --output runs/paired-semantic-integration-2026-09-18/live-v1 \
  --max-http-calls 10 --max-role-calls 4 --max-seconds 600 --max-cost 8 --env-root .
```

The first invocation stopped at relative-selector validation before creating a batch or making an
HTTP call. The fixed invocation above completed. The directory is immutable; repeating `run` with
it fails before dispatch. Use replay for this saved batch.

Frozen controls: exact Gemini `google/gemini-3.8-flash` / `google-ai-studio`, DeepSeek
`deepseek/deepseek-v4.1-flash` / `together`; temperature 0, 4096 completion tokens, native default
reasoning, strict schema, require_parameters, no fallback/retry, 60-second process deadline.
Advertised metadata and served model/provider match both configured identities. Backend checkpoint
revisions remain unknown; aliases and provider preprocessing are not immutable.

Actual use: **2 metadata GETs + 8 completions = 10 HTTP calls**, four completions per role;
**110.49 seconds** batch elapsed. The blank target made zero calls. Conservative cost reservation
was **$5.397760**, below the **$8** cap. Reported costs: primary **$0.11460525**, research
**$0.037624884**, total **$0.152230134**. All eight completion responses report cost; no-call
opportunities have no response cost. Reservations use frozen routing price ceilings, not expected
billing, and are investigation caps rather than business acceptance budgets.

The [batch ledger](../runs/paired-semantic-integration-2026-09-18/live-v1/summary.json) retains all
outcomes. Each role stores its own actual request, raw base64 response, usage/cost, served identity,
timing, validation result and independently bound completion. Semantic payload hashes are identical
within each pair; role/configuration/attempt identities differ. No credential was persisted.

## Results against the unchanged review

| Query | Primary relationship vs review | Required citations | Research outcome |
|---|---|---|---|
| Total | Correct: subtotal + lease header | Unit omitted | Truncated |
| Subtotal | Correct: two timing headers | Unit omitted | Truncated |
| Period groups | Correct: three 2025 peers; excludes 2024 | Unit omitted | Invalid output |
| Blank target | Correct local missing-evidence abstention; no call | Not applicable | Same local prerequisite; no call |
| Amount-varied total | Same correct contributors as total | Unit omitted | Truncated |

Operational coverage is **4/4 eligible queries annotated**, plus **1/1 locally blocked opportunity
retained**. Contributor-set correctness is **4/4**; full reviewed citation completeness is **0/4**.
All four omit `港幣百萬元`. This is a substantive acceptance failure, not hidden by a structurally
valid response. The host validates IDs, support membership, target, scope and spanning-group context;
it does not yet enforce the review's full contextual citation requirement.

Research response availability is **4/4 HTTP completions**, but **0/4 usable semantic answers**.
The period query returns contributor IDs while declaring `ambiguous`, violating the abstention
contract; it is rejected, even though those IDs resemble the reviewed selection. The three other
answers hit the completion limit. Pair agreement is **unavailable**, not an accuracy score or 0%.
These queries do not constitute a DeepSeek-led pipeline evaluation.

[Evaluation v2](../runs/paired-semantic-integration-2026-09-18/evaluation-v2/evaluation.json) and
[primary source/attempt traces](../runs/paired-semantic-integration-2026-09-18/evaluation-v2/primary-source-traces.json)
make each annotation inspectable. The annotations use the real pipeline artifact contract and a
provenance companion binding source/query/primary completion/annotation hashes. No dummy downstream
plans or findings were created.

An evaluator-only defect initially compared the blank case's `missing_evidence` with the review's
`expected_status=abstained`, overlooking `expected_abstention_reason`. Evaluation version 1.0.1
corrects that mapping and has regression tests. [Evaluation v1](../runs/paired-semantic-integration-2026-09-18/evaluation-v1/evaluation.json)
and its exact evaluator source are retained. Frozen expectations and live responses are untouched;
the four citation failures are unchanged. This correction is not a new confirmation run.

## Separation, failures and replay evidence

The focused deterministic suite exercises identical payload/contract identities, changed query and
configuration rejection, actual guarded file reads, independent early/late write failures for both
roles, missing/truncated/corrupt completions, interrupted starts, role binding, and `commit_unknown`
resolution by read-only replay. It tests agreement, disagreement, unsupported research selection,
refusal, malformed output, timeout, missing completion and persistence failure against a fixed
accepted primary attempt. **Actual annotation and provenance bytes remain identical**, with no
normalization of decisions, provenance, timestamps or attempt IDs. Primary failure/abstention never
promotes a plausible research answer. Research exhaustion remains visible.

A controlled event test stalls research until the real primary consumer has persisted output.
Copying valid research completion files into the primary directory is a targeted promotion mutation
that the consumer rejects. A malformed research completion cannot crash operational replay. Guard
probes attempt reads of research, credentials, PDFs, injector metadata, evaluator expectations and
a clean-counterpart sentinel; all are denied. The transport's separate guard rejects files and
foreign hosts/ports; it cannot write attempts. These are Python accidental-access controls, not a
hostile-code sandbox or proof about native-library internals.

Primary annotations are consumed before waiting on research. The batch still awaits each research
attempt's own 60-second bound before scheduling the next pair; unrestricted throughput independence
is not claimed. No shared response cache is implemented. Future planners/checks/findings must consume
the primary-only boundary; their noninterference has **not** been established by empty-output equality.

A clean `git archive 6b6e713` passed **107 tests** and built a wheel offline using existing local
setuptools. The installed wheel replayed all primary and research artifacts with **zero calls**;
primary annotation/provenance bytes match live consumption exactly, no adapter imports occur, and
operational reads contain no research files. [Replay verification](../runs/paired-semantic-integration-2026-09-18/replay-verification.json)
binds the wheel hash and paired attempt IDs. The final workspace and clean export of `58e210b` pass **110 tests**, including **21 focused
semantic/evaluator tests**. Final installed-wheel replay also passes; see the
[verification record](../eval/semantic-integration/2026-09-18/final-verification.json). Intake's 26 tests pass.

Reproducible replay (replace the output path with a new directory):

```sh
PYTHONPATH=src tools/eval-format-tools/.venv/bin/python -m hkex_audit.semantic_cli replay \
  --selection runs/paired-semantic-integration-2026-09-18/selection.json \
  --batch runs/paired-semantic-integration-2026-09-18/live-v1 --output /tmp/new-primary-replay
# Use research-replay for the separate diagnostic role; it emits no annotations.
```

Local full IR remains intentionally ignored and is required to recompute projections. Retained
selected contexts alone are not a replacement validated full-IR manifest. Clean-checkout tests are
portable; the package replay is explicitly a local saved-IR check. `/runs/` remains ignored by default;
only the named Task B evidence is force-retained. Source corpus, credentials and unrelated runs are
not staged. No history was rewritten or pushed.

## Verdict and smallest next step

**Implementation: complete for this narrow header operation. Research isolation: verified at the
implemented annotation/provenance boundary. Saved-IR validation: attempted and traceable, acceptance
not met because of missing contextual citations.** The local missing-evidence and period exclusion
controls work; the amount contrast preserves the selected header set.

The next step is a new version specifying and enforcing all required contextual support, followed
by a separately reviewed and budgeted confirmation slice. Preserve this run as development evidence;
do not silently reinterpret it, automatically retry DeepSeek, or extend its exhausted call budget.
Numerical parsing, row-level operand selection, completeness, arithmetic, findings and scoring gates
remain open. No statistically established best model or market-wide performance follows from this run.
