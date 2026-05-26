# 007 — Rebuild AbstractMusic for in-process local generation (no external server)

## Summary

Recreate `abstractmusic/` as a **standalone package** that generates music/audio **in-process** (local inference), matching the “install → generate locally” pattern of `abstractvoice` and `abstractvision`.

This includes:
- a lightweight orchestrator (`MusicManager`)
- a local backend (initially **Diffusers audio pipelines**) that produces WAV bytes
- an optional **AbstractCore capability plugin** that exposes `llm.music.t2m(...)` without requiring any external server

## Why

- Users expect **symmetry** across modality packages:
  - install `abstractvoice` → local TTS/STT
  - install `abstractvision` → local generation (Diffusers / sdcpp)
  - install `abstractmusic` → local generation (no mandatory API server)
- Running a separate server process is an operational choice, not a required architecture.

## Scope

### In scope

- Recreate `abstractmusic/` package (Python):
  - `MusicManager` + `MusicBackend` interface
  - Local **Diffusers** backend for text-to-audio/music generation
  - Encode output to **WAV** bytes (artifact-store aware)
  - Import-light plugin module (no heavy imports at module import time)
- AbstractCore integration:
  - Register `abstractmusic` under `abstractcore.capabilities_plugins`
  - Provide `llm.music.t2m(...)` that uses local inference (no HTTP server)
- Documentation updates:
  - Remove “ACE-Step API server required” wording
  - Document required config keys (e.g., `music_model_id`, `music_device`, etc.)
- Tests:
  - Unit tests that validate plugin wiring and artifact outputs without downloading model weights

### Out of scope (v1)

- First-class ACE-Step in-process backend (can be added as a separate backend once dependency constraints are stabilized).
- MP3 encoding (requires system codecs/ffmpeg; WAV is the baseline).

## Dependencies

- `torch`, `diffusers`, `transformers`, `accelerate`, `numpy` for local backend execution.

## Expected Outcomes

- `pip install abstractmusic` enables **local** text-to-music generation (given a configured model id).
- `pip install abstractcore abstractmusic` exposes `llm.music.t2m(...)` via the capability plugin layer, without a server requirement.

---

## Report

### What changed

- **Recreated `abstractmusic/`** as a local-first package:
  - `abstractmusic/src/abstractmusic/music_manager.py`: `MusicManager` orchestrator
  - `abstractmusic/src/abstractmusic/backends/diffusers_audio.py`: local Diffusers backend producing **WAV** bytes (stdlib `wave` encoding)
  - `abstractmusic/src/abstractmusic/integrations/abstractcore_plugin.py`: AbstractCore plugin registering a **local** backend (no server)
  - `abstractmusic/pyproject.toml`: batteries-included deps (Diffusers + torch stack)

- **Aligned AbstractCore defaults** for music output:
  - Default `format` is now **`wav`** in `MusicCapability` and `generate_with_outputs(outputs={"t2m": ...})`.

- **Docs updated** to reflect local generation (no backend server):
  - `docs/guide/capability-plugins.md`
  - `docs/getting-started.md` (Path 7a)
  - `README.md`

- **ADR updated**:
  - `docs/adr/001_*` marked **Superseded**
  - new `docs/adr/002_abstractmusic_inprocess_local_generation.md` **Accepted**

### Tests executed (empirical proof)

- `cd abstractcore && pytest -q tests/test_capabilities_registry.py tests/test_generate_with_outputs.py`
- `cd abstractmusic && pytest -q`

All passed.

