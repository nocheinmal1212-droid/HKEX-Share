# Four-arm prompt mapping pilot

This packet owns **experimental orchestration 1.0.0**, not production semantic policy.
The [predeclared plan](probe-plan.md) fixes hypotheses, treatments, source cases, observations,
stopping rules and the proposed aggregate budget. [arms.json](arms.json) binds exact requests,
operation identities and full runtime snapshots. [launch-proposal.json](launch-proposal.json)
is a proposal only; successful preparation makes no model call and grants no live approval.

## Versioning and replay

A uses unmodified operation 1.1.0. B/C/D use experimental operation identifiers, each in its own
complete source/schema/config snapshot. Their only source changes are `VERSION` and appended
`PROMPT` text in semantic.py. All other code, schema, source gates, citation analysis and policy
remain byte-identical. Attempt/persistence semantics remain 1.2.0; no completion is migrated.
Queries are reprojected from the retained selected corrupted IR/manifest in fresh interpreters;
the computed query and role requests must match prepared objects before dispatch. Runtime never
reads evaluator expectations or old completions to construct a new request. A's original wording
is retained exactly, with no extra common preamble.

Current source-tree replay intentionally rejects experimental operation bindings. Use the arm's
pinned snapshot and nonce for zero-call replay. Historical launchers/freezes remain unchanged.
There is no production prompt edit, default switch, numerical operation or downstream acceptance.

## Isolation and execution

[worker.py](worker.py) coordinates eight role pairs in a fixed mirrored arm order. Two metadata
requests happen once and both routes must validate before any completion. It conservatively reserves
each pair in a single cumulative ledger; reservations are never recycled. No nested live batch resets
the budget. Each slot uses a fresh interpreter and its own arm snapshot. Source preparation and
primary consumption retain existing explicit file allowlists and network/process-denying guards.
Only the selected key is forwarded to the live orchestration/pair/transport chain. Consumer workers
get an empty supplied environment. macOS/Python may add locale entries. Guard tests explicitly deny
credential paths without opening them. The guard is for accidental access, not hostile native code.

One outer POSIX session owns controller, slot processes, transports, consumers and executor threads.
Nested workers never detach. The original monotonic deadline is passed to every slot. Each wait is
bounded by remaining work time and existing stage maximum. The last second belongs to cleanup inside
the 900-second ceiling. A separate bounded prelaunch checker uses the same launch clock. The
supervisor kills only its owned group and reaps its child on success, timeout or failure; the final
receipt is also supervised within that same ceiling. There is no outer executor join or added grace.

Reservations, launch intents and proven HTTP-boundary entries remain distinct. A launch without a
complete return has unknown history, at most one call. Interrupted attempts/consumption may be partial;
only exact replay validates completion. No repair, response coercion or retry is performed. A completed
primary is consumed before research finishes; research cannot annotate, replace, validate or veto it.

## Observation

[observe.py](observe.py) runs only after the writer has returned and its owned workers have been
cleaned up. It has no network authority. Its evaluator-only source expectations are never sent to a
runtime worker. It reports availability, schema, target, exact contributor set, state, each citation
component, host state and complete primary persistence separately. It replays completion bindings and
rederives primary annotation bytes from the selected source before counting persistence available.
Missing/invalid artifacts stay in the fixed denominator. Provider-returned usage/cost is recorded;
missing values remain unknown. Research results are a separate research outcome.

The observer is absent from the dispatch process, so it adds no prompt tokens, tool calls, tracing
hooks, reasoning requests or dispatch scheduling work. Two post-run observations must agree and
leave every writer artifact hash unchanged. This is a read-only observation test, not a claim that
fresh stochastic model responses would be byte-identical in two separate live runs.

## Launch boundary

Verify the approved freeze digest with check_freeze.py immediately before launch. launch.py does this
under the aggregate deadline before reading the single credential environment entry. Changed files,
environment identities, snapshot inventory, an unready packet or an existing live output fail closed.
No regenerated request is saved over an approved one. The final verification receipt supplies the
concrete argv by substituting its digest into the bound argv template; self-inclusion of a freeze's
own digest is deliberately avoided. The reserved experiment output and four matching arm nonces
must remain unused until explicit approval of this new 18-call / 900-second / $16 experiment.

The local experiment can only establish development observations on two already exposed cases.
Historical 0/4 support, three research truncations, invalid research abstention and live-v2's 0/2
per-role results remain unchanged. No holdout/statistical/human-domain acceptance, live abstention
judgment quality, numerical compatibility, saved-IR acceptance or M2 completion follows.
