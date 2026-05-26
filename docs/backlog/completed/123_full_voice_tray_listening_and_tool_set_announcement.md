## Summary
- Improve full voice UX by:
  - announcing unique tool names (set semantics) instead of repeating duplicates
  - introducing a tray `listening` state with explicit click controls
  - making full voice mode tray-first (bubble hidden while active)

## Why
- Voice announcements currently repeat the same tool name when the same tool is called multiple times, which is noisy and confusing.
- Full voice mode still keeps the app visible, which conflicts with a tray-driven interaction model.
- Tray semantics need a dedicated listening state so users can control full voice mode without opening the app.

## Scope
- Deduplicate announced tool names for voice execution announcements.
- Add tray-level listening state handling and listening pause/resume controls.
- Hide the bubble window when full voice mode starts.
- Add regression tests for listening click behavior and tool announcement deduplication.

## Out of Scope
- Rewriting full voice pipeline architecture.
- Changing gateway-side run semantics.
- Replacing existing speaking/running tray semantics beyond requested listening behavior.

## Dependencies
- `abstractassistant/abstractassistant/ui/qt_bubble.py`
- `abstractassistant/abstractassistant/app.py`
- `abstractassistant/abstractassistant/core/gateway_voice_manager.py`
- `abstractassistant/abstractassistant/core/tts_manager.py`
- `abstractassistant/abstractassistant/utils/icon_generator.py`
- `abstractassistant/tests/basic/`

## Expected Outcomes
- Voice prompt says unique tool names once (set-like output).
- Full voice mode runs with bubble hidden by default.
- Tray icon supports `listening` state and handles:
  - single click: pause/resume listening
  - double click: stop full voice mode

## Plan
- Add listening pause/resume/is_paused methods to voice managers.
- Add full voice tray-control methods in the bubble.
- Extend app tray state machine for listening.
- Add listening icon animation mapping.
- Add regression tests and run targeted suite.

## Report
- **Tool announcement deduplication**:
  - Updated `QtChatBubble._announce_tool_execution(...)` to keep an order-preserving unique tool set.
  - Repeated calls to the same tool are no longer listed repeatedly.
  - Single-tool repeated calls now announce call count (e.g. `Executing 3 calls of fetch_url. Please wait.`).
- **Listening state in tray model**:
  - Extended app-level state machine in `abstractassistant/app.py` to include `listening`.
  - Added full voice listening state bridge methods (`_full_voice_listening_state`, toggle, stop) for tray click handling.
  - Click semantics now include:
    - `listening + single click` → pause/resume listening
    - `listening + double click` → stop full voice mode
- **Voice manager support for listening pause**:
  - Added `pause_listening`, `resume_listening`, `is_listening_paused` to:
    - `GatewayVoiceManager`
    - local `VoiceManager` wrapper in `tts_manager.py`
  - Unsupported capability paths emit explicit `#FALLBACK` warnings.
- **Full voice visibility behavior**:
  - `start_full_voice_mode()` now hides the bubble so full voice is tray-first during active listening.
- **Tray icon listening rendering**:
  - Added `listening`/`listening_paused` mapping in icon status flow.
  - Added dedicated listening pulse rendering in `IconGenerator`.
  - Added tooltip mapping for listening state.

## Tests
- `pytest -q abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py` → **7 passed**
- `pytest -q abstractassistant/tests/basic/test_gateway_events.py abstractassistant/tests/basic/test_tray_context_menu_fallback.py abstractassistant/tests/basic/test_tray_listening_state_clicks.py abstractassistant/tests/basic/test_tool_announcement_dedup.py` → **12 passed**
- `python -m py_compile abstractassistant/app.py abstractassistant/ui/qt_bubble.py abstractassistant/core/gateway_voice_manager.py abstractassistant/core/tts_manager.py abstractassistant/utils/icon_generator.py` → **OK**
