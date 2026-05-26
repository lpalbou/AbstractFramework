# 076 — OpenAI Responses API Integration

**Status**: planned  
**Priority**: high  
**Component**: AbstractCore (OpenAI provider), AbstractCore server  
**Depends on**: 075 (capability-driven parameter filtering — completed)

---

## Summary

Migrate the AbstractCore OpenAI provider from the Chat Completions API (`/v1/chat/completions`) to the Responses API (`/v1/responses`). The Responses API is OpenAI's successor to Chat Completions, recommended for all new projects. It provides all Chat Completions functionality plus reasoning summaries, built-in tools, better cache utilization, and improved reasoning model performance.

## Why

1. **Reasoning visibility**: the Responses API exposes reasoning summaries (not raw chain-of-thought), which Chat Completions does not. AbstractCore's `GenerateResponse.metadata["reasoning"]` already supports this — three providers populate it (Ollama, OpenAI-compatible, base provider normalization) — but the OpenAI provider cannot because Chat Completions hides reasoning text.
2. **Better performance**: OpenAI reports 3% improvement on SWE-bench and 40-80% better cache utilization with Responses API.
3. **Reasoning item continuity**: Responses API allows passing reasoning items between turns, reducing token usage and improving multi-step reasoning quality.
4. **Future-proof**: Chat Completions remains supported but Responses is the recommended path. OpenAI's Assistants API is being deprecated in favor of Responses.

## Empirical evidence

Live API tests (2026-02-22) confirmed:
- `client.responses.create()` works with all models (gpt-5-mini, gpt-5.1, gpt-5.2, gpt-4.1)
- Text generation, instructions (system prompt), multi-turn messages, function calling, structured output, and streaming all work
- Reasoning summaries are returned for reasoning models when `reasoning.summary: "auto"` is set
- The `openai` Python SDK v1.93.0 fully supports `client.responses.create()`

## Scope

### What we do

1. **Rewrite OpenAI provider internals**: replace `client.chat.completions.create()` with `client.responses.create()` in `_generate_internal()`, `_agenerate_internal()`, and streaming paths
2. **Map parameters**: `messages` → `input`, system prompt → `instructions`, `max_completion_tokens` → `max_output_tokens`, `response_format` → `text.format`, tool call shapes
3. **Extract reasoning summaries**: populate `GenerateResponse.metadata["reasoning"]` from `output[type="reasoning"].summary`
4. **Auto-request reasoning summaries**: when `_is_reasoning_model()` is true, include `reasoning: {"summary": "auto"}` in the request
5. **Expose `reasoning_effort`**: pass through as a `reasoning.effort` parameter (optional kwarg)
6. **Set `store: false` by default**: avoid unexpected data retention on OpenAI's side; document this clearly
7. **Rewrite `_format_response()`**: parse `Response` objects instead of `ChatCompletion` objects
8. **Rewrite streaming**: handle Responses API event types (`response.output_text.delta`, `response.function_call_arguments.delta`, `response.reasoning_summary_text.delta`, `response.completed`)
9. **Update AbstractCore server `/v1/responses`**: for OpenAI models, optionally shortcut through the provider's Responses path instead of converting to Chat Completions format
10. **Tests**: empirical API tests for all paths (generation, tools, structured output, streaming, reasoning capture, multi-turn)

### What we don't

- Change other providers (Ollama, Anthropic, OpenAI-compatible, Portkey, etc.) — they remain on Chat Completions
- Change the `GenerateResponse` type — it already has the right fields
- Change AbstractRuntime or AbstractGateway — they consume `GenerateResponse` and read `metadata["reasoning"]` when present
- Change the AbstractCore server `/v1/chat/completions` endpoint — it continues to work

## Dependencies

