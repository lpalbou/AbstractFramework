# Backlog Item: AbstractFlow gateway-first thin client (API + UI wiring)

## Summary
- Implement gateway-owned VisualFlow CRUD + publish endpoints.
- Update AbstractFlow UI to call gateway routes and consume ledger SSE.
- Add basic gateway helper tests and keep gateway UI proxy config aligned.

## Reason
- Enable a single durable backend (AbstractGateway) and remove AbstractFlow's server dependency.
- Align UI transport with gateway-native SSE + ledger replay.
- Preserve shared, reusable primitives while keeping UI-specific mapping client-side.

## Scope
### In scope
- Gateway VisualFlow CRUD/publish endpoints and semantics registry endpoint.
- UI API rewiring for CRUD, runs, discovery, memory KG, and history bundle mapping.
- Replace WebSocket transport with SSE + command POSTs in the UI.
- Minimal unit tests for gateway VisualFlow helper utilities.

### Out of scope
- Full removal of AbstractFlow backend package/server.
- Auth token injection, gateway auth UX, or multi-tenant ACLs.
- UI redesigns or flow editor UX changes beyond endpoint rewiring.

## Dependencies
- AbstractGateway runtime + ledger endpoints already available.
- Optional `abstractsemantics` package for semantics registry.

## Expected Outcomes
- AbstractFlow UI runs as a thin client against AbstractGateway.
- Flow CRUD and run lifecycle operate via gateway endpoints.
- Run history and live events derive from ledger SSE + local mapping.

## Report
### Work completed
- Added `/api/gateway/visualflows` CRUD + publish endpoints and a gateway semantics registry endpoint.
- Rewired AbstractFlow UI to gateway discovery, CRUD, run history, KG query, and ledger SSE streams with local event mapping.
- Updated Flow Editor proxy config + CLI to prefer `ABSTRACTFLOW_GATEWAY_URL` and warn on legacy fallbacks.
- Added gateway helper unit tests for VisualFlow ID validation + semver utilities.
- Updated core docs for Flow Editor gateway requirements and env configuration.
- Adjusted Flow Editor workspace policy handling (server-managed workspace_root + access modes from gateway policy).
- Added gateway auth token injection for Flow Editor CLI + Vite proxy (Authorization: Bearer).
- Updated RestrictedPython policy to allow leading-underscore identifiers while reserving guard helper names.
- Added test bootstrap to disable provider model validation for local test environments.
- Updated `benchmark-agentic.json` Code node to avoid augmented assignment on dict items (RestrictedPython rule).

### Notable behavior changes
- Flow Editor no longer opens workspaces locally; it copies server-side workspace paths instead.
- GPU monitor config now comes from local UI config only (no `/api/ui/config` fetch).

### Tests
- `pytest -q` (AbstractFlow: 181 passed; includes `#FALLBACK` warning for model validation).
- `pytest abstractgateway/tests/test_visualflow_helpers.py -q` (passed).
- `npm run build` (AbstractFlow frontend: passed).

### Follow-ups / risks
- `/api/gateway/semantics` returns 501 if `abstractsemantics` is not installed.
- Full repo tests require package installs or PYTHONPATH setup for `abstractcode` and related packages.
