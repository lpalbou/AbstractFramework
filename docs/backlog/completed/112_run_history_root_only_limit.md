# Backlog: Run History Root Runs + Higher Limit

## Summary
- Ensure the Run History modal lists root runs only and fetches more than 50 entries.

## Why
- Parent runs can be buried under subruns; the list was capped at 50 and often missed the root run.

## Scope
- In scope:
  - Request root-only runs from the gateway.
  - Increase list limit for better coverage.
- Out of scope:
  - Server-side pagination.

## Expected outcomes
- The blocking parent run appears in Run History when its workflow is loaded.

## Implementation Report
- Run History now requests root runs only.
- Increased list limit to 500 to avoid missing recent parent runs.

## Tests
- `npm run build` (abstractflow/web/frontend)

