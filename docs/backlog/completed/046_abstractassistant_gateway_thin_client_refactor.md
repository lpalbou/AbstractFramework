# 046 — AbstractAssistant gateway thin-client refactor assessment

## Summary

Assess the complexity and design for refactoring **AbstractAssistant** into a gateway-first thin client
that no longer runs local agents/runtime or installs local model stacks by default.

## Why

- Align AbstractAssistant with the gateway-first architecture used by `abstractcode/web`.
- Reduce local dependency footprint and eliminate local model/tool installs.
- Centralize durability, tool execution, and scheduling in the gateway.

## Scope

### In scope

- Audit current local-host responsibilities (agent/runtime/tool execution/provider discovery/voice).
- Map those responsibilities to gateway APIs (runs, ledger streaming, tool approvals, artifacts).
- Identify gaps in gateway APIs needed to preserve current UX.
- Produce a migration plan and effort/risk assessment.
- Propose an ADR if the architectural change is accepted.

### Out of scope

- Implementing the refactor in `abstractassistant` or `abstractgateway`.
- Changing gateway API contracts.
- Updating package dependencies or release artifacts.
- Running automated tests (analysis only).

## Dependencies

- AbstractGateway run/ledger APIs and durable command endpoints.
- Provider/model discovery endpoints (`/api/providers`, `/api/models`).
- Artifact upload/download endpoints for attachments.
- Optional: `/v1/audio/*` endpoints if voice stays.

## Expected Outcomes

- Clear scope and complexity breakdown for a thin-client refactor.
- Explicit risks and missing API surface areas.
- Recommended approach (full gateway-only vs dual-mode).
- ADR proposal outlining the decision and constraints.

## Implementation Plan (high-level)

- Build a gateway client abstraction for runs, commands, ledger streaming, and providers.
- Replace `AgentHost`/`LLMManager` with remote run orchestration.
- Rewire session/history views to gateway run + ledger data.
- Map tool approvals to gateway wait/resume flows (no silent fallbacks, `#FALLBACK` warnings).
- Rework attachments to upload to gateway artifacts before run start.
- Decide on voice: gateway audio endpoints or disable with explicit UX messaging.
- Update documentation set (`README`, `docs/architecture.md`, `docs/getting-started.md`, `docs/api.md`).

---

## Report

### Work completed

- Reviewed AbstractAssistant architecture and core modules to confirm local-host responsibilities.
- Mapped local runtime, provider discovery, tool approvals, attachments, and voice to gateway equivalents.
- Assessed refactor complexity, risks, and UX impacts for a gateway-first thin client.

### Key findings

- AbstractAssistant is a **local host** running AbstractAgent + AbstractRuntime with local stores.
- The UI directly drives local `AgentHost.run_turn(...)` and handles tool approvals on-device.
- Provider/model discovery relies on local AbstractCore instantiation.
- Default dependencies include `abstractagent`, `abstractvoice`, and `abstractcore[...]` extras.
- STT uses a local adapter that allows model downloads.

### Recommended approach

- Implement a gateway-only client abstraction and replace local agent/runtime codepaths.
- Use gateway provider/model listings; avoid local provider discovery.
- Shift attachments to gateway artifacts; keep only local selection and upload.
- Voice should either call gateway `/v1/audio/*` endpoints or be explicitly disabled with a clear warning (`#FALLBACK`).
- Treat legacy local sessions as separate; show a migration notice rather than silently merging states.

### Complexity assessment

High: the refactor touches core execution, session/history, tool approvals, attachments, voice, and packaging/tests.

### Tests

Not run (analysis only).

### ADR proposal

Create an ADR to record the decision to move AbstractAssistant to a gateway-first thin-client model
(including behavior when the gateway is unavailable and the required warning semantics).
