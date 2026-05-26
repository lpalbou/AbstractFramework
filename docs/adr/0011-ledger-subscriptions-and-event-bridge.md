# ADR-0011: Runtime Ledger Subscriptions + AbstractCore Event Bridge

## Status
Accepted (2025-12-21)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-21


## Context
We need workflow execution to be:
- **Portable** across hosts (AbstractFlow visual editor, AbstractCode CLI, 3rd-party runners)
- **Durable** (pause/resume with RunStore + LedgerStore)
- **Observable** in real time (UIs need to know which node/effect is running, waiting, or failed)

We already have two strong primitives:
- **AbstractRuntime ledger**: durable, append-only `StepRecord` stream (source of truth)
- **AbstractCore GlobalEventBus**: in-process progress events for LLM/tool operations

But we lacked a clean way to stream runtime execution progress without:
- inventing AbstractFlow-only observability code paths,
- creating a second competing global event system, or
- violating ADR-0001 (runtime kernel must not import AbstractCore).

## Decision
1. **Make runtime execution progress subscribable via the ledger**
   - Provide an optional, process-local subscription mechanism on ledger appends.
   - Keep replay/resync via `LedgerStore.list(run_id)` as the durable source of truth.

2. **Keep AbstractRuntime kernel dependency-light**
   - The runtime core does not import AbstractCore or emit GlobalEventBus events directly.
   - Subscription support is expressed via a storage decorator (`ObservableLedgerStore`) and a Runtime convenience method (`Runtime.subscribe_ledger(...)`).

3. **Optionally bridge workflow-step events onto AbstractCore’s GlobalEventBus**
   - Implement the bridge in `abstractruntime.integrations.abstractcore` (explicit opt-in to AbstractCore).
   - Map appended `StepRecord.status` to new AbstractCore event types:
     - `WORKFLOW_STEP_STARTED`
     - `WORKFLOW_STEP_COMPLETED`
     - `WORKFLOW_STEP_WAITING`
     - `WORKFLOW_STEP_FAILED`

## Consequences

### Positive
- UIs/CLIs can stream execution progress without depending on AbstractFlow backend internals.
- Disconnect/reconnect is naturally supported via ledger replay, with live push as an optimization.
- No new cross-package event bus is introduced; the ledger remains the durable log.
- Optional unification: hosts that already consume AbstractCore events can observe workflow progress on the same bus.

### Negative
- Subscriptions are process-local; cross-process/pubsub requires an external transport (future work).
- Bridging workflow events into AbstractCore expands AbstractCore’s EventType surface.

### Neutral
- Hosts decide whether to subscribe directly to the ledger or consume bridged events via GlobalEventBus.

## Packages Affected
- AbstractRuntime
- AbstractCore
- AbstractFlow (consumes via hosts; no new requirement)
- AbstractCode (can consume via either mechanism)

## Related
- ADR-0001: `docs/adr/0001-layered-architecture.md`
- ADR-0004: `docs/adr/0004-observability-strategy.md`
- Backlog: `docs/backlog/completed/083-framework-runtime-ledger-subscription-and-event-bridge.md`
