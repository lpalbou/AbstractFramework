# Backlog: Gateway assistant cleanup refactor

## Summary
Refactor gateway-first runtime logic out of the Qt UI so the assistant is clean, simple, robust, and efficient.

## Why
- `qt_bubble.py` was too large and mixed UI, network, voice, and threading concerns.
- Gateway-first features needed clearer separation to avoid regressions.

## Scope
### In scope
- Extract gateway run streaming/reattach logic into a dedicated controller module.
- Extract gateway voice logic (TTS/STT, recording/playback, fallbacks) into a dedicated manager module.
- Keep Qt UI focused on rendering, event wiring, and state updates.

### Out of scope
- Changing gateway backend APIs.
- New UI features beyond parity with current behavior.

## Dependencies
- Existing gateway client, SSE, adapter, and run state machine.
- Voice recording/playback tools on the host OS.

## Expected outcomes
- Smaller, easier-to-read UI code.
- Clear separation between UI, gateway runtime, and voice.
- Fewer race conditions and fewer UI state inconsistencies.

## Full report
### What changed
- Moved gateway run streaming logic into `GatewayRunController`.
- Moved gateway run execution into `GatewayWorker` (separate module).
- Added `GatewayVoiceManager` to unify gateway voice handling behind a VoiceManager-compatible interface.
- Simplified Qt bubble voice handling to a single backend interface.

### Files touched
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/ui/gateway_worker.py`
- `abstractassistant/gateway/run_controller.py`
- `abstractassistant/core/gateway_voice_manager.py`
- `abstractassistant/core/tts_manager.py`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `05182488-e11b-4dee-91e5-add41c98e910`
