## Summary
- Add an idle watchdog for gateway ledger streaming to prevent stuck runs.
- Surface a clear “what’s running” summary when attaching or starting runs.
- Guard auto-reattach against stale runs with no recent updates.

## Why
- SSE streams can stall without emitting completion, leaving the UI “running.”
- Users need to see which run is active without opening the UI.
- Reattaching to stale runs should not block the assistant at startup.

## Scope
- Add idle timeout + status polling in the gateway stream loop.
- Emit run activity summaries from the gateway worker.
- Handle run activity updates in the Qt bubble and tray tooltip.
- Skip auto-reattach for stale runs.

## Out of Scope
- Gateway backend changes.
- Tool execution semantics or policy changes.

## Dependencies
- GatewayClient SSE streaming implementation.
- GatewayRunController follow loop.
- Qt bubble run activity tracking.

## Expected Outcomes
- Completed runs stop showing as “running” even if SSE stalls.
- Tray tooltip/notifications show what is running.
- Startup does not block on stale runs.

## Plan
- Add idle timeout handling and status polling in the stream loop.
- Emit and consume run activity summaries (status + prompt).
- Add stale-run detection in auto-reattach.
- Run targeted tests.

## Report
- **Idle watchdog**: gateway stream now enforces idle timeouts and polls run status on idle (`#FALLBACK`) to end completed runs.
- **Run activity summary**: gateway worker emits status + prompt summaries (including waiting reason) and the bubble refreshes the tray tooltip immediately.
- **Stale reattach guard**: auto-reattach skips runs with >10 minutes of no updates and clears `last_run_id` to avoid startup lock.

## Tests
- `python -m pytest abstractassistant`
