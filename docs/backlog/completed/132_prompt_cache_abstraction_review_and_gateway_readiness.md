# 132 — Prompt Cache Abstraction Review And Gateway Readiness

**Status**: Completed  
**Date**: 2026-03-25  
**Priority**: Top  
**Components**: abstractcore, abstractruntime, abstractgateway, abstractcode, docs

## Summary

Review the current prompt-cache abstraction after the initial capability-contract work and cross-package follow-up, then harden anything that still leaks provider-specific assumptions or blocks upper-level apps using the gateway from benefiting cleanly from prompt caching.

## Reason

- The current abstraction must stay clean and stable for both `abstractcode` CLI and gateway-backed apps.
- There is active prompt-cache work on other branches, especially around GGUF, so the implementation must be reviewed against the current code rather than frozen assumptions.
- Gateway-backed apps need a clear operator/control surface for prompt caching, not just in-process provider APIs.
- The current implementation should be re-checked for simplicity, robustness, efficiency, and abstraction cleanliness.

## Scope

### In scope

- Audit current prompt-cache capabilities and implementation across:
  - `abstractcore`
  - `abstractruntime`
  - `abstractgateway`
  - `abstractcode`
- Tighten any abstraction leaks or inconsistent behavior discovered during the audit.
- Update docs in each package changed by this pass.

### Out of scope

- ReAct scratchpad redesign.
- Reverting or rewriting unrelated in-flight work from other agents.
- Inventing prompt-cache backend support that does not actually exist in the checked-out code.

## Strategies considered

### Strategy A — Only explain the current state

Pros:
- Minimal risk.

Cons:
- Leaves any abstraction weaknesses in place.

Decision:
- Reject.

### Strategy B — Audit the current state, then make only targeted hardening changes

Pros:
- Keeps the prompt-cache contract clean without broad churn.
- Compatible with a dirty multi-repo workspace.
- Lets the code reflect the checked-out reality, including any GGUF changes that may already exist.

Cons:
- Requires careful reading before editing.

Decision:
- Chosen.

## Acceptance criteria

- The prompt-cache abstraction is reviewed against the current code, not stale assumptions.
- Any remaining abstraction leaks that matter for CLI/gateway use are tightened.
- Changed-package docs reflect the final behavior.
- Focused tests pass.

## Full Report

### Clarification of the earlier MLX / HF / GGUF statement

The earlier statement was about the **checked-out code in this workspace at the time of inspection**, not a claim about every branch in your project history.

What the checked-out tree shows today:

- `MLXProvider` implements real local prompt-cache backend hooks:
  - `_prompt_cache_backend_create(...)`
  - `_prompt_cache_backend_clone(...)`
  - `_prompt_cache_backend_append(...)`
  - `_prompt_cache_backend_token_count(...)`
- `HuggingFaceProvider` in this tree still exposes GGUF prompt caching primarily as:
  - per-key `LlamaRAMCache` allocation/selection via `prompt_cache_set(...)`
  - best-effort `set_cache(...)` activation on the shared llama instance
  - no `_prompt_cache_backend_clone(...)`
  - no `_prompt_cache_backend_append(...)`
  - no `_prompt_cache_backend_create(...)` override

That is why the capability contract classified the checked-out GGUF implementation as `mode=keyed` rather than `mode=local_control_plane`.

So the important distinction is:

- if another branch already adds GGUF backend hooks, the capability contract is *supposed* to promote automatically
- if the current branch does not contain those hooks, the abstraction should not pretend that module/fork/update support exists

In other words: the abstraction must reflect the code actually present, not the intended end state.

### Review findings

The main remaining abstraction leaks were not in `abstractcore.providers.base` anymore. They were higher up:

1. `abstractcode` CLI was still querying prompt-cache support by tunneling through `runtime._abstractcore_llm_client.get_provider_instance(...)` and then inspecting the provider directly.
2. `RemoteAbstractCoreLLMClient` prompt-cache control-plane methods assumed the remote target directly exposed `/acore/prompt_cache/*`, which is true for `abstractcore-endpoint` but incomplete for the AbstractCore server proxy unless upstream `base_url` / `api_key` are forwarded.

These two issues mattered because they made the abstraction less clean than it looked:

- the CLI still depended on provider internals
- remote prompt-cache control-plane access was more endpoint-specific than the docs implied

### What changed

#### `abstractcode`

