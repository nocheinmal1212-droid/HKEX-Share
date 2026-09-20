# Paired semantic integration contracts, 1.0.0

The supported entry point is `hkex-semantic` or `python -m hkex_audit.semantic_cli`.
The operation is [direct contributor headers](semantic-operation.md). This additive contract
introduces `paired-semantic-attempt-1.0.0`, `semantic-batch-1.0.0` and
`semantic-provenance-1.0.0`; it does not modify the M1 schema inventory or historical attempt v1/v2.
No migration of frozen IR, scoring data or old completions is performed. Old completions cannot
be replayed as these attempts. The executable strict answer schema is `semantic.SCHEMA`.

`run --selection IR.json --queries queries.json --output NEW_DIRECTORY --max-http-calls 10
--max-role-calls 4 --max-seconds 600 --max-cost 8` declares investigation limits before dispatch.
Optional `--env-root ROOT` supplies only `OPENROUTER_API_KEY` from ROOT/.env when absent.
The launcher is trusted bootstrap; semantic workers receive no credential and cannot open .env.
The transport subprocess receives the credential through the environment, preloads TLS then
permits only OpenRouter HTTPS and denies file reads/external execution. It has a hard process
60-second deadline, no redirect following, retry or fallback, and cannot write attempt artifacts.
Python auditing is accidental-access protection, not hostile-code containment.

The launcher resolves the versioned IR selection. A fresh guarded worker validates selected
IR/manifest hashes and builds all projections. The model receives only the selected table's
literal/explicitly transformed projection, operation and vocabulary. Original fragments stay
linked through source IDs and offsets. Runtime imports no evaluator or experimental launcher.
The logical query identity binds source content, selection, transform, operation, prompt, schema,
context and prerequisite outcome. Model/provider/configuration/nonce bind separate attempt IDs.
Only messages and response_format form the identical semantic payload hash; role configuration
is intentionally outside it. No shared accepted-response cache is implemented.

Requests use exact policy model/provider identities, temperature zero, 4096 completion tokens,
native default reasoning, strict schema, require_parameters and no fallback. Endpoint metadata
must advertise the exact route/provider, operational status and controls. Served model/provider
must match exactly. Immutable backend revision remains unknown. Price filters cap prompt at
$5/million, completion at $20/million and per-request at zero; text-only requests contain no
image/audio/search/tool use. Conservative reservations use UTF-8 request bytes plus 4096 framing
bytes at double the prompt ceiling (cache allowance), plus the full completion cap. Metadata
HTTP calls/failures count against HTTP/time caps. Costs reserve before concurrent dispatch and
are never recycled. Reported usage cost is separate; missing cost remains unknown. These are
investigation bounds, not approved business acceptance thresholds or billing guarantees.

One batch process dispatches at most two transports concurrently, one per role. Primary replay
and annotation persistence happen as soon as its attempt finishes, before awaiting research.
Research failure/exhaustion remains in the batch ledger. The next pair starts after both bounded
attempts finish; throughput independence across all future queries is not claimed.

Each role has its own `primary/NAME/` or `research/NAME/`: query, actual request, started record,
raw HTTP response (base64, credential echoes redacted), validation result and completion record.
A fresh directory and exclusive writes prohibit resend/reuse. Completion binds exactly five
artifact hashes and its role-specific attempt. Each artifact is fsynced and read back before
publishing completion. A late result write without completion remains incomplete. An uncertain
completion publication is commit_unknown, resolved only by read-only replay. A process crash
before completion may leave just the started record; it does not authorize another call.
Validation replay recomputes the answer, request/config identities and expected selected-IR query.
Missing, corrupt, foreign-role or changed-configuration completions fail closed.

`replay --selection IR.json --batch BATCH --output NEW_DIRECTORY` launches a guarded operational
consumer per query, with exact read permissions for selected IR and **only primary** attempt
files. It recomputes query context from IR, verifies completion, and writes real M1 annotation
records plus a separate provenance record. The annotation ID binds query, primary attempt and
validated answer; provenance binds annotation bytes, completion hash, selected source and target.
Downstream consumers must use this boundary and retain the provenance companion, not load all
JSON beneath a batch directory. `research-replay` is a separate zero-call diagnostic path and
never emits operational annotations. Malformed research files cannot crash primary replay.

Only accepted/abstained Gemini responses become model annotations. Source prerequisite gaps and
service/persistence failures produce no invented annotation links; their unresolved outcome is
in provenance/consumption and the batch ledger. `not_a_total`/`incompatible_context` map to the
existing annotation `ambiguous` state; the exact semantic abstention reason is retained in the
attempt. No check, equation, plan, finding or numerical parser is implemented in this slice.
Header semantics do not establish row completeness, entity scope or operational correctness.
