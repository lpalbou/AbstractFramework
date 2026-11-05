# 1127 — Local gate: `--release-tag` skips the ci jobs already green on the same head; one gate per machine

> Package: abstractframework (scripts/ci_local)
> Type: task
> Created: 2026-11-05
> Priority: normal
> Labels: ci, local-gate, adr-0050, efficiency

## Summary

Two changes to `scripts/ci_local.py`, both operator-ordered with the release-skill rules of abstractskill 0.3.9:

1. **`--release-tag vX.Y.Z` does not repeat green `ci` jobs.** A release branch is gated with its PR and main jobs, then
   again with `--release-tag`, which today runs every `ci` job a second time beside the release workflow's own jobs.
   The release-tag pass reads the summary of the last completed run for the same commit (merged into the same base),
   skips the `ci` jobs that passed there (printed `SKIPPED (green on <run dir>)`, not counted as skipped for
   `--allow-skipped`), and runs only the release workflow's jobs and any `ci` job that did not pass. Only the `ci`
   duplicates are skipped: a `release.yml` job that runs the same steps as a `ci` job (AbstractCore's `release.yml`
   re-runs its whole test suite, console-tui crate and local-model tests as its own jobs) still runs under this item.
2. **One gate at a time per machine.** A machine-wide lock, taken with the same `fcntl.flock` mechanism the gate already
   uses for leased ports (`lease_port`, `<lock_dir>/<port>.lock`) and for the run in progress (`RUN_LOCK`), held for the
   whole run. A second gate waits (printing who holds the lock: repository, commit, start time) or exits with
   `--no-wait`. The OS releases the lock when the holder ends, so a killed gate never leaves it stuck.

## Why

On 2026-11-03/04 the release-tag run of the AbstractCore 2.34.0 head took about 32 minutes and ran the whole `ci.yml`
job set again (eleven jobs, already green on that head) beside `release.yml`'s own jobs; every extra job is one more
chance for a flaky test to turn a release head red.
The same nights, gates started side by side collided on the root bootstrap smoke's fixed port 18080, filled the disk
twice, and turned timing-sensitive tests into flakes; each collision cost a re-run of tens of minutes. The operator's
rules (abstractskill 0.3.9 `abstract-release` / `release`): never re-run green jobs on the same head; one gate at a time
per Mac.

## Scope

### In scope

- A machine-readable summary per run (job id, matrix entry, verdict, head, base) written when the run completes, and the
  release-tag pass reading the newest completed one for the same head and base.
- The machine-wide lock with wait and `--no-wait`; `docs/ci-local.md` describes both.

### Out of scope

- Locking out Xcode builds or model-loading jobs that are not gate runs (the skill rule covers them by hand).
- AbstractCore's `release.yml` test jobs. Follow-up for AbstractCore: let `release.yml` rely on the green `ci` run of the
  tagged commit instead of re-running the suite. On 2026-11-03 the Core 2.34.0 release-tag run's two failures were
  those jobs (Test console-tui crate, Local-model tests) while their `ci.yml` twins passed on the same head.

## Acceptance criteria

- [ ] A release-tag run after a green run on the same head and base runs only the release workflow's jobs and the
      `ci` jobs that did not pass; a different head or base, or no completed run, runs everything (tests with fake run
      folders).
- [ ] A `ci` job that failed or was skipped in the earlier run is run again.
- [ ] A second gate started while one runs waits and says who holds the lock; with `--no-wait` it exits non-zero at
      once; killing the first gate frees the lock (tests with two processes).
- [ ] `docs/ci-local.md` documents both behaviours.

## Receipts

- abstractskill PR #7 (0.3.9: release gate economy); the 2026-11-03/04 gate logs under root
  `untracked/release-2026-11-03/w3/` (release-tag runs of AbstractCore 2.34.0; port and disk collisions).
