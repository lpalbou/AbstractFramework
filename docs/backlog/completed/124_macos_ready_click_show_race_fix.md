## Summary
- Fix macOS ready-state tray click race where click handlers run and `show()` logs appear, but the chat bubble is still not visible.

## Why
- The first tray click can execute in the same event cycle as tray/menu focus transitions, causing the bubble reveal to be lost visually.
- Logs confirmed click routing was correct (`state=ready`, `Qt chat bubble shown`) but UX still failed.

## Scope
- Defer ready-state show action to next Qt event loop tick on macOS.
- Reassert bubble visibility + on-screen clamping when showing.
- Preserve existing listening/speaking/running click semantics.

## Out of Scope
- Broad tray architecture rewrite.
- Changing non-macOS click handling.

## Dependencies
- `abstractassistant/abstractassistant/app.py`
- `abstractassistant/abstractassistant/ui/qt_bubble.py`
- Existing tray fallback and listening-state tests

## Expected Outcomes
- Fresh-launch `ready` single click visibly opens bubble reliably.
- No regression of listening/speaking controls.

## Plan
- Add deferred ready-click helper in app.
- Use helper from Qt tray ready branch on darwin.
- Reassert visibility in bubble manager show path.
- Run focused regression tests + syntax compile.

## Report
- **Diagnosis**:
  - Your log showed `Click detected`, `state=ready`, and `Qt chat bubble shown`, proving click routing and show invocation were working.
  - The failure is a visibility race in the tray/UI event cycle, not state dispatch.
- **Implementation**:
  - Added `AbstractAssistantApp._defer_ready_click_show()` and used it for darwin ready-state clicks in `_qt_on_tray_activated(...)`.
  - Added bubble on-screen clamping (`_ensure_window_within_screen`) in `show_chat_bubble(...)`.
  - Hardened `QtBubbleManager.show()` with:
    - pre-show on-screen clamping
    - one-tick visibility reassert (`QTimer.singleShot(0, ...)`) that re-shows/raises/activates if needed.
- **Behavioral guarantees**:
  - No change to listening/speaking/running semantics.
  - Change is targeted to reliable visual opening in ready state on macOS.

## Tests
- `pytest -q tests/basic/test_tray_context_menu_fallback.py tests/basic/test_tray_listening_state_clicks.py tests/basic/test_tool_announcement_dedup.py` → **7 passed**
- `python -m py_compile abstractassistant/app.py abstractassistant/ui/qt_bubble.py` → **OK**
