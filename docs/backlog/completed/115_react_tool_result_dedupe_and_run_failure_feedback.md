# Backlog: React Tool Result Dedupe + Failure Feedback

## Summary
- Prevent duplicate tool-result messages in ReAct context history.
- Surface clearer failure context in the Run modal UI.

## Why
- Duplicate tool results can break OpenAI-compatible tool-call ordering.
- Failed runs need actionable context (node + error) for debugging.

## Scope
- In scope:
  - Deduplicate tool-result messages by `tool_call_id` in ReAct observe step.
  - Harden LLM message sanitization to drop invalid tool message ordering.
  - Add a failure summary panel in the Run modal.
  - Add targeted tests for tool-result dedupe.
- Out of scope:
  - Changes to AbstractCore provider logic.
  - Historical run repair/migration.

## Dependencies
- AbstractAgent ReAct runtime.
- AbstractFlow UI (Run modal).

## Expected outcomes
- No invalid tool-call ordering in LLM requests.
- Failures show node + error at a glance in the UI.

## Implementation Report
- Deduped tool-result messages by `tool_call_id` in ReAct observe; duplicates are skipped with `#FALLBACK` warnings.
- Hardened LLM message sanitization to drop invalid/mismatched tool messages (also `#FALLBACK` tagged).
- Added a failure summary panel in the Run modal to surface node + error.
- Added a unit test to ensure duplicate tool results are not appended.

## Tests
- `pytest abstractagent/tests/test_tool_observe_emits_result_for_tui.py -q`
- `npm run build` (abstractflow/web/frontend)

## Update
- The ReAct dedupe/sanitization workaround was removed after the root-cause idempotency fix (see `116_tool_calls_idempotency_call_id_fix.md`).
- The failure summary panel remains in place for better run diagnostics.
