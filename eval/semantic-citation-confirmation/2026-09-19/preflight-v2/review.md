# Same-agent execution review — correction 1.2.0

This is inspection by the implementing agent, not independent approval. Scope is the execution
blocker and successor bindings; semantic policy and model configuration are unchanged.

## Reviewed boundaries and resolutions

- The clock starts at `run` entry. Source selection/read, preparation, output creation, metadata,
  paired executor work, persistence and consumption execute in the owned session. The parent has
  no executor to join. It kills that group on normal, failed or timed-out exit and reaps its child.
  Final receipt I/O runs in another bounded owned session within the *same original* cleanup interval.
  This closes the initially identified unsupervised output/receipt write gap. No post-return work
  is deferred to background threads or a cleanup grace period.
- Stage waits are `min(existing maximum, remaining work time)`. Transport reservation is separate
  from dispatch admission. Checks occur before/after launch-intent persistence, before process
  creation, at transport entry and after DNS before entering the HTTP request. A launch-journal
  failure is known pre-transport zero. Timeout or missing return after launch is unknown, not zero.
  Conservative reservations are not reclaimed for a replacement attempt.
- A transport can be cancelled during response persistence or a completion-marker write. Exact
  completion binding remains authoritative: no result is repaired or marked complete on cancellation.
  Existing early/late write, marker-corruption and primary/research tests pass. An incomplete replay
  makes zero new calls and reports unknown historical calls. Complete v1 and v2 snapshot replay
  reproduces primary annotations/provenance byte-for-byte.
- Primary is awaited and consumed before the research future. An outer SIGKILL can terminate waiting
  executor threads and authored transport descendants. Completed primary plus interrupted research
  preserves accepted primary output. Failed/abstained primary plus accepted research produces no
  contributor links. Guard records continue to exclude research and evaluator inputs from primary.
- The evaluator now treats missing/partial/invalid consumption files as unavailable and separately
  reports complete primary success. Availability, host, exact contributor/state and required support
  remain separate. The known unit-plus-lease case must and does fail the independent contributor check.
- A failed output creation cannot write a receipt into a pre-existing/protected directory: the bounded
  writer requires the unique launch timestamp and validates path ownership/protected components.
  A stalled receipt writer returns failure with no false completed receipt.
- Current attempt and batch are 1.2.0, with the new deadline module in runtime identity. Operation,
  prompt, schema, analysis, vocabulary and model/provider settings retain their original bytes.
  Current batch replay rejects historical versions/runtime hashes; retained snapshots are explicit.

## Verification and practical limits

The final controlled-environment suite runs all 52 selected tests (including the five deadline tests
with stage subcases), and separate edge checks exercise HTTP-boundary expiry, launch-journal failure,
receipt cancellation and pre-existing output protection. Real cancellation observations check recorded
owned worker/transport/descendant PIDs immediately after return and require absence. Test transcripts
and complete/partial artifacts are bound in the successor freeze. No real provider calls are involved.

The short tests declare a 0.15-second measurement allowance, but the collected successful observations
are all inside their nominal ceilings. This allowance never extends the proposed 600 seconds. The
implementation is a POSIX process supervisor, not a hard-real-time operating system: scheduling or
uninterruptible OS failure cannot be certified away by a Python test. Cleanup failure is never reported
as success. Tests demonstrate actual termination for the supported owned-session process topology.
No detached-session worker is part of this runtime.

One earlier probe pass required harness fixes (sandbox process-list denial and insufficient time for
real IR validation); a budget-helper attempt initially patched only the old clock namespace. Their
transcripts/directories remain, followed by separate successful runs. These are not hidden failures or
changes to the expected production ceiling. The old preparation helper's KeyError/follow-up remain
separate historical evidence. No independent review, live availability, model success or semantic
acceptance is inferred.

Decision: execution/evaluation correction is suitable for this bounded development confirmation,
subject to the final read-only freeze check and explicit owner live approval. No automatic launch.
