# ADR-0017: Host UI Events and Durable Prompts

## Status
Proposed

## Dates
- Proposed: (unknown; predates date tracking)
- Accepted: (TBD)


## Context
We need a stable, cross-package contract for surfacing workflow execution progress and interactions in host applications (e.g. AbstractCode, web UIs, thin clients). These signals must work in flexible deployments where the UI and the durable runtime may be separated by a network and where reconnect/replay must remain correct.

We already have the core primitives:
- a durable effect system (ADR-0002)
- durable tool execution boundaries (ADR-0006, ADR-0016)
- replayable ledger subscriptions and an optional event bridge (ADR-0011)
- durable custom events (`WAIT_EVENT` / `EMIT_EVENT`) (completed backlog 098)

What is missing is a clearly documented **reserved “host UX” event namespace** and a durable way to attach **prompt metadata** to waits so a host can render richer UX while preserving resumability.

## Decision
1. Establish a reserved event namespace for host UX signals:
   - `abstract.status`
   - `abstract.message`
   - `abstract.tool_execution`
   - `abstract.tool_result`
   - Backward compatibility: hosts may continue accepting the deprecated alias namespace `abstractcode.*` during migration.
2. Define `abstract.ask` as a durable “ask and wait” interaction using `WAIT_EVENT` with host-renderable prompt metadata (`prompt`, `choices`, `allow_free_text`).
3. Preserve network stability by requiring event payloads to be dict-shaped in the runtime; non-dict payloads are normalized as `{ "value": <payload> }`.
4. Recommend host integration via **ledger-derived interpretation**:
   - hosts subscribe to StepRecord streams
   - hosts render UX based on reserved events and wait states
   - hosts resume runs via `Runtime.resume(...)` (or an equivalent transport API)

## Consequences

### Positive
- Clear, portable contract for workflow → host UX that works in local and networked deployments.
- Durable, replayable UX signals: reconnect/resync uses ledger replay rather than ephemeral UI state.
- Keeps the runtime generic while still supporting richer prompts (no host-specific persistence format).

### Negative
- Hosts must implement a small interpretation layer (reserved names + payload normalization).
- Prompt metadata expands the surface area of wait states; hosts should treat it as best-effort UX hints.

### Neutral
- Tool observability remains fundamentally ledger-driven; explicit `abstract.tool_*` events are optional UX signals, not a replacement for the tool calling pipeline.
  - Note: `abstractcode.*` remains a deprecated alias for backward compatibility.

## Packages Affected
- AbstractRuntime
- AbstractFlow
- AbstractCode
- AbstractCore (indirectly, via normalized tool call schemas and observability)

## Related
- ADR-0002: `docs/adr/0002-effect-system-design.md`
- ADR-0006: `docs/adr/0006-durable-tool-execution.md`
- ADR-0011: `docs/adr/0011-ledger-subscriptions-and-event-bridge.md`
- ADR-0016: `docs/adr/0016-tool-calling-pipeline-and-responsibility-boundaries.md`
- Docs: `docs/ui_events.md`
- Completed backlog: `docs/backlog/completed/098-framework-durable-custom-events-signals.md`
