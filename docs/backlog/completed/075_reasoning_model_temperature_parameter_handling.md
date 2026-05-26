# 075 — Reasoning Model Temperature Parameter Handling

**Status**: completed  
**Priority**: medium  
**Component**: AbstractCore (providers), model_capabilities.json  
**Related**: AbstractRuntime (llm_client, compiler), AbstractGateway (routes)

---

## Summary

A `RuntimeWarning` is emitted when using `gpt-5-mini` (and all `gpt-5*` variants):

```
Temperature parameter requested but not supported by OpenAI reasoning models (gpt-5-mini).
```

The warning is technically correct (the provider silently drops temperature), but the root cause is a cascade of design gaps that should be addressed together.

## Root Cause Analysis

### 1. `_is_reasoning_model()` uses hardcoded substring matching

```python
# openai_provider.py:878-886
def _is_reasoning_model(self) -> bool:
    model_lower = self.model.lower()
    return (
        model_lower.startswith("o1") or
        "gpt-5" in model_lower or
        model_lower.startswith("gpt-o1")
    )
```

This catches ALL `gpt-5*` variants (`gpt-5`, `gpt-5-mini`, `gpt-5-turbo`, `gpt-5-pro`, `gpt-5-vision`) with a substring match. It also misses `o3`, `o3-mini`, `o4-mini` which are also reasoning models with parameter restrictions.

**Problem**: this is a name-based heuristic that will rot as models evolve. It belongs in the capabilities registry.

### 2. No `supports_temperature` field in `model_capabilities.json`

The canonical model registry (`abstractcore/assets/model_capabilities.json`) has rich capability fields (`tool_support`, `vision_support`, `thinking_support`, etc.) but **no field for parameter restrictions** like temperature, top_p, frequency_penalty, presence_penalty, or seed.

**Problem**: the single source of truth for model capabilities doesn't declare which sampling parameters a model accepts.

### 3. Temperature always flows from upstream callers

Three independent paths always inject temperature into provider kwargs:

| Caller | How temperature arrives | Default |
|---|---|---|
| **Gateway helper LLM calls** (`gateway.py:2321,2364,9017`) | Explicit `params={"temperature": 0.2}` | 0.2 |
| **Runtime VisualFlow executor** (`compiler.py:1788,1982`) | Always sets `{"temperature": float(temperature_value)}` | 0.7 |
| **Runtime LLM client** (`llm_client.py:1295-1316`) | Pass-through from `params` dict | varies |
| **BaseProvider default** (`interface.py:73,87`) | `self.temperature = 0.7` constructor default | 0.7 |

None of these callers check whether the target model accepts temperature. They all assume the provider will handle it.

### 4. Warning condition fires on defaults

```python
# openai_provider.py:227
if ("temperature" in kwargs) or (getattr(self, "temperature", 0.7) != 0.7):
```

The left side (`"temperature" in kwargs`) fires whenever any caller passes temperature — which is **always** in practice, since both the runtime compiler and the gateway helper calls explicitly set it. The right side (`!= 0.7`) fires when the provider instance was constructed with a non-default temperature.

This means the warning fires on every single call to a "reasoning model", even when the caller didn't intentionally set temperature. It's noise, not signal.

### 5. The `gpt-5` ≠ reasoning model assumption may be wrong

OpenAI's `o1` and `o3` families are explicitly "reasoning models" with restricted parameters. The `gpt-5` family may or may not follow the same restrictions — they are distinct product lines. The current code assumes all `gpt-5*` models behave like `o1`, which is speculative.

## Call Chain (full trace)

```
Gateway / Runtime
  └─ params={"temperature": 0.7}  (always present)
      └─ LocalAbstractCoreLLMClient.generate(params=...)
          └─ OpenAIProvider.generate(**kwargs)
              └─ _prepare_generation_kwargs(**kwargs)
                  └─ result_kwargs["temperature"] = 0.7  (from kwargs or self.temperature)
              └─ _generate_internal(...)
                  └─ _is_reasoning_model() → True  (substring "gpt-5" matches)
                  └─ "temperature" in kwargs → True  (always)
                  └─ warnings.warn(RuntimeWarning)  ← THE WARNING
                  └─ temperature is silently dropped from call_params
```

## Impact

- **Functional**: none — temperature is correctly dropped for the API call, the LLM call succeeds.
- **Noise**: the warning fires on every generation call, polluting logs and making real warnings harder to spot.
- **Correctness risk**: `o3`, `o3-mini`, `o4-mini` are NOT matched by `_is_reasoning_model()`, so temperature IS sent to those models (may cause API errors if they reject it).
- **Maintainability**: every new model family requires editing hardcoded checks in provider code.

