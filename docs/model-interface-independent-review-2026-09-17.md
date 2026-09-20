# Independent review of the model-interface handoff

Reviewed 2026-09-17 UTC (2026-09-16 in the project timezone). Decision: the handoff's
central findings are supported. Retain B0 for the lexical experiment, retain the deterministic
regressions, and implement their behaviors when building the first real semantic operation.
Do **not** move the existing lexical helper into `src/` or enable production model dispatch now.
This is an implementation decision based on the missing runtime contract, not a request for
another approval or a conclusion that DeepSeek cannot perform the work.

This review supplements the [handoff](model-interface-independent-review-handoff-2026-09-16.md)
without changing its frozen sources or historical results. No inference calls, credentials,
supplied PDFs, native exports, evidence IR, or benchmark answers were used. Synthetic evaluator
keys were read only by offline review code. No model, production prompt, scoring contract,
approval, or milestone completion status changed.

## What was verified

- All **55 handoff links** resolve. All **388 checked file hashes** in the latest verification
  inventory match. The one omitted hash is the synthetic `sentinels/corpus.pdf`; even that
  invented PDF-named text file was unnecessary to read. This establishes local availability
  and agreement with recorded hashes, not independent authenticity or a portable Git bundle.
- `make evidence-check` passes **55 tests**, including the seven boundary methods exercising
  all **11 deterministic fixtures** and the intentional structurally accepted semantic error.
- Independently reviewed the **ten lexical expected answers**, then graded all **180 raw
  responses** separately from the existing classifier. Matched their request/response hashes,
  start records, model/provider identities on completed answers, and frozen expected answers.
- Verified all **90 pairs** differ only in system wording. Both the 146-call September 15
  evaluation and the 180-call September 16 evaluation replay exactly from saved records.
- Recomputed the paired passing-sample medians: B1 saves 65 prompt tokens for Pro and V4.1,
  adds 30 and nine completion tokens respectively, and adds 0.5327405 and 0.162925 seconds.
  These are conditional efficiency summaries, not all-attempt reliability or causal timing estimates.
- Reproduced the **24 DeepSeek missing-target counterfactuals**: 13 passed, five wrong selections,
  three HTTP errors, two timeouts, one truncation. Separately checked historical GLM call-120's
  record hash and wrong answer. Explicitly mapped its request to `target_id="field-missing"`:
  experimental dispatch returns `precondition/abstained/target_missing` with **zero calls**.
  The target was specified by the reviewer, not extracted from arbitrary prose. Historical failure
  records and scores remain intact; this replay is still outside production.
- Inspected the transport worker, saved launch metadata and all **20 recorded read denials**.
  This review did not relaunch or independently attest the historical OS sandbox. No stronger
  isolation claim follows from a saved attestation or the current portable runtime tests.

| Observed route | B0 explicit | B1 concise |
|---|---|---|
| Pro / Fireworks | 30 passed | 26 passed; two unexpected abstentions; two truncations |
| Existing V4 Flash / Fireworks | 30 HTTP 429 | 30 HTTP 429 |
| V4.1 Flash / Fireworks | 30 passed | 30 passed |

The two Pro abstentions have `finish_reason=stop`, no refusal, and 121 completion tokens.
Both answer C06 incorrectly. Its requested target `b` is unambiguous even though another total
label exists. The two truncations have null content and 512 reported reasoning/completion tokens.
All 60 existing Flash errors report Fireworks rate limiting. These distinctions in the handoff
are correct. V4.1 supplies no missing observations for existing Flash.

## Implementation decisions

**Carry the deterministic behaviors forward, but defer production code promotion.** Exact
membership, unique IDs, explicit target scope, immutable request scope, null-field consistency,
and preservation of rejected outputs are justified. The experimental checks already implement
and test these behaviors. Reimplementing them in an unused runtime module would not resolve the
handoff's integration question.

The actual application currently exposes ingestion and IR inspection. Its
[context builder](../src/hkex_audit/evidence_context.py) retains the evidence identity, occurrence
kind, content state, fragments, parent and limitations, with count/byte bounds. The experimental
request contains only `{operation, target_id, evidence:[{id,text}]}`. Its `total_label` output is
not a supported accounting relationship or the persisted annotation contract. There is no real
semantic dispatcher to attach it to, and
[downstream validation](../src/hkex_audit/pipeline_contracts.py) does not supply one.

Two new offline probes confirm concrete integration gaps in the existing helper:

1. A 24,001-character ASCII evidence string remains eligible, already exceeding the existing
   context builder's entire 24,000-byte budget before JSON overhead. The helper itself is unbounded.
2. An injected transport timeout makes one call and propagates an exception; it returns no
   failure record. There is also no persistence in this helper. The separate experimental worker
   records transport failures, so this does **not** invalidate the historical run.

