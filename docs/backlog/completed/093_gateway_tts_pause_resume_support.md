## Summary
- Investigate gateway TTS pause/resume behavior and align with AbstractCode/Web.
- Add real pause/resume support for gateway TTS playback in the assistant.

## Why
- AbstractCode/Web can pause/resume TTS; the assistant should match.
- The assistant previously stopped playback and warned on pause/resume.

## Scope
- Confirm gateway TTS is artifact-based and pause/resume is client-side.
- Implement process pause/resume + meter pause handling in `GatewayVoiceManager`.
- Preserve `#FALLBACK` warnings only for truly unsupported cases.

## Out of Scope
- Gateway API changes for TTS.
- AbstractVoice local TTS changes.

## Dependencies
- `abstractassistant/core/gateway_voice_manager.py`
- AbstractCode/Web TTS playback behavior

## Expected Outcomes
- Pause/resume works when playback is process-backed (macOS/Linux).
- `#FALLBACK` only appears when no pausable playback exists.

## Plan
- Inspect gateway TTS endpoint behavior vs web client playback.
- Add process pause/resume + meter pause handling.
- Run tests.

## Report
- **Gateway investigation**: `/api/gateway/runs/{run_id}/voice/tts` returns a durable audio artifact; pause/resume is not a gateway API concern. AbstractCode/Web pauses locally via WebAudio (offset-based resume).
- **Assistant fix**: `GatewayVoiceManager` now pauses/resumes process-backed playback via `SIGSTOP`/`SIGCONT` and pauses the meter thread while audio is paused.
- **Warnings**: `#FALLBACK` is retained only when no pausable playback exists (e.g., missing process or unsupported signals).

## Tests
- `python -m pytest abstractassistant`
