# 0958 — Review the gateway's remaining size bounds under ADR-0026

> Package: abstractgateway
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: adr-0026, bounds, review

## Summary

After the wave-2 cap removals the gateway still bounds several inputs and outputs: skill text 16k, search excerpt 240, `instruction_max_chars` 400, email clamps, batch prompt 1.8M, report context 80k, template 250k, assist output draft 400k. Each must be either justified (a protocol or safety limit, documented) or removed under ADR-0026.

## Why

Ledger: "smaller gateway bounds (skill 16k, search excerpt 240, instruction_max_chars 400, email clamps, batch prompt 1.8M, report ctx 80k, template 250k, assist output draft 400k)".

## Current code reality (2026-09-28)

- Listed from abstractgateway `wave2/gw-integrate` during the ADR-0026 pass; unchanged in 0.7.0.

## Scope

### In scope

- One decision per bound: keep (documented reason) or remove, with tests.

### Out of scope

- Run-chat grounding (0957).

## Acceptance criteria

- [ ] Every remaining bound has a documented reason or is gone.

## Validation

Grep the listed constants; tests for each removed bound.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
