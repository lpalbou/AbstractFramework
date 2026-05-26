# ADR-0013: Durable Run Controls (Pause/Resume/Cancel)

## Status
Accepted (2025-12-26)

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: 2025-12-26


## Context
We need to operationally control workflow runs across hosts:
- **AbstractFlow** (visual editor / Run Flow UI)
- **AbstractCode** and other executors (later)

AbstractRuntime already provides durable `RunState` + `RunStore` + `LedgerStore`, and supports `cancel_run(...)` plus standard wait/resume semantics (WAIT_EVENT / WAIT_UNTIL / ASK_USER).

However, we lacked a **manual pause/resume** primitive that:
- works for any run (RUNNING or WAITING),
- is durable (persisted in `RunStore`),
- is respected by automatic mechanisms (WAIT_UNTIL auto-unblock, EMIT_EVENT delivery, scheduler),
- does not break real ASK_USER prompts (already “paused” by definition).

## Decision
1) **Represent manual pause as runtime-owned metadata**
- Store control state under `RunState.vars["_runtime"]["control"]`.
- Use `paused: true|false` as the canonical flag.

2) **Add first-class Runtime APIs**
- `Runtime.pause_run(run_id, reason=...) -> RunState`
  - If RUNNING: transition to `status=WAITING` with a synthetic USER wait (`wait_key="pause:{run_id}"`, `details.kind="pause"`).
  - If WAITING (UNTIL/EVENT/SUBWORKFLOW): keep the existing `WaitState` intact and only set the `paused` flag.
  - If WAITING USER due to ASK_USER: no-op (already blocked by user input).
- `Runtime.resume_run(run_id) -> RunState`
  - Clear the `paused` flag.
  - If currently in the synthetic pause wait, resume to RUNNING and continue from the stored `resume_to_node`.

3) **Runtime and scheduler must respect pause**
- `Runtime.tick(...)` returns immediately when paused.
- `Runtime.resume(...)` rejects resuming a paused run.
- `Runtime._handle_emit_event(...)` skips paused listener runs.
- `Scheduler` skips paused runs for:
  - `emit_event(...)`
  - `resume_subworkflow_parent(...)`
  - polling due `WAIT_UNTIL` runs

## Consequences
### Positive
- Pause/resume/cancel becomes durable and portable across hosts (run_id-addressable).
- Time/event driven mechanisms cannot accidentally advance a paused run.
- Hosts do not need bespoke “pause” persistence formats (stays in `RunState.vars["_runtime"]` per ADR-0010).

### Negative
- Manual pause is not an interruptible preemption of in-flight effects (e.g., an LLM call already executing). It applies at step boundaries.

## Packages Affected
- AbstractRuntime
- AbstractFlow (web backend + Run Flow UI)

## Related
- ADR-0010: `docs/adr/0010-runtime-owned-node-traces.md`
- ADR-0011: `docs/adr/0011-ledger-subscriptions-and-event-bridge.md`

