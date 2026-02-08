# Prompt Caching (Prompt / KV)

This guide explains how the framework should think about caching for LLM calls, with an emphasis on prompt/KV caching
(prefill reuse) rather than response memoization.

## Terminology (three different "caches")

1. Response cache (exact/semantic)
   - Memoize final model outputs keyed by the input request.
   - Useful for repetitive questions, but risky for correctness drift.

2. Prompt/KV cache (prefix/prefill reuse)
   - Reuse the model's internal KV state for repeated prompt prefixes.
   - This can dramatically reduce time-to-first-token for long prompts with stable prefixes.

3. Composable KV modules (advanced)
   - Precompute caches for separate chunks (docs, history) and stitch them later.
   - This is typically an engine-level feature and not guaranteed uniformly across providers.

## AbstractCore support (best-effort)

AbstractCore exposes a provider-optional prompt cache surface. Depending on provider/backend, it may be:
- fully supported (in-process local backends),
- pass-through to an upstream server,
- or a no-op.

Typical usage patterns:

```python
from abstractcore import create_llm

llm = create_llm("mlx", model="mlx-community/Qwen3-4B")
llm.prompt_cache_set("tenantA:session123")  # also sets the default key

llm.generate("Hello")
llm.generate("Continue, but shorter.")
```

Or per-call:

```python
resp = llm.generate("Summarize this.", prompt_cache_key="tenantA:session123")
```

## Gateway/runtime note

In gateway-first deployments, prompt caching (when enabled) should be scoped per user/session to avoid accidental
cross-user reuse. Prefer stable `session_id` values so cache keys remain stable across multiple runs.

