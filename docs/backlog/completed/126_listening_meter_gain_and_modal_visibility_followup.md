## Summary
- Follow-up fixes for full voice UX:
  - make listening tray animation strictly mic-reactive (no synthetic default vibration), with color intensity response
  - prevent approval/input modal closure from unexpectedly hiding the visible assistant bubble

## Why
- Listening icon still appeared to vibrate even during silence, reducing trust in voice-reactive feedback.
- Closing a modal after tool approval could leave the assistant seemingly closed when it was visible before opening the modal.

## Scope
- Remove synthetic baseline oscillation from listening icon dynamics.
- Add volume-based color shift/intensity in listening pulse rendering.
- Preserve bubble visibility state across tool approval and ask-user modal dialogs.
- Remove invalid Qt stylesheet `cursor` property warning noise.

## Out of Scope
- Redesign of approval workflow.
- Gateway run/state machine changes.

## Dependencies
- `abstractassistant/abstractassistant/utils/icon_generator.py`
- `abstractassistant/abstractassistant/ui/qt_bubble.py`
- `abstractassistant/abstractassistant/core/tts_manager.py`

## Expected Outcomes
- Listening icon stays mostly stable at silence and reacts clearly to voice volume.
- Approving/closing modal dialogs no longer hides the app when it was visible pre-dialog.
- Debug logs no longer show `Unknown property cursor` from status pill styling.

## Plan
- Tune listening pulse from strict mic meter.
- Add modal pre/post visibility restore guard.
- Remove stylesheet cursor property and rely on `setCursor(...)`.
- Run focused assistant + abstractvoice regression tests.

## Report
- **Listening icon dynamics**:
  - Removed synthetic baseline pulse from listening mode.
  - Listening pulse amplitude now maps directly to live mic meter level.
  - Added volume-based color shift (toward blue) and brightness scaling with voice intensity.
  - `listening_paused` is kept visually calm and non-reactive.
- **Modal visibility fix**:
  - In `_handle_tool_request_inner(...)` and `_handle_ask_user_inner(...)`, capture `bubble_was_visible` before opening modal.
  - After modal closes, re-show/raise/activate the bubble only if it was visible beforehand.
  - This prevents modal lifecycle from inadvertently hiding the user-visible assistant window.
- **Qt warning cleanup**:
  - Removed unsupported stylesheet `cursor` property from status pill style.
  - Cursor behavior remains controlled via `setCursor(...)` (no visual regression).
- **Fallback visibility note**:
  - Added explicit `#FALLBACK` warnings where meter callback signature support is missing in older voice backends.

## Tests
- `pytest -q abstractassistant/tests/basic/test_gateway_events.py abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py abstractassistant/tests/basic/test_full_voice_start_button_mode.py` → **15 passed**
- `pytest -q abstractvoice/tests/test_recognition_audio_level_callback.py abstractvoice/tests/test_stt_mixin_audio_level_forwarding.py` → **3 passed**
- `python -m py_compile abstractassistant/abstractassistant/ui/qt_bubble.py abstractassistant/abstractassistant/core/tts_manager.py abstractassistant/abstractassistant/utils/icon_generator.py` → **OK**
