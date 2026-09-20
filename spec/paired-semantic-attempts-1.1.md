# Paired semantic attempts, version 1.1.0

This version accompanies [operation 1.1.0](semantic-operation-1.1.md). The [v1 contract](paired-semantic-attempts.md)
remains immutable. Roles, provider/model configuration, token cap, timeout, retry/fallback policy,
six-file commit protocol and primary-only annotation boundary are unchanged.

## Current attempts

New query IDs and attempt IDs include the versioned prompt, unchanged four-field schema and
source-derived policy/gate metadata. `request` and `dispatch` validate those bindings; consumption
reconstructs the query from selected IR. Host analysis is not included in model messages. Both
roles receive equal semantic inputs; role/configuration identities remain distinct.

Noneligible queries persist local attempt outcomes with zero model calls. An all-local batch does
not read credentials, bootstrap an environment file, request metadata or reserve completions. A
mixed batch keeps metadata availability/reservation accounting for eligible queries only; local
queries do not consume completion budget. No new live run is authorized by this implementation.

`semantic-provenance-1.1.0` adds host policy identity, source gate and source-referenced blocking
reasons. `semantic-batch-1.1.0` binds policy plus runtime module/resource hashes. New batch replay
requires those exact bindings. Primary consumption reads only selected IR and primary files, and
cannot promote research after failure, local block or semantic abstention. Research runs separately;
neither its validation nor completion gates primary output. Future plans/findings are not implemented,
so these checks establish isolation only at the persisted annotation/provenance boundary.

Invalid responses additionally persist a diagnostic code/reason. Missing-context diagnostics
identify the source-derived missing IDs. These are rejection evidence, not automatically inserted
citations; replay recomputes and checks the diagnostic with the rest of the validation record.

## Explicit historical replay

Use [tools/replay_semantic_v1.py](../tools/replay_semantic_v1.py) for the retained Task B batch. The
current operation and CLI reject v1 bindings; there is no automatic version dispatch, historical
query regeneration with current constants, permissive hash acceptance or new-query v1 fallback.
The launcher supports only `replay` and `research-replay` and never dispatches a completion.

Create a separate read-only export with the named old commit's `src`, `schemas` and `pyproject.toml`:

```sh
mkdir -p runs/semantic-citation-implementation-1.1.0/pinned-v1
git archive e8000e2c001983f1f65fac75de97945c628a2287 src schemas pyproject.toml | tar -x -C runs/semantic-citation-implementation-1.1.0/pinned-v1
chmod -R a-w runs/semantic-citation-implementation-1.1.0/pinned-v1
tools/eval-format-tools/.venv/bin/python tools/replay_semantic_v1.py replay \
  --pin runs/semantic-citation-implementation-1.1.0/pinned-v1 \
  --batch runs/paired-semantic-integration-2026-09-18/live-v1 \
  --selection runs/paired-semantic-integration-2026-09-18/selection.json \
  --output runs/a-new-historical-primary-replay
```

The [shared manifest](../tools/replay-semantic-v1/shared.json) pins the source inventory/bytes,
Python version/binary, installed validation dependencies and their distribution file hashes,
original batch and explicitly selected corrupted IR/manifest descriptors. Extra pin files, including
bytecode, fail. This is intentionally tied to the retained local environment; a different machine
must obtain the pinned resources or separately review an environment migration. Do not regenerate
hashes merely to allow a different installation. No dependency download is performed by replay.

Primary verifies **shared prerequisites plus only the primary role manifest and artifacts**. It
does not stat, enumerate or load the research manifest/directory. Research verification uses only
shared prerequisites plus its own manifest/artifacts in a separate invocation. Corrupt research
can fail that invocation while primary still succeeds. Shared IR corruption legitimately blocks
both; missing/corrupt selected-role files block that role before output is created. The manifests
are reviewed local replay inputs, not evaluator expectations or model prompts.

An isolated subprocess imports only the pinned package; workers retain the pinned file guard and
have socket denial installed before imports. Provider credentials and `PYTHONPATH` are removed.
Every primary annotation and provenance file is checked against its original byte hash. A separate
`pinned-verification.json` records role, pin and manifest hashes, launcher read paths and zero calls;
it does not modify or normalize provenance. Research replay checks the original validation records
(including truncation and invalid abstention) and never emits primary annotations. All five original
queries, including the blank target, remain available only under these exact historical bindings.

Historical replay remains a reproduction of a failed acceptance run. New-policy checks of saved
answers are **post-exposure diagnostic re-evaluation** and must be recorded separately. Any later
live confirmation needs separately frozen versions, fixtures, expectations and an explicitly
authorized budget. Neither semantic acceptance nor M2 is complete.
