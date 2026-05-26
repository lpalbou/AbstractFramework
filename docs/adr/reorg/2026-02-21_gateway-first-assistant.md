# ADR: Gateway-first AbstractAssistant

## Status
Accepted — 2026-02-21

## Context
- AbstractAssistant originally ran AbstractCore/Runtime locally.
- AbstractGateway now provides durable runs, bundle discovery, and a unified control plane.
- A gateway-first assistant improves consistency across clients and simplifies orchestration.

## Decision
- AbstractAssistant runs as a **thin client of AbstractGateway** by default.
- Workflow selection is exposed in the UI via gateway bundle discovery.
- Voice I/O is routed through gateway audio endpoints with local recording/playback.
- Offline/reconnect is explicit in the UI (no silent failures).
- Any fallback behavior must emit `#FALLBACK` warnings.

## Consequences
- Gateway availability becomes a runtime dependency; the UI surfaces OFFLINE/RECONNECTING states.
- Local-only mode remains available for development/testing.
- Client configuration centers on `gateway.url`, `gateway.bundle_id`, and `gateway.flow_id`.
