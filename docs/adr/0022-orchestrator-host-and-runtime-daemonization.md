# ADR-0022: Orchestrator Host Model (Runtime Kernel vs Gateway Service)

## Status
Proposed (2026-01-16)

## Dates
- Proposed: 2026-01-16
- Accepted: (TBD)

## Context
We need **durable 24/7 orchestration** for long-running agent workflows and scheduled jobs, with strong restart/reconnect behavior across:
- local dev (single machine),
- thin clients (web/iPhone),
- remote execution targets (LLM endpoints, tool workers),
- and safe operational controls (pause/resume/cancel/kill switch).

Confusion surfaced around “who gives life to AbstractRuntime”:
- Scheduled runs stop advancing when the gateway/observer processes are stopped.
- On restart, durable runs can resume, but cadence can drift (relative intervals) and side effects may repeat (at-least-once).

This ADR clarifies the **SOTA-aligned responsibilities** between:
- `abstractruntime` (durable kernel + stores),
- `abstractgateway` (deployable control plane + orchestrator host),
- and other hosts like `abstractflow` (authoring + optional local execution).

The key question:
> Should `abstractruntime` become a standalone 24/7 daemon independent of `abstractgateway`?

## Decision

### 1) Keep AbstractRuntime as a library kernel (not a network daemon)
`abstractruntime` remains an embeddable kernel that:
- represents durable waits (`WAIT_UNTIL`, `WAIT_EVENT`, …),
- persists checkpoints (`RunStore`) and append-only history (`LedgerStore`),
- enforces execution policy (pause/resume/cancel, timeouts, retries),
- but does **not** “wake itself up”.

Runs progress only when a host calls `Runtime.tick(...)` / `Runtime.resume(...)`.

Rationale (ADR-independent, SOTA check):
- Durable orchestration requires an always-on **orchestrator host + persistence** boundary; whether the state machine is implemented as a “daemon” or a “library inside a service” is packaging.
- Keeping the kernel as a library preserves portability (Flow/Code/3rd-party hosts) and keeps the orchestration algorithm dependency-light.

### 2) Define “Orchestrator Host” as the 24/7 component (stores + tick loop)
The always-on part of the system is the **orchestrator host**:
- owns the durable stores (runs/ledger/artifacts + command inbox),
- runs a tick/resume loop that advances RUNNING runs and due `WAIT_UNTIL` waits,
- applies durable commands (pause/resume/cancel/emit_event/…).

In the gateway topology, `abstractgateway` is the orchestrator host.

### 3) Use one remote control plane: Commands + History (no live RPC coupling)
Remote interaction stays “Temporal-like”:
- clients submit **idempotent commands** to a durable inbox,
- clients render by replaying/streaming **history** (ledger cursor),
- correctness never depends on a live socket.

This avoids creating a second, competing protocol surface by turning `abstractruntime` into a separate network daemon.

### 4) Operational resilience: allow splitting API and runner into separate processes (same stores)
If we need “restart the gateway API without stopping execution”, the recommended move is:
- keep a dedicated **runner worker** process alive (the tick loop),
- allow the **HTTP API** process to restart independently,
- both sharing the same durable stores/command inbox directory (or DB).

This provides most “daemon independence” benefits without introducing a new runtime network daemon and protocol.

### 5) Scheduling semantics are a policy layer, not proof of daemon-ness
Time-based waits are durable state, not OS timers.

Current v0 recurrence is **relative interval** (“now + interval”), which can drift across downtime and variable execution time.

We treat “absolute wall-clock schedules” (cron-like anchored schedules + optional catch-up) as a **future scheduling policy** improvement, not as a reason to daemonize the runtime.

## Consequences

### Positive
- Preserves an embeddable, dependency-light `abstractruntime` kernel usable by multiple hosts.
- Keeps a single SOTA control-plane contract (Commands + History) across web/iPhone/CLI clients.
- Centralizes “kill switch” behavior: stopping the orchestrator host stops further execution (especially tool execution).
- Makes “API restart without execution pause” possible via process separation (API vs runner) without inventing a new protocol.

### Negative
- Requires a long-lived orchestrator host for 24/7 behavior (something must run the tick loop).
- Without additional work, file-backed stores + polling are not a high-scale scheduler (acceptable for v0/dev; DB-backed stores are needed for production scale).
- Side effects remain at-least-once unless tools/workflows are designed to be idempotent (SOTA activity boundary reality).

### Neutral
- This ADR does not forbid building a runtime daemon in the future; it says it is not the default and is not required to reach SOTA durability properties.

## Packages Affected
- AbstractRuntime
- AbstractGateway
- AbstractObserver
- AbstractFlow
- AbstractCode

## Related
- ADR-0018: `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- ADR-0020: `docs/adr/0020-agent-host-pool-and-orchestrator-placement.md`
- ADR-0021: `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
- ADR-0015: `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- Backlog 307: `docs/backlog/completed/307-framework-durable-run-gateway-command-inbox.md`
- Backlog 318: `docs/backlog/completed/318-framework-abstractgateway-extract-run-gateway-host.md`
- Report: `docs/report/architecture-runtime-gateway.md`

