# Two-query development confirmation — live v2 results

**Execution completed within the approved budget, but the semantic confirmation failed: primary
0/2 complete successes; research 0/2.** Both primary answers selected the reviewed contributors.
All four responses supplied only the relevant group citation, omitting the target and contributor
citations. Research additionally returned incompatible answer states while retaining contributors.
No operational annotation was accepted. No retry, repair or further provider call followed.

## Approved identity and credential supply

The owner approved freeze
`46c1b25173abf95490caf42b1d589de84237284afde81ce198910f9c9475c0ae`, exactly `total` then
`period_groups`, nonce/output `live-v2`. The [immediate default prelaunch check](../runs/semantic-citation-confirmation-2026-09-19/execution-v2-env/immediate-prelaunch-check.json)
passed before credential access or provider activity. All **3,116** bound files remained unchanged
through post-run verification. No requests, runtime files, evaluation expectations or hashes were
regenerated. See the [approved packet](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/README.md)
and [exact launch argv](../eval/semantic-citation-confirmation/2026-09-19/preflight-v2/launch-proposal.json).

An earlier approved launch check found no key in the execution environment and stopped before
creating live-v2 or making calls; its [not-started receipt](../runs/semantic-citation-confirmation-2026-09-19/execution-v2/launch-not-started.json)
remains intact. The owner's subsequent instruction, “Check .env at root,” supplied the missing
credential source. The [execution wrapper](../runs/semantic-citation-confirmation-2026-09-19/execution-v2-env/launch-approved.py)
extracted the required OPENROUTER_API_KEY entry and passed it to the unchanged argv's
environment. It did not source shell code, print/save the value or forward other .env entries.
The frozen CLI credential-file bootstrap setting remains false; no CLI option or execution binding
changed. [Authorization/provisioning records](../runs/semantic-citation-confirmation-2026-09-19/execution-v2-env/authorization.json)
preserve this owner instruction separately from the immutable preparation proposal.

## Budget and execution outcome

| Measure | Observed | Approved ceiling |
|---|---:|---:|
| HTTP calls | 6: 2 metadata GETs + 4 completions | 6 |
| Primary completions | 2 | 2 |
| Research completions | 2 | 2 |
| Full launcher elapsed, including final receipt publication | 47.784289 seconds | 600 seconds |
| Conservative completion reservation | $3.659580 | $8 |
| Provider-reported completion cost, four records | $0.097904004 | Reservation bounded above |
| Retries/fallbacks/substitutions | 0 | 0 |

The [supervisor receipt](../runs/semantic-citation-confirmation-2026-09-19/live-v2/supervisor.json)
reports finished, no total timeout and the direct child reaped; the
[outer launcher receipt](../runs/semantic-citation-confirmation-2026-09-19/execution-v2-env/launcher-exit.json)
records return code zero and the elapsed launcher time, including final receipt publication. Per-attempt
limits remained 60 seconds, with the unchanged 4096-token cap and native reasoning configuration.
All four completions ended with `finish_reason=stop`; none was truncated or timed out.

Both metadata GETs returned HTTP 200 and passed the frozen route/model/provider/control/price checks.
All completions returned the required served identities: Gemini 3.8 Flash / Google AI Studio for
primary, DeepSeek V4.1 Flash / Together for research. Metadata findings apply to this execution, not
a promise of future route availability or pricing. Metadata cost is not reported in these records;
its absence is not interpreted as a zero-cost guarantee. The precise reported sum covers the four
completion records only. No mutable-alias reproducibility guarantee is inferred.

[Accounting](../runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/accounting.json)
records six request-boundary entries with returned evidence; no call has unknown accounting here.
The first missing-environment check made no calls and did not consume this provider budget. Task B's
exhausted budget was not reused.

## Frozen evaluation outcomes

The [bound evaluator output](../runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/evaluation.json)
keeps availability, schema/host validation, exact reviewed contributor/state agreement and required
support separate. All responses were available and schema-valid; all failed host validation.

| Case | Primary | Research | Required citations |
|---|---|---|---|
| `total` | `selected`; correct 合計 + 租賃(HKFRS 16) IDs | Same contributor IDs, but `ambiguous` with a nonempty list | Only 來自與客戶合約之收入(HKFRS 15) supplied; target and both contributors missing |
| `period_groups` | `selected`; correct three 2025 peer IDs | Same contributor IDs, but `not_a_total` with a nonempty list | Only 2025 supplied; target and all three contributors missing |

For both primary answers, the independent exact contributor/state comparison passed, while required
source support failed. For research, the contributor IDs match separately, but its answer states fail
the reviewed `selected` requirement; the evaluator correctly reports the combined contributor/state
check as false. Neither response is a valid abstention with its retained contributors.

The runtime's first rejection for all four is **`target support absent`**. The separate
[source-ID diagnostics](../runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/response-diagnostics.json)
record the additional omitted contributor citations and research state/list contradictions without
editing or revalidating a repaired answer. Group citation presence alone is insufficient. Parsed
candidates are evaluator-only diagnostics, never accepted semantic annotations.

The denominator remains two cases per role. Primary accepted annotations are empty for both cases,
with provenance outcome `invalid_output`. Research was not used as annotation input, fallback,
consensus or veto. This does not establish downstream financial isolation from empty outputs.
The single-column-unit-plus-lease counterexample remains the separately retained authored offline
failure; it was not added as a live case. G3, G4 revision 2, G5 and blank target remain separate
zero-call controls; nested Continued remains an offline regression.

## Post-run verification and preservation

[Verification](../runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/verification.json) confirms:

- All four persisted requests are byte-identical to the approved fresh live-v2 requests.
- The evaluator ran against the frozen expected sources and made zero provider calls.
- Primary and research were independently replayed under the corrected retained runtime snapshot,
  with zero new calls. Both primary annotation/provenance pairs are byte-identical to their originals;
  they retain the failed outcomes rather than fabricate a repaired pass.
- Actual primary consumption guard records exclude research and evaluator paths and adapter imports.
- All 3,116 approved freeze members remain unchanged; the old no-go digest
  `f98cab8947112698dc2e8d58ba30441dc6d8f40f3d1a35125994ce50a34e7643` is preserved. The old live-v1
  directory remains nonexistent. No frozen packet or completed operational artifact was rewritten.

The post-run checks read member hashes directly. The launch gate is not rerun against an already-used
output: it is correct for that gate to reject a second launch into live-v2. No second attempt is allowed
by this run's authorization. [Artifact integrity](../runs/semantic-citation-confirmation-2026-09-19/evaluation-v2/artifact-integrity.json)
binds the live output, execution/evaluation receipts, diagnostics and this report. No commit, dependency
installation, agent delegation, raw PDF/native corpus inspection, clean counterpart or held-back
outcome was needed.

## Decision

The execution correction worked for this bounded run; **the selected semantic configuration remains
unaccepted on these two development cases**. No automatic follow-up inference is scheduled. Any
future correction should first examine the citation/state failure offline under a separately scoped
instruction, preserving these exact responses and the existing semantic-policy boundary.

Historical **0/4 complete frozen support**, three research truncations and the earlier invalid research
abstention remain unchanged; this new run is separate evidence, not a repaired historical result.
These are exposed development cases, not holdout/statistical evidence or human/domain acceptance.
Saved-IR semantic acceptance and Milestone 2 remain open. No numerical compatibility or downstream
financial-isolation claim follows from this confirmation.
