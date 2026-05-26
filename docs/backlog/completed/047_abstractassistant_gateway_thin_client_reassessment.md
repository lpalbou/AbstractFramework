# 047 — AbstractAssistant gateway thin-client reassessment (core/runtime/gateway/voice/vision)

## Summary

Reassess the AbstractAssistant → AbstractGateway thin-client refactor after reviewing
AbstractCore, AbstractRuntime, AbstractGateway, AbstractVoice, and AbstractVision.

## Why

- Validate that gateway APIs fully cover AbstractAssistant’s needs.
- Identify any missing surfaces or constraints in core/runtime integrations.
- Refine effort/risk assessment with actual package capabilities.

## Scope

### In scope

- Review gateway run/ledger/command/attachments/voice/discovery APIs.
- Review runtime durability + tool-wait semantics.
- Review AbstractCore server/capability plugins (voice/vision) and media handling.
- Review AbstractVoice/AbstractVision artifact integration and download policies.
- Update refactor effort/risk assessment and recommendations.

### Out of scope

- Implementing the refactor.
- Modifying gateway or core APIs.
- Running automated tests (analysis only).

## Dependencies

- AbstractGateway HTTP API surface.
- AbstractRuntime effect/wait semantics.
- AbstractCore capability plugin architecture.
- AbstractVoice/AbstractVision artifact adapters.

## Expected Outcomes

- Updated mapping of AbstractAssistant features → gateway endpoints.
- Clear statement of remaining gaps or risks.
- Revised complexity estimate and migration approach.

## Implementation Plan (analysis)

- Map AbstractAssistant features to gateway endpoints and data contracts.
- Verify tool approval waits/resume and session handling.
- Evaluate attachments ingestion/upload and workspace policy.
- Evaluate voice/STT/TTS and vision integration requirements.
- Produce updated assessment and recommendations.

---

## Report

### Work completed

- Reviewed AbstractGateway API surface, discovery endpoints, attachments, and voice routes.
- Reviewed AbstractRuntime tool-wait/resume semantics and approval flow.
- Reviewed AbstractCore server capabilities and capability plugin model.
- Reviewed AbstractVoice and AbstractVision integration and artifact adapters.
- Updated the thin-client refactor assessment.

### Updated mapping (AbstractAssistant → Gateway)

- **Runs + durability**: `POST /api/gateway/runs/start` + `GET /api/gateway/runs/{run_id}` + ledger replay/stream.
- **Session grouping**: `session_id` is supported on run start + run list filters; gateway creates session memory runs.
- **Tool approvals**: gateway default tool mode is `approval`; tool waits surface via `run.waiting.details` + ledger.
- **Commands**: `POST /api/gateway/commands` for `pause|resume|cancel|emit_event`.
- **Attachments**: `POST /api/gateway/attachments/ingest` (workspace paths) or `POST /api/gateway/attachments/upload` (bytes).
- **Artifacts**: list/download via `GET /api/gateway/runs/{run_id}/artifacts` and content endpoints.
- **Providers/models**: `GET /api/gateway/discovery/providers` + `/providers/{provider}/models`, with defaults.
- **Tool catalog**: `GET /api/gateway/discovery/tools`.
- **Capabilities**: `GET /api/gateway/discovery/capabilities` (voice/media/tool presence).
- **Voice**: `POST /api/gateway/runs/{run_id}/voice/tts` and `/audio/transcribe` (artifact-based STT).
- **Workspace policy**: `GET /api/gateway/workspace/policy` + `/files/search` for @file UX.

### Key findings

- Gateway already exposes **thin‑client primitives**: run lifecycle, ledger replay/stream, command inbox, attachments upload/ingest, provider discovery, and voice endpoints.
- Runtime approval waits use a **durable WAITING state** and can be resumed with payloads (`{"approved": true|false}`); the gateway’s default tool mode aligns with AbstractAssistant’s tool approval UX.
- Voice can be fully **server‑side** through gateway endpoints; no local AbstractVoice install is required for a thin client.
- Vision is available via AbstractCore’s capability plugin if the gateway environment installs `abstractvision`; thin client does not need local vision deps.

### Remaining gaps / risks

- **UI event loop rewrite**: AbstractAssistant currently drives local `AgentHost.run_turn(...)`. Thin client must become ledger‑driven.
- **Conversation flow contract**: AbstractAssistant will need a gateway‑hosted workflow (e.g., agent flow bundle) to accept chat input; there is no direct “send message” endpoint beyond start run or emit_event.
- **Tool catalog coverage**: `/discovery/tools` returns AbstractRuntime default tools, not custom bundle‑specific tools; the UI may need additional hints or bundle metadata.
- **Session history UX**: Requires mapping ledger + run summaries into the existing session UI (no local snapshot).
- **Voice UX**: Full voice mode requires audio capture + upload + server STT round‑trip; latency/UX needs careful handling.

### Revised complexity assessment

**Medium‑High** (down from “very high”): gateway already provides most thin‑client APIs, but AbstractAssistant’s UI and control flow must be substantially re‑wired to be ledger‑first and command‑driven.

### Recommendations

- Build a **GatewayClient** abstraction (runs, commands, ledger stream, artifacts, discovery, workspace policy).
- Reuse gateway `session_id` + `session memory` artifacts instead of local snapshots.
- Align tool approvals with gateway waits; avoid silent fallbacks (`#FALLBACK` warnings on discovery failures).
- Treat voice as gateway‑optional: if `/discovery/capabilities.voice` is missing, disable voice with explicit warning.

### Tests

Not run (analysis only).
