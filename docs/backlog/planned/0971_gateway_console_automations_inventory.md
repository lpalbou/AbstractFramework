# 0971 — Gateway consoles: an automations inventory (split from 0930)

> Package: abstractgateway (web console, terminal console)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: automations, console, admin

## Summary

0930 planned automations in AbstractCode and in the gateway consoles. The AbstractCode half shipped in abstractcode 0.7.0 / @abstractframework/code 0.6.0. The console half remains: an admin inventory of every automation (owner, state, next run, what needs attention) with pause/resume and archive, in the web console and the terminal console, and the legacy-schedule distinction.

## Why

0930 scope; split at its completion on 2026-09-28.

## Current code reality (2026-09-28)

- abstractgateway 0.7.0 consoles have no automations screen (no automation code under `src/abstractgateway/console*` or `console-tui/src`).

## Scope

### In scope

- A read-first inventory with pause/resume/archive for admins, both consoles, from the existing Automations API.

### Out of scope

- Creating automations from the console.

## Acceptance criteria

- [ ] An admin sees and controls every automation from either console.

## Validation

`tests/test_console_automations.py` and a console-tui headless test.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
