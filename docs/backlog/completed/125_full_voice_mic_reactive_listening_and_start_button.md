## Summary
- Add real-time tray listening vibration correlated to live microphone energy and refactor full voice mic control into a start-only button.

## Why
- Listening tray animation is currently synthetic and not correlated to perceived mic energy.
- Full voice UI still carries toggle-state/layout coupling that can leave inconsistent button state and altered window height after stop actions.

## Scope
- Emit mic energy levels from existing `VoiceRecognizer` input stream (no new audio stream).
- Propagate audio levels through assistant voice managers to tray meter path.
- Drive listening tray animation amplitude from live meter.
- Convert full voice mic control from toggle to start-only button.
- Remove voice-mode window size mutation logic.

## Out of Scope
- Changes to gateway STT/TTS endpoints.
- New background audio capture implementations.

## Dependencies
- `abstractvoice/abstractvoice/recognition.py`
- `abstractvoice/abstractvoice/vm/stt_mixin.py`
- `abstractassistant/abstractassistant/core/gateway_voice_manager.py`
- `abstractassistant/abstractassistant/core/tts_manager.py`
- `abstractassistant/abstractassistant/ui/qt_bubble.py`
- `abstractassistant/abstractassistant/app.py`
- `abstractassistant/abstractassistant/utils/icon_generator.py`

## Expected Outcomes
- Tray listening icon vibrates in real time with live mic energy.
- Full voice mic button is a one-way start action (no sticky toggle state).
- Voice mode no longer mutates bubble window height.

## Plan
- Add normalized mic-level callback in recognizer loop.
- Thread callback through assistant voice manager interfaces.
- Feed listening statuses with live meter to icon animation.
- Refactor full voice button to start-only behavior.
- Add regression tests and run focused suites.

## Report
- **Real-time listening meter (no extra stream)**:
  - Added `audio_level_callback` support to `abstractvoice.recognition.VoiceRecognizer`.
  - Mic energy is emitted directly from the existing `InputStream.read(...)` loop (same capture path as VAD/STT).
  - Added smoothing + normalization in recognizer (`_emit_audio_level`) to provide stable 0..1 levels.
  - While listening is paused, level emits `0.0` so listening icon settles immediately.
- **Propagation into assistant voice stack**:
  - `GatewayVoiceManager.listen(...)` now accepts `on_audio_level` and forwards recognizer mic levels.
  - Local `VoiceManager.listen(...)` wrapper accepts `on_audio_level` and passes it to AbstractVoice (with compatibility fallback for older signatures).
  - `abstractvoice.vm.stt_mixin.listen(...)` now accepts and forwards `on_audio_level` into `VoiceRecognizer`.
- **Listening icon now meter-driven**:
  - `QtChatBubble` passes `_handle_voice_meter` into voice `listen(...)`.
  - `AbstractAssistantApp` keeps voice meter active for `listening`/`listening_paused` states (not only `speaking`).
  - `IconGenerator` listening pulse now scales with live meter rather than fixed synthetic pulse.
- **Mic button refactor (start-only, no toggle coupling)**:
  - `FullVoiceToggle` converted to a start button (`triggered` signal), no checkable toggle state.
  - Button click only starts full voice mode; when already running, clicking hides the app (no stop/toggle semantics).
  - Full voice active state is now derived from `_full_voice_running`, not button selected state.
- **Window-size stability**:
  - Removed voice-mode `setFixedSize(..., 120)` logic from `_set_voice_ui_mode`.
  - Voice-mode transitions no longer mutate bubble height.

## Tests
- `pytest -q abstractassistant/tests/basic/test_gateway_events.py abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py abstractassistant/tests/basic/test_full_voice_start_button_mode.py` → **15 passed**
- `pytest -q abstractvoice/tests/test_recognition_audio_level_callback.py abstractvoice/tests/test_stt_mixin_audio_level_forwarding.py abstractvoice/tests/test_voice_recognizer_ptt_profile.py abstractvoice/tests/test_full_mode_echo_gate.py` → **5 passed**
- `python -m py_compile abstractassistant/abstractassistant/app.py abstractassistant/abstractassistant/ui/qt_bubble.py abstractassistant/abstractassistant/core/gateway_voice_manager.py abstractassistant/abstractassistant/core/tts_manager.py abstractassistant/abstractassistant/utils/icon_generator.py abstractvoice/abstractvoice/recognition.py abstractvoice/abstractvoice/vm/stt_mixin.py` → **OK**
