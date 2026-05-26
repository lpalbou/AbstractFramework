# Backlog: SmartNote gateway integration

## Summary
Rewire SmartNote to run as an AbstractGateway bundle with SmartNote tools, removing the standalone SmartNote server.

## Why
- The tray client must connect to the existing gateway (no separate backend).
- Gateway runs provide durability, observability, and shared auth/security controls.

## Scope
### In scope
- Replace SmartNote server usage with gateway flows + tool execution.
- Add SmartNote tools to the gateway default toolset (opt-in via env).
- Update tray client and CLI to call AbstractGateway.
- Update SmartNote and framework docs + ADRs.

### Out of scope
- New UI features beyond gateway connectivity.
- VisualFlow editor changes.

## Dependencies
- AbstractGateway running with bundle mode.
- `abstractruntime[abstractcore]` and SmartNote installed in the gateway environment.

## Expected outcomes
- SmartNote tray and CLI start runs on AbstractGateway.
- No standalone SmartNote server process is required.
- Documentation reflects gateway-first behavior.

## Full Report
- **Summary**: Replaced the SmartNote server with a gateway-first bundle + tools integration and rewired the tray/CLI to call AbstractGateway.
- **Implementation**:
  - Added SmartNote gateway tools (`smartnote_ingest`, `smartnote_list_notes`, `smartnote_get_note`, `smartnote_search_notes`, `smartnote_list_topics`, `smartnote_topic_detail`) and their supporting ingest/query logic.
  - Created VisualFlow JSON entrypoints and a bundle builder (`smartnote bundle`) that packages the flows into a `.flow` bundle.
  - Updated the tray client and CLI to call AbstractGateway and upload attachments via `/api/gateway/attachments/upload`.
  - Removed the SmartNote FastAPI server/runtime modules and dropped server dependencies from `pyproject.toml`.
  - Enabled SmartNote tools in the gateway default toolset behind `SMARTNOTE_ENABLE_GATEWAY_TOOLS` and auto-approved these tools when enabled.
  - Updated SmartNote docs, framework docs, ADR 004, and AGENTS notes to reflect the gateway-first architecture.
- **Tests**: Not run (not requested).
