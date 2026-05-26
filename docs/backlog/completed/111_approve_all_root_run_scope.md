# Backlog: Approve All Applies to Root Run + Children

## Summary
- Ensure Approve All applies to the main run and all attached child runs, including future subruns.

## Why
- Approvals in child runs were not auto-approved if they did not share the UI session id.

## Scope
- In scope:
  - Track run root id and apply auto-approval to all child runs.
  - Keep existing session-based auto-approval.
- Out of scope:
  - Backend changes to approval policy.

## Expected outcomes
- Approve All applies to the main flow and any attached subruns (present or future).

## Implementation Report
- Added root-run auto-approve tracking and child run mapping.
- Approve All now sets auto-approval for both session id and root run id.

## Tests
- `npm run build` (abstractflow/web/frontend)

