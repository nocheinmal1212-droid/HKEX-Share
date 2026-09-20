# Failure investigation — two-query live v2 confirmation

**The strongest supported diagnosis is an incomplete model-facing output contract.** The prompt
communicates the semantic task but leaves the four fields' exact meanings implicit. That accounts
for a reproducible citation-placement failure in both primary answers and plausibly contributes to
research's contradictory state fields. This is a request-design finding, not proof of a provider-side
schema bug or proof that a rewritten prompt will succeed.

The validator correctly rejected all four original responses. No request drift, persistence
corruption, selected-source support mismatch, timeout or truncation explains the failure. No
runtime, prompt, schema, saved response or frozen expectation was changed during this investigation.
There were **zero provider/metadata calls, zero credential accesses and no delegation**.

## 1. A precise citation rule was lost when expressed to the model

The [operation contract](../spec/semantic-operation-1.1.md) explicitly requires the target, every
contributor and qualified source-group ancestors **in support_refs**. In contrast, the actual
[frozen prompt](../src/hkex_audit/semantic.py#L12) says to cite them but never names `support_refs`,
`target_id` or `contributor_ids`. It says only “Return only the schema's IDs and labels.” The
[schema](../src/hkex_audit/semantic.py#L13) supplies four property names and basic types/enum; none
has a description. It does not express citation-list membership across fields.

All four answers put the correct target in target_id, the reviewed contributor IDs in contributor_ids,
and **only the correct group ID in support_refs**. Read as “cite each item somewhere in the JSON,”
that is understandable; it violates the actual full-list contract. This is why a generic instruction
to “cite” was insufficiently precise for the interface.

Provider-returned diagnostic text strengthens this hypothesis. Gemini's `total` output explicitly
questions whether support_refs should include target/contributors or only contextual support. The
research outputs discuss guessing field structure and propose target/contributor/source-group
objects instead of the actual four-field contract. [Short retained diagnostic excerpts](../runs/semantic-citation-failure-investigation-2026-09-19/v1/provider-diagnostic-evidence.json)
are tied to original response hashes. These are provider self-reports, not verified causal access
to model internals; no hidden provider conversion mechanism is established from them.

The caller **did send the schema** as `response_format.json_schema.schema`, with `strict=true`.
The [request builder](../src/hkex_audit/semantic_attempt.py#L36) does not also state its field semantics
in the model messages. Therefore “the client forgot to send JSON schema” is false. Whether/how each
provider exposes that parameter to generation or reasoning is not observable in these artifacts.
The evidence supports explicit field instructions without asserting that OpenRouter dropped schema.

## 2. Research has a separate state/list inconsistency

The actual prompt describes the four failure states and says abstentions have no contributors, but
never explicitly says **set state to selected when returning a supported contributor selection**.
`selected` appears as an enum value in the schema; the prose uses “selected subtotal” in a different
sense and supplies no positive-state mapping.

Both research responses return the same reviewed contributor IDs as primary, but `total` uses
`ambiguous` and `period_groups` uses `not_a_total`. Each retains nonempty contributor_ids. This
violates the existing abstention rule independently of missing citations. The research period-group
diagnostic text even describes a supported selection with no abstention, which differs from its
final state field. That inconsistency is evidence of output construction trouble, not a reliable
explanation for why those particular enum values were generated.

This distinction matters: adding missing citations alone would not make research valid. Nor may an
application silently change its state to selected or promote its contributor list. Primary and
research remain isolated; research cannot supply an annotation, fallback, consensus or veto.

## 3. Offline probes localize both defects without repairing results

The [probe plan](../eval/semantic-citation-failure-investigation/2026-09-19/v1/probe-plan.md) declared
expected behavior before running [the probe](../eval/semantic-citation-failure-investigation/2026-09-19/v1/probe.py).
It executed **16 diagnostic variants** across the four saved answers using the unchanged current
validator and evaluator comparison. Added IDs came only from fields already returned in that same
answer. No new model call, clean-counterpart oracle or operational consumption of a changed copy occurred.

| Diagnostic input | Primary, both cases | Research, both cases |
|---|---|---|
| Original saved response | Rejected: target support absent | Rejected: target support absent |
| Copy with only target added to support_refs | Rejected: contributor support absent | Rejected: contributor support absent |
| Copy with target and returned contributors added to support_refs | Host-valid selected answer | Rejected: abstention contains contributors |
| Research copy with complete support and state changed to selected | Not needed | Host-valid, solely as an authored counterfactual |
| Research copy with complete support and contributors cleared | Not needed | Host-valid abstention, but fails the reviewed selected expectation |

All sixteen variants pass the basic JSON shape schema. The host's cross-field checks are what reject
missing citations and contradictory lists. The source-derived required support exactly matches the
already-reviewed header support for both selected sources. This rules out an evaluator-only excess
citation requirement as the cause of these four rejections.

[Localization results](../runs/semantic-citation-failure-investigation-2026-09-19/v1/localization.json)
retain every expected outcome. **Counterfactual acceptance is not a repaired model pass.** All four
originals still replay as `invalid_output`; their original completion/provenance and empty primary
annotation bytes are unchanged. No corrected response or annotation was saved into live-v2.

The host reports only its first error: [target support](../src/hkex_audit/semantic.py#L99), then
contributor support, then contextual validation and abstention shape. Thus the identical top-level
error originally masked research's independent state problem. Reporting a list of violations could
improve diagnostics later, but is not necessary to correct the model-facing instructions and is not
implemented here.

## What was ruled out, and what remains uncertain

[Request/response verification](../runs/semantic-citation-failure-investigation-2026-09-19/v1/request-response-integrity.json)
reconstructed all four approved requests, matched the saved query/message/schema bytes and role
configurations, matched transport-return to persisted response, and replayed each hash-bound
completion. Both role pairs received equal semantic input. The response content is parsed directly;
there is no client-side field remapping that invented the missing citations or research states.
All referenced target, contributor and required-group IDs are present in the selected query.

All calls returned HTTP 200, the correct served model/provider identities and `finish_reason=stop`.
The full launch completed in 47.784289 seconds, well inside 600. Reported completion/reasoning tokens:

| Case / role | Completion tokens | Included reasoning tokens | Cap |
|---|---:|---:|---:|
| total / primary | 3,504 | 3,354 | 4,096 |
| total / research | 4,037 | 3,831 | 4,096 |
| period_groups / primary | 1,662 | 1,478 | 4,096 |
| period_groups / research | 2,145 | 1,894 | 4,096 |

Research total came close to the cap, but no response was reported truncated, and the same class of
failure occurred in substantially shorter outputs. The artifacts do not establish token pressure as
the cause or justify a larger cap. Any causal effect of schema handling, field order, reasoning,
prompt wording or context length would need a separately frozen experiment. Model selection is
closed; this investigation does not recommend switching models or routes.

The earlier 52 passing tests established execution, persistence, rejection and isolation behavior
with authored responses. Authored accepted answers explicitly populate the repeated citation IDs;
negative tests intentionally violate them. Those tests do not establish that a live model understands
the prose-to-field mapping. Similarly, a freeze can ensure exact request identity while preserving
an ambiguous prompt. This distinguishes a test-coverage limit from broken validation.

## Smallest recommended correction

[The unapplied output-instruction draft](../eval/semantic-citation-failure-investigation/2026-09-19/v1/proposed-output-instructions.md)
provides a concrete candidate for a later versioned prompt change:

1. Name all four output fields and prohibit invented literal-label/source_groups fields.
2. Explicitly map supported selection to `state="selected"`; non-selected states require an empty
   contributor list.
3. Require target_id and every contributor_id to be **repeated inside support_refs**, alongside the
   relevant source groups; IDs in other fields do not satisfy citation-list membership.

Keep the four-field schema, citation policy, source analysis, model/provider choices, native reasoning,
role isolation and cap unchanged for that first correction. Do not union missing citations or replace
research states at runtime. This targets the demonstrated communication gap without weakening
validation, expanding semantic scope or introducing new live cases. A new prompt requires new
version/bindings and requests; no completed request may be rewritten in place. Model improvement
remains untested, so any later live confirmation needs a new freeze and explicit call/time/cost budget.

## Preservation and status

The [before](../runs/semantic-citation-failure-investigation-2026-09-19/v1/before.json) and
[after](../runs/semantic-citation-failure-investigation-2026-09-19/v1/after.json) checks match all **3,116**
approved freeze members and all **83** live/execution/evaluation/report artifact hashes. The
[transcript](../runs/semantic-citation-failure-investigation-2026-09-19/v1/transcript.txt) records zero
network calls. No credentials, raw PDFs/native corpus exports, clean counterpart, injector data or
held-back outcomes were read. No runtime edit, commit, install or agent delegation occurred.

A reporting-only substring check initially counted `state` inside `statements`; the initial audit is
retained, and [the corrected exact-token audit](../runs/semantic-citation-failure-investigation-2026-09-19/v1/interface-audit-corrected.json)
shows that none of the four field names is explicitly named in the prompt. Core localization and
preservation checks were unaffected. The new report is the durable investigation note; the frozen
existing development log is left byte-identical to preserve its approved binding.

The current live result remains primary **0/2**, research **0/2** complete successes. Historical
**0/4 complete frozen support**, three research truncations and the earlier invalid research
abstention remain separate, unchanged evidence. These exposed development cases establish no
holdout/statistical accuracy, human/domain acceptance, numerical compatibility or downstream financial
isolation. Saved-IR semantic acceptance and Milestone 2 remain open.
