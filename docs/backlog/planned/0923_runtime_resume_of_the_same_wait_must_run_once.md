# 0923 — A wait resumed twice starts the Agent node's child twice (runtime resume is not idempotent)

- **Status:** planned (fix committed 2026-09-26 on abstractruntime main as 61d38a1, unreleased; ships as abstractruntime 0.5.1 + a
  gateway 0.5.1 quiet-log follow-up on the operator's go)
- **Created:** 2026-09-26
- **Area:** abstractruntime (`Runtime.resume`), abstractgateway (runner resume paths)

## Summary
In the hermetic re-run of the scheduled Observer digest (untracked/missions-2026-09-25, MLXP run-1), node-2 of the parent flow was
resumed twice for the same `subworkflow:<child>` wait, 63 ms apart with byte-identical payloads (parent ledger rows #5/#6), and the
Agent node started a second full child loop: 99.8k tokens / 861 s for one loop became 205k / 1789 s for the tree. The top-level
scheduled run was resumed twice as well (harmless there: the next node re-ran with the same result). 1 of 3 runs hit it.

## Cause
When a child finishes, the gateway resumes the parent from two threads: the tick thread (`runner.py` `_resume_subworkflow_parents`)
and the loop thread's backstop (`_repair_terminal_subworkflow_waits`, run on the scan the completion triggers, from a list of waiting
runs taken before the other path saved). `Runtime.resume` checked "WAITING on this key" and saved much later, with no lock, so both
passed. The file store makes it worse: `OffloadingRunStore` caches a non-finished run as one mutable object that every `load()` hands
to every thread, so the second resume set the node back to node-2 after the first tick had consumed the child's result and moved on;
the next tick re-entered node-2, found it done, cleared the stored result and started a new child. Much easier to hit since the faster
runner wake (gateway 973c6f6, shipped since 0.2.30/0.3.0). Not the driver script: its one duplicated approval was correctly refused
("Run is not waiting"). Production (the operator's real Observer task on :8080) is affected: both paths run in every gateway and the
file store is the default backend.

## Fix
- abstractruntime 61d38a1: `_PerRunLocks` / `_RESUME_LOCKS` (runtime.py ~481–514), one lock per run shared by every `Runtime` object in
  the process (the gateway builds several over one store); `resume()` holds it around `_resume_commit()` = the waiting check through the
  save; the tick runs unlocked; a racing second caller re-reads the saved state and gets `ValueError("Run is not waiting")`. Test
  `tests/test_resume_concurrent_same_wait.py::test_concurrent_resume_of_the_same_wait_runs_once` (real `JsonFileRunStore`, red before).
- abstractgateway follow-up (in progress): both resume paths treat "not waiting" as a lost race logged at DEBUG (the tick path would
  otherwise log an ERROR traceback each time it loses; the repair path swallowed it silently).
- The lock is per process; the gateway's runner lock keeps one process resuming runs, so that is enough today. A multi-process
  gateway shape would need a store-level guard (not planned).

## Validation
Runtime suite 2610 passed / 31 skipped. Review 32 (untracked/missions-2026-09-25/REVIEW/32-runtime-double-resume.md): GO — stress test
in the gateway's shape (two `Runtime` objects over `OffloadingRunStore(JsonFileRunStore)`, 2 threads × 50 races): 50/50 exactly one
success, one resume record, the node executed once; the lock registry is reference-counted (empty after 100 races); no deadlock path;
removing the lock turns the tests red. Medium F1 (landing before staging): when the winner's tick already moved the parent to its NEXT
child's wait within the ~60 ms gap, the loser sees `wait_key mismatch` instead of "Run is not waiting", and the gateway's string match
would treat it as a failure → the runtime raises a typed `StaleResumeError` for both refusals and the gateway matches on the type.
After release: a scheduled Observer run's parent ledger shows exactly one `resume` per wait key.

## Related
0922 (MLX chat template, same experiment), 0921 (release trace), 0925, 0926 (what the per-run lock does not cover).
