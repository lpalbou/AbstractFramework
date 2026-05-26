## Summary
- Eliminate false gateway TTS pause warnings by waiting for playback readiness.
- Keep `#FALLBACK` only for truly unsupported pause/resume cases.

## Why
- Pause can be invoked before the playback process is spawned, causing a misleading warning.
- AbstractCode/Web pauses locally; the assistant should pause locally without spurious warnings.

## Scope
- Add a playback readiness event to `GatewayVoiceManager`.
- Make pause wait briefly for playback to spawn before warning.

## Out of Scope
- Gateway API changes.
- AbstractVoice local TTS changes.

## Dependencies
- `abstractassistant/core/gateway_voice_manager.py`

## Expected Outcomes
- Pause succeeds when playback is about to start.
- Warnings only appear when no pausable playback exists.

## Plan
- Add playback readiness event.
- Update pause path to wait for readiness.
- Run tests.

## Report
- **Root cause**: gateway TTS returns an audio artifact; pause/resume happens in the client. The warning was triggered when pause was clicked before the local playback process was spawned.
- **Fix**: `GatewayVoiceManager` now tracks playback readiness and waits briefly for the player to spawn before deciding pause is unsupported.
- **Warning policy**: `#FALLBACK` remains for truly unsupported playback (no process / no signals).

## Tests
- `python -m pytest abstractassistant`
