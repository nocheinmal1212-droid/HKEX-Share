# SCORING.md

**Bundle:** HKEX Annual Report Audit — Hang Lung Properties (00101.HK)
**Spec version:** 1.1.0
**Supersedes:** 1.0.0. Results are not comparable across these versions (§13).

Defines what counts as a detection, what counts as a mistake, and which number goes on the slide.
`harness/match.py` implements this file exactly; where the two disagree, this file wins.

**What this bundle measures.** One report, one issuer, deliberately. Recall and precision here are
statements about *this template*. Evidence that the system generalizes comes from the portability
gates in §7, not from the scores. Both are required; neither substitutes for the other.

---

## 1. Scope

**Scored (6):** `primary_statement_articulation`, `internal_note_reconciliation`,
`statement_to_note_articulation`, `disclosure_reference_verification`,
`document_wide_consistency`, `formatting_typography_validation`.

**Descoped (3):** `inter_note_articulation`, `table_structural_integrity`,
`textual_semantic_integrity`.

Descoped ground truth **stays in the bundle** with `scoring_status: "descoped"`. Those injections are
still physically in the document. Delete the records and every correct detection of them becomes an
unexplained false alarm, deflating precision by exactly 18 findings. They resolve to `NEUTRAL` (§5)
and enter no numerator or denominator.

The system keeps emitting the full nine-code vocabulary. Only scoring is restricted to six.

**Contamination.** A scored record sharing a `table_id` with a descoped record carries
`contaminated_by: [...]`. Scored normally in the headline, reported as a separate subset so a recall
gap concentrated there reads as a corpus defect rather than a detector weakness.

---

## 2. Definitions

**GT** — one ground-truth record. **DUT** — one document under test.

**Finding** — one line of the system's `findings.jsonl`. Scoreable only with all of:
`doc_id`, `location` (at minimum `table_id` or `section_id`), `category_code`, `confidence`,
`evidence` (non-empty). Missing any field ⇒ malformed ⇒ counted as a false positive. An
unlocalisable alert costs a reviewer as much as a wrong one.

**Abstention** — a check declining to run, emitted to `abstentions.jsonl` with `check_id`,
`table_id`, and `reason`. Abstention is **not** a finding and is never scored as one. It is the
architecturally preferred failure mode and is measured in §6.5, but it earns no recall credit: a
system cannot score by declining.

**Site** — a distinct injection location, identified by `site_id`. Several GT records at different
magnitudes may share one `site_id`. This distinction drives §9 and is not optional.

---

## 3. Match levels

| Level | Criterion |
|---|---|
| **L2** cell | `table_id` + `row_key` + `column_key` all equal |
| **L1** container | `table_id` (or `section_id`) equal |
| none | no match |

**L1 is the headline level.** A check that finds a broken footing but names the total row instead of
the corrupted component row has done everything a reviewer needs. L2 is reported separately as
*localisation rate* = L2-matched TPs / all TPs.

L0 (page-level) is removed in 1.1. It was diagnostic-only and let a system score by naming a page.

Keys are compared after normalisation (lowercase, collapsed whitespace, stripped punctuation, NFKC),
applied identically to GT and findings in `harness/normalize.py`.

---

## 4. Matching

**4.1 Location only.** `category_code` does not affect eligibility or cost. A finding that locates an
error correctly but mislabels it has detected the error; classification is scored afterwards (§6.3).

**4.2 Discrepancy pairs.** For `statement_to_note_articulation`, `disclosure_reference_verification`
and `document_wide_consistency`, GT carries `location` plus `secondary_locations`. A finding matching
**either end** is a TP. Which end it named is scored as attribution (§6.4) and never gates recall.

**4.3 Optimal assignment.** Minimum-cost bipartite matching per DUT (Hungarian). Cost 0 for L2, 1 for
L1. Ties break by ascending `(error_id, finding_index)`. Greedy matching is forbidden: its result
depends on output ordering, so a refactor silently changes scores.

**4.4 Cardinality.** One GT ↔ at most one finding. Surplus findings inside an already-matched table —
one injection tripping the footing, subtotal and articulation checks — resolve to `NEUTRAL_SURPLUS`,
not FP. Penalising corroboration pushes the design toward suppressing evidence.

---

## 5. Outcome classes

