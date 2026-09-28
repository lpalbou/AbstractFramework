# 0956 — Config manager environment restore gaps across instances

> Package: abstractcore (config manager)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: config, environment, isolation

## Summary

AbstractCore's config manager exports saved settings into the process environment for some engines and restores them afterwards. With more than one instance (different config files in one process, as the gateway and tests do), the restore is incomplete: values from one instance can remain visible to the next.

## Why

Ledger: "BACKLOG: config/manager env-restore gaps across instances" (core re-gate, 2026-09-28).

## Current code reality (2026-09-28)

- Found by the core 2.18.0 gate while reviewing the saved-key export (the key path itself was changed to a per-request host setting in 2.18.0).

## Scope

### In scope

- Every environment write by the config manager is scoped and restored, per instance.
- Prefer passing settings explicitly over exporting them.

### Out of scope

- The saved OpenAI key path (handled in 2.18.0).

## Acceptance criteria

- [ ] Two instances in one process see only their own settings; a test proves it.

## Validation

A test creating two instances with different config files, RED on the current code.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
