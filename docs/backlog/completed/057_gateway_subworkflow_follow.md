# Backlog: Gateway subworkflow follow in AbstractAssistant

## Summary
Ensure `abstractassistant` follows subworkflow runs from the gateway so tool approvals and outputs surface in the UI instead of stalling on parent runs that wait for subruns.

## Why
- Gateway runs for `basic-agent` commonly spawn subworkflows; the parent run waits and the UI never sees tool approvals.
- Users report “pending” and a non‑reopening UI while the child run is waiting for tool execution.
- This breaks the gateway-first promise and blocks core workflows.

## Scope
### In scope
- Detect `subworkflow` wait records and follow the child run ledger.
- Surface tool approval waits from child runs to the UI.
- Keep the parent run context and return to it after the subrun completes.
- Tighten tray click fallback for macOS context menu activation.

### Out of scope
- Changing gateway runner scheduling semantics.
- Altering tool approval policies or auto‑approval defaults.
- UI redesign of the tool approval dialog.

## Dependencies
- `abstractassistant` gateway client (`/api/gateway/runs/*` endpoints).
- Existing gateway wait parsing utilities and session store.

## Expected outcomes
- Tool approval prompts appear even when the parent run is waiting on a subworkflow.
- Runs no longer stall in “pending” with no UI feedback.
- Tray icon reliably reopens the bubble after context‑menu activation on macOS.

## Full report
### What changed
- Added a gateway polling loop that follows subworkflow runs so child-ledger tool waits and outputs surface in the UI.
- Extracted subworkflow run IDs from `wait.details.sub_run_id` or `wait_key` to switch the active run being polled.
- Made the macOS tray context-menu fallback check actual bubble visibility before triggering a show action.

### Files touched
- `abstractassistant/ui/qt_bubble.py` (gateway polling + subworkflow follow)
- `abstractassistant/app.py` (tray context-menu visibility check)

### Tests
- `python -m pytest abstractassistant/tests`

### Results
- Passed: 61
- Skipped: 7
- Warnings: 36 (existing warnings, plus expected `#FALLBACK` for legacy wait locations)

### Notes
- Gateway discovery calls to OpenAI/Anthropic model lists are expected server-side provider discovery, not local direct calls from the client UI.
