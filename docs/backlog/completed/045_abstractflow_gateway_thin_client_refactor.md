# Backlog Item 045: AbstractFlow gateway-first thin client refactor (investigation)

## Summary
Investigate feasibility of refactoring AbstractFlow into a gateway-first thin client, removing its dedicated backend server while preserving authoring and execution UX.

## Reason
A gateway-first approach could align all UIs on a single durable API surface and simplify operations, but it requires replacing local backend responsibilities (flow storage, execution streaming, and token handling).

## Scope
### In scope
- Map current AbstractFlow backend endpoints to gateway equivalents.
- Identify missing gateway endpoints for VisualFlow CRUD/compile/publish.
- Explain concrete transport/UI changes required (WebSocket → ledger stream).
- Provide phased plan options and risks.

### Out of scope
- Code changes or implementation.
- Benchmarks or performance testing.

## Dependencies
- AbstractGateway HTTP API and security model.
- VisualFlow compilation/bundling pipeline.
- UI reliance on `/api/*` endpoints and WebSocket execution.

## Expected Outcomes
- Feasibility assessment with concrete transport/UI implications.
- Phased plan outline for a gateway-first thin client.

## Full Report
- **Feasibility**: Possible but large refactor. The UI currently relies on a WebSocket control + event stream (`/api/ws/{flow_id}`) and backend-owned flow storage/execution. Gateway provides durable runs and ledger replay/streaming but does not yet expose VisualFlow CRUD/compile/publish endpoints.
- **Transport/UI rewrite**: Replace WebSocket with HTTP control (`/api/gateway/commands`) and SSE ledger streaming (`/api/gateway/runs/{run_id}/ledger/stream`). Build a client-side adapter (or new gateway endpoint) to translate ledger records into the existing `ExecutionEvent` shapes (node_start/node_complete/flow_waiting/trace_update).
- **Security**: The current backend stores gateway tokens server-side and never returns them to the browser; thin client needs a browser-safe auth model (scoped tokens or session auth).
- **Phased approach**:
  1) Add gateway endpoints for VisualFlow CRUD + server-side bundle compile/publish.
  2) Implement gateway-mode UI with ledger stream + command-based controls.
  3) Run dual-mode until feature parity is validated; deprecate backend later.
- **Tests**: Not run (investigation only; no code changes).
