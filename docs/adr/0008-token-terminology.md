# ADR-0008: Token Terminology and Parameter Naming

## Status
Accepted (2025-12-17)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-17


## Context

LLM APIs use various token-related parameters with inconsistent naming across providers:

- **OpenAI** uses `max_tokens` for output tokens, deprecated in favor of `max_completion_tokens`
- **Anthropic** uses `max_tokens` for output tokens
- **Local inference** (LMStudio, Ollama, vLLM) typically follows OpenAI conventions

This creates confusion when building a unified framework because:
1. "max_tokens" can mean different things at different layers
2. Users conflate context window size with output token limits
3. Framework internals need clear terminology to avoid bugs

## Decision

Adopt a strict three-tier token terminology within the Abstract Framework:

### Core Token Parameters

| Parameter | Meaning | Typical Values |
|-----------|---------|----------------|
| `max_tokens` | **Context window size** - Total tokens the model can process (input + output) | 4K-1M depending on model |
| `max_output_tokens` | **Response limit** - Maximum tokens the model can generate in one response | 2K-64K depending on model |
| `max_input_tokens` | **Input limit** - Maximum tokens available for input (prompts + history) | Calculated or explicit |

### Constraint Relationship

```
max_tokens = max_input_tokens + max_output_tokens + delta
```

Where `delta` is a small buffer (typically 100-500 tokens) to ensure we never exceed `max_tokens` due to tokenization variance.

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────────┐
│  AbstractCode / ReactShell                                          │
│  User-facing: /max-tokens = context window size                     │
│  Stored in: _limits["max_tokens"]                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AbstractAgent (ReactAgent, CodeActAgent)                           │
│  Uses: max_tokens for context tracking, history truncation          │
│  Does NOT set: max_output_tokens (let provider decide)              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AbstractCore (Providers)                                           │
│  Reads: max_output_tokens from model_capabilities.json              │
│  Translates: to provider-specific API parameter                     │
│  Example: LMStudio API "max_tokens" = max_output_tokens             │
└─────────────────────────────────────────────────────────────────────┘
```

### Model Capabilities JSON

The single source of truth for model limits is `abstractcore/assets/model_capabilities.json`:

```json
{
  "qwen3-next-80b-a3b": {
    "max_tokens": 262144,           // Context window: 256K
    "max_output_tokens": 16384,     // Max response: 16K
    "tool_support": "prompted",
    ...
  }
}
```

### Provider Translation

Each provider translates `max_output_tokens` to its API's expected parameter:

| Provider | Internal param | API param | Notes |
|----------|---------------|-----------|-------|
| OpenAI | `max_output_tokens` | `max_tokens` (deprecated) or `max_completion_tokens` | o-series uses `max_completion_tokens` |
| Anthropic | `max_output_tokens` | `max_tokens` | Required parameter |
| LMStudio | `max_output_tokens` | `max_tokens` | OpenAI-compatible |
| Ollama | `max_output_tokens` | `num_predict` | Native API |
| HuggingFace | `max_output_tokens` | `max_new_tokens` | Transformers convention |

## Consequences

### Positive

1. **Clear semantics**: Each parameter has one unambiguous meaning
2. **No confusion**: Users set context window, providers handle output limits
3. **Model-aware defaults**: Each model gets its correct output limit from JSON
4. **Extensible**: Can add `max_input_tokens` validation later

### Negative

1. **Two "max_tokens" meanings**: The agent's `max_tokens` (context) differs from most LLM APIs' `max_tokens` (output)
2. **Documentation burden**: Must clearly explain the distinction

### Neutral

1. **No user control of output tokens**: Users cannot currently override `max_output_tokens` per-request (by design - model capabilities should be trusted)

## Implementation Notes

### Common Mistake to Avoid

Do NOT derive `max_output_tokens` from user's `/max-tokens` setting:

```python
# WRONG - Overrides model's correct max_output_tokens
llm_kwargs["max_output_tokens"] = min(self._max_tokens // 4, 16384)

# CORRECT - Let provider use model capabilities
# Provider reads max_output_tokens from model_capabilities.json
```

### Debug Tip

If you see `max_tokens: 16384` in LLM API logs when expecting 100000:
- This is CORRECT behavior
- 16384 is `max_output_tokens` (response limit), not context window
- The context window is used internally for history management, not sent in API

## References

- [OpenAI API Reference - max_tokens deprecation](https://platform.openai.com/docs/api-reference/chat)
- [LMStudio API Docs](https://lmstudio.ai/docs/api/rest-api)
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