| Class | Condition | Precision denom | Recall denom |
|---|---|---|---|
| `TP` | finding assigned to a scored GT | yes | hit |
| `FN` | scored GT with no assigned finding | — | miss |
| `FP` | finding matching no GT, no allowlist | yes | — |
| `FP_DISTRACTOR` | matches `distractors.jsonl` | yes, **×3** | — |
| `NEUTRAL_DESCOPED` | matches a descoped GT | no | no |
| `NEUTRAL_SURPLUS` | co-located with a matched GT | no | no |
| `NEUTRAL_KNOWN` | matches `known_real_anomalies.jsonl` | no | no |
| `EXCLUDED` | `expected_detectable: false`, or band `within_tolerance`, or `status != active` | — | no |

Distractors carry triple weight because flagging a legitimately restated comparative or an "of which"
memo row is the specific failure that makes an audit tool unusable. Flat weighting lets it hide in
the noise floor.

**Every `FN` carries a `miss_type`**, assigned by the harness from `abstentions.jsonl`:

| `miss_type` | Meaning |
|---|---|
| `abstained` | An applicable check declined, with a reason |
| `attempted` | A check ran and did not fire |
| `no_check` | No check covers this GT's category at this site |
| `crashed` | The check raised |

All four are misses. The split is the most useful diagnostic in the bundle: `abstained` misses point
at extraction and labelling coverage, `attempted` misses point at check logic.

---

## 6. Metrics

**6.1 Precision — single-template, one clean document.** Computed on `base/00101_clean.md` plus
`distractors.jsonl`. Never on injected documents: their FP denominator is unknowable, containing the
base report's genuine anomalies, extraction artifacts, and 18 descoped injections.

```
alert_rate = weighted_FP_count / (pages / 100)
```

Report this as **"alerts per 100 pages, Hang Lung template"**. It says nothing about other issuers
and must not be labelled as though it does.

**6.2 Recall — banded, never blended.** Report `above_tolerance` and `boundary` separately;
`within_tolerance` is a non-headline stretch set. Headline covers the first two.

**6.3 Classification accuracy** over TPs. Publish the 9×9 confusion matrix including descoped codes
as prediction targets.

**6.4 Attribution accuracy** over TPs on paired categories: did the finding name the side GT marks
as corrupted.

**6.5 Coverage.** Reported alongside every recall figure, never separately:

| Metric | Definition |
|---|---|
| `table_parse_rate` | tables with resolved row hierarchy / total tables |
| `label_resolution_rate` | labels mapped to a canonical concept / total labels |
| `lexicon_hit_rate` | resolved from `lexicon.yaml` / all resolved (remainder = LLM fallback) |
| `check_coverage` | checks executed / checks applicable |
| `abstention_rate` | 1 − `check_coverage` |

**Recall MUST NOT be published without `check_coverage` beside it.** A system that skips 40% of
tables and gets the rest right shows high recall and is useless. On an unfamiliar template coverage
collapses before accuracy does, which makes it the earlier warning.

`lexicon_hit_rate` is also the extension-cost signal: the LLM-fallback log is the list of entries a
second issuer would need.

**6.6 Magnitude-response curve.** From the size sweeps, plot detection rate against
`|value_delta| / tolerance_bound`. This, not a single recall figure, is the payoff of sweeping — it
gives the size at which detection breaks down.

**Removed in 1.1:** `P@k`. It requires calibrated confidence, which this PoC will not produce.
Reinstate when calibration exists.

---

## 7. Gates

The headline is reported only when **all** gates pass. Gates fail closed: no greyed-out number, no
caveated number.

**7.1 Portability gate A — no report-specific facts.**
`tools/lint_literals.py` fails if any entry in `blocklist.txt` (issuer names, stock code, Hang Lung
note numbers, its distinctive row labels, page numbers) appears anywhere under `pipeline/`.
Binary, no partial credit.

**7.2 Portability gate B — invariance.**
Meaning-preserving transformations of the DUT must not change findings, modulo the transformation's
own mapping.

| ID | Transformation | Exempt categories |
|---|---|---|
| T1 | Renumber all notes, updating every cross-reference consistently | — |
| T2 | Replace entity name and stock code throughout | — |
| T3 | Rescale HK$m → HK$'000 with matching unit labels | `formatting_typography_validation` |
| T4 | Swap negative style: `(1,234)` ↔ `-1,234`, applied consistently | `formatting_typography_validation` |
| T5 | Substitute row labels with `lexicon.yaml` synonyms | — |
| T6 | Reorder independent notes | `disclosure_reference_verification` |

