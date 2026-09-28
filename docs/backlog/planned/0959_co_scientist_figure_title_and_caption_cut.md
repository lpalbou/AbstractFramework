# 0959 — co-scientist cuts figure titles and captions (110/300 characters) from model output

> Package: abstractflow (co-scientist flow), abstractgateway (shipped bundle)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: adr-0026, flows, co-scientist

## Summary

The shipped co-scientist workflow cuts model-written figure titles to 110 and captions to 300 characters before they enter the report. Under ADR-0026, model output is not truncated; if a length matters for layout, the prompt should ask for it and the renderer should wrap.

## Why

Ledger: "BACKLOG: co-scientist figure title/caption cut (110/300, model output into report), top-8 tournament (algorithm, keep)".

## Current code reality (2026-09-28)

- co-scientist 0.2.1 (shipped by gateway 0.7.0) still carries the 110/300 cut; the top-8 tournament is an algorithm choice and stays.

## Scope

### In scope

- Remove the cut; ask for concise titles in the prompt; let the report renderer wrap.

### Out of scope

- The tournament size.

## Acceptance criteria

- [ ] A long model title reaches the report whole.

## Validation

Flow test with a long title, RED on the current bundle.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
