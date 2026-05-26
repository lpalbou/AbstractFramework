# Backlog: Toolbar Duplicate Button

## Summary
- Add a Duplicate button in the toolbar before the New button.

## Why
- Provide a one-click way to clone the current flow without opening the library.

## Scope
- In scope:
  - Toolbar button placement and handler for duplicating the current flow.
- Out of scope:
  - Changes to FlowLibrary duplicate behavior.
  - Additional confirmation dialogs.

## Dependencies
- Existing VisualFlow create endpoint (`POST /api/gateway/visualflows`).

## Expected outcomes
- A visible Duplicate button appears before New.
- Clicking Duplicate creates a copy and loads it in the editor.

## Implementation Report
- Added a toolbar Duplicate button placed before New.
- Duplicates the current editor flow (including unsaved changes) and loads the new flow.
- Refreshes the flow list and surfaces success/failure toasts.

## Tests
- `npm run build` (abstractflow/web/frontend)

