# ADR-0010: Runtime-Owned Node Traces (Scratchpad/Trace)

## Status
Accepted (2025-12-21)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-21


## Context
We want complex workflows (including agents) to be portable across hosts:
- AbstractFlow (visual editor)
- AbstractCode (shell/REPL)
- future CLIs or server runners

Those hosts need a structured way to inspect what happened during execution (agent “scratchpad”, tool loop steps, waits, errors) while preserving the core architecture:
- **AbstractRuntime** owns durability/persistence and effect execution
- **AbstractAgent** owns agent APIs/ergonomics on top of runtime
- **AbstractFlow** orchestrates and must not introduce host-specific persistence formats

Earlier implementations attempted to persist agent scratchpads inside AbstractFlow-owned structures. That violates the layering rules (ADR-0001) and breaks portability because other hosts would not see or reuse those persisted structures.

We also want this information to be durable (pause/resume safe), JSON-safe, and bounded (to avoid bloating `RunState.vars`).

## Decision
1) **AbstractRuntime records a per-node execution trace** in persisted run state:
- Stored under `RunState.vars["_runtime"]["node_traces"][node_id]`
- Each node trace is a JSON-safe dict:
  - `node_id: str`
  - `steps: list[trace_entry]` (bounded)
  - `updated_at: str`

2) **Trace entries are recorded for effectful steps** (completed / waiting / failed) and include:
- timestamp, node_id, status
- effect metadata (type, result_key, JSON payload when safe)
- result/error/wait details when present and JSON-safe

3) **Access is standardized across layers**:
- Runtime exposes read APIs: `Runtime.get_node_trace(run_id, node_id)` and `Runtime.get_node_traces(run_id)`.
- Agents expose convenience passthroughs (no runtime internals leaked) for current run:
  - `BaseAgent.get_node_trace(node_id)` / `get_node_traces()`
  - `BaseAgent.get_context()` / `get_scratchpad()`
- Orchestrators/hosts (e.g. AbstractFlow) may expose these traces to users (e.g. as a node output pin), but must not persist a parallel “scratchpad” format.

4) **Ownership boundaries are explicit**:
- `vars["scratchpad"]`: agent/workflow-owned state schema (iteration counters, intermediate reasoning state as designed by AbstractAgent)
- `vars["_runtime"]`: runtime/host-owned metadata (including `node_traces`)

## Consequences

### Positive
- Durable, host-agnostic “scratchpad/trace” data supports pause/resume.
- Visual editors can expose traces via pins without becoming the source of truth.
- AbstractAgent provides ergonomic APIs while keeping persistence in runtime.

### Negative
- Trace entries can still grow large if effect payloads/results are large.

### Neutral / Mitigations
- Trace is bounded per node to reduce runaway growth.
- If/when large payloads become a problem, store heavy data in `ArtifactStore` and keep only lightweight references in `node_traces` (consistent with `docs/architecture.md` durability contract).

## Packages Affected
- AbstractRuntime
- AbstractAgent
- AbstractFlow
- AbstractCode (consumes traces via runtime/agent APIs)

## Related
- ADR-0001: Layered Architecture (`docs/adr/0001-layered-architecture.md`)
- ADR-0004: Observability Strategy (`docs/adr/0004-observability-strategy.md`)
- `docs/architecture.md`
- Backlog: `docs/backlog/completed/080-abstractruntime-runtime-owned-agent-scratchpad-trace.md`
- Backlog: `docs/backlog/completed/081-abstractagent-scratchpad-trace-accessors.md`
