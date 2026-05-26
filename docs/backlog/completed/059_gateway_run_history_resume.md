# Backlog: Gateway run history + resume in AbstractAssistant

## Summary
Add gateway run history APIs to the Python client and rehydrate sessions so the tray UI can reattach to durable runs after restart.

## Why
- The gateway is the source of truth for durable runs; the assistant should not lose state after a restart.
- Users expect in‑flight runs and tool waits to be visible even if the UI closes.
- `abstractcode/web` already supports run history bundles and list‑runs; parity reduces surprises.

## Scope
### In scope
- Add `list_runs(...)` and `get_run_history_bundle(...)` to the Python gateway client.
- On startup, detect the last active run for the current session and reattach to its ledger stream.
- Seed message history from the history bundle (root + subruns) and dedupe tool cards.
- Display a clear “resumed” status in the UI when reattached.

### Out of scope
- Cross‑device session synchronization.
- UI redesign of sessions/history.
- Changes to gateway backend APIs.

## Dependencies
- Gateway endpoints: `/api/gateway/runs`, `/api/gateway/runs/{id}/history_bundle`.
- Existing session store + gateway event adapter.

## Expected outcomes
- Closing/reopening the assistant does not lose in‑flight run progress.
- Tool approvals surface after reattach without manual restarts.
- Message history matches gateway ledger history.

## Full report
### What changed
- Added a history bundle fetch to the gateway client and a seeding utility that mirrors the web client.
- Added gateway run reattach on startup, including stream follow and history seeding.
- Distinguished intermediate vs final outputs so the tray state stays “working” until completion.

### Files touched
- `abstractassistant/gateway/client.py`
- `abstractassistant/gateway/history_seed.py`
- `abstractassistant/core/llm_manager.py`
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/tests/basic/test_gateway_history_seed.py`

### Tests
- `python -m pytest abstractassistant/tests`

### Results
- Passed: 64
- Skipped: 7
- Warnings: 36 (existing warnings, plus expected `#FALLBACK` for legacy wait locations)
