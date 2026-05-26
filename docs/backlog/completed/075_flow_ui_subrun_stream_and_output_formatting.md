# Backlog Item: Restore agent subrun observability + output formatting

## Summary
- Stream ledger events for agent/subflow subruns so live cycles are visible again.
- Improve run UI messaging for subworkflow waits.
- Beautify output previews and fully expand Raw JSON by default.

## Reason
- The gateway-first SSE refactor removed live subrun traces, breaking agent-cycle observability.
- Subworkflow waits were shown as generic "waiting" prompts, which is misleading.
- Output rendering should always show the received output in a readable format.

## Scope
### In scope
- Add subrun SSE streaming in the Flow UI and wire trace events to the existing panels.
- Treat subworkflow waits as running (non-interactive) with clearer messaging.
- Ensure output previews always display the received output and pretty-print JSON.
- Expand Raw JSON view by default.

### Out of scope
- Backend/runtime changes to subworkflow semantics.
- UI redesign beyond the execution/run panels.

## Dependencies
- AbstractGateway run ledger stream endpoints.
- AbstractFlow frontend (`useWebSocket`, `RunFlowModal`).

## Expected Outcomes
- Agent cycles (system/prompt/tools/results) are visible live again.
- Execution list avoids misleading "waiting" for agent subruns.
- Output previews are readable and Raw JSON is fully expanded by default.

## Report
### Work completed
- Added subrun ledger streaming in `useWebSocket`, including nested subrun discovery via `subworkflow_update`.
- Reclassified subworkflow waits as running with clearer messaging and agent/subflow trace panels.
- Ensured output previews always render a beautified response, including pretty-printed JSON.
- Expanded Raw JSON view to fully open by default.
- Dedupe on_flow_end completion events to avoid duplicate terminal steps.

### Tests
- `npm run build` (abstractflow/web/frontend)
