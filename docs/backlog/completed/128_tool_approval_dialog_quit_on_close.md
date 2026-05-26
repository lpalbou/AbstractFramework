## Summary
- Prevent the tray app from quitting when the tool-approval dialog closes.

## Why
- Accepting/denying tool approvals is closing the entire application instead of just the dialog.
- A tray app should remain alive even when no windows are visible.

## Scope
- Ensure the Qt application does not quit when the last window closes.
- Harden tool-approval and ask-user dialogs against quit-on-close behavior.

## Out of Scope
- Gateway-side changes.
- Approval workflow redesign.

## Dependencies
- `abstractassistant/abstractassistant/app.py`
- `abstractassistant/abstractassistant/ui/qt_bubble.py`

## Expected Outcomes
- Closing tool-approval dialogs no longer terminates AbstractAssistant.
- Tray app continues running with no visible windows.

## Plan
- Disable `quitOnLastWindowClosed` for the Qt app.
- Explicitly mark approval/input dialogs as not triggering app quit.
- Run assistant regression tests.

## Report
- **App quit guard**: set `QApplication.setQuitOnLastWindowClosed(False)` so the tray app stays alive when the last window (e.g., approval dialog) closes.
- **Dialog defense-in-depth**: tool-approval and ask-user dialogs set `WA_QuitOnClose=False` to avoid triggering app quit from top-level dialog close paths.
- **Intent**: approving/denying should close only the dialog; the process remains running and ready for tray re-open.

## Tests
- `python -m py_compile abstractassistant/abstractassistant/app.py abstractassistant/abstractassistant/ui/qt_bubble.py` → **OK**
- `pytest -q abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py abstractassistant/tests/basic/test_full_voice_start_button_mode.py` → **10 passed**
