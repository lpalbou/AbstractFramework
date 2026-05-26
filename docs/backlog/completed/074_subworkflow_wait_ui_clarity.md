# Backlog Item: Clarify subworkflow waits in Flow UI

## Summary
- Prevent subworkflow waits from showing a user-input prompt.
- Make it explicit when the agent subworkflow is still running.

## Reason
- Subworkflow waits are non-interactive; showing “Please respond” is misleading.
- Improves UX clarity for agent nodes that execute as child runs.

## Scope
### In scope
- Treat `wait_reason=subworkflow` as non-interactive in the live Flow UI.
- Keep run history/timeline intact while removing misleading prompts.

### Out of scope
- Streaming child-run ledger events or surfacing child prompts in real time.
- Changes to runtime wait semantics.

## Dependencies
- AbstractFlow frontend (`RunFlowModal`, `useWebSocket`) and gateway SSE wait mapping.

## Expected Outcomes
- Live runs waiting on subworkflows no longer show “Please respond.”
- The UI displays a clear “waiting on subworkflow” message instead.

## Report
### Work completed
- Suppressed interactive waiting UI for `wait_reason=subworkflow` in live runs.
- Adjusted waiting step rendering to avoid default prompts for subworkflow waits.
- Added a non-interactive “waiting on subworkflow” message in the run details panel.

### Tests
- `npm run build` (abstractflow/web/frontend)
