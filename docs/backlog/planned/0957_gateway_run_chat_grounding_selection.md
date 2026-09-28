# 0957 — Run chat grounding: select or summarise run records instead of fixed caps

> Package: abstractgateway (run chat)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: adr-0026, run-chat, grounding, design

## Summary

`POST /runs/{id}/chat` grounds the model in the run: it keeps a 180k context budget, 2,400 characters per prompt and response, 20 tool calls, and the first 30 plus last 90 records. ADR-0026 (no message caps; models use their full context) removed the caps on the chat history, but these grounding caps remain because the run can be far larger than any context. They need a selection or summary design rather than fixed cuts.

## Why

Ledger: "BACKLOG after wave: run-chat grounding caps (180k context, 2400 per prompt/response, 20 tool calls, first30/last90 records) need a selection/summary design". Operator ruling 2026-09-28 (ADR-0026).

## Current code reality (2026-09-28)

- abstractgateway 0.7.0 (`cbe2ef5`) windows the chat history through the runtime; the run grounding keeps the caps above.

## Scope

### In scope

- Design how run records are selected (relevance, recency, the question) or summarised, recorded in the answer's receipt.
- Implement it and remove the fixed cuts.

### Out of scope

- The chat history window (done in 0.7.0).

## Acceptance criteria

- [ ] No fixed per-record character cut in run grounding; the receipt says what was included.

## Validation

Tests on a large synthetic run; the receipt lists included and omitted records.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
