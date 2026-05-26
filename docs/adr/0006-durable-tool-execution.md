# ADR-0006: Durable Tool Execution (Toolsets & Executors)

## Status
Accepted (2025-12-15)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-15


## Context

AbstractRuntime’s core value proposition is **durable execution** (pause → persist → resume). The MVP persistence backends serialize:
- `RunState` checkpoints as JSON (e.g. `JsonFileRunStore` uses `json.dump(asdict(run))`)
- Ledger records as JSON/JSONL

Therefore:
- `RunState.vars` must be JSON-serializable
- `Effect.payload` and recorded results must be JSON-serializable

However, current agent/tool execution patterns can violate this:
- Tool callables are stored in `RunState.vars["_tools"]` in AbstractAgent (not JSON-serializable)
- Tool execution may be driven by runtime handler reading callables from `RunState.vars` or effect payloads
- AbstractCore’s `execute_tools=True` relies on a process-global registry (hidden global state)

This produces a fundamental failure mode:
- Runs that use tools cannot reliably persist/resume across process restarts with JSON-backed stores.

## Decision

### 1) Split “tool spec” from “tool implementation”

Define and treat as distinct concepts:

- **ToolSpec** (serializable): `{name, description, parameters, tags?, when_to_use?, examples?, version?}`
- **ToolImpl** (in-process callable): the Python function (or other executable implementation)

Persist ToolSpec (and optional `toolset_id`) in run state and ledger for auditability and reproducibility, but never persist callables.

### 2) Introduce a host-configured ToolExecutor

Tool execution happens via a `ToolExecutor` held by the host/runtime/session, not via data stored inside the durable run state.

```
RunState.vars (JSON)            Runtime (in-process)            Tools (in-process)
--------------------           ---------------------           -------------------
tool_specs: [ToolSpec...]  -->  ToolExecutor.execute()  -->  {name -> callable}
toolset_id: "ts_..."            (enforces allowlist)           (may be rebuilt on restart)
```

Execution modes become explicit:
- **executed**: ToolExecutor executes locally
- **passthrough**: ToolExecutor returns tool calls and runtime enters WAITING until host resumes with results
- **remote worker** (future): ToolExecutor submits job and runtime waits on `WaitReason.JOB`

### 3) Deprecate durability-breaking pathways

Deprecate and eventually remove:
- Storing tool callables in `RunState.vars` (e.g. `vars["_tools"] = [...]`)
- Passing tool callables in effect payloads
- Relying on AbstractCore process-global registries as the primary execution mechanism

Keep legacy global registries only as transitional adapters where necessary.

## Consequences

### Positive
- Durable tool-enabled workflows become real (JSON-backed resume works)
- Tool allowlists become enforceable per run/toolset (security boundary)
- Multi-tenant correctness improves (no hidden global registry coupling)
- Ledger records become clean evidence for provenance (“who did that?”)

### Negative
- Requires explicit wiring (host must provide ToolExecutor when resuming a run)
- Migration work for any code using `run.vars["_tools"]` / `payload.tools` patterns
- Slightly higher conceptual surface area (ToolSpec vs ToolImpl)

### Neutral
- Does not dictate *how* ToolSpecs are generated (can remain `@tool` + schema inference)
- Does not force a single packaging decision for shared primitives (can be implemented via adapters)

## Packages Affected
- **AbstractRuntime**: Tool effect handler should rely on ToolExecutor (not run.vars callables)
- **AbstractAgent**: Agents should persist tool specs/toolset IDs only; implementations wired via ToolExecutor
- **AbstractCore**: direct tool execution mode should prefer explicit tool mapping over global registry

## Related
- [ADR-0002: Effect System Design](0002-effect-system-design.md)
- [ADR-0003: Tool System Architecture](0003-tool-system-architecture.md)
- [ADR-0004: Observability Strategy](0004-observability-strategy.md) (provenance implications)
- Backlog: `docs/backlog/completed/015-framework-durable-toolsets.md`
