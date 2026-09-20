# Experimental fixture results — 2026-09-15

DeepSeek Pro, DeepSeek Flash and GLM are the subjects. Gemini is an independent comparison oracle. Reviewed fixture answers remain the scoring authority; Gemini does not receive subject outputs and its success alone cannot attribute a failure to model weights.

Executed 146 of 146 predeclared calls sequentially, without retries. API-reported cost for records with usage: USD 0.064093228; 22 records have no reported cost. These are synthetic diagnostics, not financial-audit accuracy measurements.

[Frozen plan](../runs/milestone2/hypothesis-fixtures-2026-09-15/execution-plan.json) · [Launch and isolation revision](../runs/milestone2/hypothesis-fixtures-2026-09-15/launch-attestation.json) · [Machine-readable evaluation](../runs/milestone2/hypothesis-fixtures-2026-09-15/evaluation.json)

## Findings and decision

The common explicit prompt plus strict schema passed all nine core fixtures and all six additional
scheduled strict repetitions on each primary DeepSeek route: Pro/Baidu and Flash/OpenInference
(15/15 each). This is a finite synthetic result, not a claim of general model capability.
GLM has not met the common acceptance criterion: its first core suite has five passes and four
rate-limited calls, and a later explicit-prompt missing-target repetition gives a wrong decision.
Gemini passed all nine core oracle cases; without the schema it also exposed formatting failures.

| Hypothesis | Observed evidence | Conclusion for this run |
|---|---|---|
| H1: unclear output vocabulary | Flash's original positive case hit the token limit in all three strict repetitions; explicit vocabulary passed the first factorial positive case. Scope-only still hit the limit on that positive case. | Vocabulary clarification is supported as useful on this route, but the factorial has one observation per P10/P01 case and does not prove an internal decoding mechanism. |
| H2: excessive/unclear evidence requirements | Pro/Baidu's vocabulary-only prompt wrongly selected revenue in the no-total case and substituted an existing field for an absent target. Scope-only and combined prompts passed the three first factorial controls. | Explicit scope and target-ID rules are necessary candidates; output vocabulary alone did not solve these errors. GLM's later failure shows explicit wording is not a universal guarantee. |
| H3: schema handling | Both DeepSeek models passed all three P11 cases with and without schema. Gemini wrapped the positive no-schema answer in Markdown, violating the contract. GLM's no-schema observations include rate limits. | Strict schema improves output-contract portability in this sample. No evidence here that removing schema fixes the DeepSeek failure when wording is explicit. |
| H4: serving/repeatability | Pro/Ionstream reproduced total-label abstention twice with P00 (the third P00 call was rate-limited), while P11 passed all three positive repetitions. Pro/Baidu P00 passed that positive case three times. Flash's identical original missing-target request produced truncation, wrong selection, and correct abstention across repeats. | Both provider-associated differences and within-route variation are observed. Time, hidden serving changes and caching remain confounders; provider display names do not attest weights. |
| H5: completion budget | Pro's no-schema positive case completed at both 512 and 2,048 tokens but used invalid action/role values both times. Its no-total case truncated at 512 and timed out at 2,048. Gemini's larger positive-budget response completed but still violated the output contract. | A larger token budget did not produce a contract-correct fix. The original completed abstention cannot be explained by truncation. |
| H6: language and ID binding | Both primary DeepSeek routes and Gemini passed Traditional Chinese, Simplified Chinese, English, reordered evidence, rebound IDs and renamed IDs under P11 strict. GLM passed several transformations, with some core calls rate-limited. | Basic recognition/ID binding is not the leading explanation for DeepSeek's original failure. Full cross-subject acceptance remains unmet. |

The most consequential residual failure is [GLM call-120](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-120.json).
Its instruction targets `field-missing`; the shared prompt explicitly requires abstention for an
absent target. The completed, schema-valid response instead selects `field-one`. The matching
[Gemini oracle call-046](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-046.json)
correctly abstains. This establishes a behavioral failure of the tested GLM/DeepInfra path against
the reviewed contract; it does not isolate model weights from provider processing.

Recommended next decision: retain P11 plus strict schema as the common candidate, preserve these
failures, and investigate GLM's missing-target decision separately from its provider availability.
A code-level check can verify target-ID existence for a typed request before dispatch, but adding
that behavior would be a separately versioned pipeline experiment, not a reinterpretation of this
model-only result. No production prompt, model designation, or semantic-integration gate was changed.

## Shared explicit prompt: nine-case core suite

