# Provisional interface-boundary fixtures

**Status: approved and executed on 2026-09-16.** The proposal below records the reviewed design;
the [results report](interface-boundary-results-2026-09-16.md) records all 180 attempts, including
the existing V4 Flash availability gap. The JSON fixture definitions remain unchanged.

This proposal investigates hypotheses **3 (deterministic responsibilities)** and **4 (task-contract communication)** from the latest discussion. The D/C fixture IDs intentionally avoid reusing the older H3/H4 schema/provider IDs. The [JSON definitions](../spec/diagnostics/interface-boundaries-v1.json) own the exact proposed inputs, outputs, prompts and limits.

## Working interpretation

The user’s successful Flash reruns are evidence against assuming a reliably reproduced failure. The existing explicit P11 prompt already passed the nine-case core suite and six additional strict repetitions on both primary DeepSeek routes. The objective is a clearer, more dependable interface, not to produce a failing model example. External reruns remain qualitative until exact prompt, provider, schema and budget settings are available.

Pro remains the comparison baseline and designated production semantic model. Existing V4 Flash is the primary refinement subject; V4.1 Flash is an optional exploratory extension. Pro is not an oracle: reviewed expected answers are authoritative. GLM/Gemini are outside this proposed phase.

## Findings from code and saved artifacts

- The current probe expresses the target in prose and does not perform a typed target-ID precheck. Downstream [fixture-contract validation](../src/hkex_audit/pipeline_contracts.py) already checks evidence references and vocabulary, but this is not an implemented semantic dispatch layer.
- ID membership alone misses a valid-but-wrong target. A return value can name a real node and still contradict the requested target.
- [Offline counterfactual review](../runs/milestone2/interface-review-2026-09-15/offline-target-shadow.json) found 24 historical DeepSeek attempts on the missing-target fixture: 13 passed, five selected a wrong existing ID, one truncated, three received HTTP errors, and two timed out. With a caller-supplied typed missing target, all 24 would be stopped before dispatch. Historical answers and model scores remain unchanged.
- The typed target must come from the caller’s structured task request. Extracting it from arbitrary prose with a model or ad hoc matching would recreate the dependency we are trying to remove.

## Proposed separation of responsibilities

A caller submits `operation`, `target_id`, and literal evidence with unique IDs. Code validates input structure and target existence before constructing the model’s instruction. The model decides what the label means. Code validates output syntax, cross-field consistency, evidence membership, and target agreement afterward. Code does not recognize total labels in this experiment.

An absent target or empty evidence produces a retained **precondition abstention**, with no model call. Duplicate IDs or missing required request fields are **rejected input**. Neither is a successful model answer. A malformed model response is a validation failure, never silently converted into abstention.

## D fixtures: deterministic boundaries (offline)

| Fixture | Input / simulated output | Required result |
|---|---|---|
| D01 | Target is absent; another field contains 總計 | Precondition abstention; zero calls. |
| D02 | Two evidence items share one ID | Reject input; zero calls. |
| D03 | Empty evidence | Precondition abstention; zero calls. |
| D04 | Requested target exists and says 總計 | Exactly one call; accept the correct target response. |
| D05 | Requested target says 收入; a different field says 總計 | Dispatch; model must abstain. Existence alone must not produce a label. |
| D06 | Model returns an existing ID different from the requested target | Reject output; do not remap the ID. |
| D07 | Model returns an unknown ID | Reject output; no invented evidence. |
| D08 | Model says abstain but returns non-null ID/role | Reject output; no normalization. |
| D09 | Model labels the requested 收入 field as a total | Structural validation accepts; semantic evaluator must still fail. |
| D10 | Target row-a; only Row-A exists | Exact-match precondition abstention; no fuzzy matching. |
| D11 | classify_target request omits target_id | Reject malformed request; zero calls. |

Use a transport spy and fixed response stubs to verify exact call counts and state transitions. These tests are proposed, not yet implemented. Every rejected/blocked opportunity stays in coverage. D09 is a deliberate limit test: guards cannot replace semantic interpretation.

## C fixtures: task-contract clarity (model calls after review)

Compare **B0: existing explicit P11** against **B1: concise equivalent wording**. All C inputs pass the same proposed prechecks, so differences cannot come from removing hard cases. Keep user-message bytes, schema, provider, token budget and sampling settings identical within each pair. Only the system prompt changes.

