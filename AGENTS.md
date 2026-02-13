## Agent Notes (AbstractFramework)

This file captures practical engineering notes discovered while evolving the codebase.

### 2026-02-12 — AbstractMusic + ACE-Step 1.5 integration (model size + backend options)

- **ACE-Step 1.5 model repo footprint**: the Hugging Face repo `ACE-Step/Ace-Step1.5` is ~9.4 GiB total and includes multiple components (DiT, LM planner, embedding model, VAE). The largest single artifact is `acestep-v15-turbo/model.safetensors` (~4.46 GiB).
- **Local-first default**: `abstractmusic` should follow the AbstractVoice/AbstractVision mental model — install and generate **locally in-process** (no mandatory server/daemon).
- **ACE-Step note**: ACE-Step ships an `acestep-api` server which is useful operationally, but should be an *optional* backend, not the default integration surface.
- **ACE-Step on Apple Silicon**: upstream ACE-Step docs claim **MPS** support; on macOS they advise disabling bf16 (`--bf16 false`) to avoid errors. In `abstractmusic` we default to **fp16 on MPS** (bf16 disabled) to keep memory manageable on 18‑GB class unified‑memory machines.
- **ACE-Step MPS memory cap**: `abstractmusic` can cap MPS memory (default ~16 GiB) by setting `PYTORCH_MPS_HIGH_WATERMARK_RATIO` based on `mps_max_memory_gb`/`mps_high_watermark_ratio`.
- **ACE-Step MPS watermark validation**: we validate/clamp MPS high/low watermark ratios and set a safe low watermark to avoid `invalid low watermark ratio` crashes during model load.
- **Diffusers slow-import noise**: we disable `DIFFUSERS_SLOW_IMPORT` in-process for ACE-Step VAE loading to avoid importing unrelated transformer modules that emit non-actionable warnings.
- **ACE-Step MPS cap application**: when torch is already loaded, we also call `torch.mps.set_per_process_memory_fraction` to apply the cap immediately.
- **ACE-Step MPS cap basis**: we compute the requested cap against `torch.mps.recommended_max_memory` when available; the env watermark stays ≤1.0 while the per‑process fraction can exceed 1.0 (up to 2.0) if the user requests more.
- **ACE-Step VAE load fix**: Diffusers `AutoencoderOobleck` is loaded with `low_cpu_mem_usage=False` to avoid meta‑tensor `.to()` crashes on MPS.
- **ACE-Step VAE weight_norm**: we use the new parametrizations `weight_norm` with a state‑dict key conversion to avoid deprecation warnings while still loading checkpoint weights.
- **ACE-Step MPS mixed-dtype kernel gotcha**: some MPSGraph kernels can abort on mixed f32/f16 arithmetic in conditioning/tokenizer paths (`mps_add ... f32 vs f16`). For reliability on MPS, the text-encoder conditioning path runs on CPU float32 (`#FALLBACK`) and hidden states are cast back to model dtype/device before diffusion.
- **ACE-Step VAE MPS OOM fallback**: if VAE decode fails on MPS, we move the VAE to CPU **float32** and decode in float32 to avoid dtype mismatches (input float vs bias half) during the fallback.
- **ACE-Step postprocess quality gotcha**: raw VAE-decoded waveforms can contain tiny per-channel DC bias; naive peak-normalization amplifies this into one-sided/noisy audio. We DC-center waveforms before normalization in `abstractmusic`.
- **Instrumental conditioning**: for no-lyrics prompts, `abstractmusic` uses a null lyric condition (zero mask) rather than synthetic placeholder lyric text, improving consistency of instrumental generation.
- **ACE-Step infer method default**: local `abstractmusic` currently defaults to upstream-style `infer_method=ode` (turbo `fix_nfe=8`), with a guarded retry to alternate method if non-finite latents are returned.
- **Text2music source-latent init**: for no-source generation, `abstractmusic` initializes `src_latents` from seeded random noise (instead of silence) to stay closer to expected model behavior and avoid silent/degenerate runs.
- **Prompt handling alignment**: default ACE-Step text2music now passes the raw prompt (tag-style) without SFT wrapping to better match upstream inference behavior; SFT prompt can be re-enabled explicitly.
- **Chunk mask default**: chunk masks default to zeros in text2music mode to avoid injecting constant features into context latents.
- **AbstractMusic ACE-Step backend**: `abstractmusic` ships a native local backend (`abstractmusic:acestep-v15`) that loads ACE-Step v1.5 from Hugging Face and generates WAV bytes in-process; default uses a pinned HF revision for determinism.
- **ACE-Step code loading**: the checkpoint’s custom Transformers model code is vendored into `abstractmusic` (Apache-2.0 headers), so we avoid `trust_remote_code` at runtime.
- **Transformers v5 meta-init gotcha**: Transformers v5 may initialize models on `meta` tensors by default during `from_pretrained()`. ACE‑Step’s init path performs quantizer setup that materializes tensor scalars, which crashes on meta tensors (`Tensor.item() cannot be called on meta tensors`). We override the vendored model’s `get_init_context(...)` to avoid meta initialization (also filters v4 `init_empty_weights()`).
- **Quantizer dependency minimization**: the minimal FSQ/ResidualFSQ implementation (MIT, derived from `vector-quantize-pytorch`) is vendored so `abstractmusic` does not require `vector-quantize-pytorch` (and its transitive deps) as a hard dependency.
- **AbstractCore capability plugins**: capability backends are discovered via the `abstractcore.capabilities_plugins` entry point group. Missing plugins must raise actionable errors (install/config hints) and we avoid silent fallbacks.

### 2026-02-12 — AbstractCore Server audio/music endpoints + macOS (MPS) fallback

- **AbstractCore Server audio endpoints**: `/v1/audio/speech` (TTS) and `/v1/audio/transcriptions` (STT) are implemented via capability plugins; `/v1/audio/translations` exists but returns **501** (not supported by the current capability contract).
- **Music server endpoint**: `/v1/audio/music` is provided as an extension (no official OpenAI equivalent) and delegates to `core.music.t2m(...)` when `abstractmusic` is installed.
- **MPS limitation**: some Diffusers audio pipelines (e.g. AudioLDM vocoder) can fail on Apple Silicon `mps`; `abstractmusic` retries on CPU with an explicit `#FALLBACK` warning.
- **CLI gotcha**: `argparse` subcommands normally reject top-level flags after the subcommand; `abstractmusic` duplicates “common flags” onto `t2m`/`repl` so docs-style commands like `t2m ... --duration 10` work naturally.