- OpenAI Python SDK ≥ 1.30.0 (for `client.responses.create()` — currently at 1.93.0)
- model_capabilities.json `thinking_support` field (completed in #075)

## Implementation details

### Parameter mapping (Chat Completions → Responses API)

```
messages                → input (same role/content array accepted)
messages[0] role=system → instructions (top-level param)
max_completion_tokens   → max_output_tokens
response_format         → text.format
tools[].function        → tools[] with name/parameters at top level, strict=true default
tool_choice             → tool_choice (same semantics, slightly different shapes)
temperature             → temperature (same)
top_p                   → top_p (same)
seed                    → seed (same)
n (multiple choices)    → REMOVED (not supported, AbstractCore doesn't use it)
stop                    → REMOVED in Responses API
```

### Response mapping (Responses API → GenerateResponse)

```
response.output_text          → content
response.output[type=reasoning].summary[].text → metadata["reasoning"]
response.output[type=function_call]            → tool_calls list
response.output[type=message].content[].text   → content (fallback)
response.status               → finish_reason (completed→stop, incomplete→length)
response.usage.input_tokens   → usage.input_tokens
response.usage.output_tokens  → usage.output_tokens
response.usage.output_tokens_details.reasoning_tokens → usage.completion_tokens_details.reasoning_tokens
response                      → raw_response (full Response object)
response.model                → model
```

### Streaming event mapping

```
response.output_text.delta               → yield GenerateResponse(content=delta)
response.function_call_arguments.delta   → accumulate, yield on response.output_item.done
response.reasoning_summary_text.delta    → accumulate into reasoning metadata
response.completed                       → final yield with usage
```

### Reasoning summary auto-request

When `_is_reasoning_model()` returns True for the model, automatically include:
```python
reasoning={"summary": "auto"}
```
This requests the most detailed available summarizer. For models that don't support summaries, OpenAI ignores the parameter gracefully.

When the caller explicitly passes `reasoning_effort`, map it to:
```python
reasoning={"effort": reasoning_effort, "summary": "auto"}
```

### `store: false` policy

AbstractCore must set `store=False` by default on all Responses API calls. This prevents:
- Unexpected data retention on OpenAI's servers
- Compliance issues for privacy-sensitive deployments
- Hidden cost from stored responses

Document this in:
- AbstractCore server docs (API reference)
- Provider README
- CHANGELOG

Allow opt-in via a `store` kwarg on `generate()` or provider constructor.

### `raw_response` shape impact

The runtime LLM client (`abstractruntime/integrations/abstractcore/llm_client.py`) has a fallback function `_extract_reasoning_from_openai_like()` that parses `raw_response` looking for `choices[].message.reasoning_content`. With Responses API, `raw_response` will be a `Response` object with `output[]` items, not `choices[]` messages.

This fallback will silently return `None` (no crash) because it checks `isinstance(raw, dict)` and the structure won't match. Since `metadata["reasoning"]` will be populated directly by the provider, the fallback won't be needed. No runtime change required — just document the shape change.

### `unsupported_parameters` with Responses API

The Responses API may handle parameter restrictions differently from Chat Completions (e.g., silently ignoring vs returning 400). The current `unsupported_parameters` stripping in the provider remains as defense-in-depth regardless. Empirical verification needed during implementation.

## Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Streaming protocol rewrite | Medium | Comprehensive streaming tests with real API; event types are well-documented |
| `raw_response` shape change | Low | Runtime fallback silently returns None; `metadata["reasoning"]` populated directly; document in CHANGELOG |
| `store: true` default | Low | Explicitly set `store: false`; document clearly |
| Tool call format differences | Medium | Map `function_call` items to existing `tool_calls` list format; test with actual API |
| `unsupported_parameters` behavior | Low | Keep stripping as defense-in-depth; verify empirically |
| `stop` parameter removed | Low | Responses API doesn't support `stop`; callers rarely use it for OpenAI reasoning models |
| Async client | Low | OpenAI SDK has `client.responses.create()` for both sync and async paths |

## Missing model entries (minor, discovered during investigation)

The following models from OpenAI's current lineup are not in `model_capabilities.json` and could be added as part of this work or separately:
- `gpt-5.1-codex-max` (long-running Codex variant)
- `gpt-5.1-codex-mini` (cost-effective Codex variant)
- `o3-pro` (high-compute o3 variant)
- `gpt-5.2-chat-latest` / `gpt-5.1-chat-latest` / `gpt-5-chat-latest` (ChatGPT-specific aliases)

These are low priority — the framework handles unknown models gracefully via defaults.

## Expected outcomes

1. `create_llm('openai', model='gpt-5-mini').generate(...)` returns `metadata["reasoning"]` with a reasoning summary (not raw chain-of-thought)
2. All existing functionality preserved (tools, structured output, streaming, multi-turn)
3. Better cache utilization and model performance for reasoning models
4. Clean, silent parameter stripping (no warnings on default values)
5. `store: false` by default with opt-in documentation
6. Reasoning effort controllable via `reasoning_effort` kwarg
7. No changes needed in AbstractRuntime, AbstractGateway, or thin clients — they already read `metadata["reasoning"]`

---

## Critical assessment (agent notes, 2026-02-23)

### Claims to tighten

- **"Reasoning summaries (the actual thinking text)" is inaccurate**: Responses returns a *summary* (and only when requested) — not chain-of-thought / full internal reasoning. Treat this as a UX/observability feature, not "thinking text".
- **"Reasoning item continuity" needs explicit state**: you only get continuity if some identifier/items are carried across turns (e.g. `previous_response_id` / reasoning items). If AbstractRuntime/Gateway remain unchanged, plan an explicit per-call kwarg and/or a host-level state handoff.

### Compatibility edges to plan for (these are the hard parts)

- **Multi-turn + tools**: today AbstractCore history is Chat Completions-shaped (`assistant.tool_calls` + `role=tool` with `tool_call_id`). Responses multi-turn tool history has different primitives. Define an explicit translation strategy and make it the primary integration test.
- **Media**: current OpenAI media handling in AbstractCore emits Chat Completions-style content parts (`type: "text"` / `type: "image_url"`). Responses prefers `input_text` / `input_file` types. Decide whether to (a) keep Chat Completions formatting for `media=` within the OpenAI provider, (b) add a Responses-specific formatter, or (c) gate media support behind a later step.
- **`base_url` / OpenAI-compatible servers**: many OpenAI-compatible backends do not implement `/v1/responses`. If users set `OPENAI_BASE_URL` to a compatibility server, a hard switch will break. Recommend feature-flag + fallback to Chat Completions on 404/unsupported errors.

### API surface / rollout suggestions

- **Avoid a new `reasoning_effort` knob**: consider mapping existing `thinking=` (BaseProvider) to Responses `reasoning.effort` to keep the surface unified.
- **Be careful with "auto-request reasoning summaries"**: making `reasoning.summary: "auto"` unconditional for all thinking-capable models can change cost/latency. Consider opt-in (or tie it to `thinking=`).
- **Server `/v1/responses` contract**: the server currently accepts Responses-style `input`, but returns Chat Completions output. If you add an OpenAI-provider "shortcut", spell out whether `/v1/responses` remains a ChatCompletions-shaped response for compatibility, or becomes a true Responses object (breaking change).
