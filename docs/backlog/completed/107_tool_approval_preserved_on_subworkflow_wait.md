# Backlog: Preserve Tool Approval Waits During Subworkflow Waits

## Summary
- Prevent subworkflow wait events from clearing an active tool-approval prompt.

## Why
- Runs can be blocked on tool approval in a child run while parent runs emit subworkflow waits.
- The UI was clearing approval state when it saw a subworkflow wait, hiding the approval prompt.

## Scope
- In scope:
  - Keep tool-approval waiting state even when subworkflow wait events arrive.
- Out of scope:
  - Changes to backend wait semantics.

## Expected outcomes
- Tool approval prompts remain visible even if parent runs are waiting on subflows.

## Implementation Report
- Guarded subworkflow wait handling so it does not clear an active tool-approval wait.
- Ensured the UI keeps `isWaiting` when the current wait is tool approval.

## Tests
- `npm run build` (abstractflow/web/frontend)

