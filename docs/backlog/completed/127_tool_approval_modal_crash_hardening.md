## Summary
- Harden tool-approval flow against macOS crash/exit behavior by replacing native message-box approval with a custom Qt dialog and avoiding modal teardown races.

## Why
- Approving/denying tool requests can trigger a fatal segmentation fault that terminates AbstractAssistant.
- Root requirement: accept/deny must never close the application process.

## Scope
- Remove recent modal visibility workaround requested to revert.
- Replace tool approval `QMessageBox` with custom `QDialog`.
- Defer tool-execution voice announcement one event-loop tick after approval.

## Out of Scope
- Full redesign of run approval semantics.
- Gateway-side changes.

## Dependencies
- `abstractassistant/abstractassistant/ui/qt_bubble.py`

## Expected Outcomes
- Approve/deny tool prompts no longer crash/terminate app.
- Approval UX remains visible and explicit on macOS.

## Plan
- Build custom top-level stay-on-top `QDialog` for tool approval.
- Keep allowlist checkbox + explicit approve/deny buttons.
- Resume run after dialog decision.
- Re-run assistant regression tests.

## Report
- **User-requested revert applied**:
  - Removed the prior “restore bubble visibility after modal close” workaround in approval/input modal paths.
- **Crash hardening implementation**:
  - Replaced tool approval native `QMessageBox` with a custom top-level `QDialog` using explicit Approve/Deny buttons and allowlist checkbox.
  - Kept dialog activation/top-most behavior (`ApplicationModal`, `WindowStaysOnTopHint`, foreground activation) for macOS visibility.
  - Deferred `_announce_tool_execution(...)` via `QTimer.singleShot(0, ...)` after approval to avoid immediate modal teardown + TTS callback races.
- **Intent**:
  - Reduce native dialog bridge instability and remove race window where approving can lead to process termination (segfault).

## Tests
- `python -m py_compile abstractassistant/abstractassistant/ui/qt_bubble.py` → **OK**
- `pytest -q abstractassistant/tests/basic/test_gateway_events.py abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py abstractassistant/tests/basic/test_full_voice_start_button_mode.py` → **15 passed**
