# First semantic operation: direct contributors to an expense total

The user approved the independent review's decisions on 2026-09-17 UTC: retain B0 for lexical
diagnostics, carry deterministic boundaries into the first real semantic operation, defer
production integration, and keep existing-Flash comparison separate from Pro acceptance.
This document prepares that next operation. The new exact cases below were authored after that
approval; their expected answers are proposals, not inherited owner acceptance or model results.

## Operation and evidence requirements

Propose `select_direct_addends`: for one explicitly targeted expense total, identify its nearest
supported additive children. For example, total operating expenses comprise administrative and
distribution expenses, while payroll and premises are already included in administrative expenses.
Choose the administrative subtotal and distribution expense; do not flatten the subtotal or
double-count its children. Targeting administrative expenses instead selects payroll and premises.

This operation proposes a relationship only. It neither parses amounts nor emits signs, arithmetic,
corrected values or discrepancy findings. Restrict the first fixture slice to positive additive
expense breakdowns; transfers, deductions, signed movements, unit conversions and full
statement-to-note matching need their own evidence and operations later. No new scored category
or accounting-role taxonomy is introduced.

The draft [input cases](../spec/diagnostics/direct-contributors-inputs-v1.json) contain literal
row/header/note text, explicit header associations, container scope and limitations. These are
**hand-authored logical fixtures, not validated production IR or generated semantic annotations**.
There are no issuer facts, benchmark data, financial amounts or fabricated geometry. English
wording isolates relationship and evidence requirements from language variation in this first set.
The input file also owns the proposed operation rules and output vocabulary; it is not a frozen
production schema. A future renderer must select one case's source/request, not submit the whole
fixture file or the evaluator key.

Explicit relationship evidence is required. A rectangular recovered table is insufficient to
establish completeness, and lexical total recognition does not establish contributors. This is
why the old B0 clause saying no surrounding context is required cannot serve as this operation's
prompt. Pro remains `deepseek/deepseek-v4-pro-0813`; no new live prompt or routing configuration
has been frozen.

Required context is local to the relationship. A shared but unspecified currency/scale can still
support identifying explicitly stated direct contributors within one context. Arithmetic and
conversion may remain blocked downstream. A conflicting period, entity scope, currency or
presentation basis cannot silently join the target's additive relationship. Unknown candidate
context is distinct from a known shared context whose absolute unit is unspecified.

## Fourteen prepared interpretation cases

The separate [evaluator expectations](../spec/diagnostics/direct-contributors-expectations-v1.json)
contain titles, expected contributor sets, reasons, support requirements, and the rename mapping.
They must stay outside model requests and runtime detection. Selection is compared as an unordered
set of exact source IDs. Support IDs must include the essential relationship/header evidence;
additional relevant support is allowed, with relevance reviewed separately. Structure validation
cannot certify that the cited evidence supports the model's claim.

| Case | Deliberate distinction | Proposed outcome |
|---|---|---|
| S01 | Nested payroll/premises rows under administrative subtotal | Select administrative and distribution expenses. |
| S02 | Same evidence, target administrative subtotal | Select payroll and premises. |
| S03 | Add depreciation explicitly described as already included | Same as S01; exclude memo row. |
| S04 | Distribution occurrence unrecovered; retain source note and unresolved-region limitation | Abstain: missing evidence. |
| S05 | Remove the only explicit relationship note; retain labels | Abstain: directness is ambiguous. |
| S06 | Add an unresolved region belonging to an unrelated container | Same as S01; prerequisites remain local. |
| S07 | Distribution candidate is company-only, target is group | Abstain: incompatible context. |
| S08 | Distribution candidate belongs to a different period | Abstain: incompatible context. |
| S09 | Distribution candidate uses another currency | Abstain: incompatible context; no conversion in this operation. |
| S10 | Distribution candidate is restated, target is original | Abstain: incompatible context. |
| S11 | Distribution header cannot identify group versus company | Abstain: unknown context. |
| S12 | All rows share the same unspecified currency/scale header | Same contributor relationship as S01; no arithmetic-readiness claim. |
| S13 | Reverse serialization order while preserving bindings | Same source IDs as S01. |
| S14 | Rename every source ID and preserve correspondence | Same relationship after evaluator-only inverse mapping. |

