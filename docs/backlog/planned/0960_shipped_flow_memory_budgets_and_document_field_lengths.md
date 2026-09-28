# 0960 — Shipped memory budgets (ltm-ai-kg) and flow-document field lengths

> Package: abstractflow, abstractgateway (shipped bundles)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: adr-0026, flows, memory

## Summary

Two groups of bounds were left to their owners in the ADR-0026 pass: the ltm-ai-kg memory budgets, and field length limits in the flow document format. Each needs a keep-or-remove decision like 0958.

## Why

Ledger: "Left for owners: ltm-ai-kg budgets, flow-document field lengths" and "shipped memory budgets (ltm-ai-kg); flow-doc field lengths".

## Current code reality (2026-09-28)

- Unchanged in flow 0.4.0 and gateway 0.7.0.

## Scope

### In scope

- Decide and implement per bound.

### Out of scope

- Bounds already removed in wave 2.

## Acceptance criteria

- [ ] Each bound is documented or gone.

## Validation

Tests per removed bound.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