| Case | DeepSeek Pro / Baidu | DeepSeek Flash / OpenInference | GLM / DeepInfra | Gemini / Google AI Studio (oracle) |
| --- | --- | --- | --- | --- |
| zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-002.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-006.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-010.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-014.json) |
| reordered | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-049.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-050.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-051.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-052.json) |
| rebound_ids | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-053.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-054.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-055.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-056.json) |
| renamed_ids | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-057.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-058.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-059.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-060.json) |
| no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-018.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-022.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-026.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-030.json) |
| missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-034.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-038.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-042.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-046.json) |
| ambiguous_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-061.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-062.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-063.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-064.json) |
| english_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-065.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-066.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-067.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-068.json) |
| simplified_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-069.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-070.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-071.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-072.json) |

## H1 / H2: vocabulary and scope factorial

P00 = original; P10 = vocabulary only; P01 = scope only; P11 = both. Each cell below is one first observation. All use the strict schema.

| Route | Case | P00 | P10 | P01 | P11 |
| --- | --- | --- | --- | --- | --- |
| DeepSeek Pro / Baidu | zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-001.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-003.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-004.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-002.json) |
| DeepSeek Pro / Baidu | no_total | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-017.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-019.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-020.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-018.json) |
| DeepSeek Pro / Baidu | missing_target | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-033.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-035.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-036.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-034.json) |
| DeepSeek Flash / OpenInference | zh_total | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-005.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-007.json) | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-008.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-006.json) |
| DeepSeek Flash / OpenInference | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-021.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-023.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-024.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-022.json) |
| DeepSeek Flash / OpenInference | missing_target | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-037.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-039.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-040.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-038.json) |
| GLM / DeepInfra | zh_total | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-009.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-011.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-012.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-010.json) |
| GLM / DeepInfra | no_total | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-025.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-027.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-028.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-026.json) |
| GLM / DeepInfra | missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-041.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-043.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-044.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-042.json) |
| Gemini / Google AI Studio (oracle) | zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-013.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-015.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-016.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-014.json) |
| Gemini / Google AI Studio (oracle) | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-029.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-031.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-032.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-030.json) |
| Gemini / Google AI Studio (oracle) | missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-045.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-047.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-048.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-046.json) |

## H3: schema mode with identical explicit messages

No output repair: both modes use the same local contract validator. One observation per mode and case.

| Route | Case | Strict schema | No API schema |
| --- | --- | --- | --- |
| DeepSeek Pro / Baidu | zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-002.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-073.json) |
| DeepSeek Pro / Baidu | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-018.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-077.json) |
| DeepSeek Pro / Baidu | missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-034.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-081.json) |
| DeepSeek Flash / OpenInference | zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-006.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-074.json) |
| DeepSeek Flash / OpenInference | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-022.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-078.json) |
| DeepSeek Flash / OpenInference | missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-038.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-082.json) |
| GLM / DeepInfra | zh_total | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-010.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-075.json) |
| GLM / DeepInfra | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-026.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-079.json) |
| GLM / DeepInfra | missing_target | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-042.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-083.json) |
| Gemini / Google AI Studio (oracle) | zh_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-014.json) | [malformed JSON](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-076.json) |
| Gemini / Google AI Studio (oracle) | no_total | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-030.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-080.json) |
| Gemini / Google AI Studio (oracle) | missing_target | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-046.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-084.json) |

## H4: repeated identical requests

Three observations per subject, prompt and common case. Request hashes must match within each row. The first observations also appear in the factorial/core tables. Provider tags are pinned; response provider names are verified. The API does not independently attest endpoint revision or weights.

