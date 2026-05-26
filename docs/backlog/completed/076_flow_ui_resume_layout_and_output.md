# Backlog Item: Flow UI resume cleanup + agent layout + output polish

## Summary
- Suppress ledger "resume" artifacts from Flow UI steps.
- Improve agent detail layout to prioritize live cycles.
- Restore on_flow_start inputs and beautify outputs with JSON highlighting.

## Reason
- Resume ledger records are internal bookkeeping and misleading as user-visible steps.
- Agent observability should emphasize cycle traces over secondary panels.
- Output previews should be readable and show actual answers by default.

## Scope
### In scope
- Filter resume records in ledger-to-UI mapping.
- Adjust RunFlowModal layout to allocate space to Agent cycles and move duration to header.
- Pretty-print and syntax-highlight JSON previews; expand Raw JSON by default.
- Reinstate On Flow Start input visibility via input_data fetch fallback.

### Out of scope
- Backend/runtime changes to ledger semantics.
- Full migration of UI output rendering to shared abstractuic components.

## Dependencies
- AbstractGateway run input_data endpoint.
- AbstractFlow frontend components and styles.

## Expected Outcomes
- No "resumed" steps shown for normal agent runs.
- Agent cycles dominate the right panel with clean, compact metadata.
- On Flow Start variables visible again.
- JSON previews are beautified with highlighting.

## Report
### Work completed
- Filtered ledger resume records from Flow UI step rendering.
- Added sub-run input_data fetch and synthetic On Flow Start step fallback.
- Moved duration to header badges and removed the details duration row.
- Gave agent cycles panel flex priority in the details layout.
- Switched JSON previews to the JsonViewer with syntax highlighting and full expansion.
- Added output preview fallbacks for nested output/result fields (including On Flow End).

### Tests
- `npm run build` (abstractflow/web/frontend)
