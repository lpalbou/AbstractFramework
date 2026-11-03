# 1101 — Keep the computer awake while the gateway runs on Linux and Windows

> Package: AbstractGateway
> Type: task
> Created: 2026-11-02
> Priority: normal
> Labels: power, keep-awake, follow-up

## Summary

On macOS, `abstractgateway serve` holds the `PreventUserIdleSystemSleep` assertion while it runs
(`src/abstractgateway/keep_awake.py`, AbstractGateway PR #91). Linux and Windows get the same: no idle
sleep while the gateway runs, released with the process; an explicit sleep still sleeps.

## Why

Operator, 2026-11-02: "when the gateway is on, the computer must not go to sleep, period, unless the user put
the computer to sleep (or on a MBP, close the lid)."

## Scope

### In scope

- Linux: logind idle inhibitor (`Inhibit("idle", …)` over D-Bus, or `systemd-inhibit --what=idle`) held by `serve`.
- Windows: `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` held by `serve`.

### Out of scope

- Any setting, switch or status surface; any machine-wide power setting.

## Acceptance criteria

- [ ] `systemd-inhibit --list` (Linux) / `powercfg /requests` (Windows) show the gateway while it runs, nothing after it stops.

## Receipts

- macOS: AbstractGateway PR #91.
