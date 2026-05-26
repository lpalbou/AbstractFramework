# ADR-0014: Runtime-Authoritative Timeouts (LLM + Tool Execution)

## Status
Proposed (2025-12-31) — implemented, pending broader review.

## Dates
- Proposed: 2025-12-31
- Accepted: (TBD)


## Context
We run long-lived, durable workflows where individual steps can take minutes to hours:
- Local LLM inference can be slow for large contexts (prefill + generation).
- Tool calls can block (filesystem, subprocesses, network, user code).

We observed failures where:
- The orchestrator aborted LLM requests after a short client timeout (e.g. 300s), causing “client disconnected” logs in local servers.
- Timeout behavior differed depending on topology (local providers vs remote AbstractCore server), leading to non-reproducible workflow behavior.
- Tool execution had no runtime-enforced timeout, so a single tool could stall a run indefinitely.

This surfaced a layering question: **who owns execution policy (timeouts)**?
- `abstractcore` provides capabilities (LLM providers, tool primitives, server endpoints).
- `abstractruntime` orchestrates execution (durability, effects, pause/resume/cancel, retries).

## Decision
### 1) Authority and contract
`abstractruntime` is the **source of authority** for execution policy timeouts:
- **LLM execution timeout**: how long a runtime-managed `LLM_CALL` is allowed to run.
- **Tool execution timeout**: how long a runtime-managed `TOOL_CALLS` tool call is allowed to run.

`abstractcore` must **follow orchestrator parameters** when used under orchestration:
- In **local mode**, `abstractruntime` passes `timeout` when constructing AbstractCore providers.
- In **remote/hybrid mode**, `abstractruntime` sends a per-request `timeout_s` to the AbstractCore server, and the server applies it when creating the provider for that request.

`abstractcore` global config remains valid for **direct usage** (when no orchestrator is present), but it is not the authority for workflow execution policy.

### 2) Defaults (per-effect, not per-workflow)
Default **per-effect** timeouts for orchestrated execution are:
- **LLM timeout** (one `LLM_CALL`): 7200s (2 hours)
- **Tool timeout** (one tool call inside `TOOL_CALLS`): 7200s (2 hours)

These defaults do **not** impose any maximum duration on a workflow/run. Workflows can run for hours/days or continuously; only individual operations are supervised by these timeouts.

The default is intentionally uniform (no per-provider/model heuristics). Hosts may override these by configuring `abstractruntime` explicitly.

### 3) Tool-timeout semantics (important limitation)
For arbitrary Python callables, timeouts are **best-effort**:
- The runtime can stop *waiting* after the timeout and mark the tool as failed.
- The runtime cannot forcibly terminate arbitrary in-process code without process isolation.

Therefore:
- Tool timeout is implemented as a **supervision boundary** (the run progresses with a failure result),
  not a guaranteed kill-switch for untrusted code.

## Consequences
### Positive
- **Reproducible workflow behavior**: timeout policy is owned and configured by the orchestrator.
- **Topology parity**: local vs remote/hybrid behave consistently because timeouts are propagated end-to-end.
- **Operational clarity**: errors can report the effective timeout, and “client disconnected” logs become diagnosable.
- **Durability-compatible**: timeouts are enforced without breaking the effect/ledger contracts.

### Negative
- **API surface increase**: AbstractCore server needs to accept an orchestrator timeout field (`timeout_s`).
- **Best-effort tool cancellation**: in-process tools may continue running after the runtime times out.

### Neutral
- Direct `abstractcore` usage can still rely on AbstractCore config defaults.
- Hosts can choose to expose configuration UX for these timeouts, but the policy lives in `abstractruntime`.

## Packages Affected
- AbstractRuntime (core orchestrator + AbstractCore integration)
- AbstractCore (server request model and provider construction)
- AbstractFlow (host wiring; inherits runtime defaults unless it overrides)

## Related
- ADR-0001: Layered Architecture (`abstractruntime` orchestrates, `abstractcore` provides capabilities)
- ADR-0006: Durable Tool Execution (tool execution via host/runtime executors)
- ADR-0013: Durable Run Controls (pause/resume/cancel are runtime-level control-plane)
- Code:
  - `abstractruntime.integrations.abstractcore.constants`
  - `abstractruntime.integrations.abstractcore.factory`
  - `abstractruntime.integrations.abstractcore.llm_client`
  - `abstractruntime.integrations.abstractcore.tool_executor`
  - `abstractcore.server.app` (`ChatCompletionRequest.timeout_s`)


