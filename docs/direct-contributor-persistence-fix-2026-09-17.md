# Direct-contributor late-write/replay fix — 2026-09-17

**Verdict: the observed result-write/replay defect is fixed in the experimental v2 attempt
protocol.** All 42 write-timing cases and the full 72-test suite pass. This is a persistence fix
for logical-source attempts; production IR integration, semantic correctness and power-loss
durability remain unverified. No model calls, credentials, raw PDFs or native corpus outputs
were needed for this fix.

The original [results](direct-contributor-results-2026-09-17.md) remain historical evidence.
Before the fix, a store that wrote complete result bytes and then raised `OSError` made dispatch
report `persistence_failure` while replay reported `structure_accepted`. A fresh
[v1 reproduction](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/before.json)
confirms that failure. Original v1 code and frozen records have not been rewritten.

## Experimental v2 completion contract

This document owns the new experimental persistence contract, implemented in
[direct_contributor_attempt_v2.py](../tools/experiments/direct_contributor_attempt_v2.py).
It does not change production schemas or the frozen v1 request/semantic boundary.

Each attempt has one writer and a fresh dedicated directory. Files use exclusive creation;
there are no retries, overwrites, inferred recovery, automatic resends or cleanup. A directory
with a completion record or existing source/request snapshot is refused as `attempt_conflict`.
Replay of a reused directory still describes its previous attempt, never the refused new call.
Concurrent writers and externally edited attempt directories are outside this contract.

The writer persists `source.json`, `request.json`, and, when transport is eligible,
`started.json` and `response.json`, followed by `result.json`. Each write must finish writing,
flushing, file `fsync`, and closing successfully. Source/request and start records are read back
before dispatch; all preceding records are read back before completion publication.

The final `completion.json` record contains exactly:

```json
{"version":"direct-contributor-attempt-v2","artifacts":{"<allowed filename>":"<sha256>"}}
```

Its inventory is either source/request/result, or source/request/started/response/result.
Replay validates the inventory before accessing any listed path, then requires every artifact
and hash to match. It also checks the result version, actual source snapshot hash, request hash,
configuration hash, call count/inventory, and start/response bindings. The actual source snapshot
hash is separate from the claimed source identity so an input rejected for a bad identity can
still have a faithfully persisted rejection. Invalid request versions can likewise be recorded
as rejected inputs. A completion record signifies a recorded terminal outcome, not semantic
acceptance: rejections, abstentions and transport failures remain their respective states.

| Observation | Dispatch outcome | Replay outcome |
|---|---|---|
| Artifact write/readback fails before completion publication | `persistence_failure`, `persisted=false` | `incomplete_attempt` |
| Result bytes exist but no completion record exists | Failure or interrupted caller | `incomplete_attempt` |
| Completion write/readback reports an error | `commit_unknown`, `persisted=null` | Resolves from saved marker and dependencies |
| Completion is missing, partial, malformed, or dependencies fail validation | Failure, unknown, or interrupted caller | `incomplete_attempt` |
| Complete valid marker and all bound dependencies exist | Confirmed success, unknown acknowledgement, or interrupted caller | Recorded terminal state |

A fully written completion record can become visible immediately before the writer reports an
error or is interrupted. That acknowledgement ambiguity cannot honestly be called a definite
persistence failure. Callers must resolve `commit_unknown` by read-only replay; they must not
automatically resend the model request. Replay performs zero model calls and separately reports
the saved historical call count. For incomplete attempts, the historical count remains unknown.

`persisted=true` means publication and readback were confirmed during this process. The protocol
uses file `fsync`, but does not establish directory-entry durability across power loss or validate
every filesystem's crash semantics. Interruption tests inject exceptions at write boundaries;
they are not OS-kill or power-failure experiments. Hashes detect inconsistent saved artifacts;
they are not signatures against a hostile actor who can rewrite the complete directory.

## Execution and observations

- The new [fault runner](../tools/experiments/run_direct_contributor_persistence_v2.py) exercises
  six artifact locations with seven faults each: before-write failure, partial-write failure,
  complete-write late failure, complete-write interruption, partial-write interruption, omitted
  write, and corrupted write. **42/42 pass**, with full per-case outcomes and saved bytes in the
  [observations](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/fault-matrix/observations.json).
  The specific late `result.json` case returns persistence failure and replays incomplete.
  Complete late/interrupted completion publication replays the recorded accepted structure;
  all other completion faults replay incomplete.
- [Eleven new regression tests](../tests/test_direct_contributor_persistence_v2.py) also exercise
  six terminal-outcome controls, missing/altered dependencies, invalid inventory paths, inconsistent
  rehashed bindings, result `fsync` and readback errors, refused reuse, v1 migration boundaries,
  and isolated dispatch/replay. A mutation that trusts result bytes without a completion record
  is detected. The first test execution exposed a `KeyError` in the fault runner when the mutant
  returned an empty record; the runner now counts that malformed replay as a failed assertion
  instead of crashing. No expected outcome was relaxed.
- `make evidence-check`: **72 tests pass**, including all prior tests; see the
  [full log](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/tests.txt).
- The new [isolated worker](../tools/experiments/direct_contributor_offline_worker_v2.py) reads
  only three selected input files and its exact named output artifacts under the existing guard.
  The saved [access record](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/isolated-replay/access.json)
  shows accepted dispatch/replay, one frozen-response stub invocation, zero network calls, and
  **six denied protected reads**. Permissions were extended only for named v2 self-artifact
  readbacks; the production guard is unchanged.
- All eight original [implementation hashes remain unchanged](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/historical-code-check.json).
  The original [frozen evidence verifier passes](../runs/milestone2/direct-contributor-persistence-fix-2026-09-17/historical-evidence-replay.json),
  including its exact evaluation replay and original 31/1/5/5 live outcome tally.

Reproduce the matrix in a **new** output directory:

```sh
tools/eval-format-tools/.venv/bin/python tools/experiments/run_direct_contributor_persistence_v2.py /tmp/direct-contributor-v2-new-run
make evidence-check
```

## Adoption and remaining work

Use `direct_contributor_attempt_v2` and `direct_contributor_offline_worker_v2.py` for new
experimental persistence work. V1 modules remain available only to reproduce frozen historical
experiments. A v1 result-only directory is deliberately incomplete to v2 replay; there is no
automatic marker backfill or migration. Re-execution requires a new attempt directory with
explicit selected inputs and separately recorded provenance.

This resolves the known late-result-write promotion blocker for the experimental dispatcher.
It does not promote the dispatcher to production, migrate the live transport worker, change
the model/prompt, or resolve S11's wrong selection and S08's incomplete live outcomes. The next
integration work still needs a real selected-IR consumer, end-to-end persisted source traces,
amount invariance, and independently reviewed semantic expectations.
