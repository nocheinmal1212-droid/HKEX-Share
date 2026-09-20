# Header-semantic citation investigation — offline correction proposal

**Proposed decision: require decision-bearing context, not a universal common-unit citation.**
The shared `港幣百萬元` occurrence does not distinguish the header memberships in either original
table. Keep it literal in the source/projection and available in the trace; make its response citation
optional for this header-only operation. This says nothing about readiness for numerical comparison.
The later planner must still establish currency, scale, period, entity, basis and completeness.

This is an offline investigation and a reviewable proposal, **not an implemented correction or a
new acceptance pass**. Work started at exact `e8000e2c001983f1f65fac75de97945c628a2287`.
The pre-existing untracked handoff was preserved. No provider/model calls, network calls, PDFs,
injector metadata, clean counterpart, evaluation operands or held-back outcomes were used.
The deliberately delegated source reviewer is an independent **agent**, not human/domain approval.

## Evidence and historical result

The [machine-readable trace](../eval/semantic-citation-investigation/2026-09-19/diagnostics/evidence-trace.json)
records exact target/contributor/support IDs, source fragments, attempt identities, review pointers and
artifact paths for each query. Original root:
[`live-v1`](../runs/paired-semantic-integration-2026-09-18/live-v1/summary.json).
For each row, `/primary/NAME/{query,request,response,result,completion}.json` and
`/operational/NAME/{annotations,provenance,consumption}.json` are the retained chain.

| Original query | Request input | Selection | Schema / host / persisted annotation | Frozen evaluator | Research execution |
|---|---|---|---|---|---|
| `total` | Literal unit and correct source ID present | Subtotal + lease header match review | Pass / pass / 2 primary links | Correct contributors; only common unit absent | `length`, 4096 completion tokens; truncation |
| `subtotal` | Literal unit and correct source ID present | Two recognition-timing headers match review | Pass / pass / 2 primary links | Correct contributors; only common unit absent | `length`, 4096; truncation |
| `period_groups` | Literal unit, 2025 and 2024 groups present | Three 2025 peers match review | Pass / pass / 3 primary links | Correct contributors; only common unit absent | `stop`; `ambiguous` plus 3 contributors; invalid output |
| `varied_total` | Literal unit retained; only body placeholders varied | Same set as `total` | Pass / pass / 2 primary links | Correct contributors; only common unit absent | `length`, 4096; truncation |
| `missing_target` | Actual blank target retained | Local prerequisite failure | No response, no annotation links | Correct local `missing_evidence` mapping | Zero historical calls in both roles |

`total` and `varied_total` are correlated views of one table, not independent reports. Four eligible
observations cover two unit occurrences in two tables. The original result remains **4/4 correct
contributor sets and 0/4 complete frozen support sets**. The frozen support calculation is not a bug.

The original common-unit IDs are:

- Page index 178: `cell-b52c32ff495ebd5add32f9e2f6d31a1a4625de8f528e78aa3985617119514bfa`.
- Page index 179: `cell-86475b66755aa6e1fad2ed937c0f556b06f79b2a6176cecaf0271ff49b170ebb`.

Both have `row_span=2`, `column_span=1`, column 0. Neither meets the host's spanning-group rule.
These are fixture identities, never proposed runtime constants.

The exact code path explains the result:

1. [`semantic.project`](../src/hkex_audit/semantic.py) preserves unit literals and full table descendants.
   Saved query prompt/schema equal actual request fields; the user payload equals the projected context.
