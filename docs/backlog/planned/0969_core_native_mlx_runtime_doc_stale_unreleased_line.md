# 0969 — AbstractCore docs: stale "unreleased" line in native-mlx-runtime.md

> Package: abstractcore (docs)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: docs, coredoc

## Summary

`docs/native-mlx-runtime.md` still says "These integration changes are unreleased; update both Core and Runtime together." They shipped. Remove or restate the line (and regenerate the llms files) in the next AbstractCore docs pass.

## Why

Ledger: "Follow-up: core docs/native-mlx-runtime.md:113 stale 'unreleased'."

## Current code reality (2026-09-28)

- abstractcore main `238b693`: `docs/native-mlx-runtime.md` around line 113.

## Scope

### In scope

- Fix the line; regenerate `llms-full.txt`.

### Out of scope

- Other doc changes.

## Acceptance criteria

- [ ] No "unreleased" wording for shipped features in that page.

## Validation

`grep -n unreleased docs/native-mlx-runtime.md`.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
