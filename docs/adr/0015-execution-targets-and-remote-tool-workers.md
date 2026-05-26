# ADR-0015: Execution Targets + Remote Tool Workers (MCP-first)

## Status
Proposed (2026-01-02)

## Dates
- Proposed: 2026-01-02
- Accepted: (TBD)


## Context
We want deployment topologies where:
- the **durable orchestrator** runs on a server (AbstractRuntime + AbstractAgent),
- some **tools execute remotely** (phone-local vision, server-privileged memory writes, sandboxed code runners),
- and (optionally) LLM calls can be routed to different **provider endpoints / GPU boxes**.

The framework already has the correct durability boundary (ADR-0002, ADR-0006):
- workflows emit `EffectType.TOOL_CALLS` (and other effects),
- tool execution is provided by a host-configured `ToolExecutor`,
- waits/resumes are durable (`WaitState`), and results are injected via `Runtime.resume(...)`.

What’s missing is a consistent way to express and discover **where execution should happen**, and a standard protocol for **remote tool execution** that avoids bespoke transports.

Constraints:
- run state and ledger payloads must remain **JSON-safe** (durable storage backends).
- remote tools must be treated as **at-least-once** activities (idempotency required).
- the system needs a clear security boundary (authz, allowlists, provenance).

## Decision

### 1) Introduce “ExecutionTarget” as the placement unit
Define a first-class, serializable `ExecutionTarget` concept (discovered via a registry):
- `target_id`, `label`
- tool execution endpoint(s) (primary: MCP server)
- optional LLM routing data (provider/model defaults and/or provider `base_url`)
- capabilities/labels (`gpu`, `vision`, `privileged`, …)

This target id is used by hosts (AbstractFlow backend, AbstractCode, future agent-host servers) to route effects to the correct machine.

Backlog: `docs/backlog/planned/174-framework-execution-target-discovery.md`

### 2) Remote tool workers are ToolExecutors; use `WaitReason.JOB`
Remote tool execution is implemented as a `ToolExecutor` implementation owned by AbstractRuntime:
- if executed locally: `mode="executed"`
- if delegated remotely: return a non-executed mode with a stable `wait_key` (job id)

The runtime enters a durable wait using:
- `WaitReason.JOB` for delegated remote tool work (job completion semantics),
- `WaitReason.EVENT` for passthrough/approval (human/external event resume).

Backlog: `docs/backlog/planned/012-abstractruntime-remote-tool-worker.md`

### 3) Adopt MCP as the default tool-worker protocol (MCP-first)
Use **MCP (Model Context Protocol)** as the preferred tool server protocol to avoid inventing and maintaining a bespoke worker API:
- discovery: `tools/list`
- execution: `tools/call`
- primary transport target: Streamable HTTP

AbstractCore provides MCP schema discovery + normalization to tool specs (tool *schemas*).
AbstractRuntime provides MCP execution via a runtime-side `ToolExecutor` (tool *execution*).

Backlog: `docs/backlog/planned/206-abstractcore-mcp-integration.md`

### 4) Idempotency + provenance are mandatory for delegated tools
Remote tool calls must be designed as durable activities:
- use `call_id` as an **idempotency key** for remote execution (dedupe on worker side),
- record provenance on results (which target executed it, version, timing),
- route large payloads via `ArtifactStore` references (not inline).

## Consequences

### Positive
- Clear placement model across Flow/Code/Runtime (“where does this run?”).
- Remote tool execution becomes a durable first-class capability (restart-safe).
- Avoids bespoke protocols by aligning with MCP ecosystem direction.
- Better observability and auditability via provenance.

### Negative
- Requires introducing target discovery/registry and wiring it into hosts.
- Requires building an MCP executor + worker deployment story (operational work).
- Adds new “placement” configuration surface area in AbstractFlow and hosts.

### Neutral
- Does not mandate a specific scheduler policy beyond “pick by id” (advanced scheduling can be layered later).
- Does not require multi-orchestrator migration (explicitly avoided).

## Packages Affected
- **AbstractRuntime**: remote ToolExecutor implementations; TOOL_CALLS handler wait semantics; polling/resume integration.
- **AbstractCore**: MCP tool schema discovery/normalization (tool specs).
- **AbstractFlow**: per-node `execution_target_id` and backend routing.
- **AbstractCode**: selecting targets and attaching/detaching to remote runs (future).

## Related
- ADR-0002: `docs/adr/0002-effect-system-design.md`
- ADR-0003: `docs/adr/0003-tool-system-architecture.md`
- ADR-0006: `docs/adr/0006-durable-tool-execution.md`
- Backlog:
  - `docs/backlog/planned/012-abstractruntime-remote-tool-worker.md`
  - `docs/backlog/planned/206-abstractcore-mcp-integration.md`
  - `docs/backlog/planned/174-framework-execution-target-discovery.md`
  - `docs/backlog/planned/175-abstractflow-execution-targets.md`
  - `docs/backlog/planned/177-framework-agent-host-pool.md`