Pass condition: for non-exempt categories, the set of findings after applying the inverse mapping is
identical. Exemptions exist because T3 and T4 legitimately alter the formatting checks' subject
matter and T6 alters note ordering; exempt categories are still run and their diffs logged, but
differences there do not fail the gate.

A single diff on a non-exempt category fails the run. Rationale: a leaked literal breaks the next
issuer completely rather than gradually, so partial credit would be misleading. These transformations
run on the file we already have — this is the whole of our generalization evidence at PoC scale, and
it costs a script rather than a corpus.

**7.3 Precision gate.** `alert_rate <= ALERT_BUDGET` (§15).

---

## 8. Headline

**Gated Pooled Recall (GPR)** — pooled L1 recall over scored, in-band, non-excluded GT across all six
categories, valid only if §7 passes. Otherwise the run reports `UNGATED` and no recall figure.

Pooled, not averaged across categories. At ~15 records per category the per-category rates are noise;
pooling gives a denominator worth quoting. **Per-category recall is always diagnostic, never
headline** — this replaces 1.0's `n < 15` marker, which everything now clears by a hair and which was
therefore decoration.

F1 is not used anywhere: §6.1 and §6.2 sit on different corpora, so it would be arithmetic on
incommensurable quantities.

---

## 9. Uncertainty — cluster on sites, not records

**Size sweeps break independence.** Four magnitudes injected at one site are four records but one
independent observation. Treating them as four inflates apparent precision of the estimate by roughly
√(records/sites) — with 15 records over 4 sites the naive interval is about half its true width. That
is false confidence, which is worse than no confidence.

Therefore:

- Every GT carries `site_id`.
- Confidence intervals use a **cluster bootstrap**: resample `site_id`s with replacement, 10,000
  iterations, seed recorded. Never a plain Wilson interval on record counts.
- Report `n_records` **and** `n_sites` on every figure. A figure printed with only `n_records` is
  non-compliant.
- Run-to-run comparison uses McNemar's test on paired per-record outcomes, clustered by site.

These intervals describe uncertainty about generalisation to unseen *errors on this template*. For
the four deterministic categories run noise is zero, so a tight interval means the sample is
consistent, not that the detector is reliable. State this in the report; the misreading is common.

---

## 10. Determinism and seeds

- Deterministic categories: byte-identical `findings.jsonl` across runs. CI asserts it.
- Hybrid categories (`statement_to_note_articulation`, `document_wide_consistency`): `n_seeds >= 3`
  at temperature 0. Median is headline, min–max reported as `seed_spread`. Spread above 10pp is
  flagged — temperature 0 is not deterministic across batching and hardware, and a wide spread means
  the LLM is carrying more of the decision than the architecture intends.
- Every run records `model_id`, model revision, quantisation, serving stack and version, and the
  prompt-template hash. Runs differing in any of these are different systems.

---

## 11. Failures

| Event | Treatment |
|---|---|
| Pipeline crash on a DUT | All its scored GTs count `FN` / `crashed` |
| Timeout beyond `RUNTIME_BUDGET` | Same |
| Malformed finding line | That finding is an `FP` |
| Check raises, pipeline continues | Affected GTs `FN` / `crashed`; run flagged `degraded` |

Excluding failed documents would let a system raise its score by crashing on hard inputs.

---

## 12. Dev / held-back split — at site level

Splitting records would put four magnitudes of the same injection on both sides of the wall, leaking
the site. **Split assigns whole `site_id`s**, by hashing `site_id` against a fixed salt, immutable
once assigned.

- ~⅓ of sites held back.
- The held-back set is scored **pooled only**, never per category — roughly 30 records over ~10 sites
  is too thin for category-level claims.
- Held-back scoring happens at declared milestones, once each, logged to `results/heldback_runs.log`
  before the score is read. Any other held-back run is `exploratory` and appears in no report.
- All tuning happens on the dev sites.

---

## 13. Result artifact

`results/<run_id>/result.json`, append-only, immutable:

