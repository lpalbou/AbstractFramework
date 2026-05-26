# 012 — AbstractMusic: ACE‑Step 1.5 local backend (standalone + AbstractCore `/v1/audio/music`)

## Summary

Implemented a **full local/in‑process integration** of **ACE‑Step v1.5** inside `abstractmusic`, so that:

- `abstractmusic` works **standalone** (Python API + CLI REPL) to generate music/audio locally.
- When `abstractmusic` is installed, AbstractCore Server’s `POST /v1/audio/music` works end‑to‑end via the capability plugin.

No external ACE‑Step server/daemon is required.

## Why

The intended model is `ACE-Step/Ace-Step1.5` (MIT on Hugging Face) and the ecosystem pattern is “install → generate locally” (like AbstractVoice/AbstractVision). The implementation must remain compatible with permissive licensing constraints (MIT/Apache/BSD).

---

## Report

### What changed

#### `abstractmusic` — ACE‑Step backend (local, in-process)

- Added `abstractmusic/src/abstractmusic/backends/acestep_v15.py`
  - Implements `MusicBackend.generate_audio(...) -> GeneratedAsset` producing **WAV** bytes.
  - Loads components directly from the **Hugging Face checkpoint repo**:
    - DiT model via Transformers `AutoModel` (custom architecture from the repo subfolder)
    - Text encoder (`Qwen3-Embedding-0.6B`) + tokenizer
    - VAE via Diffusers `AutoencoderOobleck`
    - `silence_latent.pt` for timbre + source latents
  - **Apple Silicon / MPS defaults**:
    - avoids bf16 on MPS (uses float32) per upstream guidance
    - explicit `WARNING #FALLBACK` CPU retry for unsupported MPS ops
    - VAE decode uses tiling and can fallback to CPU float32 per-chunk
  - Determinism:
    - default HF `revision` is **pinned** to a known commit for stable weights + remote-code

#### `abstractmusic` — dependencies

- Updated `abstractmusic/pyproject.toml` to include ACE‑Step runtime deps (permissive licenses):
  - `huggingface_hub`
  - `einops`
  - `vector-quantize-pytorch`

#### `abstractmusic` — CLI / REPL

- Updated `abstractmusic/src/abstractmusic/cli.py`
  - Default backend is now **ACE‑Step** (`--backend acestep`).
  - Added `--lyrics` support for `t2m` and `repl`.
  - Clarified that `--steps` is backend-specific (ACE‑Step turbo uses fixed schedule).

#### `abstractmusic` — AbstractCore capability plugin

- `abstractmusic/src/abstractmusic/integrations/abstractcore_plugin.py`
  - Registers **two** music backends:
    - `abstractmusic:acestep-v15` (priority 10, default)
    - `abstractmusic:diffusers` (priority 0, optional)
  - For `/v1/audio/music`, the server’s capability-only core selects the highest priority backend → ACE‑Step by default.

#### Docs / ADRs

- Updated user-facing docs to show **ACE‑Step v1.5** as default backend:
  - `abstractmusic/README.md`
  - `docs/getting-started.md`
  - `docs/guide/capability-plugins.md`
  - root `README.md`
- Updated ADRs:
  - `docs/adr/002_abstractmusic_inprocess_local_generation.md` (default backend now ACE‑Step)
  - `docs/adr/003_abstractmusic_acestep_v15_backend_source_strategy.md` (Accepted: native backend loads from HF repo)

### Tests executed

- `cd abstractmusic && pytest -q`

All passed (includes a unit “smoke” test for the ACE‑Step backend using fakes; avoids downloading the 9.4GiB model during CI/unit runs).

### How to use (standalone)

```bash
abstractmusic --backend acestep t2m "sci fi music" --duration 10 --out out.wav
abstractmusic --backend acestep repl
```

### How to use (AbstractCore server)

Once `abstractmusic` is installed in the server environment:

- `POST /v1/audio/music` generates `audio/wav` bytes (delegates to `core.music.t2m(...)`).

