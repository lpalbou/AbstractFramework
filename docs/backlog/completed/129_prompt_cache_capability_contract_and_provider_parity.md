# 129 — Prompt Cache Capability Contract And Provider Parity

**Status**: Completed  
**Date**: 2026-03-23  
**Priority**: Top  
**Components**: abstractcore, abstractruntime, abstractcode

## Summary

Replace the current boolean, best-effort prompt-cache surface with a single provider capability contract that:

- exposes the same prompt-cache API shape across providers
- reports exactly which prompt-cache operations are supported
- raises clear, structured, catchable errors for unsupported operations
- lets higher layers distinguish:
  - no prompt cache support
  - key-passthrough/server-managed prompt caching
  - local prompt-cache control plane with module/fork/update support

Primary target providers for parity in this phase:

- `mlx`
- `huggingface` text backends
- `huggingface` GGUF backends

## Reason

- The current API is too implicit. `supports_prompt_cache()` is only a boolean, so callers cannot tell whether a provider supports:
  - only `prompt_cache_key` forwarding
  - local key selection
  - append/fork/module preparation
- Unsupported operations currently tend to return `False` or `{supported: false}` rather than throwing a structured error that higher layers can catch and reason about.
- The runtime and CLI need one stable abstraction, not provider-specific branching logic.
- Prompt caching is a performance-critical primitive for agent loops and long multi-turn sessions, so capability ambiguity is a correctness problem, not just a UX problem.

## Current state

- `BaseProvider` exposes:
  - `supports_prompt_cache()`
  - `prompt_cache_set()`
  - `prompt_cache_update()`
  - `prompt_cache_fork()`
  - `prompt_cache_prepare_modules()`
  - `prompt_cache_clear()`
  - `get_prompt_cache_stats()`
- In practice:
  - MLX has local backend create/clone/append hooks and supports module/fork/update semantics.
  - OpenAI-compatible providers mainly forward `prompt_cache_key`.
  - HuggingFace GGUF only selects a per-key llama cache object today.
  - Higher layers infer too much from a single boolean.

## Architecture goals

1. One provider-facing prompt-cache contract.
2. Explicit per-operation capability reporting.
3. Structured prompt-cache exceptions with machine-readable error codes.
4. Higher layers can ask:
   - does this provider support prompt caching at all?
   - does it support local control-plane operations?
   - does it support module preparation and branching?
5. No silent fallbacks for unsupported prompt-cache operations.

## Strategies considered

### Strategy A — Keep the current boolean API and document provider differences

Pros:
- Minimal code churn.

Cons:
- Does not solve the main problem.
- Higher layers still cannot safely decide what operations are valid.
- Unsupported operations remain ambiguous.

Decision:
- Reject.

### Strategy B — Add a capability object plus structured prompt-cache exceptions

Pros:
- Clean, explicit, composable.
- Works for local and remote providers.
- Lets `abstractruntime` and `abstractcode` branch on capability, not provider name.
- Compatible with existing method names.

Cons:
- Requires touching base provider, providers, runtime, and endpoint control plane.
- Some legacy tests need to be tightened around capability/error semantics.

Decision:
- Chosen.

### Strategy C — Split prompt caching into separate local and remote APIs

Pros:
- Makes local-vs-remote differences explicit.

Cons:
- Fragments the abstraction.
- Pushes provider branching into every caller.
- Makes higher app code more complex, not less.

Decision:
- Reject.

## Proposed design

### 1. Capability object

Add a prompt-cache capability profile in `providers/base.py`, with fields along these lines:

- `supported`
- `mode`
  - `none`
  - `server_managed`
  - `local_control_plane`
- `supports_default_key`
- `supports_stats`
- `supports_set`
- `supports_clear`
- `supports_update`
- `supports_fork`
- `supports_prepare_modules`
- `supports_ttl`
- `notes`

The exact field list can be adjusted during implementation, but the contract must let higher layers reason by operation instead of by provider name.

### 2. Structured errors

Add a prompt-cache exception hierarchy in `providers/base.py`, for example:

- `PromptCacheError`
- `PromptCacheUnsupportedError`
- `PromptCacheOperationError`

Each error should carry:

- `operation`
- `provider`
- `model`
- `code`
- `message`
- `capabilities`

### 3. Provider contract

Public provider methods keep the same names, but unsupported operations must raise structured prompt-cache errors instead of silently returning `False`.

Methods:

- `prompt_cache_set(...)`
- `prompt_cache_update(...)`
- `prompt_cache_fork(...)`
- `prompt_cache_prepare_modules(...)`
- `prompt_cache_clear(...)`
- `get_prompt_cache_stats(...)`

### 4. Higher-layer behavior

