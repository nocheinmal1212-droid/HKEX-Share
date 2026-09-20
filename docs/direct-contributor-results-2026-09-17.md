# Direct-contributor tests: execution, observations and verdict

Executed 2026-09-17 under the user's instruction to run the prepared tests and report their
effectiveness. **Verdict: retain and extend the diagnostic/regression suite; do not accept the
experimental dispatcher or tested semantic configuration for production integration.** The tests expose
an incorrect relationship despite valid structure, repeated incomplete context decisions, and
a real access-guard integration defect. They also demonstrate supported relationships that
remain stable under the intended controls. They do not establish financial audit accuracy.

## Outcomes

| Test layer | Observed result | What it establishes |
|---|---|---|
| Twenty deterministic scenarios | 30/30 planned expanded fault cases and controls passed | Experimental dispatcher behavior for these particular fault timings. |
| Additional late-write failure probe | **Failed** | The planned persistence tests miss a replay defect after bytes have already been written. |
| Four implementation mutations | All four rejected by the regression suite | Assertions detect bypassed prechecks, bypassed candidate scope, accepted truncation, and falsely reported persistence success. |
| Isolated offline replay | One selected-source/frozen-response replay passed; ten protected reads denied | Experimental dispatch can read selected data and its own request while denying unselected source/answer/credential reads. |
| Full portable test suite | 61 tests passed | Existing checks plus six new dispatcher/regression/isolation test methods. |
| Pro interpretation, 42 attempts | **31 full passes; one wrong relationship; five timeouts; five truncations** | A useful but insufficient result on these fixed logical fixtures and this route/budget. |

All 42 attempts are retained. There were 37 HTTP 200 responses, of which 32 contained usable
structurally accepted decisions; 31 of those matched the frozen relationship, reason and required
support expectations. The ten unavailable decisions remain in the 42-attempt total. They are
not ten incorrect semantic answers, and the conditional 31/32 result is not the overall success
rate or a production accuracy estimate.

All seven positive fixtures passed all three repetitions: **21/21**. Of the 21 expected-abstention
attempts, ten passed, one selected an unsupported relationship, and ten were unavailable.
This distinction matters: the configuration handles explicit supported breakdowns better in
this small sample than the context/insufficiency decisions needed to stop unsupported checks.

| Case | Expected behavior | Pass | Wrong | Timeout | Truncated |
|---|---|---:|---:|---:|---:|
| S01 | Direct administrative subtotal plus distribution | 3 | 0 | 0 | 0 |
| S02 | Payroll/premises when administrative subtotal is targeted | 3 | 0 | 0 | 0 |
| S03 | Exclude the included depreciation memo | 3 | 0 | 0 | 0 |
| S04 | Abstain on missing contributor occurrence | 2 | 0 | 1 | 0 |
| S05 | Abstain without direct-relationship evidence | 3 | 0 | 0 | 0 |
| S06 | Ignore unrelated-container limitation | 3 | 0 | 0 | 0 |
| S07 | Abstain on group/company conflict | 1 | 0 | 1 | 1 |
| S08 | Abstain on period conflict | 0 | 0 | 1 | 2 |
| S09 | Abstain on currency conflict | 3 | 0 | 0 | 0 |
| S10 | Abstain on original/restated conflict | 1 | 0 | 2 | 0 |
| S11 | Abstain on ambiguous group/company allocation | 0 | 1 | 0 | 2 |
| S12 | Permit local role selection with shared unspecified units | 3 | 0 | 0 | 0 |
| S13 | Preserve selection under serialization reorder | 3 | 0 | 0 | 0 |
| S14 | Preserve selection under exact ID renaming | 3 | 0 | 0 | 0 |

## What the interpretation fixtures revealed

**S11 found a substantive error that deterministic validation cannot prevent.**
[call-011](../runs/milestone2/direct-contributors-2026-09-17/responses/call-011.json)
returned `select` with contributors `r01` and `r04`, even though the latter's header is
`Group / Company (allocation not identified)` and the target is group-only. It also cited the
ambiguous header `s06`. These are valid source IDs and valid output fields; the relationship is
unsupported under the frozen operation contract. Citing a relevant source does not establish
that the inference drawn from it is correct. The other two S11 attempts truncated, so this case
has no passing observation.

**S08 exposes an execution limit, not a completed wrong interpretation.** Its prior-year
candidate differs from the target's period. All three attempts were unavailable: one timeout and
two truncations. The experiment therefore cannot assess the final semantic answer for this case.
It does establish that the selected configuration failed to deliver the required decision under
its frozen bounds. Similar incomplete outcomes occurred on S07 and S10.

