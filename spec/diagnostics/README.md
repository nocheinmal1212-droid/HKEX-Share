# Frozen development fixtures

These synthetic logical fixtures support the closed September 2026 model/interface experiments.
They are exposed development examples, not production evidence IR or independent holdout labels.

- `hypothesis-fixtures-v1.json`: lexical prompt/schema controls and evaluator expectations.
- `interface-boundaries-v1.json`: lexical boundary/failure controls and evaluator expectations.
- `direct-contributors-inputs-v1.json`: source-only direct-contributor cases and operation requests.
- `direct-contributors-expectations-v1.json`: evaluator-only expected decisions and support rules.

Some early fixture files contain both source and expected answers. Only preparation/evaluation
may read them; workers receive isolated request-only projections. Version control does not grant
runtime access. Keep expectations and benchmark-authored contributor lists outside inference.

The later H01/H02 linked-header pair is frozen with the selected sources and separate evaluator
key in `runs/milestone2/model-selection-2026-09-17/`; retain the original hashes and paths.
Historical proposals/results in `docs/` explain each fixture family and its qualification limits.

See the [current decision and closure](../../docs/model-policy-reconciliation-2026-09-18.md).
Do not rewrite fixture answers or historical configurations to match the new model policy.