- `abstractruntime` uses the capability profile to decide whether module preparation is available.
- `abstractendpoint` and any other control plane catch prompt-cache errors and return machine-readable failure payloads.
- `abstractcode` can query the capability profile and decide whether prompt-cache auto mode is meaningful for the selected provider/model.

## Acceptance criteria

- All prompt-cache operations are discoverable via one provider capability API.
- Unsupported prompt-cache operations raise clear, catchable errors.
- Existing prompt-cache method names remain stable.
- MLX advertises full local control-plane capabilities.
- GGUF and HuggingFace expose the same top-level prompt-cache contract, even if individual operations remain capability-gated.
- Endpoint control-plane responses surface structured prompt-cache failure details.
- Runtime no longer infers full module support from a single boolean.

## Tests

Planned verification:

- Provider-base unit tests for capability profiles and structured errors.
- Control-plane endpoint tests for structured unsupported-operation responses.
- Runtime tests for capability-aware module preparation behavior.
- Existing prompt-cache API/control-plane tests must still pass.

## Notes

- This item is the implementation driver for the primary task.
- A separate research-only backlog item documents the ReAct scratchpad architecture and best-practice comparison. That item is intentionally not implemented here.

## Full Report

### What changed

Implemented a unified prompt-cache contract centered in `abstractcore.providers.base`:

- added `PromptCacheCapabilities`
- added structured prompt-cache exceptions:
  - `PromptCacheError`
  - `PromptCacheUnsupportedError`
  - `PromptCacheOperationError`
- added provider capability introspection:
  - `get_prompt_cache_capabilities()`
  - `prompt_cache_supports_operation(...)`
- made prompt-cache public methods capability-aware:
  - `prompt_cache_set(...)`
  - `prompt_cache_update(...)`
  - `prompt_cache_fork(...)`
  - `prompt_cache_prepare_modules(...)`
  - `prompt_cache_clear(...)`
  - `get_prompt_cache_stats(...)`

Unsupported prompt-cache operations now raise structured, catchable errors instead of silently returning ambiguous `False`/`supported=false` shapes from the provider layer.

### Higher-layer integration

Updated `abstractcore.endpoint.app` so `/acore/prompt_cache/*` responses now expose:

- `operation`
- `code`
- `capabilities`
- a clearer `error` message

This means higher apps can distinguish:

- prompt caching unsupported
- prompt caching supported but key-only
- prompt caching supported with local control-plane operations

Updated `abstractruntime` prompt-cache preparation so it checks provider capability before attempting module preparation. Key-only providers now skip local module-prep instead of relying on exceptions for control flow.

Updated `abstractcode` cache status handling so it reads the provider capability profile and surfaces:

- provider prompt-cache mode
- whether local update/fork/module operations are available

### Effective provider contract after this change

- MLX:
  - reports `local_control_plane`
  - supports `set`, `clear`, `update`, `fork`, `prepare_modules`, `stats`
- HuggingFace GGUF:
  - reports `keyed`
  - supports `set`, `clear`, `stats`
  - does not falsely claim module/fork/update support
- HuggingFace transformers:
  - reports unsupported unless/until a real prompt-cache backend is implemented

This does not yet create true backend parity between MLX and HuggingFace text backends, but it does establish one stable abstraction and explicit machine-readable support boundaries. That was the necessary first step so higher layers can stop guessing.

### Files changed

- `abstractcore/abstractcore/providers/base.py`
- `abstractcore/abstractcore/endpoint/app.py`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`
- `abstractcode/abstractcode/react_shell.py`
- `abstractcore/tests/test_prompt_cache_api.py`
- `abstractcore/tests/test_prompt_cache_control_plane.py`
- `abstractruntime/tests/test_prompt_cache_modules.py`
- `docs/backlog/planned/130_react_scratchpad_prompt_flow_and_best_practice_review.md`

### Tests

Passed:

- `pytest -q abstractcore/tests/test_prompt_cache_api.py abstractcore/tests/test_prompt_cache_control_plane.py abstractruntime/tests/test_prompt_cache_modules.py`
- `./.venv/bin/python -m pytest -q abstractcode/tests/test_tools_examples_toggle.py abstractcode/tests/test_executor_command.py abstractcode/tests/test_executor_real_logic.py`
- `python -m py_compile abstractcore/abstractcore/providers/base.py abstractcore/abstractcore/endpoint/app.py abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractcode/abstractcode/react_shell.py`

### Follow-up work

Still open for a later implementation item:

- true local prompt-cache backend parity for HuggingFace transformers
- potential GGUF extension from `keyed` mode to full `local_control_plane`
- ReAct scratchpad lane redesign so changing cycle state does not live inside the stable system-prefix lane
