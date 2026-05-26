# ADR-0018: Durable Run Gateway and Remote Host Control Plane (Commands + Ledger Replay)

## Status
Accepted

## Dates
- Proposed: 2026-01-07
- Accepted: 2026-01-08
- Updated: 2026-05-08 (aligned with ADR-0033)

## Context
We want flexible deployment topologies where:
- a **thin client** (AbstractCode on a phone / lightweight web UI) controls and renders runs executed on a **remote durable host**,
- clients can disconnect/reconnect without losing correctness,
- control actions (resume/cancel/emit/approve) are reliable under retries and intermittent networks.

We already have the correct durability primitives in AbstractRuntime:
- durable run checkpoints (RunStore),
- append-only execution history (LedgerStore StepRecords),
- durable waits and resumptions (WaitState + `Runtime.resume(...)`),
- optional live subscriptions (ADR-0011).

What is missing is a **canonical remote control plane** that avoids “live RPC coupling” and supports:
- idempotent command submission,
- cursor-based history replay,
- thin clients that are effectively stateless.

This matches SOTA durable-workflow practice (Temporal/Cadence/Step Functions) and the core SQS insight: **decouple request from fulfillment** for resilience and correct retries.

## Decision
1. Standardize a remote run control plane as **Commands + History**:
   - **Commands** are durably recorded messages (append-only inbox) with idempotency keys.
   - **History** is rendered by replaying the durable ledger (cursor-based), not by relying on ephemeral streams.

2. Define the minimal **Run Gateway Protocol** surface:
   - start/attach run
   - submit commands: `resume`, `emit_event`, `pause`, `cancel`, approvals
   - replay ledger by cursor; optionally stream via SSE/WS (replay-first)

### Workflow references (bundle-first)
When workflows are distributed as **WorkflowBundles (.flow)**, the bundle is the portable unit clients exchange and cache.

Contract:
- Clients should identify “what to start” primarily via `bundle_id`.
- `flow_id` is used to select which **entrypoint/subflow** inside a bundle to start.
  - If a bundle has a single entrypoint **or** declares `manifest.default_entrypoint`, starting a run can omit `flow_id` (`{bundle_id, input_data}`).
  - If a bundle has multiple entrypoints and no `default_entrypoint`, clients must specify `flow_id` (or pass a fully-qualified workflow id like `bundle:flow`).

3. Make “single host per run” the default invariant:
   - choose a host for a run at start
   - avoid mid-run migration (explicitly out of scope)
   - host pools and discovery are layered on top (ADR-0015 + backlog 177).

4. Security baseline is mandatory before public deployments:
   - protect **both** command endpoints and read endpoints (ledger/run state can be sensitive)
   - default bind to localhost; recommend HTTPS behind a reverse proxy or VPN/mesh
   - require Gateway authentication (v0: bearer token) and basic abuse resistance (origin checks,
     body limits, rate limiting)
   - keep Gateway auth/origin policy separate from AbstractCore server auth and from outbound
     provider API keys
   - if Gateway calls a standalone Core server, configure the Core server URL and Core server
     `Authorization` token explicitly
   - treat direct Gateway image/TTS/STT endpoints as Gateway HTTP/artifact contracts whose backend
     provider configuration remains owned by AbstractCore and capability packages
   - codified as backlog 309 (aligned with the threat model in backlog 279).

## Diagram
```
(thin client)                    (gateway / host)                      (runner)
┌───────────────┐     POST cmd    ┌────────────────────┐    poll/apply  ┌──────────────┐
│ AbstractCode  ├───────────────▶ │ Command inbox       ├──────────────▶ │ Runtime tick  │
│ / other UI    │                 │ (durable, idempot.) │                │ + stores      │
│ (stateless)   │   replay/stream └─────────┬──────────┘   append        └──────┬───────┘
│ ledger cursor │◀──────────────────────────┘            StepRecords            │
└───────────────┘                 ┌────────────────────┐◀──────────────────────┘
                                  │ Ledger replay/stream│
                                  │ (cursor-based)      │
                                  └────────────────────┘
```

## Consequences

### Positive
- Network-safe UX: clients can reconnect and deterministically re-render by replaying history.
- Correct retry semantics: commands are idempotent; fulfillment is decoupled from submission.
- Clear separation of responsibilities:
  - runtime is authoritative for correctness,
  - hosts/clients are interpreters and control submitters.

### Negative
- Requires implementing and operating a command inbox and replay endpoints.
- Introduces eventual-consistency UX: a command can be accepted before it is fulfilled (by design).

### Neutral
- Does not mandate a specific transport (HTTP+SSE vs WS); replay semantics remain the invariant.
- Does not decide multi-host scheduling policy; host pools/discovery are layered later.

## Packages Affected
- AbstractRuntime (stores + wait/resume semantics; history replay primitives)
- AbstractGateway (control-plane HTTP/SSE surface and deployment security)
- AbstractFlow (gateway reference server in web host; UI consumption)
- AbstractCode (thin-client mode; remote attach/resume)
- AbstractCore (indirect: provider/tool routing via targets; security secrets)

## Related
- ADR-0011: `docs/adr/0011-ledger-subscriptions-and-event-bridge.md`
- ADR-0013: `docs/adr/0013-durable-run-controls-pause-resume-cancel.md`
- ADR-0015: `docs/adr/0015-execution-targets-and-remote-tool-workers.md`
- ADR-0017: `docs/adr/0017-host-ui-events-and-durable-prompts.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- Backlog:
  - `docs/backlog/completed/307-framework-durable-run-gateway-command-inbox.md`
  - `docs/backlog/planned/308-abstractcode-remote-thin-client-runtime-gateway.md`
  - `docs/backlog/completed/309-framework-run-gateway-security-and-auth.md`
  - `docs/backlog/planned/177-framework-agent-host-pool.md`
  - `docs/backlog/planned/279-framework-remote-worker-security-hardening.md`
