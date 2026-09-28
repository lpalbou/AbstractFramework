# 0963 — The kit's gateway pointer reader can hang on a FIFO

> Package: abstractuic (app-server gateway_pointer.js)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: gateway-pointer, robustness
> Status: completed 2026-09-28 — every pointer reader opens FIFO-safe (kit app-server 0.1.12 in AbstractUIC v0.1.15, published)
> Moved: `planned/0963_kit_gateway_pointer_reader_fifo_safe_open.md` → `completed/0963_kit_gateway_pointer_reader_fifo_safe_open.md` on 2026-09-28

## Summary

The app-server pointer reader opens `~/.abstractframework/gateway.json` without `O_NONBLOCK`. If the path is a FIFO (only the same user can create one), the open blocks and the app server hangs at start. The reader should open non-blocking and refuse anything that is not a regular file.

## Why

Ledger: "Kit nit: pointer open without O_NONBLOCK (FIFO hang, same user) -> backlog."

## Current code reality (2026-09-28)

- `abstractuic/app-server/src/gateway_pointer.js` (v0.1.14) opens with `O_NOFOLLOW` but not `O_NONBLOCK`.

## Scope

### In scope

- Open with `O_NONBLOCK | O_NOFOLLOW`, `fstat`, refuse a non-regular file; same check in the other readers if they share the gap.

### Out of scope

- Other pointer rules.

## Acceptance criteria

- [ ] A FIFO at the pointer path is refused at once.

## Validation

Test that creates a FIFO and asserts a fast refusal (RED: the current reader blocks).

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

## Completion (2026-09-28)

- **Kit:** `app-server/src/gateway_pointer.js` opens with `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, then
  `fstat`s. A FIFO or device is refused as not a regular file, and a file over 64 KiB is refused
  unread. Commit `48a0dbf` (app-server 0.1.12), in tag `v0.1.15`; `@abstractframework/app-server@0.1.12`
  is on npm. Its tests failed before the change.
- **Other readers**, checked on 2026-09-28:
  - AbstractCode TUI `tui/src/gateway_pointer.rs:76` and the gateway console
    `console-tui/src/pointer.rs:131` open with `O_NOFOLLOW | O_NONBLOCK`;
  - the Assistant got the same fix in `a3d7c9f` (ships in abstractassistant 0.9.1).
