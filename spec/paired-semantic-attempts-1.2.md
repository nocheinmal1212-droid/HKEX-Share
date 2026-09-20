# Paired execution 1.2.0 — total deadline

This execution revision supersedes the batch/attempt execution rules of
[1.1](paired-semantic-attempts-1.1.md) for new runs only. Operation 1.1.0, analysis 1.0.1,
prompt, response schema, citation vocabulary, provenance format and both role configurations
are unchanged. Batch and attempt identifiers are 1.2.0; runtime identity includes
`semantic_deadline.py`. Old requests and completions are never rebound to new attempts.

The monotonic total clock begins at `run` entry, before preparation. A POSIX supervisor creates
one owned session for the batch. Preparation/consumption waits retain their 180-second maximum;
transport waits retain 60 seconds. Each is shortened to the remaining work interval. The last
`min(1 second, total/10)` is reserved *inside* the total ceiling for SIGKILL of the owned group,
pipe closure, direct-child reaping and receipt publication. This is not a timeout extension.
Workers/transports must not detach or create a new session. Guards prohibit descendant execution
inside source consumers and transports; the supervisor also cancels descendants during bootstrap.
Thread executor shutdown is confined to the supervised process, never the outer launcher.
Normal and failed exits both clean the owned group. Failure to verify cleanup is failure, not success.

Reservation does not authorize starting after expiry. Recheck after the durable launch-intent write,
before subprocess creation, at transport entry and immediately before the HTTP request boundary.
Already-issued work may be interrupted. Stop all new work at the cleanup cutoff; no retry, repair,
route fallback or replacement query follows. Primary consumption starts after committed primary
work returns, before waiting on research; accepted research cannot replace primary failure/abstention.

Exclusive-write attempt artifacts and six-file completion bindings are unchanged. SIGKILL can
leave partial JSON, a complete result without marker, or an uncertain completion publication.
Only exact read-only replay resolves the selected role's completion; never overwrite partial files.
Consumption's annotations/provenance/consumption files can also be partial; absent or invalid
consumption records are not proof of completed operational persistence. Complete original files
remain immutable. `summary.json` is produced only after all batch stages finish inside work time;
`supervisor.json` reports the actual outer outcome. A missing receipt is incomplete, not success.

Per-query `*-reservations.json` records conservative call/cost allocations. Per-transport
`*-launch.json` records intent, not a proven HTTP call. `*-return.json` records returned evidence:
`request_started=false` is known zero, `true` means the HTTP boundary was entered (remote acceptance
may still be unknown); absent/partial return or a timeout without this field means unknown, at most
one issued call. Do not call such histories zero or infer cost zero. The existing `model_calls` in
a complete attempt counts transport invocations, not confirmed provider acceptance. Incomplete replay
makes zero *new* calls and explicitly reports `historical_model_calls=null`. Reservations remain
conservative and are never recycled within an interrupted run.

The local no-go packet's `prepared-v1/runtime-snapshot` preserves the exact 1.1 execution bytes for
its authored replay. Verify its recorded inventory first and use the original environment and nonce.
The separate Task B v1 pinned launcher/manifests remain unchanged. Current replay rejects old batch
versions or runtime hashes; there is no automatic migration or new inference via historical pins.

No live authorization, semantic acceptance, numerical compatibility or M2 completion follows from
this execution correction. Historical 0/4 complete frozen support, three research truncations and
invalid research abstention remain unchanged.
