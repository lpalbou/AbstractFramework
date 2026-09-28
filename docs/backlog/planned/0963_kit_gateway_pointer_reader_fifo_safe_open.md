# 0963 — The kit's gateway pointer reader can hang on a FIFO

> Package: abstractuic (app-server gateway_pointer.js)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: gateway-pointer, robustness

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
