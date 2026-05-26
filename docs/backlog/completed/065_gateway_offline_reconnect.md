# Backlog: Gateway offline handling + reconnect UX

## Summary
Make gateway connectivity failures explicit and recoverable without restarting the assistant.

## Why
- Network or gateway restarts are common; the UI must recover cleanly.
- Silent failures lead to stuck sessions and distrust in the system.

## Scope
### In scope
- Detect gateway connectivity loss and surface a clear UI status.
- Retry ledger streaming with exponential backoff and user‑visible feedback.
- Provide a manual “Reconnect” action.

### Out of scope
- Offline queuing of user messages.
- Multi‑gateway failover.

## Dependencies
- Gateway client error handling and SSE reconnection logic.
- Tray UI status controls.

## Expected outcomes
- Clear error state when gateway is unreachable.
- Runs resume automatically once the gateway returns.

## Full report
### What changed
- Added offline/reconnecting states to `RunStateMachine` and UI status mapping.
- Emitted offline status when `stream_ledger` fails; reset to thinking on recovery.
- Added **Reconnect gateway** menu action to refresh discovery + reattach runs.
- Mapped offline/reconnecting tray icon state to the “thinking” animation.

### Files touched
- `abstractassistant/gateway/run_controller.py`
- `abstractassistant/ui/gateway_worker.py`
- `abstractassistant/ui/run_state.py`
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/app.py`
- `abstractassistant/tests/basic/test_run_state_machine.py`
- `docs/getting-started.md`
- `docs/faq.md`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `05182488-e11b-4dee-91e5-add41c98e910`
