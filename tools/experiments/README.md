# Closed semantic model experiments

These development-only tools preserve the September 2026 lexical, relationship, persistence and
API-selection investigations. They are not the operational semantic pipeline. Their hardcoded model
IDs, routes and dated directories describe historical experiments, not the current model policy.
Do not change frozen modules to implement the [new policy](../../docs/model-policy-reconciliation-2026-09-18.md).

Fixture definitions are in `spec/diagnostics/`; evaluator expectations must remain outside workers.
The closed experiment snapshot is explicitly versioned under `runs/milestone2/`, although `/runs/`
remains ignored for future generated artifacts. Reports and frozen request/source/code hashes
preserve source correctness separately from oracle agreement, availability and completion.

## Offline verification

From the repository root, with the project's Python dependencies available:

```sh
make evidence-check
PYTHONPATH=tools/experiments tools/eval-format-tools/.venv/bin/python tools/experiments/evaluate_model_selection.py availability screen-s04 screen-s08 screen-s11 screen-s09 screen-s10 confirmation diagnostics
tools/eval-format-tools/.venv/bin/python runs/milestone2/flash-context-check-2026-09-17-r2/verify.py
```

These commands make no model calls. The Python path is the repository's existing development
environment convention; configure `PYTHON` for the Make target if using another environment.
Do not run `prepare_*`, `launch_*`, or dated run execution modes merely to reproduce a result.
Preparation/execution may write artifacts or spend API credits; use read-only evaluators for replay.
Historical absolute paths and macOS sandbox profiles are execution provenance, not portable launch
instructions. Frozen v1 result-only replay has a known late-write defect; new work must use the
hash-bound v2 completion contract. A committed result may still be a refusal, failure or wrong answer.

The fixture, experiment-code/test, saved-evidence and policy commits are separate. Earlier Milestone 1
review work is outside this closure. Production integration and its separation tests remain planned.
