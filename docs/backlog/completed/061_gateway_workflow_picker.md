# Backlog: Gateway workflow picker for AbstractAssistant

## Summary
Expose gateway bundle/flow selection in the UI so users can run any AbstractFlow workflow from the tray.

## Why
- Gateway‑first assistant should be able to execute specialized workflows, not just the default agent.
- `abstractcode/web` already exposes entrypoint selection; parity reduces surprises.
- Removing hardcoded bundle/flow IDs improves usability and reduces config errors.

## Scope
### In scope
- Fetch bundles/entrypoints from `/api/gateway/bundles`.
- Add a workflow/template selector with sensible defaults and persistence per session.
- Show the selected workflow in the UI and include it in run input data.

### Out of scope
- Workflow authoring or editing from the tray.
- Advanced permissions UI for workflow ACLs.

## Dependencies
- Gateway bundle discovery endpoints.
- Session store for persisting template choices.

## Expected outcomes
- Users can pick and run any gateway workflow from the assistant UI.
- Per‑session workflow selection persists across restarts.

## Full report
### What changed
- Added a workflow dropdown in the tray UI for gateway mode.
- Added per‑session persistence of `bundle_id`/`flow_id` via `GatewaySelectionStore`.
- Added `list_agent_entrypoints(...)` to expose `abstractcode.agent.v1` entrypoints for UI selection.
- Wired workflow selection into gateway run creation and session switching.

### Files touched
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/core/gateway_selection_store.py`
- `abstractassistant/core/llm_manager.py`
- `abstractassistant/gateway/templates.py`
- `abstractassistant/gateway/__init__.py`
- `abstractassistant/tests/basic/test_gateway_selection_store.py`
- `abstractassistant/tests/basic/test_gateway_templates.py`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `05182488-e11b-4dee-91e5-add41c98e910`
