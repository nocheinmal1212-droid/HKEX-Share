# Interface-boundary experiment — 2026-09-16

The approved experiment separates deterministic request/output consistency from model interpretation. Pro is a baseline, existing V4 Flash is the primary subject, and V4.1 Flash is a distinct extension. Reviewed fixture expectations are the authority. All routes were pinned to Fireworks; no fallback, prompt repair or retries were used.

Executed 180/180 planned calls: 120 base-comparison calls and 60 extension calls. API-reported cost across available usage records: USD 0.042627614; 60 records have no reported cost.

[Approved fixture proposal](interface-boundary-fixture-proposal.md) · [Frozen plan](../runs/milestone2/interface-boundaries-2026-09-16/execution-plan.json) · [Evaluation](../runs/milestone2/interface-boundaries-2026-09-16/evaluation.json)

## Findings and implications

**Keep the existing explicit P11 wording as the current candidate.** Pro passed 30/30 with B0;
the proposed concise equivalent passed 26/30, with two unexpected abstentions and two outputs
truncated at 512 completion tokens. V4.1 Flash passed 30/30 under each prompt. Existing V4 Flash
returned HTTP 429 for all 60 calls: that primary-subject comparison remains unassessed, not a
model-capability failure. No provider was switched and no extra calls were made to replace errors.

The clearest decision failure is C06: both supplied labels say `總計`, but the instruction asks
specifically to classify ID `b`. B0 passed all three Pro repetitions. B1 truncated once and
returned `{"action":"abstain","evidence_id":null,"role":null}` twice
([call-091](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-091.json),
[call-152](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-152.json)).
Both abstentions finished normally with `finish_reason=stop` and `refusal=null`; they are task
decisions to make no selection, not recorded refusals. Each used 121 completion tokens, so a
512-token limit does not explain those two completed decisions. Their output passed structural
postconditions; rejecting it as semantically wrong requires the reviewed expectation.

The two separate truncations are [call-032](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-032.json)
(C06) and [call-085](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-085.json)
(C05, a non-total target with a total distractor). Both have null content and report all 512
completion tokens as reasoning tokens. They establish failure under the approved budget, not
an incorrect final semantic answer. Larger-budget performance was not tested in this run.

For hypothesis 3, all 11 offline boundary fixtures passed: exact input/ID checks can prevent
invalid dispatches and reject inconsistent outputs without interpreting label text. D09 preserves
the counterexample: structurally valid semantic mistakes survive the guard. The live C fixtures
were all eligible; no live pass-rate gain is attributed to prechecking or dropping cases.

For hypothesis 4, the comparison shows that shortening this prompt did not preserve observed Pro
behavior. Scope communication—classify one requested ID versus choose a unique item across the
whole list—is a plausible next hypothesis, not an established internal cause. The two prompt arms
change several phrases, so this experiment cannot identify a particular sentence as causal.
Nor does it show that the original intermittent failure has one cause across providers.

Among pairs where both arms passed, B1 saved a median 65 prompt tokens on both successful routes,
but used 30 more completion tokens on Pro and nine more on V4.1; median latency increased by
0.533 seconds and 0.163 seconds respectively. These samples provide no speed argument for
adopting B1. Three repetitions per case are small and not guaranteed statistically independent;
provider caching and hidden serving state remain uncontrolled.

The next useful experiment is a separately frozen rerun of both prompt arms on an available
existing V4 Flash endpoint, keeping that provider fixed across the arms. A subsequent scope-only
ablation should explicitly separate targeted classification from global selection and include
new reviewed examples, retaining C06 as a regression. These are proposed next steps, not additional
calls executed here. Production integration, its designated Pro model, and milestone acceptance
remain unchanged; synthetic successes do not establish real audit-pipeline accuracy.

Verification: [55 local tests](../runs/milestone2/interface-boundaries-2026-09-16/local-tests-final.txt),
11 offline fixtures, 20 protected-read denials in each preflight/live isolation check, exact
request/response hashes, reviewed input/answer preservation, and identical offline evaluation
replay. See the [verification manifest](../runs/milestone2/interface-boundaries-2026-09-16/verification.json).

## Per-model prompt results

