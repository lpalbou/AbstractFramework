# 053 — Gateway-first AbstractAssistant Phase 1 (Qt tray run)

## Summary

Wire the Qt tray app to run the default gateway workflow (`basic-agent`) using
ledger replay + SSE streaming, while keeping the current UI shell.

## Why

- Prove the gateway-first runtime loop in the tray UI.
- Reuse the `abstractcode/web` thin-client contract directly.

## Scope

### In scope

- Gateway run start, ledger replay/stream, and wait resume.
- Default workflow selection via gateway bundle discovery.
- Session message persistence for UI history.

### Out of scope

- Full UI migration to web components.
- Advanced provider discovery UX.
- Cross-platform tray packaging changes.

## Dependencies

- Gateway must expose the `basic-agent` bundle entrypoint.
- `abstractcode/web` run loop patterns for reference.

## Expected Outcomes

- Tray can send a prompt to `basic-agent` through the gateway.
- Tool approvals and ask-user waits resume correctly.
- Manual testing path documented.

## Implementation Plan

- Add a gateway worker that mirrors `abstractcode/web` (start run + replay + SSE).
- Add run input builder aligned to `abstractcode/web` contract.
- Select the default entrypoint from bundle discovery.
- Persist messages into the session store for UI history.

---

## Report

### Work completed

- Added `GatewayWorker` in the Qt tray to run via gateway (start run + ledger replay + SSE + resume).
- Added gateway run input builder (`gateway/run_input.py`) aligned to `abstractcode/web`.
- Added gateway entrypoint selection (`gateway/templates.py`) defaulting to `basic-agent`.
- Persisted gateway chat messages into the session store for history UI.
- Extended gateway config (`bundle_id`, `flow_id`) and updated docs.

### Tests

- `pytest` (full abstractassistant test suite; 22 passed)
- `pytest tests/basic/test_gateway_events.py tests/basic/test_gateway_adapter.py tests/basic/test_gateway_sse_parser.py tests/basic/test_tool_policy.py` (post-change spot check)
