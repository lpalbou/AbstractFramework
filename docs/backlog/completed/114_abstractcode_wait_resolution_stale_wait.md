# Backlog: Clear Stale Tool Approvals in AbstractCode Web

## Summary
- Fix AbstractCode Web’s wait resolution so tool approvals clear after a resume/completion.

## Why
- The UI was holding onto an old subrun wait even after approval was accepted in another client.

## Scope
- In scope:
  - Use the latest subrun record to decide if a wait is still active.
  - Add unit tests for the wait resolution behavior.
- Out of scope:
  - Backend changes to wait semantics.

## Expected outcomes
- Approvals disappear in AbstractCode Web once another client resumes the wait.

## Implementation Report
- Wait resolution now uses the latest subrun record and clears waits after resume/completion.
- Added unit tests covering stale-wait clearing and active-wait retention.

## Tests
- `npm run test -- src/lib/wait_resolution.test.ts` (abstractcode/web)

