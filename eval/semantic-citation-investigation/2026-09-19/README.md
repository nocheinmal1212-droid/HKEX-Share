# Offline header citation investigation

Start with the [report and proposed diff](../../../docs/semantic-citation-investigation-results-2026-09-19.md).
This packet proposes a conditional citation policy; it implements no runtime correction and authorizes
no inference. The original frozen failure remains unchanged.

- `independent-source-review.{json,md}`: distinct agent review without candidate answers, with
  source hashes and per-ID required/optional rationale. Agent review is not human/domain approval.
- `sources/`: immutable authored/derived source fixtures, faithful evidence, honest v1 projections,
  manifests and occurrence mappings. Original G4 is a preserved rejected draft; use G4_revision2
  for the reviewed conflict source. Source profile names are parser syntax, not OCR execution claims.
- `fixture-expectations.json`: proposed 1.1 expectations separate from runtime source inputs.
- `fixture-freeze.json`: 34 hashed source/review/expectation files. No prospective 1.1 request exists;
  freeze actual implementation/prompt/request bindings separately if implementation is authorized.
- `diagnostics/reproductions.json`: 24 exposed R1–R4 checks; modified answers are diagnostic copies.
- `diagnostics/evidence-trace.json`: every original request/response/annotation/evaluator chain.
- `diagnostics/generalization-response-pairs.json`: 38 authored positive/negative response probes,
  created after source review and expectation freeze, with actual v1 host versus proposed review outcomes.
- `diagnostics/additional-boundary-controls.json`: reproduced contributor-group omission, rejection
  of role promotion, changed completion payload and edited projection.
- `diagnostics/primary-replay/`: five fresh zero-call replays; annotation/provenance bytes equal
  original files. Consumption access traces are fresh and are not normalized to historical traces.
- `diagnostics/authored-isolation/`: transport-stub artifacts for primary failure/abstention and
  slow research. These are not provider/model completions. Internal dispatch `model_calls` counts
  stub invocations; actual provider calls are zero. Do not consume them operationally.
- `diagnostics/research-diagnostics.json`: saved research failures; no repairs or promotion.
- `diagnostics/verification.json`, `diagnostics/protected-before.json`, `bundle-integrity.json`:
  original 127 retained hashes, contract/runtime/schema preservation and final packet inventory.

Preparation scripts are investigation tooling only. They use exclusive file creation and will
refuse an existing output; they are not routine test or production entry points. Do not rerun them
over this freeze. A new investigation must use a new directory/version. No network is needed.

The reviewed operation can be expressed with four fields, but current structural validation cannot
enforce all note-dependent semantic prerequisites. See the report's unresolved questions before
authorizing implementation or treating a host pass as semantic certification.
