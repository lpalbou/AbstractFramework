## Summary
- Fix fresh-launch macOS tray click behavior where ready-state clicks can fail to open the assistant window.

## Why
- On macOS, `QSystemTrayIcon` can open the context menu path without reliably emitting `activated`, so the ready-state open action is skipped.
- This breaks the required UX contract: one click in ready state must always show the app.

## Scope
- Add a darwin-specific fallback path in `abstractassistant/app.py` that handles tray menu show events when activation is missing.
- Keep existing state rules unchanged for running/speaking.
- Add automated regression tests for the fallback behavior.

## Out of Scope
- Rewriting the entire tray architecture.
- Changing running/speaking interaction semantics.
- Gateway or workflow execution behavior changes.

## Dependencies
- `abstractassistant/app.py`
- `abstractassistant/tests/basic/`
- Qt tray behavior on macOS (`QSystemTrayIcon` + context menu lifecycle)

## Expected Outcomes
- Fresh-launch tray click opens the app in ready state, even when `activated` is not emitted.
- No duplicate click handling when `activated` is emitted.
- Running/speaking rules stay intact.

## Plan
- Add activation timestamp tracking and menu-show fallback.
- Restrict fallback to ready state only.
- Add regression tests and execute targeted test suite.

## Report
- **Root cause**: on macOS, the tray icon can enter the context-menu lifecycle without reliably emitting `QSystemTrayIcon.activated` on the first click. When this happens, the ready-state single-click handler is never called, so the app does not open.
- **Implementation**:
  - Added `self._tray_last_activation_ts` to track when activation was actually emitted.
  - Added `self._qt_context_menu` + `_qt_on_context_menu_show()` in `abstractassistant/app.py`.
  - Wired the darwin context menu `aboutToShow` signal to `_qt_on_context_menu_show()`.
  - In fallback handler:
    - Hide the empty menu immediately.
    - If `activated` fired recently, do nothing (duplicate guard).
    - If state is not `ready`, do nothing (preserves running/speaking rules).
    - If state is `ready` and activation is missing, call `show_chat_bubble()`.
- **Semantics preserved**:
  - Running and speaking behavior is unchanged.
  - Double-click logic for non-ready states remains timestamp-based and untouched.
  - Ready-state UX is hardened so fresh-launch click opens the app even when activation is swallowed by macOS tray/menu behavior.

## Tests
- `pytest -q abstractassistant/tests/basic/test_tray_context_menu_fallback.py` → **3 passed**
- `pytest -q abstractassistant/tests/basic/test_gateway_events.py abstractassistant/tests/basic/test_tray_context_menu_fallback.py` → **8 passed**
