# Backlog: Tool Calls Idempotency Call-ID Fix

## Summary
- Fix tool-calls idempotency collisions by including `call_id` in the idempotency key.

## Why
- Reusing prior tool results for a new tool call breaks tool-call ordering and can crash LLM requests.

## Scope
- In scope:
  - Adjust idempotency normalization for TOOL_CALLS to retain `call_id` when present.
  - Update idempotency tests to reflect call-id aware behavior.
  - Remove workaround logic that masked duplicate tool results.
- Out of scope:
  - Provider-specific tool-call formatting changes.

## Expected outcomes
- Distinct tool calls with the same arguments no longer collide.
- Restart idempotency remains stable when `call_id` is unchanged.

## Implementation Report
- Tool-call idempotency now retains `call_id` when present, preventing cross-call collisions.
- Updated tool-call idempotency tests for call-id aware behavior.
- Removed the ReAct dedupe/sanitization workaround (root fix now covers the issue).

## Tests
- `pytest abstractruntime/tests/test_tool_calls_idempotency_keys.py -q`
- `pytest abstractagent/tests/test_tool_observe_emits_result_for_tui.py -q`