## Proposed Resolutions

### Option A: Capability-driven parameter filtering (recommended)

**Scope**: AbstractCore only.

1. **Add `supported_parameters` to `model_capabilities.json`**:
   ```json
   "gpt-5-mini": {
     "supported_parameters": ["temperature", "top_p", "frequency_penalty", "presence_penalty", "seed"],
     ...
   }
   "o1": {
     "supported_parameters": [],
     ...
   }
   ```
   Or inversely, a negative list: `"unsupported_parameters": ["temperature", "top_p", ...]`.

2. **Replace `_is_reasoning_model()` with capability lookup**:
   ```python
   def _supports_parameter(self, param: str) -> bool:
       if self.model_capabilities:
           supported = self.model_capabilities.get("supported_parameters")
           if supported is not None:
               return param in supported
       # #FALLBACK: unknown model — send the parameter (let the API decide)
       return True
   ```

3. **Silently strip unsupported parameters** (no warning) when the caller used a default value. Only warn when the caller explicitly requested a non-default value that gets dropped.

**Pros**: single source of truth, no name-matching heuristics, easy to maintain, covers all models.  
**Cons**: requires updating `model_capabilities.json` for all models (one-time effort).

### Option B: Smarter warning condition (minimal fix)

**Scope**: AbstractCore `openai_provider.py` only.

1. Fix `_is_reasoning_model()` to also match `o3*`, `o4*`.
2. Change warning condition to only fire when temperature was **explicitly requested with a non-default value**:
   ```python
   requested_temp = kwargs.get("temperature")
   if requested_temp is not None and abs(float(requested_temp) - 0.7) > 1e-9:
       warnings.warn(...)
   ```

**Pros**: minimal diff, stops the noise.  
**Cons**: still uses hardcoded name matching, doesn't fix the structural problem.

### Option C: Caller-side awareness (upstream fix)

**Scope**: AbstractRuntime + AbstractGateway.

Have callers stop sending temperature when the target model is a reasoning model. This requires model-awareness in the runtime/gateway layer.

**Pros**: clean separation — callers decide what to send.  
**Cons**: duplicates model knowledge across layers, violates separation of concerns. The provider should be the authority on what its API accepts.

## Recommendation

**Option A** is the clean, robust, and efficient solution. It aligns with the existing pattern where `model_capabilities.json` is the single source of truth (per ADR in AGENTS.md: "Canonical registries: AbstractCore's model capabilities and architecture formats are owned by `abstractcore/assets/model_capabilities.json`").

**Option B** can be applied immediately as a low-risk noise fix while Option A is implemented.

**Option C** should be avoided — it scatters model-specific knowledge.

## What We Do / Don't

**Do**:
- Add parameter support metadata to model_capabilities.json
- Replace hardcoded `_is_reasoning_model()` with data-driven checks
- Fix the missing `o3`/`o4` detection
- Distinguish "caller explicitly set a value" from "default flowed through"

**Don't**:
- Change the gateway or runtime callers (they should remain model-agnostic)
- Remove the warning entirely (explicit non-default overrides should still warn)
- Break backward compatibility for existing provider subclasses

## Dependencies

- `abstractcore/assets/model_capabilities.json` schema update
- `abstractcore/providers/openai_provider.py` refactor
- Potentially `abstractcore/providers/openai_compatible_provider.py` (same pattern)
- Potentially `abstractcore/assets/README.md` (document new field)

## Expected Outcomes

1. No spurious `RuntimeWarning` for default temperature on reasoning models
2. Correct parameter filtering for `o3`, `o3-mini`, `o4-mini` (currently missed)
3. Single source of truth in `model_capabilities.json` for parameter support
4. Clean warning only when a caller explicitly requests a dropped parameter

---

## Report

**Investigation completed 2026-02-22. Implementation completed 2026-02-22.**

### Investigation findings
Traced the warning from `openai_provider.py:229` through the full call chain:
- `BaseProvider.generate()` → `_prepare_generation_kwargs()` → `_generate_internal()` → warning
- Upstream callers (gateway helper functions, runtime VisualFlow compiler, runtime LLM client) all always pass temperature
- The `_is_reasoning_model()` heuristic catches all gpt-5 variants via substring but misses o3/o4
- The warning condition `"temperature" in kwargs` fires on every call because callers always include it
- Root cause was architectural: parameter restrictions were hardcoded in provider methods instead of being declared in the capabilities registry

