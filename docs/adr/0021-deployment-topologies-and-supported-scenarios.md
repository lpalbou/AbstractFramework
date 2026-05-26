# ADR-0021: Deployment Topologies and Supported Scenarios

## Status
Accepted

## Dates
- Proposed: 2026-01-08
- Accepted: 2026-01-08
- Updated: 2026-05-08 (aligned with ADR-0033)

## Context
AbstractFramework is explicitly designed to support:
- durable orchestration (runs survive restarts, can pause/resume/cancel),
- thin clients (stateless UIs that can reconnect/replay),
- multiple tool execution placements (local tools, remote tools, delegated execution),
- multiple deployment environments (local dev, servers, LAN, remote machines).

In practice, contributors and users need a single document that answers:
1) what deployments are supported **today** (code reality),
2) what is explicitly **not** supported today,
3) what additional work would unlock more scenarios.

This ADR is that compatibility matrix.

## Decision
We define deployment topologies in terms of **roles** (not packages), then map them to concrete packages and current capabilities.

### Core roles (conceptual)
- **Client UX**: renders run progress and collects user input/approvals (stateless or stateful).
- **Orchestrator**: durable state machine that ticks workflows and persists state (AbstractRuntime + stores).
- **Control plane**: remote durable command inbox + ledger replay/stream API (AbstractGateway).
- **LLM endpoint**: local or remote OpenAI-compatible API (LMStudio/vLLM/OpenAI/etc), accessed via AbstractCore.
- **Core server**: optional standalone OpenAI-compatible AbstractCore HTTP server. It has its own
  auth, origin policy, base URL allowlists, and provider-key override rules.
- **Capability backend**: Vision/Voice/Music/embedding/memory backend used by Core or Gateway.
  These are usually outbound clients or in-process libraries, not browser-facing control planes.
- **Tool execution**: side effects, executed by a host-configured `ToolExecutor` (local, remote via MCP, or delegated).

### Portable workflow input (today)
- **VisualFlow JSON** is the portable workflow “source” format.
- **WorkflowBundle (.flow)** is the portable distribution unit: `manifest.json` + `flows/*.json` (+ optional assets).
- Hosts compile VisualFlow via the single semantics engine: `abstractruntime.visualflow_compiler`.

## Supported topologies (today)

### Topology A — Single machine (local everything)
Everything runs on one machine/process (or one machine with multiple local processes).

- Orchestrator: `abstractruntime` with file-backed stores (or in-memory for dev).
- LLM: `abstractcore` calling a local or remote provider endpoint.
- Tools: local `MappingToolExecutor` (and optionally remote MCP tools).
- Client UX: AbstractCode (TUI) and/or AbstractFlow Web (editor + run inspector).

This is the most complete topology today for “real workflows” (LLM + tools).

### Topology B — Local orchestrator + remote LLM endpoint
Same as Topology A, but LLM calls go to a remote machine (GPU box / cloud).

- Only change: provider config (`base_url`, model) points to the remote endpoint.
- The remote endpoint can be a hosted provider, an OpenAI-compatible inference server, or a
  standalone AbstractCore server.
- If it is an AbstractCore server, Core server auth and Core server allowlists apply; Gateway
  tokens and origins do not silently apply.
- Tools remain local (or remote via MCP as in Topology C).

### Topology C — Remote tool execution via MCP (host-driven)
Orchestration stays local, but tools execute on another machine.

- Tools: `abstractruntime.integrations.abstractcore.tool_executor.McpToolExecutor` (host calls MCP over the network).
- Optional worker: `abstractruntime-mcp-worker` can run remotely and expose toolsets over stdio or HTTP.

This is supported today and documented in `docs/misc/deploy-remote-tool-executor.md`.

### Topology D — Thin client UI ↔ AbstractGateway (remote durable host)
The orchestrator and durable stores live on a host running AbstractGateway.
Clients are stateless UIs that:
- **act** by submitting durable commands,
- **render** by replaying/streaming the durable ledger (cursor-based).

See ADR‑0018 for the control plane contract.

