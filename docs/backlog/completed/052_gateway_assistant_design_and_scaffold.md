# 052 — Gateway-first AbstractAssistant design + scaffold

## Summary

Design the gateway-first AbstractAssistant and add initial scaffolding for
gateway connectivity and ledger-driven UX, referencing `abstractcode/web` and
shared UI components in `abstractuic/`.

## Why

- Align AbstractAssistant with the gateway-first platform strategy.
- Reuse the proven thin-client contract from `abstractcode/web`.

## Scope

### In scope

- Architecture/design doc for gateway-first AbstractAssistant.
- Initial gateway client + event mapping scaffolding.
- Config surface for gateway settings.

### Out of scope

- Full UI migration to web or full feature parity.
- Release packaging or cross-platform tray runtime changes.
- End-to-end production deployment.

## Dependencies

- `abstractcode/web` gateway client + ledger loop patterns.
- `abstractuic/` shared UI components (for future reuse).
- AbstractAssistant Qt UI (current host surface).

## Expected Outcomes

- Clear design direction and module boundaries.
- Python gateway client skeleton aligned to `/api/gateway/*`.
- Event adapter plan to feed existing UI while gateway-first work proceeds.

## Implementation Plan (initial)

- Add a design doc outlining architecture and reuse strategy.
- Implement a Python `GatewayClient` aligned to `abstractcode/web`.
- Add a minimal event adapter API for ledger-driven UI updates.
- Add configuration for gateway URL/token and mode selection.

---

## Report

### Work completed

- Added a gateway-first design draft in `abstractassistant/docs/gateway-first-design.md` referencing `abstractcode/web` and shared UI direction.
- Implemented Python gateway scaffolding in `abstractassistant/abstractassistant/gateway/`:
  - `GatewayClient` (runs, ledger, commands, attachments, voice).
  - SSE parser + ledger event helpers + adapter stub for UI events.
- Extended config with `gateway` settings and documented it in `abstractassistant/docs/api.md`.
- Added unit tests for SSE parsing, event extraction, and adapter mapping.
- Updated docs index + architecture with gateway-first pointer.

### Tests

- `pytest tests/basic/test_gateway_sse_parser.py tests/basic/test_gateway_events.py tests/basic/test_gateway_adapter.py`

### OpenAI / gpt-5-mini validation

- Not run. Requires a running gateway with an OpenAI provider configured and a known workflow bundle to start runs.