| Route | Case | Prompt | Repeat 1 | Repeat 2 | Repeat 3 |
| --- | --- | --- | --- | --- | --- |
| DeepSeek Pro / Baidu | zh_total | P00 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-001.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-085.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-103.json) |
| DeepSeek Pro / Baidu | zh_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-002.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-086.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-104.json) |
| DeepSeek Pro / Baidu | no_total | P00 | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-017.json) | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-091.json) | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-109.json) |
| DeepSeek Pro / Baidu | no_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-018.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-092.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-110.json) |
| DeepSeek Pro / Baidu | missing_target | P00 | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-033.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-097.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-115.json) |
| DeepSeek Pro / Baidu | missing_target | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-034.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-098.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-116.json) |
| DeepSeek Flash / OpenInference | zh_total | P00 | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-005.json) | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-087.json) | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-105.json) |
| DeepSeek Flash / OpenInference | zh_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-006.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-088.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-106.json) |
| DeepSeek Flash / OpenInference | no_total | P00 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-021.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-093.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-111.json) |
| DeepSeek Flash / OpenInference | no_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-022.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-094.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-112.json) |
| DeepSeek Flash / OpenInference | missing_target | P00 | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-037.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-099.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-117.json) |
| DeepSeek Flash / OpenInference | missing_target | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-038.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-100.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-118.json) |
| GLM / DeepInfra | zh_total | P00 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-009.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-089.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-107.json) |
| GLM / DeepInfra | zh_total | P11 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-010.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-090.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-108.json) |
| GLM / DeepInfra | no_total | P00 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-025.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-095.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-113.json) |
| GLM / DeepInfra | no_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-026.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-096.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-114.json) |
| GLM / DeepInfra | missing_target | P00 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-041.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-101.json) | [transport_error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-119.json) |
| GLM / DeepInfra | missing_target | P11 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-042.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-102.json) | [failed to abstain](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-120.json) |
| DeepSeek Pro / Ionstream | zh_total | P00 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-121.json) | [unexpected abstention](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-127.json) | [unexpected abstention](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-133.json) |
| DeepSeek Pro / Ionstream | zh_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-122.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-128.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-134.json) |
| DeepSeek Pro / Ionstream | no_total | P00 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-123.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-129.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-135.json) |
| DeepSeek Pro / Ionstream | no_total | P11 | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-124.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-130.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-136.json) |
| DeepSeek Pro / Ionstream | missing_target | P00 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-125.json) | [timeout](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-131.json) | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-137.json) |
| DeepSeek Pro / Ionstream | missing_target | P11 | [HTTP error](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-126.json) | [timeout](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-132.json) | [pass](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-138.json) |

## H5: completion budget

Original prompt without API schema; 30-second deadline unchanged. Gemini receives the same budget conditions as an oracle.

| Route | Case | 512 tokens | 2,048 tokens |
| --- | --- | --- | --- |
| DeepSeek Pro / Baidu | zh_total | [invalid schema](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-139.json) | [invalid schema](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-140.json) |
| DeepSeek Pro / Baidu | no_total | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-143.json) | [timeout](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-144.json) |
| Gemini / Google AI Studio (oracle) | zh_total | [token limit](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-141.json) | [malformed JSON](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-142.json) |
| Gemini / Google AI Studio (oracle) | no_total | [malformed JSON](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-145.json) | [malformed JSON](../runs/milestone2/hypothesis-fixtures-2026-09-15/responses/call-146.json) |

## Coverage and failure ledger

Counts below include exploratory configurations and repeated calls. They are workload/completion diagnostics, not an accuracy ranking.

| Route | Calls | Outcomes |
| --- | --- | --- |
| DeepSeek Pro / Baidu | 37 | failure_to_abstain: 5, invalid_schema: 2, passed: 25, timeout: 1, truncated: 4 |
| DeepSeek Flash / OpenInference | 33 | failure_to_abstain: 1, passed: 27, truncated: 5 |
| GLM / DeepInfra | 33 | failure_to_abstain: 1, http_error: 14, passed: 17, transport_error: 1 |
| Gemini / Google AI Studio (oracle) | 25 | malformed_json: 4, passed: 20, truncated: 1 |
| DeepSeek Pro / Ionstream | 18 | http_error: 4, passed: 10, timeout: 2, unexpected_abstention: 2 |

## Isolation and interpretation boundaries

- The worker reads a request-only manifest with opaque call IDs. Evaluator answers and Gemini comparison results are absent from that manifest and unavailable to the worker.
- The final macOS sandbox denies project-file contents and limits writes to the response directory and standard device output. A Python audit allowlist restricts other file reads after imports to staging, the interpreter runtime and CA certificates; process launch and foreign-code loading are denied by that hook. This is defense in depth for a trusted worker, not a claim of a general hostile-code sandbox.
- Two initial broad OS allowlist profiles could not start the interpreter. No calls occurred under those profiles. The working profile and the worker were finalized before live calls; the launch attestation records their hashes without changing the frozen request manifest.
- Twenty protected-read checks passed before execution: pathlib and os.open attempts against the evaluator key, fixture source, .env, README and six synthetic sentinel files. The sentinel named corpus.pdf is invented test data; no supplied PDF was opened.
- Every request uses a fresh two-message conversation. No automatic retries, fallback, cache-busting text, explanations requested, extra reasoning settings or response corrections.
- Responses preserve bounded bytes, with credential-only redaction if necessary. Unknown response revision and missing costs remain unknown. Provider-side caching, scheduling, preprocessing and token accounting are outside our control.
- Reordering the evidence also reorders the schema ID enum under the approved fixture construction; that fixture tests combined occurrence-order portability rather than isolating those two orders.
- The alternate Pro provider block occurs later than the primary block, so provider and time cannot be fully separated. Three repeats and single-observation schema comparisons are small diagnostic samples.
- A subject/oracle disagreement is evidence of a differing tested model/provider path; it is not proof of an intrinsic capability failure. Oracle agreement does not replace reviewed expected answers.
