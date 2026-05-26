# Backlog: AbstractAssistant visibility state cleanup

## Summary
Make chat bubble visibility state reflect the real Qt window state and decouple voice stop from UI show logic.

## Why
- Manual visibility flags drift from actual widget visibility, causing clicks to fail to reopen the app.
- Stopping voice playback should not implicitly open the UI.

## Scope
### In scope
- Replace manual visibility tracking with real Qt `isVisible()` checks.
- Ensure open/close handlers only act on explicit user intent.
- Remove UI auto-open when stopping voice.

### Out of scope
- New UI behaviors or additional tray actions.
- Gateway run lifecycle changes.

## Dependencies
- Existing Qt bubble manager show/hide behavior.
- Tray click handlers in `abstractassistant/app.py`.

## Expected outcomes
- Clicking the tray icon always opens the app when requested.
- Stopping voice does not force the UI to open.
- Visibility checks match actual window state.

## Full Report
- **Summary**: Removed manual visibility flags, tied visibility to the real Qt widget state, and separated voice stop from UI show logic.
- **Implementation**:
  - `AbstractAssistantApp` now queries `bubble.isVisible()` directly and avoids stale flags; showing an already-visible bubble only raises/activates it.
  - Tray double‑click now stops voice without opening the UI, so “stop voice” does not imply “show window”.
  - Visibility logic is centralized in `_bubble_is_visible()` to keep state authoritative and simple.
- **Tests**: `python -m pytest` (fails: 31 collection errors, missing `abstractcode.react_shell`, `abstractcode.fullscreen_ui`, and `create_llm` imports, plus abstractgateway/abstractruntime/abstractvoice collection errors).
