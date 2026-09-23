# 0213 — ReAct Context Fidelity: Thought Retention, De-duplication, Truncation Hygiene

**Status**: Planned
**Date**: 2026-07-07
**Priority**: High (multi-step coherence + token cost + ADR-0026 hygiene)
**Components**: abstractagent (react_runtime, logic/react)

## Summary
Keep the model's own reasoning reachable across ReAct cycles, stop paying for tool observations
twice, and bring the loop's bounded previews into ADR-0026 compliance. This is a coherence/cost
improvement, **not** a data-loss fix — the underlying content is already durably preserved.

## ADR status
- Governing ADRs: ADR-0026 (truncation policy — tagging + marker requirements).
- ADR impact: None new. This item *closes* a minor ADR-0026 hygiene gap.

## Context / current code reality
Verified 2026-07-07:
- When the model emits tool calls, the assistant transcript message is stored with **`content=""`**
  (`react_runtime.py:1054-1061`; comment: "thought is stored in scratchpad (not user-visible
  history)"). The full reasoning IS preserved in `scratchpad.cycles[i].thought` (`:974`) and in the
  ledger LLM-response record — so no data is destroyed.
- The reasoning is re-surfaced to the model only via `_render_cycles_for_system_prompt` (last **6**
  cycles, thoughts truncated to **600** chars, observations to **220** chars, `react_runtime.py:423-494`),
  appended to the system prompt (`:909-917`).
- Tool observations are **double-carried**: the full rendered output is appended to
  `context.messages` as a `role="tool"` message (`observe_node`, `:1378-1385`) **and** a 220-char
  copy is rendered into the system-prompt scratchpad. The model already has the full copy in
  messages; the scratchpad copy is a redundant, truncated duplicate.
- The render truncations use a `…` marker but **lack** the `#[WARNING:TRUNCATION]` code tag and any
  `_truncation` metadata/warning event that ADR-0026 §1/§4 require. Contrast: CodeAct's
  `_truncate_block` (`codeact_runtime.py:945-951`) does it correctly (`#[WARNING:TRUNCATION]` +
  `… (truncated, N chars total)`).

## Problem
1. **Coherence gap ("thought amnesia"):** because the transcript stores `content=""` and the
   scratchpad only re-surfaces the last 6 (truncated) cycles, on iteration 15 the model cannot see
   its own reasoning from iteration 3. Multi-step coherence silently degrades on long tasks.
2. **Double-carry cost:** recent observations are sent twice (full in messages + truncated in the
   system prompt), wasting tokens and (with 0212) churning the cache prefix.
3. **ADR-0026 hygiene:** bounded previews exist without the required tag/metadata.

## What we want to do
Make the transcript the single, faithful record the model reads, and remove the redundant
system-prompt scratchpad copy.

## Requirements
1. **Retain assistant thought in the transcript.** Store the model's reasoning `content` on the
   assistant tool-call message (providers accept assistant messages carrying both `content` and
   `tool_calls`). This keeps reasoning in the append-only, cacheable message lane and removes the
   dependency on the 6-cycle window. Keep the durable `scratchpad.cycles` record for host-side
   observability/trace.
2. **Stop rendering the scratchpad into the system prompt** (coordinates with 0212). Observations
   already live in `context.messages`; the reasoning now lives there too, so the system-prompt copy
   is redundant. If any host-facing rolling summary is still wanted, keep it host-side, not in the
   model prefix.
3. **ADR-0026 hygiene for any remaining bounded preview** (e.g. host-side trace rendering): use the
   `#[WARNING:TRUNCATION]` tag + a clear `… (truncated, N chars total)` marker + metadata, mirroring
   CodeAct.

## Non-goals
- Do not truncate or drop the transcript itself (ADR-0026); this item removes a *duplicate*, it does
  not shrink the primary record.
- Do not change how tool observations are captured durably.
- Long-session growth of the primary transcript is handled by 0218, not here.

## Dependencies and related tasks
- **0212** (same file; implement together — 0212 removes the scratchpad-in-prompt, this item makes
  that safe by moving thought into the transcript).
- `planned/130_...` (research).

## Expected outcomes
- The assistant tool-call transcript messages carry the model's reasoning (non-empty `content`).
- The system prompt no longer contains a per-cycle scratchpad block.
- On a ≥12-iteration run, the model can reference its own earlier reasoning (verified behaviorally).
- Per-iteration prompt token count drops (no duplicated observations).
- No untagged lossy truncation remains in the ReAct render path.

## Validation
- Unit: after a tool-calling cycle, assert the assistant message in `context.messages` has non-empty
  `content` equal to the parsed reasoning; assert the system prompt contains no scratchpad block.
- Unit: grep the ReAct adapter for lossy slices; each must carry `#[WARNING:TRUNCATION]`.
- Live (endpoint `http://127.0.0.1:8317/v1`): a 12+ step task that requires recalling an early
  decision; compare task success + token/iteration before vs after.

## Progress checklist
- [x] Persist assistant reasoning into the transcript message.
- [x] Remove scratchpad-from-system-prompt rendering.
- [x] Tag/mark any remaining bounded preview per ADR-0026.
- [x] Tests + LIVE evidence (2026-07-08, OVH `gpt-oss-120b`): in a 12-call run, the final
      request's transcript carried all 5 assistant tool-call messages with non-empty reasoning
      content ("We need to read notes_a.txt. Use read_file tool." …) — the model's per-cycle
      thinking, which previously was stored as `content=""` (thought amnesia). Note: gpt-oss
      returns thinking via the reasoning channel (`result.content` is empty on tool rounds);
      the adapter folds it into the transcript message — exactly the retention this item asked
      for. System prompt simultaneously byte-stable (no scratchpad double-carry), see 0212.

## Guidance for the implementing agent
This is coherence + cost + hygiene, not a data-loss emergency: the reasoning is already durably
preserved. Do not add truncation anywhere. Coordinate edits to `react_runtime.py` with 0212.
