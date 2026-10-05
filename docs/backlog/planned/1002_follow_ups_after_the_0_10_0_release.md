# 1002 — Follow-ups after the 0.10.0 release (rounds 4–13 leftovers)

> Package: abstractframework (root), abstractgateway, abstractruntime, abstractcore, abstractassistant, abstractcode, abstractflow, abstractuic
> Type: task
> Created: 2026-10-05
> Priority: high
> Labels: release-follow-up, security, sandbox

## Summary

Root 0.10.0 shipped the round-4 → round-13 work (command sandbox, most-specific-workspace nesting,
automations that follow the default workspaces with re-clamping at each admission, the
`_replay_receive` busy-loop fix, Flow palette, kit 0.8.5). The credit budget cut round 13 down to
its minimal fixes. This item tracks what was built but not shipped, what was found during the
release, and what is still unverified, so a later agent can pick each one up without the round notes.

## Why

The release driver was told to fold these leftovers (`untracked/round4/BACKLOG-R5.md`,
`untracked/round4/BACKLOG-R13.md`, and the release ledger `untracked/round4/RELEASE-0.10.0.md`) into
one root backlog item. Several of them are user-visible (hangs, a Linux sandbox gap); none blocked
the 0.10.0 publish.

## Current code reality (2026-10-05, published matrix)

- abstractcore 2.25.0, abstractruntime 0.9.0, abstractagent 0.3.18, abstractgateway 0.13.0,
  abstractvoice 0.14.0, abstractmusic 0.1.16, abstractassistant 0.13.0, ui-kit 0.8.5,
  panel-chat 0.4.1, code web 0.11.0 / terminal 0.9.0, flow 0.8.0, observer/continuum/entity 0.7.0.
- Gateway 0.13.0 includes the R13-W1 minimal fix (`_replay_receive` waits on the connection's
  receive after the body). The rest of R13.1 lives on unpushed local branches
  `round4/2026-10-04-r13w1` (worktrees `untracked/round4/wt/abstractgateway-r13w1` and
  `…/abstractruntime-r13w1`), recipe `untracked/round4/r13/w1/RECIPE.md`, mutation 14/14 red.

## Scope

### In scope

1. **Linux command sandbox, nested workspaces (abstractruntime CI, RED).** The `linux-sandbox` job
   on runtime main (run 37245682201, commit 640ca24 = release 0.9.0) fails 4 of 26 tests:
   `tests/test_r12_workspace_sandbox.py:239`. In those tests an allowed child (`home/parent/child`)
   sits inside a refused parent. Under bubblewrap, `cat` of the child's file exits 1. This fails
   closed (it refuses more than the policy says), so it leaks nothing, but on Linux the
   "most specific row wins" rule does not hold for commands yet. Core's own Linux job
   (bubblewrap + Landlock) is green. Fix the bwrap profile builder in
   `abstractcore.tools.sandbox` so it binds the allowed child after it masks the parent, then make
   the runtime job green.
2. **Hang recovery / wait key / incident surface (R13.1 B1–B5, built on branches):** Read aloud must
   never be a run wait (runtime `stream_voice` child recorded COMPLETED, `close_interrupted_voice_stream`).
   Close orphaned voice-stream waits at boot (gateway runner). Bound the voice stream and keep it
   strictly off-loop (`voice_stream.py`). One `replay_body_receive` helper plus a structural guard
   (core_endpoint sub-requests also answered "empty body" forever). Watchdog incident file
   `<data>/incidents/watchdog-<stamp>.json` plus a "Last restart" row (console Resources, TUI F3).
   Rebase onto today's tips, re-gate, push.
3. **browser_probe outside the command sandbox (R12-W1 residual).** A local page inside an allowed
   workspace can embed `file://` subresources from a refused folder. Recommended fix: serve local
   files through a scoped loopback HTTP origin (option b in BACKLOG-R5). Test: an
   `<img src="file:///<refused>/marker.png">` must not render; a mutant must turn it red.
4. **Gateway per-account client preferences.** The Assistant's default workflow is per device
   (`preferences.json`). Add an account preference store (admin defaults + per-account override),
   then move the Assistant and Code default-workflow choice onto it.
5. **Named per-user OpenAI API keys:** see 1000 (proposed). Root scripts
   (`scripts/lib/apps_common.sh:72-73`) still export `ABSTRACTGATEWAY_TRIAGE_REPO_ROOT` /
   `ABSTRACTGATEWAY_BACKLOG_EXEC_RUNNER`. Gateway 0.13.0 has the setting and the
   `serve --backlog-root` / `--exec-runner` flags, so replace the exports with flags, gated on
   `abstractgateway --version`.
6. **Assistant test-harness idle crash.** An offscreen Qt test run crashes when idle. The harness
   needs a fix (see the Assistant offscreen-review recipe: disable the traffic-light bridge and
   the hotkey first).
7. **TUI parity rounds 9–13.** Bring the gateway terminal console and the Code TUI up to the web
   console for the round 9–13 surfaces: workspace chooser v2, command-sandbox line, Apps status
   badge, automations "Use my default".
8. **Kit icon gaps (Flow palette, R13-W3).** The kit has no icon for: image, video, camera, music,
   database, branch, loop, variable, minus, divide, function, zoom-out, fit-view, lock. Flow's
   palette shipped in 0.8.0.
9. **Lockfiles.** The app lockfiles were regenerated against the published ui-kit 0.8.5 /
   panel-chat 0.4.1 at release time. `app-server` stayed at 0.1.11 in the locks (0.1.12 is
   published). Add a CI guard so an app lockfile can never lag its `package.json` kit floor again
   (round 11 found them on ui-kit 0.5.x).
10. **abstractagent parked commit.** Local commit 55c9fe8 (ReAct retries rejected tool-call formats
    twice, 2026-10-03) was never gated or pushed. It is parked on the local branch
    `parked/react-format-retry-2026-10-03` in abstractagent. Gate it and ship it, or drop it.

### Out of scope

- New features beyond the items above. Windows, email end-to-end and the 0.9.6 → 0.10.0 upgrade
  path are listed under validation, not built here.

## Acceptance criteria

- [ ] Runtime `linux-sandbox` CI job green on main, with no skipped tests.
- [ ] R13.1 B1–B5 re-gated and released; the incident file shows up on a forced watchdog trip.
- [ ] browser_probe `file://` subresource test red without the fix and green with it.
- [ ] Account preference store; the Assistant and Code read the default workflow from it.
- [ ] Root scripts use gateway flags, not env exports.
- [ ] Assistant offscreen harness runs idle without crashing.
- [ ] TUI parity checklist for rounds 9–13 closed.
- [ ] Kit icons added; Flow palette uses them.
- [ ] Lockfile guard in each app's CI.
- [ ] abstractagent 55c9fe8 shipped or dropped on the record.
- [ ] Validation still owed for 0.10.0: Linux sandbox (item 1), Windows install, email E2E,
      upgrade from 0.9.6.

## Receipts

- Release ledger: `untracked/round4/RELEASE-0.10.0.md`; report `untracked/round4/RELEASE-REPORT-0.10.0.md`.
- Source notes: `untracked/round4/BACKLOG-R5.md`, `untracked/round4/BACKLOG-R13.md`, `untracked/round4/COORD.md`.
- Runtime CI: https://github.com/lpalbou/AbstractRuntime/actions/runs/37245682201
