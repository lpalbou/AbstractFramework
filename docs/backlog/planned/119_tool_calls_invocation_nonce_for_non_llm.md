# 119 — TOOL_CALLS Invocation Nonce for Non‑LLM Tool Calls

**Status**: Planned  
**Date**: 2026-02-24  
**Priority**: Medium (correctness + durability)  
**Components**: abstractruntime (core runtime + policy), visualflow compiler (optional)

## Summary

Guarantee that **two identical tool calls intended as separate invocations** are executed twice (not deduped) even when the workflow emitted `EffectType.TOOL_CALLS` entries without a `call_id`/`id`, while preserving **crash-safe replay/idempotency**.

## Problem

AbstractRuntime reuses prior effect results based on an **idempotency key**. For `EffectType.TOOL_CALLS`, the key includes each tool call’s `call_id` when present, but tool calls created outside an LLM can omit `call_id`/`id`.

When `call_id` is missing:
- Two distinct invocations with identical `{name, arguments}` can collide on the same idempotency key.
- The second invocation may incorrectly reuse the first invocation’s result (skipping execution).
- For OpenAI-style tool transcripts, this can also create invalid tool-call ordering/correlation.

## Goal

If a workflow emits tool calls without `call_id`/`id`, the runtime should still be able to:
1) Assign a **durable** per-invocation identifier before execution.
2) Use that identifier to prevent “run twice” calls from colliding.
3) Preserve **restart-safe reuse** for the *same* invocation (don’t double-execute after crashes).

## Proposed Approach (Runtime‑Owned Invocation Nonce)

Add a runtime-owned per-node invocation counter and assign `call_id` deterministically when missing:

- Introduce a durable counter under `run.vars["_runtime"]["tool_calls"]["invocations"][node_id]` (or similar).
- When producing/executing a `TOOL_CALLS` effect:
  - If any tool call lacks `call_id`/`id`, mint `call_id` from:
    - `run_id`, `node_id`, **invocation_index**, and tool-call index within the batch.
  - Persist the counter increment **before** running the tool handler (two-phase style), so restarts reuse the same invocation index.
- Compute idempotency keys including this minted `call_id` so identical args in consecutive invocations do not collide.

## Scope

### In scope
- Runtime assigns durable per-invocation `call_id` for missing IDs (non-LLM tool calls).
- Idempotency keys become stable per invocation (no unintended reuse).
- Tests for:
  - “Same args twice” executes twice when minted invocation id differs.
  - Restart reuses the prior result for the same invocation id.

### Out of scope
- Changing existing behavior when model/provider already supplies `call_id`.
- Removing idempotency/replay semantics for tool calls.
- UI changes (warnings panels, etc.).

## Notes / Open Questions

- **Where to implement**: runtime core is the lowest common choke point (covers VisualFlow, agents, and custom workflows). VisualFlow compiler may optionally add call IDs earlier, but cannot enforce global semantics alone.
- **Batch semantics**: decide whether the invocation index increments per `TOOL_CALLS` effect or per tool call within the effect (recommend: per effect, plus tool-call index within effect).
- **Failure modes**: if persistence of the invocation index fails, must emit a `#FALLBACK` warning and default to conservative behavior.

## Acceptance Criteria

- Two consecutive `TOOL_CALLS` effects with identical `{name, arguments}` and missing IDs both execute (no reuse), and the second does not reuse the first result.
- After a simulated crash/restart at the same node, the same invocation reuses the prior completed result (idempotency preserved).
- No silent fallback: missing IDs are observable (warnings already exist); nonce assignment is deterministic and durable.

