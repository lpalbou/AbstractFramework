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

## Update (2026-09-26, after experiment XP)
The experiment (untracked/missions-2026-09-25/XP/REPORT.md) did not reproduce calls inside an unclosed thinking block in 162
generations, but reproduced a related failure every time: a one-sentence announcement ("Let me verify …") with no call accepted as
the final answer. Re-prompting once with the VERBATIM reply gave 5/5 compliance; with the emptied record the model hallucinated
that the tools had run. abstractagent 3eb34e6 (0.3.15 candidate) implements: announcement/unrunnable detection → one re-prompt
with the verbatim reply → visible error on a second failure; `tool_calls_from_reasoning` shown. Root cause of the announcements:
0922 (MLX prompt template).

## Completion report (2026-09-27)
- **Completed:** 2026-09-27 (released as abstractagent 0.3.15, tag v0.3.15 → 6595453, PyPI 22:44 CEST 2026-09-26; abstractcore 2.16.0
  already shipped the recovery of tool calls written inside the thinking block, ffbd1e6).
- **Original path:** proposed/0918_… (promoted straight to completed by the release).
- **Outcome:** abstractagent 3eb34e6 → 66c376d → a28ce85 → 1b54ce4: a reply that announces tool use without calling a tool, or whose tool
  calls could not run, is re-prompted ONCE with the failed reply quoted verbatim in the corrective user message (Qwen3.5/3.6 templates
  strip `<think>` from assistant history); `stop_reason.code = "no_tool_call"` (+ `budget_exhausted`) in all three loops; the
  announcement or tool markup is never published as the answer; the long-reply nudge is bounded to once per step; detector patterns
  extended (English only, agent backlog 0033); crash fix for 0.3.13/0.3.14 (CodeAct/MemAct NameError). Reviews 28 NO-GO → 29 GO → 30 GO.
- **Residual:** CodeAct/MemAct return no `stop_reason` on plain iteration exhaustion (only `outcome: iteration_budget`); non-English
  announcements are not detected.

## Addendum (2026-09-27): the announcement heuristic is reverted (unreleased)
The text heuristic is withdrawn by the operator's decision: text heuristics that infer intent from wording are not accepted in the
framework, and a fix must not target one model's occasional failure. abstractagent daf49be (local, unpushed, unreleased) reverts 3eb34e6,
a28ce85 and 1b54ce4 — the announcement detector, the corrective re-prompt, the `no_tool_call` stop, the conclusion-path drop, the
`check_unrunnable_calls` switch, the jinja2 test extra and the Qwen3.6 fixture — and keeps 66c376d (the CodeAct/MemAct crash fix).
The tree equals v0.3.14 + the crash fix + version/changelog strings + backlog 0034. Suite 458 passed / 2 skipped. Evidence behind the
decision: REVIEW/35 (0 misfires on 1,889 real answers, but 16/30 realistic "result delivered, follow-up promised" answers fire; a misfire
replaces the answer with an error; no reachable switch on gateway workflow steps). The digest stop itself is fixed structurally in
abstractcore 2.16.1 (0922). Released 0.3.15 still carries the heuristic; the removal ships when the operator decides (a Codex sweep of
the revert is pending at the time of writing). Text heuristics already present in 0.3.14 (`_looks_like_deferred_action` followthrough
nudge, `circling_streak`) are listed for the operator's decision, not changed.