B0 is the existing explicit P11 wording. B1 is the approved concise equivalent. Each model/prompt has ten cases, repeated three times. A service failure is not a semantic wrong answer, but it prevents acceptance for that planned observation.

| Model | Prompt | Calls | Passed | Other outcomes |
| --- | --- | --- | --- | --- |
| V4 Pro (baseline) | B0 | 30 | 30 | none |
| V4 Pro (baseline) | B1 | 30 | 26 | truncated: 2, unexpected_abstention: 2 |
| V4 Flash (primary subject) | B0 | 30 | 0 | http_error: 30 |
| V4 Flash (primary subject) | B1 | 30 | 0 | http_error: 30 |
| V4.1 Flash (extension) | B0 | 30 | 30 | none |
| V4.1 Flash (extension) | B1 | 30 | 30 | none |

## Deterministic fixtures

These are offline tests with response stubs and a call spy; no live model call is credited as saved or passed by these fixtures. The guard inspects structure and IDs only.

| Fixture | Fixture passed | Calls to stub | Actual boundary result | Semantic check |
| --- | --- | --- | --- | --- |
| D01_missing_target | True | 0 | precondition: abstained | not_model_evaluated |
| D02_duplicate_ids | True | 0 | input_validation: rejected | not_model_evaluated |
| D03_empty_evidence | True | 0 | precondition: abstained | not_model_evaluated |
| D04_existing_total | True | 1 | output_validation: accepted | expected |
| D05_existing_non_total | True | 1 | output_validation: accepted | expected |
| D06_wrong_existing_target | True | 1 | output_validation: rejected | wrong |
| D07_unknown_returned_id | True | 1 | output_validation: rejected | wrong |
| D08_inconsistent_abstention | True | 1 | output_validation: rejected | wrong |
| D09_semantic_error_survives_guards | True | 1 | output_validation: accepted | wrong |
| D10_exact_id_membership | True | 0 | precondition: abstained | not_model_evaluated |
| D11_missing_typed_target | True | 0 | input_validation: rejected | not_model_evaluated |

D09 deliberately remains a semantic error even though output consistency is accepted. D01/D03/D10 retain precondition abstentions; duplicate/malformed input is rejected. Wrong IDs and inconsistent outputs are rejected, never repaired.

## Paired prompt observations

Efficiency figures use only pairs where both arms passed for the same model/case/repetition. Negative differences mean B1 used less time or fewer tokens. These are small observed samples with provider caching and scheduling outside our control, not performance guarantees.

| Model | Matched pairs | Both passed | Median prompt-token delta | Median completion-token delta | Median latency delta (s) |
| --- | --- | --- | --- | --- | --- |
| V4 Flash (primary subject) | 30 | 0 | None | None | None |
| V4 Pro (baseline) | 30 | 26 | -65.0 | 30.0 | 0.5327405000000001 |
| V4.1 Flash (extension) | 30 | 30 | -65.0 | 9.0 | 0.16292500000000001 |

## Exact case outcomes

### V4 Pro (baseline)

| Case | B0 repeats 1–3 | B1 repeats 1–3 |
| --- | --- | --- |
| C01_unique_total | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-001.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-062.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-121.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-002.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-061.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-122.json) |
| C02_no_total | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-007.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-068.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-127.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-008.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-067.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-128.json) |
| C03_ambiguous_totals | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-013.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-074.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-133.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-014.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-073.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-134.json) |
| C04_target_total_with_distractor | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-019.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-080.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-139.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-020.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-079.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-140.json) |
| C05_target_non_total_with_total_distractor | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-025.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-086.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-145.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-026.json), [truncated](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-085.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-146.json) |
| C06_target_disambiguates_two_totals | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-031.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-092.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-151.json) | [truncated](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-032.json), [unexpected_abstention](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-091.json), [unexpected_abstention](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-152.json) |
| C07_reorder_same_ids | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-037.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-098.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-157.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-038.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-097.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-158.json) |
| C08_rebind_and_rename_ids | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-043.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-104.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-163.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-044.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-103.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-164.json) |
| C09_english_labels | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-049.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-110.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-169.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-050.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-109.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-170.json) |
| C10_simplified_labels | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-055.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-116.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-175.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-056.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-115.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-176.json) |

### V4 Flash (primary subject)

