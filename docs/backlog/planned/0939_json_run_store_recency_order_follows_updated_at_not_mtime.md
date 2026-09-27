# 0939 — JSON run store: recency order follows the runs' `updated_at`, not file mtime (a restored backup must not reorder history)

- **Status:** planned
- **Created:** 2026-09-27
- **Area:** abstractruntime (`storage/json_files.py`)
- **Parent:** [0928](../completed/0928_automations_v1_runtime_native_scheduled_and_triggered_tasks.md)
- **Source:** review 43 F5 (`untracked/missions-2026-09-25/REVIEW/43-runtime-r1.md`, LOW, pre-existing); MISSIONS follow-up "R1 F5"

## Summary
`JsonFileRunStore` ranks runs by file mtime as a cheap stand-in for `updated_at`. This affects `list_runs`,
`list_run_index` and the windows they take. In normal operation the two agree. When the files are copied without their
mtimes (a restored backup, `cp` without `-p`, a sync tool, a migration), the newest-first windows are computed from the
wrong order:
- the first 5,000 rows of the JSON listing differed from SQLite's in review 43's synthetic data, although the full sets
  were identical;
- Automations v1 leans on these windows: turn roots for session folds, `root_only` listings, and growing-mode history
  bounded to the newest turns.

So after a restore, a growing automation's context, or an app's session list, can pick the wrong "latest" turns without
any error.

## Scope
### In scope
- Rank by the run's own `updated_at`, cached in the existing scan memo / session index (the store already parses rows
  for its index), with mtime kept only as the change detector. Alternatively, detect an mtime/`updated_at` disagreement
  at open and rebuild the order once, loudly logged.
- A test: write runs, reset every mtime to one value (or shuffle them), and assert that the JSON listing order equals
  SQLite's for the same runs. It must be RED today.
- Keep the 2026-07-11 performance verdict: no full parse per listing call. The order comes from the index, not from
  re-reading files.

### Out of scope
- The SQLite store (it orders by `updated_at` already).

## Current code reality (2026-09-27, runtime `d02578a`)
- `storage/json_files.py:969`: "We order by run file mtime (close to updated_at) and stop once we have `limit` matches".
- `:1062-1072`: `list_run_index` ranks `(mtime_ns, path)` and sorts by it.
- `:1111`: a later sort by `updated_at`, applied only to the window already chosen.
- The session index and creation journal (`b000036`, `d02578a`) already keep per-run rows in memory: the place to keep
  `updated_at`.

## Acceptance criteria
- [ ] Same order as SQLite after an mtime reset, on a 20k-run folder, within today's listing latency.
- [ ] Deleting the new ordering (back to mtime) turns the test RED.