The explicit source prose makes these initial controls intentionally tractable; it does not measure
performance on implicit relationships in real statements. S04 and S05 change evidence sufficiency,
whereas S06, S12 and S13 guard against unnecessary abstention. The set has no amount cells, so it
cannot establish amount invariance. A later paired native/IR fixture must change actual source
amounts, verify code masking before model submission, and show that relationship selection is
unchanged while code-only arithmetic can change. Do not manufacture that claim by changing an
evaluator answer field or by comparing two already amount-free payloads.

## Twenty dispatch and failure scenarios

The evaluator file specifies D01–D20 as **unexecuted scenarios** with expected call counts, result
states, reasons and injected faults. They cover target omission versus source absence, duplicate
IDs, foreign source binding, request mutation, byte bounds, blank/unsupported targets, timeout,
refusal, truncation, wrong/unknown IDs, structural acceptance of a semantic error, persistence
failures before and after dispatch, interrupted-attempt replay, transport mutation, lost
limitations, and malformed output modes. D20 contains distinct malformed JSON/envelope/tool-call
subcases. These states describe the proposed semantic attempt record, not new check-ledger states.

Two success controls must accompany fault execution: one normal selected response persisted
with exact provenance and one valid model abstention. For byte limits, test the exact boundary
and one-byte overflow in serialized UTF-8; do not compare Python character counts. For a model
timeout, retain an attempted call. For a failure before request persistence, assert zero calls.
If all output writes fail, the process exit/returned error and absence of a completion marker
must still reveal failure; it is impossible to promise a saved terminal record on an unavailable
filesystem. A start without a terminal record stays incomplete on replay, with no automatic resend.

These scenarios do not claim to exercise a nonexistent production dispatcher. The implementation
must eventually run them through the actual selected-IR → bounded request → dispatch → persisted
attempt path, including access isolation, before passing any integration gate. The existing
lexical stub dispatcher cannot establish that result.

## Contract decisions before implementation

Use the current [evidence contract](../spec/evidence-contract.md) for real source identities,
fragments, content states and limitations. The logical fixture inputs are a review convenience;
they must not become a second production evidence format. Keep the future annotation and
comparison-plan transformations separate, and use SCORING.md's existing opportunity states.

The current [stage-failure schema](../schemas/pipeline_artifacts.schema.json) only permits
`selection`, `adapter`, and `consumer`. It cannot represent a semantic dispatch failure. Also,
IR replay compares the manifest's complete schema-hash inventory, including pipeline artifacts.
Silently expanding that schema under version 1.0.0 would invalidate existing IR replay hashes.
Define a separately versioned semantic-attempt artifact, with its own schema/configuration
fingerprints, or perform an explicit compatibility migration. Prefer the separate attempt artifact
for this PoC; keep accepted M1 evidence schemas/hashes intact. No such schema has been added here.

The future attempt record needs selected document/variant/evidence identity, request hash and
operation version, model/prompt/schema/configuration identity, start state, terminal outcome,
actual dispatch count and references to available raw response bytes. The attempt result must
distinguish host precondition abstention, model abstention, refusal, invalid output, incomplete
response, transport failure, and persistence failure. A structurally accepted response remains
semantically unverified. Do not manufacture check passes from successful model calls.

## Preparation checks and next execution

Run the [offline consistency checker](../tools/experiments/check_direct_contributor_fixtures.py):

```sh
tools/eval-format-tools/.venv/bin/python tools/experiments/check_direct_contributor_fixtures.py
```

It verifies case/reference uniqueness, contributor/support membership, declared vocabularies,
input/key field separation, and exact reorder/rename/shared-unknown controls. Its output records
file hashes and draft logical payload sizes. It does not execute the proposed operation or the
failure scenarios, validate native-to-IR fidelity, review accounting labels independently, or
demonstrate production isolation. No live worker, provider choice, call budget, retries or model
tokens are approved or inferred from this preparation.

Executed preparation checks passed: 14 interpretation cases, 20 specified boundary scenarios,
and a maximum draft logical payload of 1,924 UTF-8 bytes. The
[saved validation result](../runs/milestone2/direct-contributor-preparation-2026-09-17/validation.json)
records hashes and limitations. Interpretation and boundary execution counts remain zero.

Next: independently review these exact evidence requirements and expected relationships, translate
the fixtures into the existing synthetic evidence/IR workflow, and implement/test the actual offline
dispatch-and-persistence slice. Freeze any subsequent live experiment separately. Existing-Flash
availability and lexical scope/budget ablations remain separate experiments, not prerequisites for
this Pro-focused operation definition. Production integration and headline scoring remain deferred.
