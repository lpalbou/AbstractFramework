# 009 — AbstractCore Server audio/music endpoints + AbstractMusic MPS fallback fix

## Summary

1) Verified OpenAI-style audio endpoints in **AbstractCore Server** and completed the missing route:
- `POST /v1/audio/transcriptions` (STT; capability plugin-backed)
- `POST /v1/audio/speech` (TTS; capability plugin-backed)
- `POST /v1/audio/translations` (**now exists**, returns **501** because translation is not part of the current capability contract)

2) Added a **music generation** endpoint using the same server conventions:
- `POST /v1/audio/music` → delegates to `core.music.t2m(...)` and returns **`audio/wav`** bytes

3) Fixed `abstractmusic` crashing on macOS **MPS** for AudioLDM vocoder:
- detect the known MPS limitation and **retry on CPU** with an explicit `#FALLBACK` warning
- keep the CLI REPL alive (errors don’t terminate the session)

## Why

- Provide an OpenAI-ish HTTP surface for audio capabilities and a consistent extension for music generation.
- Ensure local in-process generation works on Apple Silicon even when MPS cannot run the vocoder.

## Scope

### In scope (done)

- Server routes for audio + music (music as an extension).
- Clear 501 behavior with actionable messaging when plugins/capabilities are missing.
- MPS → CPU fallback in Diffusers backend with visible warning (`#FALLBACK`).
- Documentation updates mentioning `/v1/audio/music`.

---

## Report

### What changed

#### AbstractCore Server

- Updated `abstractcore/abstractcore/server/audio_endpoints.py`:
  - Added `POST /v1/audio/translations` (returns 501; not supported)
  - Added `POST /v1/audio/music` (binary `audio/wav`, delegates to `core.music.t2m`)
- Added tests:
  - `abstractcore/tests/server/test_server_music_endpoints.py`
  - Extended `abstractcore/tests/server/test_server_audio_endpoints.py` to cover `/v1/audio/translations`
- Updated server docs:
  - `abstractcore/abstractcore/server/README.md` now lists `/v1/audio/translations` and `/v1/audio/music`

#### AbstractMusic

- Updated `abstractmusic/src/abstractmusic/backends/diffusers_audio.py`:
  - Added explicit `#FALLBACK` retry-on-CPU for the known MPS channel-limit error
- Updated `abstractmusic/src/abstractmusic/cli.py`:
  - REPL no longer crashes on one failed generation; prints error and continues
- Updated `abstractmusic/README.md`:
  - Added macOS/MPS note and `--device cpu` guidance

#### Framework docs / agent notes

- Updated:
  - `docs/guide/capability-plugins.md`
  - `docs/getting-started.md`
  - `docs/faq.md`
  - `AGENTS.md` (server endpoints + MPS fallback note)

### Tests executed

- `cd abstractmusic && pytest -q`
- `cd abstractcore && pytest -q tests/server/test_server_audio_endpoints.py tests/server/test_server_music_endpoints.py`

### Manual verification (empirical)

- Ran `abstractmusic` on a machine with `torch.backends.mps.is_available() == True` and confirmed the MPS error triggers a visible `#FALLBACK` and the generation completes on CPU.

