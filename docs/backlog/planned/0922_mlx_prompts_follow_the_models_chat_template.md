# 0922 — MLX prompts must follow the model's chat template (tool calls in history, tool responses, thinking opening)

- **Status:** planned (fix committed 2026-09-26 on abstractcore main as 3b9f6bf, unreleased; ships as abstractcore 2.16.1 on the operator's go)
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

## Progress (2026-09-26)
- abstractcore 3b9f6bf: every MLX lane (mlx-lm, native MTP/APC, vision add-on, Outlines) renders through `tokenizer.apply_chat_template`;
  earlier assistant turns keep their tool calls, tool results render as the template renders them, `tools=` reaches the template's tool
  block, the generation prompt opens `<think>` when the template does; a later system message becomes a `<system_instruction>` user turn;
  no-template tokenizer → built-in renderer (logged once); raising template → fallback + `#FALLBACK` warning; prompt-cache fragments carry
  serializer `mlx-prompt-fragment/v2:chat-template:<sha>` so old KV artifacts rebuild. 25 golden tests against the real Qwen3.8 tokenizer.
- Hermetic re-run of XP config A (gateway on 18891): iteration-3 visible tool calls 3/3 (was 0/5); digest 2/3. Run-3 looped on its own past
  reasoning from iteration 9 (see 0925). Prompt cache: 4 cold starts then 76 `hit_restore`; E2E check 6 holds (A2 8.27 s, B2 TTFT 0.40 s).
- Review 31 (untracked/missions-2026-09-25/REVIEW/31-core-mlx-chat-template.md): GO; rendered prompts byte-identical to the native
  template 12/12 on Qwen3.5/3.6/3.8. Medium follow-up D1 to land in the same patch: one history tool call whose arguments are not a JSON
  object makes the template raise and the whole run falls back to the old renderer for its remaining calls → wrap unparseable arguments
  and report the renderer in each response's metadata. Lows: a template merely containing the word "tools" is assumed to render tool
  definitions; image parts in history are dumped as JSON with base64; Outlines with thinking explicitly on decodes inside `<think>`.
