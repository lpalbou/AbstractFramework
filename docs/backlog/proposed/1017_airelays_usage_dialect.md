# 1017 — AIRelays answers Chat Completions with Responses-API usage fields; AbstractCore reads only the Chat names

> Package: AIRelays (operator's relay app, outside the framework), abstractcore
> Type: proposal (defect report)
> Created: 2026-10-11
> Priority: normal
> Labels: providers, usage, tokens, openai-compatible
> Related: AbstractAssistant `docs/backlog/proposed/0011_token_usage_lost_upstream.md` (defect A, 2026-09-07, same root cause)

## Summary

The `endpoint:airelay` provider (AIRelays, `http://127.0.0.1:8317/v1`, served by
`/Applications/AIRelays.app … -m airelays serve`) returns a **Chat Completions** response
(`"object": "chat.completion"`, `choices[].message`) whose `usage` uses the **Responses API**
field names (`input_tokens`, `output_tokens`, `input_tokens_details`, `output_tokens_details`, plus a
non-standard `attribution` block). The OpenAI Chat Completions schema names them `prompt_tokens`,
`completion_tokens`, `prompt_tokens_details`, `completion_tokens_details`. AbstractCore's
OpenAI-compatible provider reads only the Chat names, so every call through AIRelays is recorded
with `input_tokens: 0, output_tokens: 0` and only `total_tokens` right.

## Why

Operator, 2026-10-11: "isn't airelay answering with proper openai standards? if not, explain and
detail in a proposed backlog."

Answer: not for usage. The envelope is Chat Completions, the usage is the Responses API's: AIRelays
relays a Responses-API upstream and translates the message but passes the usage through
untranslated (the item ids in `attribution`, `msg_…`, `rs_…`, `fc_…`, are Responses output items).

## Evidence (2026-10-11, run b683459f, sub-run 5596be5a, first `llm_call`)

- `result.raw_response`: keys `id, object, created, model, choices, usage`; `object` =
  `chat.completion`; `choices[0].message.tool_calls` in Chat format.
- `result.raw_response.usage`: `input_tokens 6340, output_tokens 228, total_tokens 6568,
  input_tokens_details {cached_tokens 2560, cache_write_tokens 0}, output_tokens_details
  {reasoning_tokens 8}, attribution {...}`.
- `result.usage` (normalised by AbstractCore): `input_tokens 0, output_tokens 0, total_tokens 6568,
  prompt_tokens 0, completion_tokens 0`.
- Whole run tree of b683459f (16 runs, 178 model calls): 3.76M tokens with no split recorded; the
  split recovered from the raw responses is 3.7M in / 80k out.
- AbstractCore: `abstractcore/abstractcore/providers/openai_compatible_provider.py:372-376`
  (`usage.get("prompt_tokens", 0)` / `completion_tokens`), cached tokens read only from
  `prompt_tokens_details` (`:385-388`).

## Consequences

Zero input/output tokens in every client for AIRelays calls (AbstractFlow's run pulse, run badges,
AbstractAssistant footers, Observer), wrong cost estimates, and the cached-token count lost.
AbstractFlow's run pulse works around it since 2026-10-11 by reading the split from
`raw_response.usage` (a client reading raw provider data, which should not be needed).

## Options

1. **AIRelays** (the standards fix): translate usage on its Chat Completions surface to
   `prompt_tokens` / `completion_tokens` / `total_tokens` with `prompt_tokens_details.cached_tokens`
   and `completion_tokens_details.reasoning_tokens`; keep `attribution` only under a vendor key.
2. **AbstractCore** (robustness, recommended in any case): accept both dialects in
   `_build_usage_dict` (Chat names first, Responses names as fallback, details from either),
   with a test per dialect. This is AbstractAssistant 0011 defect A.
3. Then remove AbstractFlow's raw-response fallback in `src/utils/runPulse.ts`.

## Promotion criteria

The operator's choice between 1 and 2 (or both).
