## Task
Add a Follow Up action in the run modal and rename Run Again to New Run.

## Summary
Introduce a Follow Up button that returns to the preflight screen while keeping
the current run session context, and rename Run Again to New Run (fresh context).

## Reason
Users need to continue a run's context for follow-up tasks without losing the
prior session state, while still supporting a clean new run option.

## Scope
- Do: add Follow Up and New Run actions, keep Follow Up on the same session,
  reset session context for New Run, and update UI labels.
- Do not: change runtime policy or gateway behavior.

## Dependencies
- None (frontend-only changes).

## Expected Outcomes
- Run modal shows Follow Up after Close.
- New Run resets session context; Follow Up preserves it.

## Full Report
- **Run modal actions**: Added Follow Up button after Close and renamed Run Again
  to New Run in `RunFlowModal`.
- **Follow Up behavior**: Clears run result/events to return to the start screen
  while keeping the stable session id (context continuity). Follow Up now seeds
  `input_data.context.messages` with the prior prompt + last answer so the agent
  can continue the conversation.
- **New Run behavior**: Resets the stable session id (sessionStorage key) and
  clears run state to start a fresh context.
- **Session handling**: Added a `resetSession` helper in `useWebSocket` to drop
  the stable session id and generate a new one on the next run.