All five truncations ended with `finish_reason=length` and 2,048 completion tokens. Four have
null content with all 2,048 tokens reported as reasoning. S08
[call-040](../runs/milestone2/direct-contributors-2026-09-17/responses/call-040.json)
has 2,032 reasoning tokens and the partial JSON prefix
`{"action":"abstain","target_id":"r05","contributor`.
That prefix is not a completed abstention and earns no semantic pass. No budget increase,
response repair, retry or replacement call was performed.

The positive controls are useful: all repetitions preserve the direct subtotal relationship,
switch contributors with the target, exclude the memo, tolerate irrelevant limitations and
shared unknown units, and follow source identity under reorder/renaming. S04 and S05 also produce
correct abstentions when complete answers are available. Correct selections include the required
relationship-note and header citations. Inspection of the other returned support IDs found local
target/candidate context references; support ordering was not scored. This was same-agent source
and support review, not independent human adjudication.

As simple checks against a permissive fixture set, an always-abstain policy matches only **7/14**
expected relations; selecting the first two candidates matches **1/14**. These are offline trivial
policy controls, not additional model experiments or deployable detectors.

## What the deterministic execution revealed

Implemented a separate
[experimental dispatcher](../tools/experiments/direct_contributor_boundary.py), with exact source
binding, request snapshots, immutable validation scope, UTF-8 bounds, strict output parsing,
raw-response preservation, explicit outcome states and replay without redispatch. The
[runner](../tools/experiments/run_direct_contributor_boundaries.py) executes all 20 prepared
scenarios, expanding identity, truncation, persistence and malformed-output variants, plus
normal selection/model-abstention controls. The source is still the authored logical fixture
format: this is **not** a production IR consumer or an application CLI integration.

Observed boundaries include zero calls on rejected/precondition inputs, acceptance at exactly
24,000 serialized UTF-8 bytes and rejection at 24,001, distinct timeout/refusal/truncation/output
failure outcomes, and retained wrong/unknown-ID responses. The D14 parent-plus-child selection
remains structurally accepted but explicitly semantically unverified, with its wrong relationship
visible to evaluation. The planned snapshot-write failures prevent dispatch; their injected
response/result-write failures occur before writing bytes and leave no completion record.
Replay of an interrupted attempt makes zero new calls and
does not assume the prior call completed.

**A further timing probe falsified the broader persistence claim.** When the store writes complete
result bytes and then raises an error, dispatch reports `persistence_failure/result_not_persisted`,
but replay reads the leftover JSON as `structure_accepted`. The original D16 variants inject an
error before the write, so all 30 planned cases and 61 portable tests can pass while this defect
remains. The [failing observation](../runs/milestone2/direct-contributors-2026-09-17/exploratory-late-write-failure/observation.json)
and [reproducer](../runs/milestone2/direct-contributors-2026-09-17/late_write_probe.py) are saved.
This additional exploratory case was not folded into or hidden by the original 30/30 count.
It requires explicit commit/completion semantics and tests for partial writes, errors after bytes
are written, and interrupted completion. The prototype is intentionally left as the tested
version; this defect is unresolved, not a passed gate.

The isolated replay caught a defect in its launch configuration: dispatch rereads the saved
request to verify it before transport, but that exact output file was missing from the read
allowlist. The worker failed before a stub call. Adding only `output/request.json` to the exact
read allowlist fixed it; a regression now checks successful own-request readback and denial of
unselected data. This is concrete evidence that an in-process stub pass alone missed an
integration problem. The isolated replay uses the existing audit guard and a frozen stub response;
it does not attest the production model runtime or hostile-code containment.

Other preparation/verification observations are retained:

- The first live preflight failed before network use because the interpreter/current directory
  was under the sandbox-denied project path. Absolute Python and the isolated staging directory
  resolved it; no denied project-data read was enabled.
- The first offline replay launch used a base interpreter without `jsonschema`; the project
  virtual environment resolved that dependency issue. Both failed launches are saved.
- The initial null-content truncation test used the JSON text `null`; the final run uses actual
  null envelope content. Both runs remain saved and the expected outcome did not change.
- The first independent verifier incorrectly assumed every truncation had null content and all
  tokens spent on reasoning. Raw call-040 disproved that assumption. The corrected verifier
  records partial content separately. The primary evaluator already handled it as incomplete;
  no expected answer, raw response or outcome count changed.

## Configuration, evidence and limits

