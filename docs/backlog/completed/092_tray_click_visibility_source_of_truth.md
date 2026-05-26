## Summary
- Use actual bubble visibility as the only source of truth for tray click behavior.
- Prevent stale voice state from blocking UI open after a stop.

## Why
- After stopping speech, the app could refuse to reopen due to stale voice state.
- Visibility should be driven by `isVisible()` rather than inferred click state.

## Scope
- Gate voice actions on actual voice activity (`is_speaking`/`is_paused`).
- Toggle show/hide using `_bubble_is_visible()` only.

## Out of Scope
- Changing run‑active blocking behavior.
- Tray animation changes.

## Dependencies
- `AbstractAssistantApp` tray click handlers.

## Expected Outcomes
- Single/double click uses real visibility to show/hide.
- Stopping TTS no longer blocks reopening the UI.

## Plan
- Update single/double click handlers to use actual state.
- Run tests.

## Report
- **Visibility source of truth**: single/double click now toggles the bubble strictly via `_bubble_is_visible()` (Qt `isVisible()`), avoiding inferred click state for UI visibility.
- **Voice gating**: tray click handlers only short‑circuit when voice is truly active (`is_speaking`/`is_paused`), with a safe fallback to `get_state()` so stale flags no longer block reopening.

## Tests
- `python -m pytest abstractassistant`
