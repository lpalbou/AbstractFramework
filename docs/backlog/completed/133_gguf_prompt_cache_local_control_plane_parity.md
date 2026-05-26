# 133 — GGUF Prompt Cache Local Control Plane Parity

**Status**: Completed  
**Date**: 2026-03-25  
**Priority**: Top  
**Components**: abstractcore, abstractruntime, abstractgateway, docs

## Summary

Upgrade the GGUF prompt-cache implementation in `abstractcore` from keyed cache selection only to the same local prompt-cache control-plane contract already exposed by MLX:

- `set`
- `clear`
- `update`
- `fork`
- `prepare_modules`
- `stats`

The end goal is that higher layers such as `abstractruntime`, `abstractgateway`, `abstractcode`, and future gateway-backed apps can treat GGUF prompt caching as a first-class modular prefix cache rather than a best-effort opaque key swap.

## Reason

- The current GGUF path can select a `LlamaRAMCache` by key, but it does not expose the full append/fork/module semantics needed by the runtime’s modular prompt-cache flow.
- `abstractruntime` already knows how to build `system | tools | history` caches when the provider exposes the local control plane.
- Gateway-backed clients should benefit from the same behavior as local clients without provider-specific logic.
- The checked-out workspace already contains the necessary llama.cpp primitives:
  - `LlamaRAMCache`
  - `save_state()`
  - `load_state()`
  - prefix lookup by token sequence

## Scope

### In scope

- Implement real GGUF prompt-cache backend hooks in `abstractcore.providers.huggingface_provider.HuggingFaceProvider`.
- Ensure GGUF prompt-cache state can represent append-only modular prefixes and forked branches.
- Align the GGUF generation path with the modular prompt-cache contract so cached prefixes match the prompts actually sent to llama.cpp.
- Add focused tests in `abstractcore` and `abstractruntime`.
- Run a local validation against `unsloth/Qwen3.5-2B-GGUF` with a memory budget capped to roughly 4 GiB.
- Update docs in every package changed by this item.

### Out of scope

- ReAct scratchpad redesign.
- New transformers-native KV-cache work.
- Remote persistence of local prompt-cache state across process restarts.

## Strategies considered

### Strategy A — Keep GGUF as keyed-only and document the limitation

Pros:
- Minimal risk.

Cons:
- Fails the parity goal.
- Keeps runtime modular caching unavailable for GGUF.

Decision:
- Reject.

### Strategy B — Fake `update` / `fork` / `prepare_modules` above llama.cpp without provider-level backend hooks

Pros:
- Smaller provider diff.

Cons:
- Pushes backend-specific behavior into higher layers.
- Breaks the abstraction that `abstractruntime` already uses for MLX.
- Harder for gateway and future hosts to reason about.

Decision:
- Reject.

### Strategy C — Implement a GGUF local control plane around llama.cpp cache/state primitives

Pros:
- Preserves the provider-level abstraction already established in `BaseProvider`.
- Lets `abstractruntime` and `abstractgateway` benefit automatically through the existing contract.
- Makes GGUF modular prefix caching explicit, testable, and capability-driven.

Cons:
- Requires careful prompt rendering so cached prefixes match real GGUF request formatting.
- Needs provider-local state wrapper logic, not just raw `LlamaRAMCache`.

Decision:
- Chosen.

## Design intent

### Expected GGUF cache model

Each prompt-cache key should own a backend state object that can answer:

- what cache object is attached to llama.cpp
- what full prompt-token prefix that cache currently represents
- how to clone/fork that state safely
- how to append new prompt modules without recomputing prior modules

### Target higher-level behavior

For GGUF, this item should make the following runtime flow valid and efficient:

```text
prepare_modules(namespace, [system, tools]) -> immutable shared prefix keys
fork(final_prefix_key -> session_key) -> mutable session cache
update(session_key, messages=[new_turn_delta]) -> append-only history growth
generate(prompt_cache_key=session_key) -> llama.cpp reuses the cached prefix
```

## Acceptance criteria

- GGUF reports `mode=local_control_plane` only when the backend hooks are truly implemented in this checkout.
- GGUF supports `prompt_cache_update`, `prompt_cache_fork`, and `prompt_cache_prepare_modules` through real provider hooks.
- `abstractruntime` modular cache preparation no longer skips GGUF as a keyed-only provider.
- Focused tests pass in `abstractcore` and `abstractruntime`.
- A local smoke test with `unsloth/Qwen3.5-2B-GGUF` confirms prefix reuse behavior under the requested memory budget.

## Notes for implementation

- Keep changes compatible with a dirty multi-repo workspace.
- Do not revert unrelated in-flight edits from other agents.
- Prefer exact prompt compatibility over clever abstractions that silently diverge from real llama.cpp request formatting.

## Full Report

### What changed

Primary implementation:

- `abstractcore/abstractcore/providers/huggingface_provider.py`
  - GGUF now implements the same provider-level prompt-cache backend hooks used by the shared control plane:
    - `_prompt_cache_backend_create(...)`
    - `_prompt_cache_backend_clone(...)`
    - `_prompt_cache_backend_append(...)`
    - `_prompt_cache_backend_token_count(...)`
  - The stored GGUF cache value is no longer just a raw `LlamaRAMCache`. It is a provider-owned state object that keeps:
    - the raw llama.cpp cache object
    - rendered prompt text
    - rendered prompt tokens
    - accumulated system parts
    - accumulated message history
    - tool module state
  - GGUF capabilities now report `mode=local_control_plane` only when AbstractCore has an exact cached prompt renderer for the active llama.cpp chat format.
  - Current exact cached renderers:
    - `chatml-function-calling`
    - `llama-3`
  - Other GGUF chat formats remain honest `mode=keyed`.
  - The `chatml-function-calling` cached renderer now mirrors assistant `tool_calls` history instead of silently dropping it.

