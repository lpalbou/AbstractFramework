## Summary
- Fix gateway cache initialization order to avoid discovery failures.
- Make tool policy defaults resilient when runtime version lacks `ToolApprovalPolicy`.
- Ensure pending waits are rehydrated even when history seeding fails.

## Why
- Missing cache initialization causes gateway discovery to fail at startup.
- Older runtime installs should not disable safe tool defaults.
- Pending waits must surface to unblock runs on reattach.

## Scope
- Initialize gateway cache before tool inventory refresh.
- Add local policy fallback for tool approval defaults.
- Always attempt pending-wait rehydrate after history bundle fetch.
- Add run-summary fallback for waits when ledgers don’t include them.
- Add wait-key heuristic for tool approval detection.

## Out of Scope
- Gateway backend changes.
- Workflow behavior changes.

## Dependencies
- Qt bubble initialization flow.
- Gateway history bundle + run summary endpoints.

## Expected Outcomes
- No `_gateway_cache` attribute errors at startup.
- Tool policy defaults resolve even with older runtime installs.
- Reattached runs surface pending waits consistently.

## Plan
- Reorder cache initialization and tool inventory refresh.
- Add policy fallback + wait detection heuristics.
- Run tests.

## Report
- **Init order**: gateway cache is now initialized before tool inventory refresh, fixing `_gateway_cache` attribute errors during startup discovery.
- **Policy fallback**: if `ToolApprovalPolicy` isn’t available in the installed runtime, the UI falls back to the local policy with a `#FALLBACK` warning.
- **Wait rehydrate**: pending waits are emitted even when history seeding fails, with a run-summary fallback for subruns missing wait records.
- **Approval heuristic**: tool approval waits are recognized by `tool_approval` wait keys when details are missing.

## Tests
- `python -m pytest abstractassistant`
