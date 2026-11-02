# 1101 — Keep the machine awake for remote access: Linux, Windows and the terminal console

> Package: AbstractGateway
> Type: task
> Created: 2026-11-02
> Priority: normal
> Labels: remote-access, power, keep-awake, follow-up

## Summary

AbstractGateway keeps its Mac from idle-sleeping while remote access is on (`keep_awake.py`, contract
`gateway_keep_awake_v1`, branch `feat/keep-awake-remote`): the gateway process holds the macOS
`PreventUserIdleSystemSleep` assertion "AbstractGateway: remote access" through IOKit while it was started
with the `internet` exposure or Tailscale Serve/Funnel forwards to its port, and macOS drops it with the
process. Two residuals stay open: Linux and Windows hosts report `state: unsupported` (the machine may sleep
and drop phones and watches), and the terminal console (console-tui) has no **Stay awake** row next to
**Start at login** on its Resources/Gateway page.

## Why

Operator ruling 2026-11-02 (~22:00), on keeping the gateway's computer awake for the phone and the watch:
"yes, unless a user specifically put the mac on sleep mode." Context: the Mac idle-slept after one minute on
the charger at 11:29 and stayed asleep until 15:54; the watch and phone could not reach
https://forge.tail43a344.ts.net meanwhile (council-B D1,
`untracked/council-2026-11-02/council-B.md`). The macOS part shipped first because the operator's gateway
runs on a Mac; the same need exists on a Linux or Windows server reached through Tailscale Funnel.

## Scope

### In scope

- **Linux**: the idle-sleep equivalent held by the gateway process and released with it. Candidates:
  a `systemd-inhibit --what=idle --who=AbstractGateway --why="remote access" --mode=block sleep infinity`
  child (dies with the gateway only if supervised: prefer the logind D-Bus `Inhibit("idle", ...)` call,
  whose file descriptor closes with the process), no-op with the current one-line log where logind is
  absent (containers, servers without a desktop session, where idle sleep rarely applies).
- **Windows**: `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` from a dedicated thread
  that stays alive while held (the state belongs to the calling thread), cleared on release; the OS clears
  it when the process exits.
- Both as `default_backend(platform)` backends behind the existing `acquire(name)` / `release(id)`
  interface; status `supported: true` there; the console switch then shows on those systems with
  "Keep this computer awake while remote access is on" (the macOS wording stays "this Mac").
- **Terminal console parity**: a **Stay awake** row and switch on the console-tui Resources/Gateway page
  (`ui/host.rs`, beside Start at login), reading `GET /api/gateway/host/keep-awake` and writing
  `POST /api/gateway/admin/runtime-config {"keep_awake": bool}` (`keep_awake_status` in the answer).

### Out of scope

- Preventing an explicit sleep (menu, lid, power button): never, per the ruling.
- Display sleep, any machine-wide power setting (pmset, powercfg, logind.conf), or anything that
  outlives the gateway process.
- The `lan` exposure as a trigger (not remote access).

## Current code reality (2026-11-02)

- `abstractgateway/src/abstractgateway/keep_awake.py`: `default_backend()` returns
  `MacIdleSleepAssertion()` on `darwin`, else `None`; `_UNSUPPORTED` names the Linux and Windows
  equivalents in the boot line; `KeepAwake.status()` reports `unsupported` there.
- Tests: `abstractgateway/tests/test_keep_awake.py` (fake backends, `platform="linux"` case; a darwin-only
  IOKit acquire/release smoke test).
- console-tui: `src/ui/host.rs` renders Start at login (`load_start_at_login`, `toggle_start_at_login`);
  no keep-awake call exists in `api_operator.rs` / `store_operator.rs`.

## Acceptance criteria

- [ ] Linux: on a desktop session with logind, `systemd-inhibit --list` shows "AbstractGateway" with
  `idle` while remote access is on, and nothing after the gateway is stopped or SIGKILLed.
- [ ] Windows: `powercfg /requests` lists the gateway under SYSTEM while remote access is on, and nothing
  after it stops or is killed.
- [ ] Unit tests with the system calls faked for both backends; a real-call smoke test per OS, skipped
  elsewhere (as the darwin one is).
- [ ] console-tui shows the same `line`/`detail` and switch as the web console; the switch is disabled
  with the launch-flag sentence when `setting.source == "flag"`.
- [ ] Docs: `abstractgateway/docs/configuration.md#keep-this-mac-awake-for-remote-access` and
  `docs/console.md` updated in the same change; llms files regenerated.

## Receipts

- macOS delivery: AbstractGateway branch `feat/keep-awake-remote` (PR to be linked), AbstractAssistant
  branch `feat/keep-awake-remote` ("Your Mac may be asleep." on the watch and the iPhone).
