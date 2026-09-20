# Proposed synthetic hypothesis fixtures

**Status: owner-approved and executed on 2026-09-15.** The linked fixture JSON preserves the original proposal unchanged. Approval, subject/oracle roles, execution details and outcomes are recorded in the [fixture report](experimental-fixture-results-2026-09-15.md).

The [machine-readable proposal](../spec/diagnostics/hypothesis-fixtures-v1.json) owns the exact prompts, evidence, expected outputs, comparison axes, bounds and interpretation rules. This page is its review summary. These are development diagnostics, separate from report evaluation and its frozen scoring contract.

## Intended outcome

Use one explicit task prompt and output contract across the four reviewed models. Keep model/provider routing in configuration. A shared client must expose unsupported capabilities or failed answers; it cannot guarantee that every model will perform the task correctly. No per-model prompt patches or silent correction of invalid answers.

## Hypotheses and discriminating comparisons

| Fixture | Question | Exact controlled comparison |
|---|---|---|
| H1 | Successful output vocabulary is not communicated clearly enough. | Compare P00 vs P10 and P01 vs P11. Only the vocabulary paragraph differs within each pair. |
| H2 | Evidence sufficiency or task scope is interpreted too cautiously. | Reuse H1 factorial calls. Compare P00 vs P01 and P10 vs P11. Only the scope paragraph differs within each pair. |
| H3 | Strict API schema handling contributes to divergent decisions or output failures. | Same exact messages with explicit vocabulary in both arms. Change response_format only; require the same pinned endpoint to support both. |
| H4 | Serving path or repeated-call variability explains the original intermittent abstention. | Repeat byte-identical requests three times on one pinned endpoint. Interleave paired arms with fixed case order; freeze order in the execution manifest. Reuse first observations from H1 only if endpoint, requests, and schedule match. Optional provider comparison repeats the same schedule on a second verified endpoint for Pro. |
| H5 | Insufficient completion budget explains the newly observed no-schema truncation. | Change max_tokens only, same pinned endpoint and 30-second deadline; record timeouts separately. |
| H6 | Residual lexical, language, or occurrence-binding weakness. | Shared prompt, schema construction and validation across models; compare language, evidence order and ID changes with explicit expected selections. |

H1 and H2 share a 2 × 2 prompt experiment, so vocabulary and scope are no longer bundled into a single edit. P00 is the historical system prompt; P10 adds only vocabulary, P01 adds only scope, and P11 adds both. The common three cases are `zh_total`, `no_total`, and `missing_target`. H3 uses explicit vocabulary in both arms, fixing the earlier schema-removal confound. H5 concerns the newly observed truncation, not the earlier completed abstention.

Each hypothesis has a support criterion and a limit in the JSON. A passing baseline leaves the original cause unresolved; do not interpret it as proof that a changed prompt repaired the issue.

## Candidate shared prompt (P11)

```text
Return only the requested JSON object. Interpret labels using supplied evidence IDs. Never invent an ID or supply amounts, computed answers or corrections. For insufficient evidence return action abstain with null evidence_id and role. Output vocabulary: action must be exactly "label" or "abstain". For a selection, use action "label", the selected evidence ID, and role "total_label". For abstention, use action "abstain", evidence_id null, and role null. Return exactly these three JSON keys: action, evidence_id, role; no other text. This task classifies label text, not financial amounts or accounting relationships. A label explicitly naming a total is sufficient; no amounts, table, or surrounding context are needed. If the instruction targets an ID, consider only that ID; an absent target requires abstention. Otherwise select only when exactly one supplied label explicitly names a total. If none or more than one qualify, abstain; do not guess or select by order.
```

The user message contains only the selected fixture instruction and evidence. The expected answer is evaluator-only and is never sent. In strict mode, evidence_id enumerates the supplied IDs plus null. Without the API schema, message bytes stay identical and the same local validator still applies.

## Core fixtures for all four models

| ID | Evidence (ID: literal text) | Instruction | Expected output |
|---|---|---|---|
| `zh_total` | `field-one: 總計`; `field-two: 收入` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "field-one", "role": "total_label"}` |
| `reordered` | `field-two: 收入`; `field-one: 總計` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "field-one", "role": "total_label"}` |
| `rebound_ids` | `field-one: 收入`; `field-two: 總計` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "field-two", "role": "total_label"}` |
| `renamed_ids` | `source-17: 總計`; `source-42: 收入` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "source-17", "role": "total_label"}` |
| `no_total` | `field-one: 成本`; `field-two: 收入` | Select the total label from the supplied evidence. | `{"action": "abstain", "evidence_id": null, "role": null}` |
| `missing_target` | `field-one: 總計`; `field-two: 收入` | Classify field-missing as a total label if supported by the supplied evidence. | `{"action": "abstain", "evidence_id": null, "role": null}` |
| `ambiguous_total` | `field-one: 總計`; `field-two: 總計` | Select the total label from the supplied evidence. | `{"action": "abstain", "evidence_id": null, "role": null}` |
| `english_total` | `field-one: Total`; `field-two: Revenue` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "field-one", "role": "total_label"}` |
| `simplified_total` | `field-one: 总计`; `field-two: 收入` | Select the total label from the supplied evidence. | `{"action": "label", "evidence_id": "field-one", "role": "total_label"}` |

The ambiguity rule is deliberate: this is a unique-selection task. Two separate total occurrences require abstention. ID renaming and rebinding prevent a model from passing by always returning field-one. The missing-target case does not explicitly tell the model the expected answer.

## Execution proposal after review

1. Resolve and freeze a currently available endpoint for each exact model, including supported parameters. Recorded provider display names are lookup candidates, not executable routing slugs. Freeze the request schedule before calls. Unsupported routes remain explicitly blocked.
2. Run the shared P11 core suite on DeepSeek Pro, DeepSeek Flash, GLM and Gemini (nine cases each). Run the H1/H2 factorial on the two DeepSeek models using the three common cases, reusing matching P11 observations where applicable.
3. Run the H3 schema comparison on all four models. Keep both arms on the same endpoint; do not permit routing mode changes to masquerade as schema effects.
4. Run H4 as three predeclared repetitions per case and prompt on both DeepSeek models, interleaving original/explicit prompts. Count matching scheduled H1 observations as the first repetition. A second verified Pro endpoint is an optional separate provider comparison, not a fallback.
5. Run the small H5 budget diagnostic on Pro only; retain wrong labels as failures even if a larger budget allows completion.

All fixtures have zero retries. Base limits remain 512 output tokens, 30 seconds, and 128 KiB per response; only H5 changes the output-token cap to 2048. No report, PDF, OCR or benchmark inputs. Save exact requests, raw responses, usage, latency, identities and failures. Returned reasoning may aid interpretation but cannot establish internal cause.

## Acceptance and limitations

One frozen P11 prompt and output contract must pass all nine core cases on each supported reviewed model/endpoint, with planned repeat evidence reported separately. No per-model prompt variants, field-position shortcuts, automatic fallback, or output repair. Unsupported routes are explicit capability failures, not semantic passes. Passing this finite suite does not guarantee success for every underlying model.

Report syntax/contract compliance, semantic decision, abstention correctness and completion separately. The all-pass criterion is for the common task contract; exploratory diagnostic failures remain visible and do not get rewritten as passes. A parsed correct ID with invalid action/role is still a contract failure. An API error or truncation is not an abstention.

Offline preparation verified JSON readability, schema validity for every instantiated case, expected-output shape, and isolated prompt construction. These checks do not validate model behavior or substitute for the owner’s review of fixture meanings.
