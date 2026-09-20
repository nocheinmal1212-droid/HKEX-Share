# Header source analysis 1.0.1 — presentation partition correction

This implementation revision fulfills the presentation exemption in
[operation 1.1.0](semantic-operation-1.1.md), following the approved
[independent implementation review](../docs/semantic-citation-implementation-review-2026-09-19.md).
It does not change the operation, prompt, four-field response schema, finite vocabulary,
summary rule, prose gate or model/role policy.

A recognized presentation wrapper remains in the complete source projection and
`presentation_refs`. It is excluded from the membership child partition of its enclosing context
group. Headers beneath the wrapper still belong to their nearest potential context group, and
must form the same complete, non-overlapping partition. The wrapper cannot count alongside those
headers, create an accounting branch, satisfy missing content, or qualify an unknown group.
Required group citations and the separate finite subtotal summary rule are unchanged.

## Binding and replay

`header-source-analysis-1.0.1` is bound through `host_analysis.policy.analysis_version` into every
query, request, attempt and provenance identity. Runtime file hashing also changes. The unchanged
policy JSON retains `header-support-policy-1.0.0`; operation/attempt/batch/provenance retain their
1.1.0 formats. Query IDs therefore change even for sources whose gate and model-facing context do
not change. No old completion is migrated, patched or accepted under the corrected runtime.

The original implementation packet and review remain as-of evidence. Its twelve-file binding now
intentionally differs at `src/hkex_audit/header_support.py` only. The complete pre-correction package
and schemas are preserved in
[the new packet's runtime-before directory](../eval/semantic-citation-implementation/1.1.1/runtime-before/),
with their original hashes in [baseline.json](../eval/semantic-citation-implementation/1.1.1/baseline.json).
Use those exact bytes and the retained environment for offline 1.1.0-artifact reproduction; verify
the inventory first. Current query/batch validation rejects old analysis/runtime bindings.
The separate pinned v1 launcher and its manifests are unchanged. No dispatch or inference through
an old package is authorized by preservation of its bytes.

The new regression freeze is exposed development evidence. It preserves the review's source
meaning and expected boundaries before this correction's runtime edit. Neither this revision nor
its deterministic tests establish new model behavior, saved-IR semantic acceptance or M2 completion.
G3–G5 remain local zero-call controls. Historical 0/4 complete frozen support and research failures
remain unchanged; a later confirmation packet still needs separate review and an explicit budget.
