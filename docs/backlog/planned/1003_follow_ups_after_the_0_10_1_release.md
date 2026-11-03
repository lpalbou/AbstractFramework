# 1003 — Follow-ups after the 0.10.1 release

> Package: abstractframework (root), abstractgateway, abstractcode, abstractflow, abstractruntime, abstractcore
> Type: task
> Created: 2026-10-08
> Priority: normal
> Labels: release-follow-up, tui, flow, windows

## Summary

Root 0.10.1 (2026-10-08) closed the 0.10.0 follow-ups in 1002: the Linux nested-workspace sandbox,
the Read aloud hang and the watchdog incident surface, `browser_probe` behind a scoped loopback
origin, the per-account default workflow, the launcher flags, the Assistant offscreen harness, the
round 9–13 TUI parity, the kit icons, the lockfile guard and the parked ReAct format repair. This
item tracks what is still open after that release, so a later agent can pick each one up without
the round notes.

## Why

The release driver was told to close 1002 and fold the remaining leftovers of rounds 13–15 into
one planned root item. None of them blocked the 0.10.1 publish.

## Current code reality (2026-10-08, published matrix)

- abstractframework 0.10.1 pins abstractcore 2.25.1, AbstractRuntime 0.9.1, abstractagent 0.3.19,
  abstractgateway 0.13.1, abstractassistant 0.13.1, abstractvoice 0.14.0, abstractmusic 0.1.16;
  npm ui-kit 0.8.6 (abstractuic 0.6.1), panel-chat 0.4.1, flow 0.8.1, code web 0.11.1,
  observer/continuum/entity 0.7.0; crates abstractgateway-console 0.15.1, abstractcode 0.9.1,
  abstractcore-console 0.8.0.
- Ledger: `untracked/round14/RELEASE-0.10.1.md`; report `untracked/round14/RELEASE-REPORT-0.10.1.md`.

## Scope

### In scope

1. **Gateway terminal console redesign (round 15, in progress).** Design `untracked/round15/DESIGN-TUI.md`
   (R15.1), branch abstractgateway `round15/2026-10-07` (`console-tui/**` only, engine abstracttui
   0.3.6). Ships as `abstractgateway-console` 0.16.0 with a gateway patch release and a root pin bump.
2. **Code TUI default workflow.** Code Web 0.11.1 reads and writes the account's default workflow on
   the gateway (`GET`/`PUT /api/gateway/accounts/me/preferences`); the `abstractcode` terminal client
   (0.9.1) still keeps its workflow choice per device. Move it onto the gateway preference, with the
   same one-time upload of the device's choice and the same fallback for an older gateway.
3. **Code TUI `/schedule` Mailbox step.** `/schedule` in the terminal client has Workspaces and Title
   and limits steps (0.9.1) but no Mailbox step; the web schedule dialog has one. Add it with the
   web's words.
4. **`abstractcode-tui` has no git remote.** The repository at `abstractcode-tui/` (crate
   `abstractcode-tui` 0.5.0, 25 local commits, last two named `checkpoint`) has no `origin`. Decide
   whether it is superseded by `abstractcode/tui` (crate `abstractcode`); then archive it or give it a
   remote. Until then its history exists on one disk only.
5. **Flow run window.** (a) The run window's step rows do not use the per-category node colours the
   palette and the canvas got in 0.8.1. (b) A late `flow-start` event can arrive after a step failed
   and wipe the failed mark on its node card; the failed state must win over a late start.
   Each needs a test that turns red without the fix.
6. **Runtime test temp folder.** `tests/test_r12_workspace_sandbox.py::test_e2e_entity_exec_is_sandboxed`
   failed in the round-14 close run, which set a non-default `TMPDIR` under the workspace
   (`untracked/round14/close/runtime-suite.txt`: the refused marker was printed, exit 0). It passes in
   CI (Linux and macOS jobs) with the default temp folder. Find out whether the sandbox or the test
   setup depends on where `TMPDIR` points; fix the product if it does, otherwise make the test choose
   roots that cannot nest under `TMPDIR`, or skip loudly with the reason.
7. **Windows coverage.** `scripts/install.ps1` and the Windows command-sandbox story are not verified
   on a real Windows machine for 0.10.x. Run the installer on Windows 11 (light and gpu profiles),
   record what works, and state the sandbox posture on Windows in the install guide.
8. **Core cloning-engine probe tests are skipped in CI.** Since 2.25.1 the OpenF5 / Chroma presence
   tests skip when `abstractvoice.cloning.engine_f5` / `engine_chroma` do not import, which is the case
   on the CI runners. Add a CI job (or a stub engine module) that runs them.
9. **`ACKNOWLEDGEMENTS.md` missing.** The core doc set lacks `ACKNOWLEDGEMENTS.md` in abstractruntime,
   abstractagent, abstractgateway, abstractassistant, abstractuic and abstractflow. Add one per repo,
   from each package's real dependencies and lineage, and link it from `llms.txt`.
10. **Upgrade re-run on 0.10.1.** Repeat the hermetic 0.9.6 → current upgrade
    (`untracked/round14/w6/UPGRADE-0.9.6-0.10.0.md` recipe) on the 0.10.1 matrix, and a 0.10.0 → 0.10.1
    upgrade of a store 0.13.0 already migrated, to prove the D1 repair end to end with the released
    installer.
11. **Watchdog re-check window under CPU contention.** In the 0.13.1 release CI (run 37712028272, Python
    3.11 only) `tests/test_r13_gateway_concurrency.py::test_health_stays_fast_under_generation_plus_concurrent_read_aloud_and_the_watchdog_never_fires`
    saw the watchdog fire once with a 17.6 s age (limit 3 s) while every `/health` sample stayed under
    1.5 s. A plausible cause is a runner pause followed by a loop thread that did not tick within the
    single re-check tick while four threads burned CPU. Reproduce (pause the process under CPU load), and
    if confirmed widen the re-check (several ticks or a minimum wall time) so a busy machine waking up
    is never restarted.
12. **Named per-user OpenAI API keys** stay in proposed item 1000 (build decision: gate 1001).

### Out of scope

- New features beyond the items above.

## Acceptance criteria

- [ ] `abstractgateway-console` 0.16.0 released with the round-15 redesign; root pins it.
- [ ] Code TUI reads and writes the gateway's default workflow preference.
- [ ] Code TUI `/schedule` has a Mailbox step.
- [ ] `abstractcode-tui` archived or given a remote, on the record.
- [ ] Flow run window uses the category colours; a late flow-start never clears a failed mark (tests red without the fix).
- [ ] Runtime sandbox e2e test independent of `TMPDIR`.
- [ ] Windows install verified on real hardware; the install guide states the Windows sandbox posture.
- [ ] Cloning-engine probe tests run somewhere in CI.
- [ ] `ACKNOWLEDGEMENTS.md` in each listed repo.
- [ ] Watchdog never fires on a paused-then-resumed process under CPU load (test red without the fix), or the CI fire is explained.
- [ ] Hermetic upgrade re-run on the 0.10.1 matrix (0.9.6 → 0.10.1 and 0.10.0 → 0.10.1): every allowed folder listed.

## Receipts

- Closed predecessor: [1002](../completed/1002_follow_ups_after_the_0_10_0_release.md).
- Release ledger `untracked/round14/RELEASE-0.10.1.md`; report `untracked/round14/RELEASE-REPORT-0.10.1.md`.
- Round 15 design `untracked/round15/DESIGN-TUI.md`.