| Fixture | Task and evidence | Expected |
|---|---|---|
| C01_unique_total | Select unique total; a: 總計, b: 收入 | label a as total_label |
| C02_no_total | Select unique total; a: 成本, b: 收入 | abstain |
| C03_ambiguous_totals | Select unique total; a: 總計, b: 總計 | abstain |
| C04_target_total_with_distractor | Classify target b; a: 收入, b: 總計 | label b as total_label |
| C05_target_non_total_with_total_distractor | Classify target a; a: 收入, b: 總計 | abstain |
| C06_target_disambiguates_two_totals | Classify target b; a: 總計, b: 總計 | label b as total_label |
| C07_reorder_same_ids | Select unique total; b: 收入, a: 總計 | label a as total_label |
| C08_rebind_and_rename_ids | Select unique total; source-42: 收入, source-17: 總計 | label source-17 as total_label |
| C09_english_labels | Select unique total; a: Revenue, b: Total | label b as total_label |
| C10_simplified_labels | Select unique total; a: 收入, b: 总计 | label b as total_label |

B1 candidate wording:

```text
Classify supplied label text only. If an ID is requested, consider only that exact ID; if it is absent, abstain. Otherwise select only when exactly one supplied item explicitly names a total; if none or more than one qualify, abstain. A label naming a total is sufficient; amounts and surrounding tables are unnecessary. Return only a JSON object with exactly action, evidence_id, and role. For a selection use action "label", its supplied evidence_id, and role "total_label". For abstention use action "abstain", evidence_id null, and role null. Do not invent IDs, supply amounts, compute answers, or correct source text.
```

Both arms retain the existing three-field model output. IDs in the schema are sorted independently of evidence order, fixing the previous ordering confound. Keep all supplied IDs in the enum for both arms; narrowing it to the target would be a second intervention. The new wrapper states belong to the proposal, not the production pipeline schema.

## Model choices and routing

- Baseline: `deepseek/deepseek-v4-pro-0813`.
- Primary subject: `deepseek/deepseek-v4-flash-0731`.
- Optional extension: `deepseek/deepseek-v4.1-flash`.

V4.1 Flash is [listed on OpenRouter](https://openrouter.ai/deepseek/deepseek-v4.1-flash). Its page FAQ claims no response_format support, while the [endpoint API](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints) advertises response_format and structured_outputs on endpoints including DeepInfra and Fireworks. The [saved metadata](../runs/milestone2/interface-review-2026-09-15/v41-endpoints.json) records that discrepancy. Treat those as routing candidates, not verified conformance or live access. Do not silently drop strict schema to include the new model.

Refresh endpoint metadata when preparing execution. Prefer a common provider if it supports the compared configurations; at minimum pin one endpoint per model for both prompt arms. If providers differ, report model/provider pairs instead of attributing every difference to model capability. No automatic fallback or model-specific prompt variants.

## Proposed execution and interpretation

1. Implement and run D01–D11 offline with spies/stubs; retain the historical shadow analysis separately.
2. Freeze the 10 C cases × two prompts × three repetitions on Pro and existing Flash: **120 calls maximum**. Interleave paired arms and alternate pair order by repetition, with fresh conversations and no automatic retries.
3. Optionally add the same frozen suite for V4.1 Flash: **60 additional calls maximum**, contingent on available compatible routing. A first fixture doubles as the access/identity/format check; unsupported conditions stay visibly blocked.
4. Retain the established isolation boundaries and compare raw model outcomes only on the common eligible population. Report code abstentions and saved calls separately from model accuracy.

Default diagnostic limits stay 512 output tokens, 30 seconds, strict schema, temperature zero, and one call at a time. This preserves the interface experiment’s controlled settings; truncation must remain separate from interpretation failure. Any budget change belongs in a separately declared experiment, not an adaptive rescue.

If both prompts pass, report preserved behavior on the reviewed suite. Claim efficiency only from measured tokens/latency, and do not claim a capability improvement or require a failure to justify the work. Newer-model improvements cannot substitute for checking that the infrastructure handles the existing Flash model correctly.

Offline preparation checked proposed output shapes, prompt/payload consistency, unique case IDs and recorded source hashes. It did not implement the guards, run the fixtures against models, or change the production interface.
