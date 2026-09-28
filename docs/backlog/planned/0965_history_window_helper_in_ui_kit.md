# 0965 — One TypeScript history-window helper in ui-kit instead of per-app copies

> Package: abstractuic (ui-kit), abstractflow, other TS apps
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: adr-0026, dedup, ui-kit

## Summary

Several TypeScript apps carry their own copy of a history window estimate (`len/4` tokens, Flow's per-message fold). The runtime owns the window; where a client still needs to estimate or show it, one ui-kit helper with the runtime's estimator should replace the copies.

## Why

Ledger: "BACKLOG: TS window copies (len/4, flow per-message fold) -> ui-kit helper".

## Current code reality (2026-09-28)

- Copies exist in flow 0.4.0 and the apps listed by the apps gate; ui-kit 0.1.15 has no helper.

## Scope

### In scope

- A ui-kit helper matching the runtime's `window_transcript` estimator; apps switch to it.

### Out of scope

- Moving the window out of the runtime.

## Acceptance criteria

- [ ] No app carries its own window estimator.

## Validation

Grep for the copies; helper unit tests against runtime examples.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