Prompt-cache capability lookup is now centralized in `ReactShell._prompt_cache_capabilities()`.

This helper:

- prefers the runtime-level prompt-cache contract:
  - `runtime._abstractcore_llm_client.get_prompt_cache_capabilities(...)`
- falls back to provider-instance inspection only for older runtimes that do not expose the newer contract yet

This removed duplicated provider-introspection logic from:

- `/cache` status display
- session runtime prompt-cache auto-enablement during `_sync_tool_prompt_settings_to_run(...)`

Result:

- the CLI now uses the same abstraction layer as the gateway/runtime work
- local and future remote/gateway-backed runtime integrations are cleaner

#### `abstractruntime`

`RemoteAbstractCoreLLMClient` prompt-cache control-plane methods now support forwarding upstream proxy context:

- `base_url`
- `api_key`

This matters when the remote target is the AbstractCore server proxy rather than a direct endpoint:

- GET prompt-cache calls now append proxy query params when supplied
- POST prompt-cache calls now include proxy fields in the JSON payload when supplied

Result:

- the runtime prompt-cache control plane is more honest and more generally usable
- remote prompt-cache management is no longer silently endpoint-only in practice

#### `abstractcode/web`

Added gateway prompt-cache capability access to the web client:

- `GatewayClient.prompt_cache_capabilities(provider, model)`

Also updated the web `/cache list` flow to display:

- capability mode
- supported local prompt-cache ops when available

This gives upper-level gateway consumers a cleaner prompt-cache surface instead of inferring support only from stats/save/load behavior.

### Documentation updates

Updated docs to match the cleaned abstraction:

- `abstractcode/README.md`
- `abstractcode/docs/getting-started.md`
- `abstractcode/docs/faq.md`
- `abstractcode/docs/api.md`
- `abstractcode/docs/architecture.md`
- `abstractruntime/docs/integrations/abstractcore.md`

The docs now describe:

- runtime-level prompt-cache capability discovery
- the distinction between `keyed` and `local_control_plane`
- the remote proxy-context nuance for prompt-cache control-plane calls

### Files changed

- `abstractcode/abstractcode/react_shell.py`
- `abstractcode/tests/test_prompt_cache_capabilities.py`
- `abstractcode/README.md`
- `abstractcode/docs/getting-started.md`
- `abstractcode/docs/faq.md`
- `abstractcode/docs/api.md`
- `abstractcode/docs/architecture.md`
- `abstractcode/web/src/lib/gateway_client.ts`
- `abstractcode/web/src/ui/app.tsx`
- `abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py`
- `abstractruntime/tests/test_remote_llm_client.py`
- `abstractruntime/docs/integrations/abstractcore.md`

### Verification

Passed:

- `python -m py_compile abstractruntime/src/abstractruntime/integrations/abstractcore/llm_client.py abstractcode/abstractcode/react_shell.py abstractruntime/tests/test_remote_llm_client.py abstractcode/tests/test_prompt_cache_capabilities.py`
- `pytest -q abstractruntime/tests/test_remote_llm_client.py abstractruntime/tests/test_prompt_cache_modules.py`
- `/Users/albou/tmp/abstractframework/.venv/bin/python -m pytest -q abstractcode/tests/test_prompt_cache_capabilities.py abstractcode/tests/test_tools_examples_toggle.py abstractcode/tests/test_executor_command.py abstractcode/tests/test_executor_real_logic.py`
- `pytest -q abstractcore/tests/test_prompt_cache_api.py abstractcore/tests/test_prompt_cache_control_plane.py abstractcore/tests/test_server_prompt_cache_control_plane_proxy.py`
- `PYTHONPATH=/Users/albou/tmp/abstractframework/abstractruntime/src:/Users/albou/tmp/abstractframework/abstractcore:/Users/albou/tmp/abstractframework/abstractgateway/src /Users/albou/tmp/abstractframework/.venv/bin/python -m pytest -q tests/test_gateway_prompt_cache_endpoints.py`

Not run in this pass:

- frontend build/typecheck for `abstractcode/web` (no package-local build command was assumed in this dirty multi-repo workspace)

### Notes

- No unrelated pending changes were reverted or discarded.
- This pass did not attempt to invent or fake GGUF/HF backend parity beyond what the checked-out code actually provides.
- If a later branch adds GGUF backend clone/append/create hooks, the capability abstraction should largely absorb that automatically rather than needing another abstraction redesign.
