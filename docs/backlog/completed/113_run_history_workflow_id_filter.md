# Backlog: Run History Workflow-ID Filtering

## Summary
- Query the gateway with workflow_id filters so parent runs are not dropped by global limits.

## Why
- The run list was capped globally, hiding older parent runs even when the correct flow was loaded.

## Scope
- In scope:
  - Compute workflow_id candidates from flow name/id and query `/runs` with `workflow_id`.
  - Deduplicate results by run id.
- Out of scope:
  - Server-side pagination.

## Expected outcomes
- Root runs for a loaded flow always appear in Run History.

## Implementation Report
- Added workflow_id candidate generation using flow name/id (bundle-id style).
- Query `/runs` by workflow_id with root_only=true and merge results.
- Added fallback to global root-run list filtered by flow id suffix to handle renamed bundles.

## Tests
- `npm run build` (abstractflow/web/frontend)

