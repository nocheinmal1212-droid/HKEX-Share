# Independent commit and return-to-integration review — 2026-09-18

**Verdict: the model-experiment closure is correctly separated and reproducible from committed
HEAD `f539e9de1f93cc6a33b6d8c332f912411f11ab50`. Return to the main semantic-integration work.**
No experiment-archive blocker was found. The broader workspace is not clean, and this verdict
is not production acceptance or approval of pending Milestone 1 changes.

## Commit boundaries

| Commit | Verified contents |
|---|---|
| `2584415` | Five diagnostic fixture/documentation files only |
| `fcd40f0` | 34 experimental tool files and ten regression-test modules |
| `2c50596` | 1,934 saved run files, 15 documentation files, and the model-history portion of PLAN |
| `f539e9d` | Reconciled policy in AGENTS, README, PLAN, development notes, and the dated decision |

No tracked experiment, fixture or archive changes remain outside HEAD. Source-only inputs and
expectations are distinct where the later contract requires it. Earlier mixed fixture files remain
evaluator/preparation artifacts, with their worker boundary documented. H01/H02 were frozen inside
the run archive, rather than moved into the fixture directory and invalidating historical paths.
No raw corpus inputs or credential files are included in these commits. Two PDF-named files are
sentinel markers under experiment sentinel directories; this review did not read them.

## Independent verification

- Exported actual committed HEAD to a fresh temporary directory, excluding all unstaged/untracked
  work. Its complete included suite passes **79 tests**. The workspace passes **86 tests**; the
  extra seven are pending Milestone 1 review tests.
- Verified **536/536 final-inventory hashes** directly against that export (413 selection hashes
  and 123 follow-up hashes).
- Replayed historical September 15/16 lexical/interface evaluations, the original 42-attempt
  direct-contributor run, the 15-attempt connected-live-v2 run, all **46 selection completions**
  and all **11 Flash-follow-up completions**. Saved evaluations agree. Gemini's 12 scored passes
  and V4.1's six scored follow-up passes are preserved without treating them as production proof.
- Commit-range whitespace checks pass. Pattern-scanned 2,000 changed non-PDF files and 473 decoded
  response bodies: no credential-pattern matches. This is not a proof against every secret format.
- No live API calls, credential reads, raw PDFs, native corpus reads, OCR or production edits were
  performed. Existing requests, responses and hashes remain unchanged.

[Machine-readable verification](verification.json), [review script](verify.py),
[committed-tree tests](committed-tests.txt), and [workspace tests](workspace-tests.txt) retain the
checks. The exported source location is recorded in [context](context.json).

## Qualifications and next step

The active model policy is committed consistently: Gemini 3.8 Flash / Google AI Studio is primary;
DeepSeek V4.1 Flash / Together receives the same bounded semantic query for research only. Research
cannot supply a fallback, veto, correction, operational cache entry, annotation, plan or finding.
Model selection is closed. Real-IR integration and validation remain explicitly unchecked.

The working tree still has **seven modified paths and 22 untracked entries** for earlier Milestone 1
review/scope work and ignore-file changes. In particular, the strict current no-PDF wording and M1
acceptance reconciliation are partly pending, and the `.env` ignore rule is not in HEAD. Current
owner instructions and workspace guidance remain binding. These are separate outstanding changes,
not missing model-experiment artifacts. Preserve and reconcile them separately before claiming the
whole project is clean or publishing a complete project checkpoint.

`docs/openrouter-probe.md` is preserved historical evidence through September 16. Its prospective
Pro/Flash rerun suggestions and the Pro default in `tools/probe_openrouter.py` are superseded by
README section 4 and the September 18 reconciliation; they are not the current execution plan.
Returning to that work should mean resuming Milestone 2 under the new policy:

1. Connect one bounded semantic operation to explicitly selected saved IR, with deterministic
   prerequisites, exact-decimal financial handling, and independent v2 primary/research records.
2. Prove research noninterference, primary-failure handling, file isolation and independent replay
   before live use. Check current route capability/served identity under declared bounds.
3. Validate a small independently reviewed real-IR slice with compatible/incompatible context,
   positive/missing-evidence controls and amount invariance, then extend through checks/findings.

No new model tournament is needed to begin this integration work. Historical fixture success does
not substitute for these implementation and source-correctness checks.
