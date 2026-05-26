# Backlog: Show Tool Approval When Viewing Run History

## Summary
- Ensure tool-approval waits are visible when inspecting a persisted run.

## Why
- Run history view was relying on run summary wait fields, which omit tool-approval details in child runs.
- This hid approvals even though the ledger contains them.

## Scope
- In scope:
  - Derive tool-approval waiting info from ledger events when viewing a run.
- Out of scope:
  - Backend changes to run summary payloads.

## Expected outcomes
- Tool approval panel appears while viewing a run with pending child-run approval.

## Implementation Report
- Added ledger-derived tool-approval extraction for inspected runs.
- Prioritized approval wait info over summary wait fields when viewing history.
- Added approval fallback using latest waiting step when global waiting info is missing.
- Resume commands now accept explicit run_id + wait_key for history approvals.
- Approve All now targets the root run id so child approvals auto-approve.

## Tests
- `npm run build` (abstractflow/web/frontend)

