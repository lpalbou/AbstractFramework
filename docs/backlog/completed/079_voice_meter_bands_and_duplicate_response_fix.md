# Backlog: Voice meter bands + duplicate response fix

## Summary
Improve the speaking icon to reflect frequency-band amplitude and prevent duplicate responses/voice playback in gateway runs.

## Why
- The current speaking bars use a single amplitude, making them look flat and unrealistic.
- Gateway runs can emit duplicate final outputs, producing repeated messages and TTS.

## Scope
### In scope
- Add multi-band audio meter support for TTS (local and gateway).
- Update tray icon rendering to use per-band amplitudes.
- Deduplicate final assistant responses to avoid duplicate history entries and TTS.

### Out of scope
- Gateway server changes or protocol changes.
- New UI widgets beyond the tray icon visualizer.

## Dependencies
- Existing AbstractAssistant voice meter callbacks.
- Gateway ledger streaming and adapter events.

## Expected outcomes
- Speaking icon shows realistic, varied bar heights tied to frequency bands.
- Single response and single TTS playback per run final output.

## Full Report
- **Summary**: Added frequency-band voice meters for speaking animations and guarded gateway final outputs to prevent duplicate chat messages and TTS.
- **Implementation**:
  - FFT-based band extraction (log-spaced 80–6k Hz) now drives per-bar meter levels for local AbstractVoice chunks and gateway WAV playback, with RMS scaling and `#FALLBACK` warnings when band analysis is unavailable.
  - Tray icon speaking animation accepts per-band levels, resamples to bar count, and uses band amplitudes for realistic bar heights.
  - Gateway worker dedupes assistant message appends, tags events with run ids, and filters assistant outputs to the root/follow run; UI enforces a per-turn final-output gate to prevent duplicate messages/TTS even when multiple runs emit the same response.
- **Tests**: `python -m pytest` (fails: 31 collection errors, missing `abstractcode.react_shell`, `abstractcode.fullscreen_ui`, and `create_llm` imports, plus abstractgateway/abstractruntime/abstractvoice collection errors).
