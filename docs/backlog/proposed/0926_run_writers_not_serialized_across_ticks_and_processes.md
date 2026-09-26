# 0926 — Writers of one run are not serialized beyond resume (concurrent tick/cancel in-process; split-mode processes)

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractruntime (run store, `Runtime.resume`/tick/cancel), abstractgateway (split mode)

## Summary
0923 serializes concurrent RESUMES of one run inside a process (per-run lock held from the waiting check through the save). Review 32
of that fix (untracked/missions-2026-09-25/REVIEW/32-runtime-double-resume.md) found two older gaps it does not cover:
1. In-process: a concurrent tick or cancel of the same run is not serialized against a resume (or against each other). The file
   store's `OffloadingRunStore` cache hands every caller the same mutable run object, so two writers can interleave on it.
2. Cross-process (gateway split mode): a resume in the serve process (a Telegram answer, an entity resume) can race a runner-process
   resume of the same wait (e.g. a Telegram answer and a UI answer to the same question). A per-process lock cannot close this; it needs
   a compare-and-set (expected version/etag) in the store's `save`, with the loser refused as stale.

## Scope
Design a store-level optimistic-concurrency guard (`save(run, expected_version=…)` raising a typed stale-write error), adopt it in
resume, tick and cancel, and make the gateway's paths treat a stale write as a lost race (as 0923 does for resumes). Out of scope:
distributed locks; changing the run store format beyond a version field.

## Validation
A stress test with resume + cancel + tick racing on one run (in-process) and a two-process test (two stores over one directory) each
end with one consistent history and no duplicated node execution.

## Related
0923; abstractruntime `core/runtime.py` (`_PerRunLocks`); gateway `runner.py` (`_resume_subworkflow_parents`, `_repair_terminal_subworkflow_waits`).
