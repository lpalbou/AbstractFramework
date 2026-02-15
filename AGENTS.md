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
- **CLI gotcha**: `argparse` subcommands normally reject top-level flags after the subcommand; `abstractmusic` duplicates "common flags" onto `t2m`/`repl` so docs-style commands like `t2m ... --duration 10` work naturally.

### 2026-02-14 — Telegram Bot activation (Bot API) + telegram-agent workflow

- **Telegram bridge actor_id gotcha**: the GatewayRunner tick loop only processes runs with `actor_id == "gateway"`. The Telegram bridge originally created runs with `actor_id="telegram"`, which the runner silently ignored. Fix: bridge now uses `actor_id="gateway"`; Telegram origin is recorded in session_id, binding state, and event payloads.
- **telegram-agent workflow pattern**: `basic-agent` (single-shot `abstractcode.agent.v1`) cannot handle Telegram because the bridge is event-driven (one run per chat + `telegram.message` events). The `telegram-agent` bundle uses an `on_event` node that compiles into a durable session-scoped listener child workflow, creating a message loop.
- **Agent provider/model defaults**: VisualFlow Agent nodes now inherit provider/model from run-scoped runtime defaults (`_runtime.provider`/`_runtime.model`, typically set by the gateway) and fall back to AbstractCore global defaults (`abstractcore --config`) when missing, recording a `#FALLBACK` warning.
- **Typing indicator keepalive**: the Telegram bridge now sends `sendChatAction(action="typing")` on a short loop (default 4s interval, 600s max) so the "..." bubble stays visible while the agent processes. Env: `ABSTRACT_TELEGRAM_TYPING_INTERVAL_S`, `ABSTRACT_TELEGRAM_TYPING_MAX_S`.
- **Bot API polling (outbound)**: the Bot API transport uses long-polling (`getUpdates`) — the gateway calls OUT to `api.telegram.org`. Telegram does not need to know the gateway's IP. No webhook/public URL required.
- **Telegram media handoff**: media artifacts are now promoted to top-level `attachments` in the event payload and wired into the agent `context`, enabling AbstractCore's existing multimodal path (`generate(media=...)`) for VLMs.
- **Telegram media + text pairing**: Bot API images often arrive without text; the bridge now uses `caption` when present and stashes `pending_media` so a follow-up text message can reference the previous image.
- **/reset command**: `/reset`, `/clear`, `/new` cancels all runs for the chat session, deletes the binding, and sends a confirmation. Optional best-effort message deletion is controlled by `ABSTRACT_TELEGRAM_RESET_DELETE_MESSAGES`/`ABSTRACT_TELEGRAM_RESET_DELETE_MAX` and may still fail depending on Telegram permissions and message age.
- **Telegram-only routing override**: set `ABSTRACT_TELEGRAM_MODEL` (and optionally `ABSTRACT_TELEGRAM_PROVIDER`) to override the model used for Telegram without changing other gateway traffic.
- **AbstractFlow PropertiesPanel crash**: `providers.filter(...)` crashes when `/api/providers` returns non-array data (e.g. `{"detail":"Not Found"}`). Fix: guard with `Array.isArray()` on providers and models fetch callbacks.
- **Gateway default model fallback**: when `ABSTRACTGATEWAY_PROVIDER/MODEL` are unset and flows do not specify provider/model, the gateway now falls back to AbstractCore config defaults (`abstractcore --config`) using `default_models.global_provider/global_model`.
- **Agent node default model fallback**: Visual Agent nodes now fall back to AbstractCore global defaults when provider/model are missing, recording a `#FALLBACK` warning in `_flow_warnings`.
- **Agent pin default marker**: setting agent `provider`/`model` pins to `__abstractcore_default__` uses AbstractCore global defaults (treated as an explicit default, not a missing-value fallback).
- **Media artifact resolution**: LLM client now resolves `{"$artifact": ...}`/`artifact_id` media items via the runtime artifact store into file paths before passing to AbstractCore media handlers.
- **Workflow-owned delivery**: the `telegram-agent` bundle executes `send_telegram_message` via `call_tool`, avoiding brittle “LLM must tool-call” patterns (and provider-specific hacks).

### 2026-02-14 — AbstractCore model/architecture registry source of truth

- **Canonical registries**: AbstractCore's model capabilities and architecture formats are owned by `abstractcore/assets/model_capabilities.json` and `abstractcore/assets/architecture_formats.json`. When new models or architectures ship, update these files first (see `abstractcore/assets/README.md` for field rules).

### 2026-02-15 — Per-repo commit helper

- **Commit script**: `scripts/commit.sh` commits changes per repository (root + siblings) with a shared message, skips clean repos, and prints a summary.
