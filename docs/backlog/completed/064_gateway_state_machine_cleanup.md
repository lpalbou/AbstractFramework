# Backlog: Gateway run state machine + completion guarantees

## Summary
Introduce a clean run state machine so tray status reflects real run progress and always presents a final response or an explicit completion notice.

## Why
- Users reported “ready” while runs were still active and no visible output.
- Status transitions were scattered across UI callbacks, creating race conditions.
- A single authoritative state machine makes the UX robust and predictable.

## Scope
### In scope
- Define explicit run states (idle, running, waiting, executing, speaking, completed, error).
- Ensure “final” outputs always render (or show a `#FALLBACK` completion message when missing).
- Centralize tray icon updates to the state machine.

### Out of scope
- Major UI redesign.
- Changing gateway run semantics.

## Dependencies
- Gateway event adapter (final vs intermediate messages).
- Tray icon animation controller.

## Expected outcomes
- Tray icon state always matches run state.
- Users always see or hear a final response.

## Full report
### What changed
- Added a dedicated run state machine and routed gateway/local run status updates through it.
- Centralized tray icon updates so only the state machine drives icon state.
- Added a fallback completion message when a run completes without a final assistant output.

### Files touched
- `abstractassistant/ui/run_state.py`
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/app.py`
- `abstractassistant/docs/architecture.md`
- `abstractassistant/tests/basic/test_run_state_machine.py`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E (OpenAI / gpt-5-mini) on `http://127.0.0.1:8081` (run id `9a5bd5ae-ea36-46aa-b198-cd429e148b8c`, model `gpt-5-mini-2025-08-07`)

### Results
- Passed: 68
- Skipped: 7
- Warnings: 36 (existing warnings)
