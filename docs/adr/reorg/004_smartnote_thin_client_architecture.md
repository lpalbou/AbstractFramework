# ADR 004: SmartNote gateway-first thin client

**Status**: Accepted  
**Date**: 2026-02-21  
**Scope**: SmartNote application

## Context

SmartNote must be easy to access (systray UI) while remaining durable and observable.
AbstractAssistant currently runs the runtime in-process, but SmartNote must **not**
follow the same backend strategy. We need a thin client that **connects to an
existing AbstractGateway** without introducing a separate SmartNote server.

## Decision

- **UI**: SmartNote tray app is a **thin client** that calls **AbstractGateway**.
- **Backend**: SmartNote runs as a **gateway bundle** (.flow) and **SmartNote tools**
  executed in-process by the gateway runtime.
- **Startup**: SmartNote performs a bundle preflight (builds locally if needed and uploads
  to the gateway) so users can run `smartnote` without manual bundling.
- **Durability**: Ingestion is a gateway-managed run with a durable ledger.
- **Ingestion**: Notes are processed with a chunked LLM workflow (no truncation) to
  extract summary, topics, entities, and triples.
- **Artifact-first cards**: ingestion persists fragments and cards as artifacts; see ADR 005.
- **Warnings**: Any fallback emits `#FALLBACK`; any truncation (if ever needed for UI)
  must use `#TRUNCATION` tags.

## Consequences

- The UI requires an available gateway (no standalone SmartNote server).
- Notes are replayable and auditable via gateway ledgers.
- Tool registration is explicit (`SMARTNOTE_ENABLE_GATEWAY_TOOLS=1`) to avoid silent
  behavior changes in unrelated gateway deployments.