### Key design decisions
1. **`thinking_support` and `unsupported_parameters` are orthogonal**: `thinking_support` means "this model can reason/think" (output format). `unsupported_parameters` means "this model's API rejects these parameters" (API constraint). A model can think AND accept temperature (GPT-5.1, GPT-5.2, Qwen3, DeepSeek-R1), or think AND reject temperature (o1, o3, gpt-5, gpt-5-mini).
2. **`_is_reasoning_model()` answers "can this model think?"** — reads from `thinking_support`. No longer used for parameter filtering.
3. **Parameter filtering is driven by `unsupported_parameters`** — a data-driven list in model_capabilities.json. Absent = all parameters supported (backward-compatible).

### Empirical verification (live API testing 2026-02-22)

All parameter restrictions were verified by making live API calls to each model:

| Model | temperature | top_p | freq_penalty | pres_penalty | seed | max_tokens |
|---|---|---|---|---|---|---|
| **o1** | REJECTED | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **o3-mini** | REJECTED (1 ok) | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **o4-mini** | REJECTED | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **gpt-5** | REJECTED | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **gpt-5-mini** | REJECTED (1 ok) | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **gpt-5-nano** | REJECTED | REJECTED | REJECTED | REJECTED | ACCEPTED | REJECTED |
| **gpt-5.1** | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | REJECTED |
| **gpt-5.2** | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | REJECTED |
| **gpt-4.1** | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED |
| **gpt-4o-mini** | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED | ACCEPTED |

Key finding: GPT-5.1 and GPT-5.2 are the first reasoning models to re-accept sampling parameters.
All reasoning models (o-series + GPT-5 family) require `max_completion_tokens` instead of `max_tokens`.

### End-to-end verification
AbstractCore `create_llm('openai', model='gpt-5-mini').generate(...)` was tested:
- Before fix: crashed with 400 error (temperature=0.7 forwarded, rejected by API)
- After fix: succeeds, temperature stripped, reasoning_tokens=64 captured in usage

### Reasoning token capture
OpenAI reasoning models report `reasoning_tokens` in `usage.completion_tokens_details`. AbstractCore already captures this correctly in the GenerateResponse usage dict. The actual reasoning text is NOT exposed via Chat Completions API (only via Responses API with reasoning summaries).

### Changes made
- **model_capabilities.json**: added `thinking_support: true` to o1, o1-mini, o3, o3-mini, o4-mini, DeepSeek-R1, all GPT-5 family, Claude 4/4.1/4.5/4.6 models, Claude Haiku 4.5. Added `unsupported_parameters` to o1, o1-mini, o3, o3-mini, o4-mini, gpt-5, gpt-5-mini, gpt-5-nano, gpt-5-pro, gpt-5-codex (all empirically verified to reject temperature). Did NOT add `unsupported_parameters` to gpt-5.1 and gpt-5.2 (empirically verified to accept temperature). Added `token_param_name: "max_completion_tokens"` to all models that reject `max_tokens`. Added new model entries: GPT-5.1, GPT-5.2, GPT-5.2-pro, GPT-5.2-codex, GPT-5.1-codex, GPT-5-codex, GPT-5-nano, o4-mini, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, Claude Opus 4.6, Claude Sonnet 4.6.
- **base.py**: added `_is_reasoning_model()`, `_is_parameter_supported()`, `_get_token_param_name()` to `BaseProvider`.
- **openai_provider.py**: deleted local `_is_reasoning_model()` and `_uses_max_completion_tokens()`. Rewrote parameter filtering in sync and async generate methods to use `_is_parameter_supported()` loop. Warning now only fires when a caller explicitly passes a parameter that gets dropped (not on defaults).
- **portkey_provider.py**: deleted local `_is_reasoning_model()` and `_uses_max_completion_tokens()`. Rewrote parameter filtering to use `_is_parameter_supported()` and `_get_token_param_name()`.
- **assets/README.md**: documented new `unsupported_parameters` and `token_param_name` fields.
- **test_model_capabilities_schema.py**: added validation for new optional fields.
- **test_portkey_provider_unit.py**: updated reasoning model test to use `o3-mini` (has `unsupported_parameters`) instead of `gpt-5-mini`.
- **CHANGELOG.md**: added v2.13.0 entry.

### Tests
Schema tests pass (6/6). Portkey unit tests pass (18/18). In-process capability validation verified for all 9 key models. Live end-to-end test verified for gpt-5-mini (parameter stripping + reasoning capture) and gpt-5.2 (temperature pass-through).