Fresh endpoint metadata advertised Fireworks support for the designated
`deepseek/deepseek-v4-pro-0813`. The run froze one explicit task-specific prompt, strict output
schema, temperature zero, 2,048 completion tokens, a 30-second per-call deadline, 128-KiB response
bound, one concurrent call, zero retries and no provider fallback. Fourteen cases ran three times
with case-order rotations of 0, 5 and 10. All conversations were fresh. This richer operation's
budget differs from the earlier 512-token lexical experiment; results are not a controlled
comparison with B0/B1.

The key was initially absent from the task environment. The user explicitly authorized the root
`.env`; a bootstrap loaded only `OPENROUTER_API_KEY` into the isolated worker's minimal environment.
The worker could not read `.env`, fixtures, evaluator answers or project data. Ten protected reads
were denied during both preflight and execution; the separate offline replay denied another ten.
No credential appeared in saved output and no response credential redaction was triggered.

The transport worker consumed frozen requests only. Prechecks ran in preparation and output checks
ran offline; it did not call the new experimental dispatcher for each live call. Thus the live
interpretation results and stubbed persistence results remain separate pieces of evidence.
Neither is proof that the production selected-IR path invokes these checks correctly.

Reported API cost is **USD 0.169704744**; the five timeouts have no reported cost. Exact saved
evaluation replay succeeds, and a separate direct raw-response tally confirms 31/1/5/5.
The original fixture files, expected answers, earlier runs and M1 schemas remain unchanged.
No supplied PDF, native export, report IR, benchmark ground truth, arithmetic calculation or
amount-invariance experiment entered this run. Actual weights, cache state and statistical
independence are unverified. These are 14 related English synthetic cases with explicit source
prose, authored header associations, and same-agent expectation review.

## Decision and next useful work

**Keep and extend these tests.** The deterministic cases detect the intended boundary regressions and the
guard test caught a real configuration omission. The interpretation cases are more discriminating
than the earlier total-label fixtures: they expose a context-ambiguity error, repeated unfinished
context decisions, and successful controls that prevent a blanket-abstention policy from passing.

**Do not promote this dispatcher or semantic configuration on the current evidence.** Fix the
late-write/replay defect with an independently specified completion contract before treating
persisted results as reliable. Keep Pro designated and
retain explicit task wording, but leave semantic integration and headline scoring unaccepted.
The next investigation should separate supported relationship selection from referenced-context
interpretation and deterministic compatibility checks, with independently reviewed conflict/unknown
examples. A separately frozen budget-only arm can investigate truncations; it must retain all
failures and cannot resolve the completed S11 error by assumption. No conclusion about the cause
of timeouts, a particular prompt sentence, intrinsic model incapability or another model's
superiority follows from this single-route experiment.

Before a production claim, run the same faults through the actual selected-IR dispatcher, preserve
source limitations/fragment provenance, and instantiate the missing source-amount invariance tests.
Those remain substantive gaps, not passed gates.

## Artifacts and reproduction

- [Frozen plan](../runs/milestone2/direct-contributors-2026-09-17/execution-plan.json),
  [prompt](../runs/milestone2/direct-contributors-2026-09-17/prompt.txt),
  [requests](../runs/milestone2/direct-contributors-2026-09-17/requests.json),
  [evaluator key](../runs/milestone2/direct-contributors-2026-09-17/evaluator-key.json),
  [raw responses](../runs/milestone2/direct-contributors-2026-09-17/responses).
- [Interpretation evaluation](../runs/milestone2/direct-contributors-2026-09-17/evaluation.json),
  [30 boundary observations and artifact paths](../runs/milestone2/direct-contributors-2026-09-17/boundaries-r2/summary.json),
  [isolation replay](../runs/milestone2/direct-contributors-2026-09-17/isolated-offline-replay-r3/access.json).
- [61-test log](../runs/milestone2/direct-contributors-2026-09-17/local-tests-final.txt),
  [regression and mutation tests](../tests/test_direct_contributor_boundary.py),
  [code hashes](../runs/milestone2/direct-contributors-2026-09-17/implementation-manifest.json).
- [Independent verification and retained failing verdict](../runs/milestone2/direct-contributors-2026-09-17/verification-final.json),
  [verifier correction](../runs/milestone2/direct-contributors-2026-09-17/verification-attempt-1.json),
  [launch observations](../runs/milestone2/direct-contributors-2026-09-17/launch-observations.json).

Offline reproduction from the repository root:

```sh
make evidence-check
tools/eval-format-tools/.venv/bin/python tools/experiments/evaluate_direct_contributor_run.py runs/milestone2/direct-contributors-2026-09-17
tools/eval-format-tools/.venv/bin/python runs/milestone2/direct-contributors-2026-09-17/verify.py
```

Do not rerun the dated preparation or live launcher into these directories. A new inference
experiment needs a new frozen run. The replay commands above make no network calls.