Shared metadata improvement:

- `abstractcore/abstractcore/providers/base.py`
  - `prompt_cache_update(...)` and `prompt_cache_fork(...)` now refresh/store `token_count` metadata for provider-managed cache state.

Tests:

- `abstractcore/tests/huggingface/test_gguf_prompt_cache_control_plane.py`
  - added GGUF control-plane coverage for:
    - capability reporting
    - `prepare_modules -> fork -> update` reuse
    - `llama-3` capability parity
    - assistant tool-call history rendering
    - attachment of the underlying raw cache object during generation

Docs updated:

- `abstractcore/docs/prompt-caching.md`
- `abstractruntime/docs/integrations/abstractcore.md`
- `abstractgateway/docs/api.md`
- `abstractcode/README.md`
- `abstractcode/docs/api.md`
- `abstractcode/docs/architecture.md`
- `abstractcode/docs/faq.md`
- `abstractcode/docs/getting-started.md`

### Design result

GGUF now fits the same abstraction layers as MLX:

1. AbstractCore provider advertises machine-readable prompt-cache capabilities.
2. AbstractRuntime can use `prepare_modules / fork / update` automatically when GGUF reports `local_control_plane`.
3. AbstractGateway and AbstractCode can consume the same contract without inventing GGUF-specific orchestration.

The important boundary is explicit:

- GGUF is not treated as universally MLX-equivalent.
- GGUF is treated as `local_control_plane` only when the checked-out code can render the llama.cpp prompt exactly enough for modular cache reuse to stay correct.
- Otherwise GGUF stays `keyed`.

That is cleaner than pretending all GGUF chat formats already have safe modular prefix semantics.

### Real-model investigation

Requested model:

- `unsloth/Qwen3.5-2B-GGUF`

Result:

- The file exists locally, but the installed llama.cpp / `llama-cpp-python` build cannot load it in this environment.
- Direct load fails with:
  - `ValueError: Failed to load model from file: ...Qwen3.5-2B-Q4_K_M.gguf`
- String inspection of the GGUF metadata shows:
  - `general.architecture = qwen35`

So the blocker is not “GGUF prompt caching is missing”; it is that this checkout’s local llama.cpp build cannot open that newer `qwen35` architecture.

Fallback requested by the user:

- downloaded `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- exact file tested:
  - `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`

Fallback smoke-test findings:

- Load-only probe:
  - `rss_after_load_gib = 2.891`
  - `mode = local_control_plane`
  - `exact_prompt_renderer = chatml-function-calling`
- Cache-control-plane probe with a lean tool schema:
  - `prepare1_s = 8.813`
  - `fork_ok = true`
  - `update_ok = true`
  - `rss_after_update_gib = 3.303`
- Constrained end-to-end generation with a cached system prefix:
  - `rss_after_load_gib = 2.885`
  - `generate_s = 0.856`
  - `rss_after_generate_gib = 2.941`

Important limit found during testing:

- A tool-heavier `system + tools + prompt` generation run in a 256-token context overflowed the context window and pushed RSS to `4.14 GiB`.
- So the final smoke validation was split into:
  - under-budget control-plane validation with a lean tool schema
  - under-budget cached generation validation with a system-only prefix

That kept the real fallback validation within the requested 4 GiB budget for the successful path.

### Files changed

- `abstractcore/abstractcore/providers/base.py`
- `abstractcore/abstractcore/providers/huggingface_provider.py`
- `abstractcore/tests/huggingface/test_gguf_prompt_cache_control_plane.py`
- `abstractcore/docs/prompt-caching.md`
- `abstractruntime/docs/integrations/abstractcore.md`
- `abstractgateway/docs/api.md`
- `abstractcode/README.md`
- `abstractcode/docs/api.md`
- `abstractcode/docs/architecture.md`
- `abstractcode/docs/faq.md`
- `abstractcode/docs/getting-started.md`

### Verification

Passed:

- `python -m py_compile abstractcore/abstractcore/providers/huggingface_provider.py`
- `./.venv/bin/python -m pytest -q abstractcore/tests/huggingface/test_gguf_prompt_cache_control_plane.py`
- `./.venv/bin/python -m pytest -q abstractcore/tests/test_prompt_cache_api.py abstractcore/tests/test_prompt_cache_control_plane.py`
- `./.venv/bin/python -m pytest -q abstractruntime/tests/test_prompt_cache_modules.py`
- `PYTHONPATH=/Users/albou/tmp/abstractframework/abstractruntime/src:/Users/albou/tmp/abstractframework/abstractcore:/Users/albou/tmp/abstractframework/abstractgateway/src /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest -q abstractgateway/tests/test_gateway_prompt_cache_endpoints.py`

Real-model checks run:

- direct load failure check for local `unsloth/Qwen3.5-2B-GGUF`
- remote file listing for `unsloth/Qwen3-4B-Instruct-2507-GGUF`
- download of `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`
- load-only fallback probe
- lean tool-schema control-plane probe
- constrained cached-generation probe

### Notes

- No unrelated pending changes were reverted or discarded.
- This item did not attempt to solve the separate ReAct scratchpad design problem.
