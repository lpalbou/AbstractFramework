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

## Current code reality (2026-09-28, investigated at the operator's request)

- **Where:** `abstractagent/src/abstractagent/adapters/transcripts.py:67` `OVERSIZED_MESSAGE_CLAMP_CHARS = 200_000`, applied in `sanitize_transcript_messages` (`:329`), the payload seam every agent loop passes (ReAct, CodeAct, MemAct, and entity visits, which run ReAct).
- **Why it exists:** the 2026-08-01 incident (entity "ephemeral"): a 5 MB screenshot read as text produced a 494,932-character `role:"tool"` message. The durable transcript was replayed whole on every later call, the request grew to 722,453 characters and was refused for exceeding the model context, and the session stayed wedged because the transcript is durable. The clamp lets an already-poisoned stored session recover without editing history. The 200,000 figure was chosen as "the largest whole-history budget in the stack" (the gateway session-seeding ceiling of that time, since removed in wave 2).
- **Scope: per message, every role, every call.** It is not limited to tool results: any single message (tool, user, assistant) whose content exceeds 200,000 characters is sent as its first 200,000 characters plus a labelled `… [N chars elided: oversized tool result - clamped at the LLM payload boundary; the full text remains in the durable record]` stub (`#[WARNING:TRUNCATION]`, ADR-0026 §1 marking). Test `test_structural_floor_applies_to_every_role` pins that. The durable transcript and ledger keep the whole text. Each message is judged alone; there is no cap on the total.
- **What changed since:** runtime 0.7.0/0.7.1 + agent 0.3.17 apply the 50,000-token history window, so a poisoned turn drops out as soon as a newer turn exists. The clamp still bites on (a) the current turn, where the oversized result is the thing the model must read, and (b) any lane that does not set the window flag (plain task runs).
- **Other agent caps:** `max_history_messages` and `max_message_chars` default to -1 (off) in ReAct/CodeAct/MemAct.
- **Related bug found during the investigation:** the same seam does `str(content)`, so a multimodal content list is stringified before the clamp (see 0977).

## Options for the ruling

1. **Remove it** (strict ADR-0026): an oversized result goes whole; if it exceeds the model's context the provider returns an error, which the run reports. Risk: a small-context model fails on that turn (the history window prevents the permanent wedge from 0.7.x on, but only on lanes that set it).
2. **Keep it, documented as the one ADR-0026 exception**, marked and recorded as today.
3. **Replace it with a model-aware rule:** no fixed character number; a single message is only bounded when it alone exceeds the model's real context (from AbstractCore's model capabilities), and the bound is recorded in the run. This removes the arbitrary 200k and keeps the incident fixed.

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
