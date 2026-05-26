# 131 — Prompt Cache Cross-Package Capability Follow-Up

**Status**: Completed  
**Date**: 2026-03-23  
**Priority**: Top  
**Components**: abstractcore, abstractruntime, abstractgateway, docs

## Summary

Follow through on the new prompt-cache capability contract so it is exposed consistently across package boundaries, not only inside `abstractcore.providers.base`.

This item improves:

- `abstractgateway` prompt-cache control-plane responses
- `abstractruntime` access to prompt-cache capability data in local and remote modes
- package documentation for every repo touched in this follow-up

## Reason

- `abstractcore` now has structured prompt-cache capabilities and errors.
- `abstractgateway` still uses legacy boolean checks and unstructured prompt-cache responses.
- `abstractruntime` has no explicit cross-process prompt-cache capability accessor yet.
- The docs for `abstractcore`, `abstractruntime`, and `abstractgateway` should describe the new contract in package-local terms.

## Scope

### In scope

- Add prompt-cache capability reporting where gateway/runtime callers can consume it.
- Make gateway prompt-cache endpoints mirror the new `abstractcore` capability/error shape.
- Add or tighten tests for gateway/runtime capability reporting.
- Update the documentation set of each package changed in this follow-up.

### Out of scope

- ReAct scratchpad redesign.
- New HuggingFace transformers KV backend work.
- Changing prompt-cache persistence semantics.

## Strategies considered

### Strategy A — Only document the new base-provider contract

Pros:
- Very small change.

Cons:
- Leaves gateway/runtime behavior inconsistent.

Decision:
- Reject.

### Strategy B — Propagate the capability contract across gateway/runtime surfaces

Pros:
- Clean cross-package consistency.
- Higher layers can reason about support in local and remote deployments.
- Minimal architectural risk.

Cons:
- Requires touching multiple repos and tests.

Decision:
- Chosen.

## Acceptance criteria

- Gateway prompt-cache endpoints expose capability-aware responses.
- Runtime has a prompt-cache capability accessor for local and remote LLM clients.
- Docs are updated in each changed package.
- Targeted tests pass for `abstractcore`, `abstractruntime`, and `abstractgateway`.

## Full Report

### What changed

This follow-up pushed the prompt-cache contract one layer higher so it is not only a provider concern inside `abstractcore`.

Implemented in `abstractruntime`:

- `AbstractCoreLLMClient` protocol now exposes a prompt-cache control-plane surface, not only capability inspection:
  - `get_prompt_cache_capabilities(...)`
  - `get_prompt_cache_stats(...)`
  - `prompt_cache_set(...)`
  - `prompt_cache_update(...)`
  - `prompt_cache_fork(...)`
  - `prompt_cache_clear(...)`
  - `prompt_cache_prepare_modules(...)`
- `LocalAbstractCoreLLMClient` now normalizes provider prompt-cache behavior into the same JSON-safe response shape used by the endpoint/server contract.
- `MultiLocalAbstractCoreLLMClient` now routes all of those prompt-cache operations by `(provider, model)`, not only generation calls.
- `RemoteAbstractCoreLLMClient` now proxies the full `/acore/prompt_cache/*` control plane instead of stopping at capability inspection.
- `create_remote_runtime(...)` and `create_hybrid_runtime(...)` now expose `_abstractcore_llm_client` on the runtime, matching local runtime behavior for host-side prompt-cache tooling.

Implemented in `abstractgateway`:

- Gateway prompt-cache routes no longer rely on direct provider-instance access for the core prompt-cache contract.
- Core routes now operate against the runtime LLM client abstraction:
  - `GET /api/gateway/prompt_cache/capabilities`
  - `GET /api/gateway/prompt_cache/stats`
  - `POST /api/gateway/prompt_cache/set`
  - `POST /api/gateway/prompt_cache/update`
  - `POST /api/gateway/prompt_cache/fork`
  - `POST /api/gateway/prompt_cache/clear`
  - `POST /api/gateway/prompt_cache/prepare_modules`
- This means the gateway can consume the same prompt-cache contract in local, remote, and hybrid runtime modes, as long as the runtime LLM client exposes it.
- Provider-specific `save/load` routes remain separate, but their unsupported/unavailable cases now return clearer structured payloads.

Implemented in `abstractcore`:

- Added explicit endpoint coverage for `GET /acore/prompt_cache/capabilities`.
- Updated docs so the provider capability contract and endpoint response contract are documented together.

### Design result

The prompt-cache abstraction is now layered consistently:

1. `abstractcore` providers define capability/error semantics.
2. `abstractruntime` LLM clients expose a stable prompt-cache control plane for hosts.
3. `abstractgateway` consumes that runtime contract instead of reaching through to provider internals for core operations.

That is a materially cleaner architecture than the previous state, where:

- provider capabilities existed in `abstractcore`
- runtime only partially exposed them
- gateway still depended on `get_provider_instance(...)` for prompt-cache control

### Important boundary kept explicit

This follow-up intentionally did **not** flatten provider-specific cache serialization into the unified contract.

- `save/load` are still local/provider-specific.
- In practice that currently means `mlx` and `huggingface` GGUF (`llama.cpp`) gateway workers.
- The unified cross-provider contract covers capability discovery, key management, branching, stats, and module preparation.

That separation is deliberate. The common contract now describes what every host can rely on. Serialization remains an optional extension until more backends can support it honestly.

### Files changed

- `abstractcore/docs/endpoint.md`
- `abstractcore/docs/prompt-caching.md`
- `abstractcore/tests/test_prompt_cache_control_plane.py`
- `abstractruntime/docs/integrations/abstractcore.md`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/factory.py`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`
- `abstractruntime/tests/test_prompt_cache_modules.py`
- `abstractgateway/docs/api.md`
- `abstractgateway/src/abstractgateway/routes/gateway.py`
- `abstractgateway/tests/test_gateway_prompt_cache_endpoints.py`

### Verification

Passed:

- `python -m py_compile abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractruntime/src/abstractruntime/integrations/abstractcore/factory.py abstractgateway/src/abstractgateway/routes/gateway.py`
- `pytest -q abstractruntime/tests/test_prompt_cache_modules.py`
- `pytest -q abstractcore/tests/test_prompt_cache_api.py abstractcore/tests/test_prompt_cache_control_plane.py`
- `PYTHONPATH=/Users/albou/tmp/abstractframework/abstractruntime/src:/Users/albou/tmp/abstractframework/abstractcore:/Users/albou/tmp/abstractframework/abstractgateway/src /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest -q tests/test_gateway_prompt_cache_endpoints.py`
- `/Users/albou/tmp/abstractframework/.venv/bin/python -m pytest -q abstractcode/tests/test_tools_examples_toggle.py abstractcode/tests/test_executor_command.py abstractcode/tests/test_executor_real_logic.py`

### Notes

- The separate ReAct scratchpad investigation remains planned in `130_react_scratchpad_prompt_flow_and_best_practice_review.md`.
- This item did not modify ReAct scratchpad behavior.