```json
{
  "run_id": "…", "spec_version": "1.1.0", "bundle_version": "…", "split": "dev",
  "system": {"pipeline_sha": "…", "model_id": "deepseek-v4-flash",
             "serving": "…", "prompt_template_sha": "…", "n_seeds": 3},
  "gates": {"literals_lint": "pass",
            "invariance": {"status": "pass", "failed_transforms": []},
            "alert_rate": 6.2, "alert_budget": 8.0, "precision_gate": "pass",
            "all_passed": true},
  "headline": {"gated_pooled_recall": 0.78, "ci95": [0.63, 0.88],
               "n_records": 92, "n_sites": 24, "valid": true},
  "coverage": {"table_parse_rate": 0.86, "label_resolution_rate": 0.91,
               "lexicon_hit_rate": 0.74, "check_coverage": 0.83},
  "bands": {"above_tolerance": 0.85, "boundary": 0.51, "within_tolerance": 0.08},
  "per_category": [{"code": "…", "revision": 1, "recall": 0.92,
                    "n_records": 15, "n_sites": 4, "diagnostic_only": true}],
  "misses": {"abstained": 9, "attempted": 11, "no_check": 0, "crashed": 0},
  "secondary": {"classification_accuracy": 0.81, "attribution_accuracy": 0.64,
                "localisation_rate_l2": 0.73},
  "neutral": {"descoped": 14, "surplus": 31, "known": 4},
  "failures": {"crashed_docs": [], "degraded": false}
}
```

Comparable only when `spec_version`, `bundle_version`, `split` and every
`(category_code, category_revision)` pair match. The harness refuses to render a comparison
otherwise and names the differing field rather than degrading gracefully.

---

## 14. Worked adjudications

Binding precedent. Extend this list rather than reinterpreting §3–§5.

1. Footing failure reported at the total row; GT says the corruption is in `additions` of the same
   table → **TP** at L1, non-L2.
2. "Note 21 total ≠ balance-sheet cash", naming only the Note 21 end; GT's primary is the other end →
   **TP**. Attribution takes the miss.
3. One injection trips three checks in one table → one **TP**, two `NEUTRAL_SURPLUS`.
4. System correctly flags a `table_structural_integrity` injection → `NEUTRAL_DESCOPED`.
5. System flags a restated comparative listed in `distractors.jsonl` → `FP_DISTRACTOR`, ×3.
6. Finding gives `table_id` but no row or column → eligible at L1, **TP**, non-L2.
7. Finding says "this document contains errors", `doc_id` only → malformed, **FP**.
8. GT band is `within_tolerance` and the system finds it → `EXCLUDED` from headline, credited in the
   stretch set. The sensitivity that caught it is generating clean-document alerts that §7.3 prices.
9. Check abstains on the table holding a scored GT, with a reason → **FN**, `miss_type: abstained`.
   No credit for abstaining; the diagnostic split is the reward.
10. Scored GT in a table also carrying a descoped injection, missed → **FN** in the headline, also
    reported under `contaminated_n`.
11. Invariance transform T5 changes one finding on `statement_to_note_articulation` → run
    **UNGATED**, no headline, regardless of recall. Non-exempt category.
12. T3 changes findings on `formatting_typography_validation` only → gate passes; diff logged.

---

## 15. Open parameters

Fixed before the first scored run, never adjusted afterwards to improve a result.

| Parameter | Method |
|---|---|
| `ALERT_BUDGET` | Reviewer tolerance first, sanity-checked against the clean Hang Lung report. Provisional: 8 alerts / 100 pages. |
| `RUNTIME_BUDGET` | Wall clock per DUT. |
| Distractor weight | 3, fixed. |
| Bootstrap seed | Fixed and recorded. |

Setting `ALERT_BUDGET` after seeing a run's alert rate turns the gate into a rubber stamp. Fix it
from the clean document and stated reviewer tolerance, in that order, and record the date.

---

## Appendix A — Unseen-issuer smoke run (diagnostic, not scored)

**Optional. Not a gate. Produces no score.** Three clean annual reports from other HKEX issuers
(suggested: a bank, a small-cap, one reporting in RMB), unlabelled. Run the pipeline and record only:

`table_parse_rate`, `label_resolution_rate`, `lexicon_hit_rate`, `check_coverage`,
`abstention_rate` with reason histogram, raw alert count, crash count.

No recall, no precision — there is no ground truth. The output is a coverage profile, and it is the
most direct evidence available for "does this fall over on an unfamiliar template". Roughly an
afternoon's work. Cut it if the budget doesn't allow; nothing else in this document depends on it.