2. [`semantic.SCHEMA` and `validate_answer`](../src/hkex_audit/semantic.py#L68) validate shape,
   IDs, nonblank support, target/contributor citations, header scope, and qualifying groups **above
   the target**. Schema alone does not define particular support IDs or semantic sufficiency.
3. [`semantic_attempt.interpret` and `replay`](../src/hkex_audit/semantic_attempt.py) revalidate
   role identity, response, request and hash-bound completion. All ten saved role outcomes replayed
   with zero calls. No completion was repaired or reinterpreted as a different historical state.
4. [`semantic_cli.consume_worker`](../src/hkex_audit/semantic_cli.py#L56) reads only primary files;
   accepted answers become [`semantic.annotation`](../src/hkex_audit/semantic.py#L97) records.
   Five replays reproduced original annotation **and provenance bytes exactly**, without normalization.
5. [`review_decision`](../eval/semantic-integration/validate.py#L10) separately compares contributor
   sets and `required_support_ids ⊆ support_refs`. The pre-inference freeze accepted those unit
   requirements unchanged. Runtime does not load them.

The mismatch is between a stronger frozen expectation and the operation's explicit prompt/host
prerequisites. Saved outputs cannot distinguish model interpretation, instruction ambiguity, or a
citation omission. No context-length or reasoning-behavior causal claim follows.

## Offline controls

[`reproductions.json`](../eval/semantic-citation-investigation/2026-09-19/diagnostics/reproductions.json)
contains 24 R-case diagnostics, with copied answers explicitly marked as authored diagnostics.
They are not model completions or operational annotations.

| Control | Actual result |
|---|---|
| R1: four unchanged answers | Strict schema and host pass; contributor equality true; frozen support subset false |
| R2: add only the actual common-unit ID | Same contributors; host and frozen support subset pass |
| R2: remove target or each contributor citation separately | Host rejects with `target support absent` or `contributor support absent` |
| R3: remove only 2025 support | Host rejects with `spanning context support absent` |
| R3: select the three 2024 peers for the 2025 target | Host rejects with `incompatible spanning context` |
| R4: genuine blank target | `missing_evidence`, no call, empty annotations, unresolved opportunity retained |

An additional, specifically reproduced omission justifies a narrower host proposal:
removing only the revenue-group citation from `total` or `varied_total` still passes v1; removing it
from `subtotal` fails. The [source-only review](../eval/semantic-citation-investigation/2026-09-19/independent-source-review.md)
requires that group for the overall total because it establishes the selected subtotal's hierarchy.
The target is outside that group's span. **Necessary context can belong to a contributor's hierarchy,
not only the target's ancestors.** The original saved answers already cite this group; this new
diagnostic does not explain their original unit omissions.
See [additional boundary controls](../eval/semantic-citation-investigation/2026-09-19/diagnostics/additional-boundary-controls.json).

The same controls reject research-to-primary promotion, changed completion payload bytes and an
edited projection. The original amount-masked/varied relationship is retained as a
[development regression](../eval/semantic-citation-investigation/2026-09-19/diagnostics/amount-contrast.json).

Four [persisted authored isolation probes](../eval/semantic-citation-investigation/2026-09-19/diagnostics/isolation.json)
use offline transport stubs with separate identities. A plausible research selection supplies no
links when primary times out, has no completion, or abstains; an abstention annotation has zero links.
The slow-research probe releases research only after a nonempty primary annotation has been persisted.
Primary worker access logs contain no research reads. Stub dispatch counters are explicitly **not
provider-call counts**. These artifacts are segregated from historical model completions.
This proves behavior at the existing annotation/provenance boundary, not future plans or findings.

## Source-only adjudication and fixture freeze

The [independent review JSON](../eval/semantic-citation-investigation/2026-09-19/independent-source-review.json)
contains source-only contributor judgments, required/optional support reasons for each ID, exposure
limits and input hashes. The reviewer received no parent conversation history, saved answers, prior
review expectations, evaluator outputs, or host-validation results. Policy wording was reconciled
with this reviewer before generating G-case diagnostic responses. Literal body amounts were visible
as source material; no arithmetic or amount agreement justified a selection.

The proposed 1.1 clarification is:

- Require the target, every contributor, and source context establishing or disambiguating membership
  or hierarchy, including contributor-side groups. A shared display unit with no such function is
  optional. Unit-bearing labels that distinguish money from quantity are decision-bearing.
- `missing_evidence`: a necessary discriminator is absent, even if the target itself is nonblank.
  `ambiguous`: competing supported readings or conflicting effective statements remain unresolved.
  `incompatible_context`: target context is established and supplied candidates are affirmatively
  excluded by the source restriction. A scale difference alone does not establish this state.
- Keep target/contributor IDs in the header band. Allow support IDs for nonblank literal occurrences
  anywhere in the selected table's validated descendant inventory, including explicitly associated
  notes/captions. Blank occurrences remain in the complete input and trace; do not invent or cite a
  unit from them. This resolves a v1 documentation inconsistency: its “output IDs” header-band rule
  is narrower than current executable support validation and cannot express essential note evidence.
- Preserve empty contributors for abstentions. Execution/validation failures are not source abstentions.
  Treat table notes as evidence about the table, never instructions changing the operation or model role.

| Fixture | Source change and proposed outcome | Citation rationale |
|---|---|---|
| G1 | New derived source makes only the common-unit cell blank; subtotal + lease relationship stays `selected` | Revenue hierarchy, target and contributors required; no unit invented. Literal 2026 caption and all cell labels/spans preserved. Numeric unit context remains unknown. |
| G2 | Authored amount/quantity groups; amount total selects its two amount product occurrences | Amount-group citation discriminates otherwise repeated product labels; wrong group and missing group support rejected |
| G2 variation | Swap group order, rename/reorder products, vary body values | Membership must remain equal under the recorded occurrence mapping, not equal opaque IDs |
| G3 | Nonblank orphan total has a blank basis discriminator and an explicit same-basis restriction | `missing_evidence`, empty contributors; target, candidate groups and literal note required; absent context remains visible in complete source |
| G4 draft | Header says amount; note says quantity | Preserved as **not freeze-ready**: note could be read as correction/exception |
| G4 revision 2 | Adds explicit mutually exclusive, equally effective statements with no correction/priority | `ambiguous`, empty contributors; target, amount group and conflict note required. Artificial logical contradiction, not report realism. |
| G5 | Amount total; only quantity categories supplied; literal same-basis restriction and no bridge | `incompatible_context`, empty contributors; target, candidates, quantity group and note establish the exclusion |

G1 was not made by deleting a field from a frozen query. Its separate authored source was adapted
through the existing parser and evidence validation, then faithfully projected using unchanged v1
code. Its manifest records original HTML provenance, all cell-ID mappings and the administrative
single-page/source-identity changes. G2–G5 are authored logical sources, not claims about the report.
Parser profile strings select the existing adapter syntax; they do not claim an actual MinerU run.

All new source/expectation hashes and disposition are in
[`fixture-freeze.json`](../eval/semantic-citation-investigation/2026-09-19/fixture-freeze.json).
Exact required/optional support lists and expected/observed host outcomes are in
[`fixture-expectations.json`](../eval/semantic-citation-investigation/2026-09-19/fixture-expectations.json).
This is a review freeze for a **proposed** operation. `query-v1.json` files remain honest v1 projections;
they are not prospective 1.1 requests. Actual future prompt/code/request bindings must be frozen
after separately authorized implementation. No inference is authorized by these files.

The 38 [authored G response probes](../eval/semantic-citation-investigation/2026-09-19/diagnostics/generalization-response-pairs.json)
make the current enforcement limits concrete. All six minimal reviewed responses pass the v1 host.
G2 wrong-group choices and abstentions retaining contributors are rejected. However, v1 also accepts
the deliberately unsupported `selected` pair in G3, G4 revision 2 and G5, and accepts omission of
necessary note citations from those abstentions. These fail the proposed source review. This is
evidence of a remaining semantic enforcement boundary, not a completed fix or a schema defect.

| Frozen G source | SHA-256 of `source.json` |
|---|---|
| G1 | `8f7634859c9c46858f6cac23b7477deb581ccfd6003db7911d879f51badc802a` |
| G2 | `dca066994a3b470f7ee3f2f7b9234b2cde8442c941d54d91f5e5c3ef6f919153` |
| G2 variation | `1898719969e5e60d8ef9deeba4d856c92de5f627b730efd2724fdf958f48eaf7` |
| G3 | `27f62bea109db2573f49ad3ca877f37c2e1cd9795888c1c0f5db771240869e80` |
| G4 revision 2 | `ecca8e5066c8cc6c83008a05cd50c36a39e3f05f59ee458c111bcdbdbdf595d2` |
| G5 | `eae32564b55a09b98f47f055afa63dde298de1554ed93fbb4b2ebda872baadf8` |

Any application of the clarified policy to old responses is **post-exposure diagnostic re-evaluation**.
No revised historical headline or untouched-confirmation claim is made here.

## Smallest proposed change, by file and function — not applied

| File/function | Proposed correction and boundary |
|---|---|
| `spec/semantic-operation.md` | Preserve v1 verbatim as a versioned authority; add 1.1 conditional citation sufficiency, distinct abstention semantics, and support-vs-contributor ID domains above. State explicitly that display-unit optionality grants no numerical prerequisites. |
| `src/hkex_audit/semantic.py::VERSION, PROMPT` | Bind the clarification to a new operation/prompt version. Replace blanket “incompatible unit” wording with source-supported measurement-group discrimination and explicit missing/conflict states. Keep four response fields and unchanged schema bytes unless a separately reproduced need warrants more. |
| `semantic.py::validate_answer` | Retain current ID, nonblank support, target/contributor, group exclusion and abstention checks. For a later bounded patch, extend necessary structural support to the selected contributor's qualifying explicit spanning hierarchy, reproducing the revenue-group omission above. Derive prerequisites from runtime source relationships, never evaluator support arrays. Do not add a universal unit parser or insert missing citations. |
| `semantic.py::project, verify_query` | Retain complete descendant inventories and exact source-derived projection checks. No field deletion, inferred external-note association, amount-driven selection or invented unit. No extraction adaptation is needed. |
| `semantic_attempt.py::request, dispatch, replay`; `semantic_cli.py::prepare_worker, consume_worker` | Preserve exact v1 replay through a pinned old checkout/package or explicit version-dispatched contracts. Current code recomputes queries/requests with module constants; changing VERSION/PROMPT in place breaks replay. Verify byte-identical annotation/provenance before accepting any versioned replay path; never weaken hashes. New operational queries cannot silently select v1. |
| `spec/paired-semantic-attempts.md` | Document chosen versioned replay path and new-operation binding. Keep roles, completion integrity, zero-call replay, guards, and primary-before-research consumption unchanged. |
| New versioned evaluator expectations | Keep `review_decision` subset semantics. Load the new reviewed expectations only for new paths/operation; retain original review and evaluations unchanged. No expected support list enters the model payload. |
| Future focused semantic tests | Add the reproduced contributor-hierarchy omission, G2 mapped variation, G3/G4/G5 states and citation negatives, nonblank support, malformed/foreign IDs and edited projection controls. Retain failure/isolation and frozen v1 replay regressions. No model call is needed for these host checks. |
| README §4 / PLAN M2 | After any authorized implementation, record its version and actual verification separately. Leave historical 0/4 support result and the saved-IR acceptance gate open until their new exit evidence exists. |

Suggested replacement prompt clause, to be reviewed and bound only in the future version:

> Cite the target, every contributor, and source headers or associated notes that establish or
> disambiguate membership or hierarchy, including the hierarchy of a selected subtotal. A common
> table-wide display unit is optional when it does not determine that relationship. Unit-bearing
> group labels can distinguish measurement bases; do not select across an explicit source restriction.
> Display-scale differences alone do not disprove a conceptual header relationship. If a necessary
> discriminator is absent, return missing_evidence. If effective source statements conflict or
> supported readings remain unresolved, return ambiguous. If established target context excludes
> all supplied candidates, return incompatible_context. Abstentions have no contributors. This
> operation establishes no numerical compatibility or permission to calculate.

This does not assume a more emphatic prompt will fix behavior. The bounded host patch also does not
solve arbitrary note interpretation. Four fields can **express** G3–G5 evidence; the current host
cannot certify its semantic sufficiency. Before claiming full enforcement, define a bounded,
source-derived prerequisite for decision-bearing notes (or restrict that operation's supported
scope and leave unresolved cases blocked). Do not implement a blanket “cite all context” workaround.

## DeepSeek and unresolved questions

The separate [saved research diagnostics](../eval/semantic-citation-investigation/2026-09-19/diagnostics/research-diagnostics.json)
retain three truncations and the invalid abstention. Reported reasoning tokens are zero for the
truncations; this does not explain the generation behavior. The period answer includes the unit but
still contradicts its abstention state. There is no usable research agreement metric. No token cap,
reasoning setting, source length, state or role was changed. State-dependent schema constraints and
provider support are separate future investigations, not a remedy for this citation issue.

Remaining decisions before implementation/inference:

1. Accept or revise this source-only **agent** policy adjudication; human/domain approval is not claimed.
2. Bound the contributor-hierarchy support rule so geometry alone does not manufacture a semantic role.
   The reproduced omission warrants a targeted change, not universal unit attestation.
3. Decide the source-derived enforcement boundary for necessary notes and missing/conflicting context.
   Existing structural acceptance must not be marketed as source-semantic certification.
4. Choose explicit version dispatch or pin the old package for v1 replay; freeze new request bindings
   after separately authorized implementation. No live budget from Task B remains reusable.

The [verification record](../eval/semantic-citation-investigation/2026-09-19/diagnostics/verification.json)
checks all **127 retained hashes** and 142 protected files, including original operation/review/freeze,
runtime implementation, evaluator, schema files and the user's handoff. The final bundle inventory
records another unchanged check after report preparation. No tracked runtime, contract, original
review, request, response, annotation, completion or evaluation was edited. Full M2 and semantic
acceptance remain open.
