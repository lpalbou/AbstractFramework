# 005 — Add AbstractMusic (ACE-Step client) + AbstractCore `music` capability plugin

## Summary

Introduce a new standalone package, **`abstractmusic`**, that enables text-to-music generation as an **optional “capability plugin”** for `abstractcore`, in the same spirit as `abstractvoice` (voice/audio) and `abstractvision` (vision).

Initial backend target: **ACE-Step 1.5** via its official **REST API server** (`acestep-api`), keeping `abstractmusic` lightweight and avoiding bundling GPU-heavy dependencies into the Abstract ecosystem by default.

## Why

- We want **music generation** as a first-class, deterministic capability alongside voice and vision, but we do not want to turn `abstractcore` into a “kitchen sink”.
- ACE-Step 1.5’s official distribution strongly encourages a **server/UI workflow** (`uv run acestep` / `uv run acestep-api`), which maps naturally to an **HTTP backend** (similar to AbstractVision’s OpenAI-compatible backend).
- Clear separation improves operational ergonomics:
  - durable hosts (gateway/runtime) can run the music backend server and store outputs in the ArtifactStore
  - thin clients do not need heavy ML deps or model weights installed locally

## Investigation notes (model size)

The unified Hugging Face repository `ACE-Step/Ace-Step1.5` contains multiple weight bundles (DiT, LM, embedding model, VAE).

Measured via Hugging Face repository tree metadata (bytes on Hub):
- Total repo footprint (all files): **~9.40 GiB**
- Largest artifacts:
  - `acestep-v15-turbo/model.safetensors`: **~4.46 GiB**
  - `acestep-5Hz-lm-1.7B/model.safetensors`: **~3.45 GiB**
  - `Qwen3-Embedding-0.6B/model.safetensors`: **~1.11 GiB**
  - `vae/diffusion_pytorch_model.safetensors`: **~321.8 MiB**

## Scope

### In scope

- Add an official **`music`** capability in `abstractcore`:
  - `llm.music.t2m(...)` facade
  - plugin discovery via existing `abstractcore.capabilities_plugins` entry points
  - actionable “missing plugin” errors (install hint: `pip install abstractmusic`)
  - optional `generate_with_outputs(..., outputs={"t2m": {...}})` support
- Create a new standalone package **`abstractmusic`**:
  - `abstractcore` integration via entry point: `abstractmusic.integrations.abstractcore_plugin:register`
  - backend: **ACE-Step API client** (POST `/release_task`, poll `/query_result`, download `/v1/audio`)
  - ArtifactStore-aware outputs (return bytes or `{"$artifact": ...}` refs)
  - clear warnings for any fallback behavior (`#FALLBACK : reason`)
- Add unit tests in `abstractcore` validating:
  - missing plugin errors for `music`
  - plugin registration + calling `llm.music.t2m(...)`
  - `generate_with_outputs` support for `t2m`
- Update docs:
  - `docs/guide/capability-plugins.md` to include music
  - minimal getting-started snippet for `abstractmusic`

### Out of scope (v0)

- Embedding ACE-Step as an in-process Python dependency (ACE-Step pins Python 3.11 and heavy CUDA stacks).
- Implementing advanced ACE-Step editing tasks (cover/repaint/vocal2bgm) as first-class APIs.
- Adding OpenAI-compatible `/v1/audio/*` server endpoints for music generation (can be layered later).

## Dependencies

- ACE-Step 1.5 server mode (`uv run acestep-api`) running on a reachable host.
- `httpx` for the API client.
- Optional: `abstractruntime` ArtifactStore integration when running in framework mode.

## Expected Outcomes

- Developers can install and use:
  - `pip install abstractcore abstractmusic`
  - run ACE-Step’s API server separately
  - generate audio bytes (or durable artifacts in framework mode) via `llm.music.t2m("...")`
- AbstractCore remains lightweight: music is **opt-in**.

## Implementation Plan

- Extend `abstractcore.capabilities.types` with a `MusicCapability` protocol.
- Extend `abstractcore.capabilities.registry.CapabilityRegistry`:
  - add `register_music_backend(...)`, `get_music()`, `music` facade
  - include `music` in `.status()` and install hints
- Extend `abstractcore.core.interface.AbstractCoreInterface`:
  - add `.music` property
  - add `outputs={"t2m": {...}}` to `generate_with_outputs`
- Implement `abstractmusic`:
  - `abstractmusic.backends.acestep_api.AceStepApiClient`
  - `abstractmusic.integrations.abstractcore_plugin.register(...)`
- Add tests and run `pytest` for touched packages.

---

## Report

### What was delivered

- **AbstractCore**
  - Added `music` as a first-class deterministic capability:
    - `MusicCapability` protocol in `abstractcore.capabilities.types`
    - `CapabilityRegistry` facade + backend registration helpers (`register_music_backend`, `.music`, `.get_music()`)
    - `llm.music` property on `AbstractCoreInterface`
  - Extended `generate_with_outputs(...)` to support `outputs={"t2m": {...}}`.
  - Added/extended unit tests for:
    - missing music plugin error messaging
    - plugin registration and `llm.music.t2m(...)`
    - `generate_with_outputs` for `t2m`

- **AbstractMusic (new package)**
  - New standalone package `abstractmusic/` (src layout) with:
    - `AceStepApiClient` (HTTP client for ACE-Step v1.5 server: `/release_task`, `/query_result`, `/v1/audio`)
    - AbstractCore capability plugin registration: `abstractmusic.integrations.abstractcore_plugin:register`
    - ArtifactStore-aware outputs (bytes in library mode; `{"$artifact": ...}` in framework mode)
  - Added unit tests using `httpx.MockTransport` (no external server required).

- **Docs + tooling**
  - Updated `docs/guide/capability-plugins.md` and `docs/getting-started.md` (added “Path 7a”).
  - Updated `README.md` to list AbstractMusic in the modality plugins table.
  - Updated `scripts/build.sh` to install/verify `abstractmusic` in the local dev build.
  - Added ADR: `docs/adr/001_music_as_capability_plugin_via_acestep_api.md`
  - Added repo-level notes: `AGENTS.md`

### Tests executed (empirical proof)

- `cd abstractcore && pytest -q tests/test_capabilities_registry.py tests/test_generate_with_outputs.py`
- `cd abstractmusic && pytest -q`

All passed.

