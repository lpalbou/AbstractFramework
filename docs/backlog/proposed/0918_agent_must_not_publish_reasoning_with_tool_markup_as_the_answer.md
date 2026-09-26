# 0918 — The agent must not publish reasoning that still holds tool-call markup as the answer

- **Status:** proposed
- **Created:** 2026-09-26
- **Area:** abstractagent (react loop), abstractcore (parser)

## Summary
When a reply has no visible content, `abstractagent/logic/react.py:~178` uses the model's reasoning as the final answer. On
2026-09-26 a scheduled Observer run with `Jundot/Qwen3.8-27B-oQ4e-mtp` "completed" with three raw `<tool_call><function=fetch_url>`
blocks as its outcome: the model had written the calls inside its thinking block, the MLX non-streamed path strips thinking before
tool parsing, so no call was found. abstractcore ffbd1e6 (2.16.0) recovers complete calls from the reasoning when tools are offered;
the agent fallback is still the wrong behaviour for what is left (calls naming a tool that was not offered, calls cut off
mid-parameter): it should surface the failure, not present the markup as an answer.

## Why
Silent completion with tool markup as the outcome hides a failed step from the user and from every host (Observer, Code, Assistant).

## Current code reality
Evidence: untracked/missions-2026-09-25/TC/NOTES.md (root cause, template quote, per-parser behaviour). Core: `base.py`
`_recover_tool_calls_from_reasoning` (metadata `tool_calls_from_reasoning`, warnings for unknown tools / cut calls).

## Scope / non-goals
In the agent: when content is empty and the reasoning contains tool-call markup that was not executed, end the step with a visible
error ("the model asked for `<tool>` which is not available" / "the tool call was cut off") instead of an answer; keep the
plain-reasoning-as-answer fallback for replies without markup. Also review the legacy `execute_tools=True` mode, which does not see
recovered calls.

## Validation
A ReAct test with a fake provider emitting the operator's exact text, tools not offered → the step fails loudly; tools offered →
three tool executions (already covered in core).