Current workflow sources in gateway:
- **Bundle mode (default)**: `.flow` bundles containing `flows/*.json` (VisualFlow), compiled via `abstractruntime.visualflow_compiler` (no `abstractflow` import).
- **VisualFlow directory mode (optional)**: loads VisualFlow JSON files from a directory and wires execution using AbstractFlow host helpers.

Bundle mode execution wiring (code reality):
- In **bundle mode**, AbstractGateway compiles VisualFlow via the single semantics engine (`abstractruntime.visualflow_compiler`) and wires:
  - built-in runtime effects (ASK_USER/WAIT_EVENT/START_SUBWORKFLOW/MEMORY_*),
  - `LLM_CALL` + `TOOL_CALLS` via `abstractruntime.integrations.abstractcore` when needed (provider/model configured),
  - derived Visual Agent ReAct subworkflows (requires `abstractagent`),
  - derived “On Event” listener workflows (started as child runs in the same session).

Tool execution policy is host-configurable:
- Default: **passthrough wait** (`ABSTRACTGATEWAY_TOOL_MODE=passthrough`) so untrusted servers do not execute side effects implicitly.
- Optional: **local execution** (`ABSTRACTGATEWAY_TOOL_MODE=local`) for single-host dev deployments.

Gateway deployment profile is also host-configurable:
- remote-light server profiles install HTTP, Runtime/Core/Agent, and light Voice/Vision capability
  packages without local model engines;
- memory profiles explicitly add the Memory backend dependencies needed for KG workflows;
- GPU/local profiles are explicit heavy profiles and must not be implied by a default server image.

Gateway auth/origin policy protects the Gateway control plane. If Gateway embeds Core in-process,
Core server auth/origin policy is not exposed to clients. If Gateway calls a standalone Core server,
that Core server has a separate service URL and auth configuration.

### Topology E — Multi-host orchestrator pool (planned)
Distribute **runs** across multiple orchestrator hosts (one host per run).

- Architectural direction: ADR‑0020 (run-pinned hosts; no mid-run migration).
- Not implemented as a first-class feature yet (host discovery, placement, orchestration).

## Not supported today (explicit)
- **Non-Python execution environments** (e.g., native iOS runtime): the runtime is Python; porting is future work.
- **First-class multi-domain tool routing in one run** (some tools on client, some on server) as a stable protocol:
  - the durability primitives exist (WAIT + resume),
  - but routing/auth/leases are not yet standardized end-to-end.
- **Multi-tenant RBAC / per-user auth** beyond the current gateway security baseline.
- **Implicit auth/config cascades** from Gateway into Core or capability packages. Cross-service
  auth, provider credentials, and browser origins must be configured explicitly.

## Future work (what could be made possible)
The following additions would unlock more deployment scenarios without changing core durability semantics:

1) **Delegated tool execution for thin clients**
   - Standardize a “delegated tool execution” flow where:
     - the orchestrator emits tool calls,
     - the run enters a durable wait,
     - a client (or remote worker) executes tools and resumes with results.
   - Requires explicit routing + security boundaries (see ADR‑0015 and backlog 279/320).

2) **Host pool + placement**
   - Implement host discovery + placement and route each run to an orchestrator host (ADR‑0020).

## Packages Affected
- `abstractruntime`
- `abstractcore`
- `abstractvoice`
- `abstractvision`
- `abstractmusic`
- `abstractmemory`
- `abstractgateway`
- `abstractflow`
- `abstractcode`

## Related
- ADR‑0015: `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- ADR‑0018: `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- ADR‑0020: `docs/adr/0020-agent-host-pool-and-orchestrator-placement.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- Deployment guide: `docs/guides/deployment-topologies.md`
- Remote tool executor: `docs/misc/deploy-remote-tool-executor.md`
- Topology discussion notes: `docs/misc/architecture-deployment-discussions.md`
- Thin client (web/PWA): `docs/backlog/completed/317-abstractcode-react-thin-client-web-pwa-ios-dev-deploy.md`
