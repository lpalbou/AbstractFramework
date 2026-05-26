# Backlog: Gateway audio pipeline (STT/TTS) for AbstractAssistant

## Summary
Route voice features through gateway audio endpoints so voice mode works in gateway‑first operation without local AbstractVoice dependencies.

## Why
- Gateway-first UX must not rely on local core services to speak or transcribe.
- Voice mode is a core assistant feature and must behave consistently across restarts.
- Clean separation reduces local install complexity and aligns with durable runs.

## Scope
### In scope
- Use `/v1/audio/speech` for TTS and `/v1/audio/transcriptions` for STT when `use_gateway=true`.
- Preserve existing voice UI (push‑to‑talk/full voice) while swapping the backend.
- Add explicit `#FALLBACK` warnings when gateway audio is unavailable and fall back to local only if configured.

### Out of scope
- Streaming voice over WebRTC.
- New voice UX beyond parity with current UI.

## Dependencies
- Gateway audio endpoints and capability plugins (`abstractvoice` installed server‑side when needed).
- Session store for retaining voice settings across restarts.

## Expected outcomes
- Voice features operate without local AbstractVoice in gateway mode.
- Clear warnings when gateway audio is unavailable.
- Consistent voice UX across restarts and sessions.

## Full report
### What changed
- Added gateway TTS path that calls `voice_tts`, downloads the audio artifact, and plays it with OS‑native tools; integrates with the run state machine for speaking state.
- Added gateway STT loop that records short audio clips locally (macOS `afrecord`, Linux `arecord`/`ffmpeg`) and calls `audio_transcribe`.
- Enabled TTS and full‑voice toggles when gateway audio is available even without local AbstractVoice.
- Skipped local recognizer warmup/health checks in gateway mode and added `#FALLBACK` warnings for missing recorder/player or gateway failures.
- Increased STT request timeout to 120s for gateway transcription calls to avoid premature timeouts.
- Documented gateway voice behavior in the FAQ.

### Files touched
- `abstractassistant/ui/qt_bubble.py`
- `abstractassistant/docs/faq.md`

### Tests
- `python -m pytest abstractassistant/tests`
- Gateway E2E run (gpt-5-mini) `c6ab9840-5efc-46b7-853a-cfa4fb6ddc62`
- Gateway TTS test: `voice_tts` succeeded (artifact `8db4fdd68aa96ce29e4c96c56c48409e`)
- Gateway STT test: `audio_transcribe` succeeded (120s timeout)