| Case | B0 repeats 1–3 | B1 repeats 1–3 |
| --- | --- | --- |
| C01_unique_total | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-003.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-064.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-123.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-004.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-063.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-124.json) |
| C02_no_total | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-009.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-070.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-129.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-010.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-069.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-130.json) |
| C03_ambiguous_totals | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-015.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-076.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-135.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-016.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-075.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-136.json) |
| C04_target_total_with_distractor | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-021.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-082.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-141.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-022.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-081.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-142.json) |
| C05_target_non_total_with_total_distractor | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-027.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-088.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-147.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-028.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-087.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-148.json) |
| C06_target_disambiguates_two_totals | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-033.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-094.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-153.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-034.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-093.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-154.json) |
| C07_reorder_same_ids | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-039.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-100.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-159.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-040.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-099.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-160.json) |
| C08_rebind_and_rename_ids | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-045.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-106.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-165.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-046.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-105.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-166.json) |
| C09_english_labels | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-051.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-112.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-171.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-052.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-111.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-172.json) |
| C10_simplified_labels | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-057.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-118.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-177.json) | [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-058.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-117.json), [HTTP 429](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-178.json) |

### V4.1 Flash (extension)

| Case | B0 repeats 1–3 | B1 repeats 1–3 |
| --- | --- | --- |
| C01_unique_total | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-005.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-066.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-125.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-006.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-065.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-126.json) |
| C02_no_total | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-011.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-072.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-131.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-012.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-071.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-132.json) |
| C03_ambiguous_totals | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-017.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-078.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-137.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-018.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-077.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-138.json) |
| C04_target_total_with_distractor | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-023.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-084.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-143.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-024.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-083.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-144.json) |
| C05_target_non_total_with_total_distractor | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-029.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-090.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-149.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-030.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-089.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-150.json) |
| C06_target_disambiguates_two_totals | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-035.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-096.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-155.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-036.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-095.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-156.json) |
| C07_reorder_same_ids | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-041.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-102.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-161.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-042.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-101.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-162.json) |
| C08_rebind_and_rename_ids | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-047.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-108.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-167.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-048.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-107.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-168.json) |
| C09_english_labels | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-053.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-114.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-173.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-054.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-113.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-174.json) |
| C10_simplified_labels | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-059.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-120.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-179.json) | [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-060.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-119.json), [passed](../runs/milestone2/interface-boundaries-2026-09-16/responses/call-180.json) |

## Isolation and verification boundaries

- The experimental typed boundary validates C requests and renders the user payload during offline preparation. Every C case is eligible in both prompt arms, so the comparison does not improve scores by dropping difficult cases. The frozen request hashes protect the exact bytes sent.
- Model responses are evaluated against the original schema and reviewed expected outputs, then against the typed output postconditions. Raw model failure and guard rejection are reported separately; no response is repaired. The guard is not integrated into production semantic dispatch.
- The transport worker is the previously verified worker with only its accepted manifest version changed. Its OS sandbox denies project-file data; a Python audit allowlist restricts other reads after imports. Writes are limited to new response files and standard device output. Bootstrap injects the credential into a minimal environment; the worker cannot read .env, source fixtures or evaluator answers.
- Twenty protected-read checks use pathlib and os.open against the evaluator key, fixture source, .env, README and six synthetic sentinels. No supplied PDF, native extractor output, evidence IR or benchmark data is used.
- All comparisons use fresh two-message conversations, strict JSON schema, 512 output tokens, temperature zero, a 30-second deadline, sequential calls, and zero retries/fallback. First V4.1 calls also check observed access/model/provider and output shape within its planned 60 calls.
- Metadata advertises structured outputs on the selected Fireworks endpoints. Requests pin the endpoint tag and returned provider names are checked; backend revision/weights and hidden provider preprocessing remain unknown. Same provider does not make different models identical serving environments.
- IDs are sorted independently of evidence order in the schema enum. Prompt arms differ only in the system prompt; case data, schema and request settings are identical within each pair.
- Unexpected abstention, wrong selection, malformed output, truncation, timeout and service errors remain separate outcomes. No intrinsic-capability conclusion follows from service or budget failures. This is synthetic interface testing, not full audit-pipeline validation.
