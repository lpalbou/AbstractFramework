# ADR-0020: Agent Host Pool and Orchestrator Placement (Run-Pinned Hosts)

## Status
Accepted

## Dates
- Proposed: 2026-01-07
- Accepted: 2026-01-08

## Context
AbstractFramework already supports two kinds of “distributed execution”:
- **Remote LLM endpoints** (providers / AbstractCore servers): orchestration can remain local.
- **Remote tool workers** (MCP-first): orchestration can remain local, while tools run elsewhere (ADR-0015).

But there is a distinct, harder problem:
**remote durable orchestration itself** (Runtime + Agent loop + stores) running on one or more machines,
while clients (AbstractCode, AbstractFlow, or third-party apps) attach/detach over unreliable networks.

This introduces questions we need to settle early:
- Do we allow **mid-run migration** between orchestrator hosts?
- How do we keep pause/resume/cancel and “ask user” durable across disconnects?
- How do clients pick a host, and how do we prevent accidental multi-host split-brain?

## Decision
Adopt a **run-pinned host** model for orchestrator placement:

1) **A run is pinned to exactly one Agent Host**
- A run is started on a chosen host and stays there for its lifetime.
- We explicitly do **not** support migrating a running workflow between hosts in v0/v1.

2) **Remote orchestration uses the durable run gateway protocol**
- Control plane is **idempotent commands** (resume/cancel/emit/approve/etc).
- Data plane is **durable history** (ledger replay + optional live subscription).
- This aligns with ADR-0018 (Commands + History) and avoids fragile “live RPC coupling”.

3) **A “host pool” is discovery + selection + routing**
- The pool/registry layer exists to:
  - list available Agent Hosts,
  - select a host deterministically (by id/label),
  - route client attach/resume operations to the correct host.
- It does **not** introduce cross-host transactions or shared mutable state between hosts.

4) **Provenance: record host identity in durable records**
- Each run records `host_id` (and later, host identity/signatures) so audits can answer “where did this run execute?”.

### Clarification: run-pinned orchestration still allows multi-machine work
Pinning a run to one orchestrator host does **not** mean “everything runs on one machine”.
It means only the **durable state machine + stores** are pinned.

Within a single run, specific steps can still execute on other machines via:
- remote LLM endpoints (providers)
- remote tool workers (MCP, ADR-0015)
- future “remote agent workers” / execution targets (planned: 177/174/175)

This is the same conceptual split as durable workflow engines (e.g., “workflow history pinned; activities can run anywhere”).

## Consequences

### Positive
- **Durability-first**: correctness and resumability are owned by the runtime host, even with disconnects.
- **Operational simplicity**: no distributed locking or state replication required for v0.
- **Clean layering**: “placement” becomes a routing concern, not a change to core runtime semantics.
- **Security clarity**: authentication/authorization applies to commands and subscriptions (ADR-0018 / backlog 309).

### Negative
- **No mid-run migration**: a host outage can delay progress until the host is restored (or the run is restarted elsewhere).
- **Capacity management**: a host pool needs policies for placement (later), but v0 may be static/manual.

### Neutral
- We can add more advanced placement later (labels/capabilities) without changing the core contract.

## Packages Affected
- `abstractruntime` (gateway API surface; durable run control ownership)
- `abstractcode` (thin-client attach/detach UX)
- `abstractflow` (run placement UI, if exposed in authoring)
- `framework` (cross-cutting deployment model)

## Related
- ADR-0015: `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- ADR-0018: `docs/adr/0018-durable-run-gateway-and-remote-host-control-plane.md`
- Backlog 177 (host pool): `docs/backlog/planned/177-framework-agent-host-pool.md`
- Backlog 307/308/309 (gateway + thin client + security):
  - `docs/backlog/completed/307-framework-durable-run-gateway-command-inbox.md`
  - `docs/backlog/planned/308-abstractcode-remote-thin-client-runtime-gateway.md`
  - `docs/backlog/completed/309-framework-run-gateway-security-and-auth.md`
- Backlog 174/175 (execution targets + routing):
  - `docs/backlog/planned/174-framework-execution-target-discovery.md`
  - `docs/backlog/planned/175-abstractflow-execution-targets.md`


