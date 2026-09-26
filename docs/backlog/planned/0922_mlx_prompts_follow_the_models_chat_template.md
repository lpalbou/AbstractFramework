# 0922 — MLX prompts must follow the model's chat template (tool calls in history, tool responses, thinking opening)

- **Status:** planned (fix in progress 2026-09-26; ships as abstractcore 2.16.1 on the operator's go)
- **Created:** 2026-09-26
- **Area:** abstractcore (MLX provider)

## Summary
The scheduled Observer digest run with `Jundot/Qwen3.8-27B-oQ4e-mtp` ends at iteration 3 with one sentence ("Let me verify …
before writing the digest.") and no tool call, 15/15 at the provider level and 5/5 through the gateway (experiment XP,
untracked/missions-2026-09-25/XP/REPORT.md). Cause: `mlx_provider.py` ~2147–2176 builds the prompt by hand and diverges from the
model's chat template: earlier assistant turns lose their tool calls, tool results are sent under an untrained `tool` role instead
of the template's `<tool_response>` block inside a user turn, and the prompt does not end with `<think>` when thinking is on.
Rendering the history exactly as the template does gave visible tool calls 5/5 at iteration 3.

## Scope
Render MLX prompts through the tokenizer's `apply_chat_template` (canonical messages with `tool_calls`, `tools=`,
`enable_thinking`), on every MLX lane; hand-built fallback only when a model has no template; byte-stable prefix across turns
so prompt caches keep hitting (E2E check 6 must still hold). Not in scope: other providers.

## Validation
Golden tests against the real Qwen3.8 template; the XP config-A run through the gateway produces a digest 3/3 with visible calls
at iteration 3; latency/prompt-cache proof unchanged.

## Related
0918 (agent re-prompt when a reply announces tools without calling them — abstractagent 0.3.15 candidate 3eb34e6).
