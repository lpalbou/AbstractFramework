# 0918 — Tool calls left in a thinking block: execute them; only surface what cannot run

- **Status:** proposed
- **Created:** 2026-09-26 (reworded the same day after the operator's ruling)
- **Area:** abstractagent (react loop), abstractcore (parser)

## Operator ruling (2026-09-26)
A stray `<think>` must not change what happens: if the reply has no visible content and the thinking block holds clean tool
calls (typically: the block contains only the calls), they are executed exactly as visible calls would be. This is what
abstractcore ffbd1e6 (2.16.0) implements: complete calls at the end of the reasoning are recovered when tools are offered, the
markup is removed from the reasoning, and the record notes `tool_calls_from_reasoning`.

## What is still open (this item)
Only the cases where nothing can run: a call that names a tool that was not offered, or a call cut off mid-parameter (core reports
both with a warning / `unparsed_tool_call`). Today `abstractagent/logic/react.py:~178` then falls back to publishing the reasoning
text as the final answer, so the user sees raw markup as an "answer". The agent should instead end the step with a visible
error naming the problem ("the model asked for `<tool>` which is not available" / "the tool call was cut off") and let the loop
retry or stop; the plain reasoning-as-answer fallback stays for replies without any tool markup. Also review the legacy
`execute_tools=True` mode, which does not see recovered calls.

## Evidence
untracked/missions-2026-09-25/TC/NOTES.md (root cause, chat-template quote, per-parser behaviour); the Observer run of
2026-09-26 with `Jundot/Qwen3.8-27B-oQ4e-mtp` (three `fetch_url` calls inside the thinking block, run "completed" with the markup
as outcome).

## Validation
ReAct test with a fake provider emitting the operator's exact text: tools offered → three executions (covered in core);
tools not offered / call cut off → the step ends with the named error, never a markup "answer".
