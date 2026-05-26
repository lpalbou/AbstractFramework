# Backlog: Gateway run follow streaming + UI status correctness

## Summary
Replace the gateway polling loop with SSE-driven streaming + subworkflow follow, and keep UI status correct until the run truly completes.

## Why
- Polling every 250ms spams the gateway and wastes CPU/network.
- Parent runs can wait on subruns; waits and tool approvals must surface without stalling the UI.
- UI should not show “ready” while a run is still executing.

## Scope
### In scope
- Stream ledgers via SSE with reconnect/backoff (no tight polling).
- Follow subworkflow run ledgers and surface waits/tool approvals.
- Distinguish intermediate vs final assistant messages to avoid premature “ready”.

### Out of scope
- Changing gateway runtime scheduling or workflow semantics.
- Redesigning the chat UI or tool approval UX.
- Adding new gateway endpoints.

## Dependencies
- Gateway ledger + stream endpoints (`/api/gateway/runs/*`).
- Existing gateway event adapter and session store.

## Expected outcomes
- No rapid-fire polling in the gateway logs.
- Tool approvals appear for subworkflow waits.
- Tray/icon state stays “working” until completion, then switches to “ready”.

## Full report
### What changed
- Replaced the tight polling loop with SSE streaming + reconnect backoff and subworkflow follow logic.
- Added run replay + follow logic to switch into child runs when a `subworkflow` wait appears.
- Marked gateway assistant messages as final vs intermediate to prevent premature “ready” states.

### Files touched
- `abstractassistant/gateway/client.py`
- `abstractassistant/gateway/adapter.py`
- `abstractassistant/ui/qt_bubble.py`

### Tests
- `python -m pytest abstractassistant/tests`

### Results
- Passed: 61
- Skipped: 7
- Warnings: 36 (existing warnings, plus expected `#FALLBACK` for legacy wait locations)