These are limitations of the prototype, not regressions against its documented experiment scope.
Leave the hashed implementation unchanged. When the first real operation is built, use one owning
request/dispatch contract that consumes validated selected evidence, enforces bounds, retains
provenance, and persists every outcome. Test rejected input and missing prerequisites with zero
calls; model abstention, invalid output, refusal, truncation and transport failure with distinct
reasons; and valid structure with semantic correctness still unknown. A missing target in a caller's
selection may be a selection defect rather than absence in the underlying evidence: specify that
distinction before mapping it into an opportunity's abstention reason.

**Keep explicit wording; do not adopt B1.** B1 has demonstrated regressions and no observed
efficiency advantage sufficient to justify them. B0 is a supported choice for this tiny lexical
task. Its statement that no table/context is needed must **not** be copied into financial
relationship prompts. Retain explicit vocabulary and operation scope as design principles;
review the actual evidence requirements for each new operation. The observed prompt difference
does not identify a particular causal sentence.

**Leave existing Flash unresolved and Pro designated.** An available-provider comparison is
needed to answer the existing-Flash question. It is **not a prerequisite for implementing or
accepting Pro's own semantic path**, and V4.1 is not an authorized replacement. No claim is made
about current provider availability: only the saved Fireworks failures were reviewed. A future
comparison needs fresh metadata and a new frozen run with all attempted calls retained.

## Highest-value next fixtures

These are proposals, not executed interpretation experiments or newly approved expected labels.
Prioritize the first real operation and its failure handling over additional broad lexical sweeps.

| Priority | Missing distinction and small fixture | Observable expectation |
|---|---|---|
| 1 | Evidence availability versus projection loss: target exists in selected IR but is omitted from the candidate payload; contrast truly absent target, blank text, unsupported content and a partial table. | Record distinct selection/prerequisite reasons; preserve limitations; no unsupported relationship or dropped opportunity. Freeze which conditions block the particular operation. |
| 1 | Complete breakdown versus missing contributor: otherwise identical synthetic row-role evidence with an unresolved intervening region, then a complete version. Include a memo row and nested subtotal. | Unsupported completeness abstains; supported contributors follow reviewed roles. Amount changes cannot change selection. Labels/support IDs only, with arithmetic left to code. |
| 1 | Compatible versus incompatible counterparts: identical labels but different group/parent scope, current/restated basis, period, or units; then a genuinely compatible pair. | Choose only context-compatible source references; unknown context stays unresolved. Avoid a unique lexical label masquerading as a valid financial match. |
| 1 | Actual dispatch and persistence: timeout, refusal, truncated envelope, wrong existing ID, caller/payload mutation, and failure to write the result. Replay an interrupted attempt. | Preserve the frozen request and raw available response; zero calls for invalid inputs; no semantic-success record for a crash; incomplete persistence cannot look complete. |
| 2 | Identifier validity beyond syntax: same-looking labels from a different document/revision, an existing ID outside the selected scope, and literal quote/newline/Unicode IDs if the contract permits them. | Verify source namespace and selected scope, retain exact IDs, and keep instructions separate from identifier data. Do not infer an ID-injection success from string concatenation alone. |
| 2 | Required-context ablation: remove only a header or limitation supporting a previously justified accounting relationship. Contrast irrelevant distractor removal. | Removing required evidence changes to abstention; irrelevant changes preserve the supported selection. This tests sufficiency rather than just prompt length. |

For prompt diagnosis, the already proposed targeted/global scope-only pair is more discriminating
than another multi-clause rewrite. Use fresh reviewed labels and positions. For the very narrow
lexical task, also compare a reviewed exact-label lookup with explicit unknown-label abstention;
it can establish whether model calls add value there without claiming that a lookup solves
accounting relationships. Keep these experiments separate from the existing-Flash availability
comparison and any budget-only truncation arm.

## Reproduction and scope

The one-off [review script](../runs/milestone2/interface-independent-review-2026-09-17/review.py)
prints its results without writing historical files. Its
[saved output](../runs/milestone2/interface-independent-review-2026-09-17/review.json) and
[observed test summary](../runs/milestone2/interface-independent-review-2026-09-17/test-summary.json)
record this review. Run from the repository root:

```sh
tools/eval-format-tools/.venv/bin/python runs/milestone2/interface-independent-review-2026-09-17/review.py
make evidence-check
```

The September 11/12 narrative was inspected as context; this review did not independently replay
every early probe. The central September 15/16 claims have the verification described above.
Repeated tiny cases, fixed case order and unequal arm ordering do not establish statistical
independence, a causal prompt clause, serving-weight identity, production reliability, or financial
audit accuracy. Full-pipeline acceptance remains open and headline scoring remains UNGATED.
