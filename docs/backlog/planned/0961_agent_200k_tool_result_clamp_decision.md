# 0961 — OPERATOR DECISION GATE: keep or remove the agent's 200k-character tool-result clamp

> Package: abstractagent
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: decision-gate, adr-0026, agent, tool-results

## Summary

OPERATOR DECISION GATE (never assignable): AbstractAgent clamps an oversized tool result to 200,000 characters (`OVERSIZED_MESSAGE_CLAMP_CHARS`) before it enters the model input. That is a character cap on model input, which ADR-0026 otherwise forbids; it exists because a single poisoned tool result (495k characters) once rode every later turn. Since AbstractRuntime 0.7.0 the history window drops a poisoned turn once a newer turn exists, which weakens the reason for the clamp but not for the current turn.

## Why

Ledger: "DECISION for operator (report): agent's 200k-char tool-result clamp (OVERSIZED_MESSAGE_CLAMP_CHARS) remains = char cap on model input; runtime's tighter 32k visit cap removed."

## Current code reality (2026-09-28)

- `abstractagent/src/abstractagent/adapters/transcripts.py:67` `OVERSIZED_MESSAGE_CLAMP_CHARS = 200_000` (agent 0.3.17).

## Scope

### In scope

- Operator ruling: keep (and document it as the one exception) or remove (tool results enter whole; the window handles history).

### Out of scope

- Implementing before the ruling.

## Acceptance criteria

- [ ] The ruling is recorded, and the code and ADR-0026 agree with it.

## Validation

Per the ruling.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
