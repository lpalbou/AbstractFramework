# 1116 — Local CI gate, pre-push hook, strict-timing switches, and the eight flaky tests

> Package: AbstractFramework (root scripts), AbstractCore, AbstractGateway, AbstractAssistant
> Type: task
> Created: 2026-11-03
> Priority: high
> Labels: ci, adr-0050, release-process, flaky-tests

## Summary

The enforcement and validation ADR 0050 names does not exist yet in the tree. This item delivers
it: the root gate `scripts/ci_local.sh <repo> [--job <name>] [--fresh-venv] [--allow-skipped]`
with `docs/ci-local.md`, the opt-in `pre-push` hook installed by `scripts/install_hooks.sh`, a
strict-timing switch in AbstractCore's tests (the gateway has one in `tests/timing.py`), and the
rewrite of the eight tests that produced every red `main` of 2026-11-03. Until the gate lands, the
by-hand procedure in the `abstract-release` skill (section 10 of `references/release-process.md`:
run every step of the repository's PR and push-to-main jobs, scratch HOME, own temp directory,
fresh venv for release branches) **is** the gate.

## Why

Operator, 2026-11-03: "you have to do more tests before pushing to GH, CI/CD fail should be the
exception, not the normal path … it must succeed here before even attempting a push on GH".
Evidence: `untracked/release-2026-11-03/ci-failures-24h.md` — 22 failed runs in 24 h; 14 would
have failed locally under the gate; the other 8 are timing flakes, all seven red mains among them.

## Scope

### In scope

- `scripts/ci_local.sh`: reads each repository's `.github/workflows/*.yml` (PR and push-to-main
  workflows), runs every step of every job for each matrix Python that exists locally (a missing
  version is printed as `SKIPPED <job> python X.Y not installed`, never silent), same extras and
  services where they can run on this machine, scratch `HOME`, per-run `--basetemp`; exit 0 only
  when every runnable job passed; `--allow-skipped` is the explicit acknowledgement of skipped
  jobs; `--fresh-venv` installs from the registries' pins instead of editable siblings; release
  workflows' validate/build/sdist-test steps included for release branches; dispatch-only suites
  (the Assistant's full iPhone UI suite) runnable when their paths change.
- `docs/ci-local.md`: the contract, what cannot run locally per repository, the proof runs with
  timings (red on the Core release branch with fragments left in and on a gateway branch importing
  an unreleased Core symbol under `--fresh-venv`; green on `origin/main` of Core, Gateway, UIC).
- `scripts/install_hooks.sh` + the `pre-push` hook template (opt-in, never installed into shared
  checkouts without the operator; `--no-verify` the only override, noted in the PR).
- AbstractCore: a strict-timing switch mirroring the gateway's; every wall-clock assertion in
  `tests/` converted to an event/condition wait or placed behind the switch (first: the three
  `test_mlx_native_owner_retirement_unit.py` GC-timing tests).
- AbstractGateway: boot readiness waits for the server to answer HTTP (one shared helper), the
  0966 race family (`test_a_real_serve_audits_the_flag_at_boot` and its siblings on 3.10/3.11)
  rewritten; wall-clock bounds behind the existing switch.
- AbstractAssistant: the playhead/stall timing assertion rewritten; the full iPhone UI suite green
  on the simulator the upload workflow names (PR #50).

### Out of scope

- Changing what CI runs (the matrices stay); replacing GitHub Actions; any new CI service.

## Current code reality (2026-11-03)

- No `scripts/ci_local.sh`, `docs/ci-local.md` or hook in the root; `*_TIMING_STRICT` exists only
  in the gateway (`tests/timing.py`).
- Core `main` is red at de1f9c8 on the three GC-timing tests; gateway `main` is green at 0109bcb
  after four red runs on 3.10/3.11 timing tests; the Assistant upload run 41580477038 failed on
  five UI tests.
- The `abstract-release` skill 0.3.5 (AbstractSkill #2) already carries the by-hand gate.

## Acceptance criteria

- [ ] `scripts/ci_local.sh abstractcore` on `origin/main` exits 0; on the Core release branch with
      fragments left in it exits non-zero naming the `changelog` job; timings in `docs/ci-local.md`.
- [ ] `scripts/ci_local.sh abstractgateway --fresh-venv` on a branch importing an unreleased Core
      symbol exits non-zero at the install/import step.
- [ ] A missing matrix Python prints `SKIPPED` and the gate exits non-zero without `--allow-skipped`.
- [ ] The pre-push hook refuses a push whose gate fails (demonstrated in a scratch clone).
- [ ] Core and gateway test suites contain no wall-clock assertion outside the strict switch; the
      eight named tests pass 5/5 on the loaded CI jobs.
- [ ] ADR 0050's Enforcement and Validation sections are updated from "planned" to the landed paths.

## Receipts

- ADR 0050 (`docs/adr/0050-ci-passes-locally-before-any-push.md`); AbstractSkill #2.
- Evidence: `untracked/release-2026-11-03/ci-failures-24h.md`.
