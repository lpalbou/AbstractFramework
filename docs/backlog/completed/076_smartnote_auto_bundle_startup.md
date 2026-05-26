# Backlog: SmartNote auto bundle preflight

## Summary
Make SmartNote build and upload its gateway bundle at startup so users can run `smartnote` without manual bundling.

## Why
- Users should not have to run `smartnote bundle` for a production-friendly experience.
- Startup checks should ensure the gateway has the required bundle and flow before ingestion.

## Scope
### In scope
- Add a startup preflight that builds the bundle when needed and uploads it to the gateway.
- Default `smartnote` to launch the tray UI.
- Update SmartNote and root docs to reflect the new single-command flow.
- Update ADR 004 and AGENTS notes to capture the behavior change.

### Out of scope
- Gateway runtime changes.
- New UI features or backend logic changes.

## Dependencies
- Gateway bundle upload endpoint (`/api/gateway/bundles/upload`).
- SmartNote gateway bundle flows.

## Expected outcomes
- `smartnote` runs without manual bundle steps.
- Gateway has the required bundle before runs start.

## Full Report
- **Summary**: Added a SmartNote startup preflight that builds and uploads bundles, updated the CLI to default to tray mode, and refreshed docs/ADR notes to match the single-command UX.
- **Implementation**:
  - Added bundle ensure + gateway upload logic (`smartnote.client.bootstrap`, `smartnote.client.api`, `smartnote.gateway.bundle`).
  - Updated CLI to run the preflight before tray/ingest and default `smartnote` to tray.
  - Updated SmartNote and root docs and the SmartNote specialized workflow doc to remove manual `smartnote bundle` steps.
  - Updated ADR 004 and AGENTS notes for the new startup behavior.
- **Tests**: Not run (not requested).
