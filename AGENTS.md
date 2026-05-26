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

### 2026-02-14 — Telegram Bot activation (Bot API) + thin-client bridge

- **Telegram bridge actor_id gotcha**: the GatewayRunner tick loop only processes runs with `actor_id == "gateway"`. The Telegram bridge originally created runs with `actor_id="telegram"`, which the runner silently ignored. Fix: bridge now uses `actor_id="gateway"`; Telegram origin is recorded in session_id, binding state, and event payloads.
- **Thin-client-only behavior**: the bridge starts **one run per incoming Telegram message** (stable `session_id` for durable memory) and sends the completed output back to Telegram. Default flow is the shipped `basic-agent` entrypoint (no special event-driven flow required).
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
- **Bridge-owned delivery**: Telegram replies are sent by the bridge from run output; workflows do not need to tool-call `send_telegram_message`.

### 2026-02-14 — AbstractCore model/architecture registry source of truth

- **Canonical registries**: AbstractCore's model capabilities and architecture formats are owned by `abstractcore/assets/model_capabilities.json` and `abstractcore/assets/architecture_formats.json`. When new models or architectures ship, update these files first (see `abstractcore/assets/README.md` for field rules).

### 2026-02-15 — Per-repo commit helper

- **Commit script**: `scripts/commit.sh` commits changes per repository (root + siblings) with a shared message, skips clean repos, and prints a summary.

### 2026-02-20 — Tool argument coercion risk

- **Tool-call parsing can yield string values**: several tool-call formats preserve raw strings (XML-ish tags, code blocks), so tool args may arrive as `"false"`, `"0"`, or numeric strings.
- **Security implication**: in Python, non-empty strings are truthy; without coercion, flags like `allow_dangerous` can be unintentionally enabled.
- **Direction**: centralize schema-aware coercion with explicit `#FALLBACK` warnings, keep local defense-in-depth in high-risk tools like `execute_command`.

### 2026-02-20 — AbstractFlow gateway-first thin client wiring

- **Gateway VisualFlow CRUD + publish**: `/api/gateway/visualflows` now stores VisualFlow JSON and publishes WorkflowBundles via the gateway registry (optional reload after publish).
- **UI transport rewrite**: AbstractFlow UI consumes `/api/gateway/runs/{run_id}/ledger/stream` SSE and maps ledger records to `ExecutionEvent` client-side (`ledgerEvents.ts`).
- **Run history alignment**: history replay uses `/api/gateway/runs/{run_id}/history_bundle` with local mapping and terminal state synthesis.
- **Gateway semantics endpoint**: `/api/gateway/semantics` exposes the AbstractSemantics registry; returns 501 if the optional package is unavailable.
- **Thin-client proxy env**: frontend proxy prefers `ABSTRACTFLOW_GATEWAY_URL` with legacy env fallbacks tagged `#FALLBACK`.
- **Workspace policy UX**: Flow Editor treats gateway workspaces as server-managed by default and derives `workspace_access_mode` options from the gateway policy.
- **Gateway auth injection**: Flow Editor CLI + Vite proxy can attach `Authorization: Bearer` from `ABSTRACTGATEWAY_AUTH_TOKEN` (legacy envs warn with `#FALLBACK`).
- **RestrictedPython private names**: AbstractRuntime now allows leading-underscore identifiers in Code nodes while reserving guard helper names (prevents shadowing `_getattr_`, `_getitem_`, etc.).
- **RestrictedPython AugAssign rule**: augmented assignment on dict/list subscripts is rejected; flows must use explicit read/modify/write instead.

### 2026-02-21 — AbstractFlow subworkflow wait UX

- **Subworkflow waits**: live Flow UI treats wait_reason=subworkflow as non-interactive (no prompt), showing a status message instead to avoid misleading “Please respond”.

### 2026-02-21 — AbstractFlow subrun observability + output formatting

- **Subrun streaming**: Flow UI opens ledger SSE streams for agent/subflow subruns (and nested subruns) to restore live cycle traces in `AgentSubrunTracePanel`.
- **Output preview**: run details always show beautified responses, with Raw JSON expanded by default.

### 2026-02-21 — AbstractFlow run UI polish

- **Resume suppression**: Flow UI filters `resume` ledger records (resumed=true) so internal wait bookkeeping does not surface as a fake step.
- **On Flow Start inputs**: UI fetches `/api/gateway/runs/{run_id}/input_data` and injects a synthetic On Flow Start step when ledger events are missing.
- **Agent layout**: duration is shown in the header badge; the agent cycles panel takes priority in the details layout.

### 2026-02-21 — AbstractAssistant gateway audio pipeline

- **Gateway TTS/STT client path**: gateway mode now calls `/voice/tts` and `/audio/transcribe`, downloads audio artifacts, and plays/records locally without AbstractVoice.
- **Local recorder/player detection**: macOS uses `afrecord`/`afplay`; Linux uses `arecord`/`ffmpeg` and `paplay`/`aplay`/`ffplay`/`mpg123`, with `#FALLBACK` warnings when unavailable.
- **STT timeout bump**: gateway transcription calls temporarily raise the client timeout to 120s to avoid premature timeouts.
- **Gateway TTS pause/resume**: process-backed playback now pauses via `SIGSTOP` and resumes via `SIGCONT`, including pausing the meter thread; `#FALLBACK` warnings remain for unsupported cases.
- **Pause readiness**: gateway TTS pause waits briefly for the playback process to spawn, avoiding false `#FALLBACK` when pause is clicked immediately.
- **State sync after stop**: gateway voice now clears `_speaking/_paused` even if no process is tracked and syncs state on queries to avoid phantom active voice after interruption.

### 2026-02-21 — AbstractAssistant gateway cleanup + workflow picker

- **Gateway run controller**: ledger replay/streaming moved into `GatewayRunController`; `GatewayWorker` lives outside `qt_bubble.py`.
- **Gateway voice manager**: `GatewayVoiceManager` provides a VoiceManager-compatible interface for TTS/STT in gateway mode.
- **Workflow picker**: gateway entrypoints are selectable in the tray UI and persisted per session via `GatewaySelectionStore`.
- **Offline reconnect**: gateway stream failures set OFFLINE state, with a manual “Reconnect gateway” menu action.

### 2026-02-21 — AbstractVoice default dependency enforcement

- **Voice backend required**: tests now assert `abstractvoice` is importable; docs remove “optional voice” language.
- **Monorepo import fix**: tests insert the `abstractvoice` project root to avoid namespace-package shadowing.

### 2026-02-21 — SmartNote thin-client architecture

- **Thin client UI**: SmartNote tray app is a lightweight HTTP client; runtime/LLM never run in-process in the UI.
- **Gateway-first backend**: SmartNote runs as a gateway bundle + tools (no separate SmartNote server).
- **Durable ingestion**: gateway-managed runs execute chunked LLM ingestion (avoid truncation).
- **Semantic memory**: knowledge triples are stored in AbstractMemory with AbstractSemantics predicate validation.
- **Fallback policy**: any degraded path emits `#FALLBACK` warnings; truncation is reserved for UI-only and must be labeled `#TRUNCATION`.

### 2026-02-21 — SmartNote ingest overrides + attachment provenance

- **Provider/model overrides**: ingest tools accept optional `provider`/`model` inputs to override gateway defaults per request.
- **Attachment provenance**: locally stored attachments now persist `artifact_run_id` for traceability.

### 2026-02-21 — SmartNote specialized workflow (bundle rationale)

- **WorkflowBundle entrypoints**: SmartNote flows are packaged as a bundle so the gateway can run versioned, durable workflows.
- **Tool-first logic**: flows are minimal wrappers that call `smartnote_*` tools because VisualFlow code nodes cannot import Python modules.
- **Docs location**: SmartNote's specialized workflow explanation lives in `smartnote/docs/specialized-workflow.md`.

### 2026-02-21 — SmartNote auto bundle preflight

- **Startup bundling**: SmartNote builds the bundle when needed at startup and uploads it to the gateway for a single-command UX.

### 2026-02-21 — SmartNote artifact-first cards + graph

- **Artifact source of truth**: fragments and cards are stored as gateway artifacts; indexes are derived.
- **Auto-classification**: fragments attach to existing cards or create new cards, with KG edges for navigation.

### 2026-02-21 — SmartNote tray quick note UI

- **Quick note panel**: tray capture dialog is a top-right frameless panel (below the menu bar) with a drag-and-drop attachment zone and lightweight styling for fast capture.

### 2026-02-21 — Claude skills research (server tools + automation)

- **Web search tool**: server-side search returns citations; latest versions support dynamic filtering via code execution to reduce token load and improve relevance.
- **Web fetch tool**: server-side fetch can pull full pages/PDFs with optional citations; supports domain allowlists and content limits (truncation must be labeled `#TRUNCATION`).
- **Computer use tool**: desktop automation via screenshot + mouse/keyboard actions in an agent loop; requires sandboxed environment and strong prompt-injection defenses.
- **Thinking controls**: some models expose a `thinking` parameter with a token budget to increase deliberation depth; should be logged for reproducibility.
- **Context compaction**: Claude 4.6 introduces context compaction (automatic summarization) to extend effective context length.

### 2026-02-21 — Agent Skills (shareable skills standard)

- **Agent Skills format**: skills are folders with a required `SKILL.md` (YAML frontmatter + instructions) and optional `scripts/`, `references/`, `assets/`.
- **Progressive disclosure**: only `name`/`description` metadata loads at startup; full `SKILL.md` loads on activation; extra files load on demand.
- **Claude Code extensions**: skills support slash commands, invocation control (`disable-model-invocation`, `user-invocable`), `allowed-tools`, subagents (`context: fork`), and dynamic context injection (`!`).
- **Claude API skills**: skills are attached via `container.skills` and require code execution tools; types `anthropic` or `custom` with version pinning.

### 2026-02-21 — Agent Skills ecosystem (additional libraries)

- **Vercel skill pack**: React/Next performance rules, composition patterns, React Native guidance, and UI review guidelines.
- **HashiCorp skill pack**: Terraform style guide, module refactoring, and provider acceptance testing workflows.
- **Trail of Bits skill pack**: CodeQL and Semgrep scan workflows plus SARIF parsing; emphasizes approval gates and auditability.
- **Security-focused skills**: OWASP/ASVS review checklists and Varlock secrets hygiene.
- **Process/PM skills**: TDD, systematic debugging, PRD/problem-statement/experiment design skills for workflow discipline.

### 2026-02-21 — Agent Skills integration proposal (skills vs flows)

- **Flows run; skills activate**: flows (`.flow` bundles / VisualFlow) are the durable executable unit; skills (`SKILL.md`) are portable procedure packs that are loaded/activated and can optionally expose scripts as explicit tools.
- **Composition model (v0)**: run-attached skills are primary; `.flow` bundles may declare skill dependencies via `manifest.metadata`; bundle-embedded skills under `assets/*` is optional for hermetic distribution.
- **Safety + durability**: skill bodies/resources must be artifact-backed when large; activation/resource reads should be ledger-recorded; `allowed-tools` should restrict execution (intersection with run allowlists) and out-of-policy calls must emit `#FALLBACK` (any truncation labeled `#TRUNCATION`).
- **Docs**: design notes in `docs/guide/agent-skills.md`; backlog + plan in `docs/backlog/planned/074_agent_skills_integration.md`.

### 2026-02-20 — OpenAI-compatible discovery validation bypass

- **Model listing safety**: provider discovery instantiates OpenAI-compatible providers with `model="default"` to avoid validating a specific model during model enumeration (prevents LMStudio discovery failures when the configured default model is absent).

### 2026-02-21 — AbstractAssistant window positioning

- **Top-right clamp**: tray bubble, dialogs, and toasts align to the available screen top-right (below the menu bar) and clamp inside screen bounds.
- **Popup positioning**: input dialogs and message boxes use the same top-right positioning to avoid right-edge clipping.

### 2026-02-21 — AbstractAssistant tray voice meter + animation smoothing

- **Speaking meter**: tray speaking animation can now be driven by real audio levels (local AbstractVoice chunks or gateway WAV envelope).
- **Thinking spinner**: flicker reduced by switching to a smooth dot spinner rendered at higher resolution and downsampled.
- **Tray click robustness**: single-click falls back to opening the bubble if pause/resume fails after voice stops.

### 2026-02-21 — Tool policy selector (thin clients)

- **Gateway tool defaults**: gateway tool inventory now applies runtime approval defaults (safe auto-approve vs mutating ask).
- **Fallback clarity**: when gateway discovery fails, the UI falls back to local default tool specs with a `#FALLBACK` note.
- **Shared component**: AbstractUIC UI kit now ships `ToolPolicyEditor` for allowlist + approve/ask selection.

### 2026-02-21 — AbstractAssistant voice meter bands + duplicate response guard

- **Frequency-band meter**: speaking meter derives log-spaced FFT band levels (80–6k Hz) with RMS scaling to drive per-bar animation.
- **Gateway WAV analysis**: gateway TTS WAVs are decoded into per-frame band levels when possible; RMS fallback emits `#FALLBACK`.
- **Duplicate finals**: gateway worker + UI skip duplicate final outputs and enforce a per-turn final-output gate to avoid repeated history entries and TTS/toasts.
- **Foreground filtering**: assistant events now render only for the root run (and its foreground subworkflow) to prevent duplicated outputs from background subruns.

### 2026-02-21 — AbstractAssistant visibility state cleanup

- **Real visibility checks**: tray open/close logic uses the Qt widget’s `isVisible()` instead of manual flags.
- **Stop vs show**: stopping voice playback no longer opens the chat bubble; visibility changes are explicit.
- **Voice-active gating**: tray clicks only short‑circuit when TTS is truly active (`is_speaking`/`is_paused`), preventing stale voice state from blocking reopen.
- **Bubble visibility state**: the app derives a `BubbleVisibility` state from actual Qt window state (visible/minimized/hidden) and uses it to show/restore without toggling on click.
- **Tray click state machine**: `_app_state()` returns `ready`/`running`/`speaking` from `current_status`. Ready+click = always show. Running+click = ignore. Speaking+click = pause/resume. Speaking+dblclick = stop + reset to ready. Double-click is never perceived as single-click (200ms timer gate).
- **show_chat_bubble never refuses**: no run-active gate, no toggle-hide; the user controls window lifetime.
- **Response callbacks are informational**: `handle_bubble_response`/`handle_bubble_error` never hide the widget.
- **No auto-hide after send**: removed `QTimer.singleShot(500, self.hide)`.
- **Crash protection**: `on_agent_event`, `_handle_tool_request`, `_handle_ask_user`, `_finalize_response` wrapped with try/except + stderr tracebacks; `faulthandler` enabled at startup; global `sys.excepthook`/`threading.excepthook` installed.
- **Approval dialog activation**: approval/ask-user dialogs are parentless top-level windows with `WindowStaysOnTopHint`; macOS `NSApp.activateIgnoringOtherApps_(True)` brings the app to the foreground; a tray notification fires so the user knows approval is needed even across desktop spaces.
- **Ledger wait canonical path**: `extract_wait_from_record` reads only `result.wait` (the format written by `StepRecord.finish_waiting`); synthetic rehydration records in `_maybe_emit_pending_wait` also use `result.wait`.
- **Font stack**: `SF Mono` is not available in Qt on macOS; use `Menlo`, `Monaco`, `Consolas` for monospace.
- **Gateway STT via AbstractVoice VoiceRecognizer**: mic capture + VAD uses AbstractVoice's `VoiceRecognizer` (webrtcvad, sounddevice) with a `GatewaySTTAdapter` that uploads audio to the gateway `/audio/transcribe` endpoint. No local whisper model loads; the heavy transcription stays on the gateway. Removed all duplicated recording/VAD code from `GatewayVoiceManager`.
- **Tool execution voice**: in voice mode, the assistant speaks "Executing <tool> with <params>. Please wait." before auto-approved or manually approved tool batches.

### 2026-02-21 — AbstractCore installer wizard parity

- **GUI config parity**: the AbstractCore installer wizard now mirrors `abstractcore --config` phases (vision fallback, audio/video strategies, embeddings, logging), so non-technical setups can be completed without a terminal.

### 2026-02-21 — AbstractCore installer prototype behavior

- **Installer source**: the GUI installer installs AbstractCore from PyPI via pip (no Git clone) into an isolated venv; bundled apps must be rebuilt to pick up UI changes.

### 2026-02-21 — AbstractCore wizard clarity (current values)

- **Wizard defaults**: the GUI wizard now shows current config values (vision/audio/video/embeddings/logging), uses an STT language dropdown, and explains the advanced STT backend id field to reduce confusion.

### 2026-02-21 — macOS installer manager prototype

- **Rust/Tauri manager**: a macOS installer manager prototype now exists at `abstractinstallers/abstractframework-macos`, using a manifest‑driven plan to install AbstractFramework via PyPI/pip with explicit `#FALLBACK` warnings.
- **Build output**: Tauri v2 config produces a macOS `.app` bundle under `src-tauri/target/release/bundle/macos/`.

### 2026-02-22 — macOS installer UI fixes

- **Custom + folder picker**: Custom mode now enables component selection and the install directory uses a native macOS folder picker.

### 2026-02-22 — Tauri global API enabled

- **withGlobalTauri**: enabled global JS bridge so the installer UI can invoke backend commands and respond to clicks.

### 2026-02-22 — macOS installer progress UX

- **Progress + cancel**: installer now shows per‑component progress, overall progress, and a cancel action, with backend events driving the UI.

### 2026-02-22 — macOS installer bridge fallback

- **Bridge fallback**: the installer UI now falls back to `window.__TAURI_INTERNALS__` for `invoke`/`listen` when the global API is unavailable, and surfaces the bridge mode in the header/log for diagnostics.

### 2026-02-22 — macOS installer event ACL

- **Event permissions**: added a Tauri v2 capability granting `core:event:default` so the installer UI can `listen` for progress events without ACL errors.

### 2026-02-22 — macOS installer Python prerequisite modal

- **Python prereq UX**: missing or outdated Python now emits a `prereq` event that triggers a modal with a download action and retry flow, keeping installs unblocked and explicit.

### 2026-02-22 — macOS installer Python auto-download

- **Guided installer download**: the Python prerequisite modal can now download the official python.org macOS installer, cache it, and launch the `.pkg`, with fallback to the download page.

### 2026-02-22 — macOS installer Python detection

- **PATH‑independent detection**: Python detection now scans framework installs and common toolchain paths, selecting the newest Python ≥ 3.10 to avoid GUI PATH issues.

### 2026-02-22 — macOS installer retry diagnostics

- **Retry + logs**: Python selection now considers patch versions and prefers python.org installs when tied; installer command output streams into logs so pip failures are visible.

### 2026-02-22 — macOS installer PyPI pin fallback

- **Pinned version guard**: pip installs now validate pinned PyPI versions and fall back to latest with a `#FALLBACK` warning when a pin is missing.

### 2026-02-22 — macOS installer setup wizard UI

- **Unified progress + setup**: install logs are consolidated into a single panel with progress bar, and a post‑install AbstractCore configuration wizard now runs inside the installer.

### 2026-02-22 — macOS installer setup wizard steps

- **Step-by-step setup**: the configuration UI now uses card-based steps with Back/Next navigation and a single Base URL field bound to the default provider.

### 2026-02-22 — macOS installer provider cleanup

- **Supported providers only**: removed Gemini/HF token inputs, kept Hugging Face as local-only, and limited API key application to OpenAI/Anthropic/OpenRouter/Portkey.

### 2026-02-22 — macOS installer full wizard

- **Step-by-step flow**: the installer now shows one major step at a time with Back/Next navigation across install and setup phases.

### 2026-02-22 — macOS installer finish navigation

- **Finish + nav cleanup**: the outer wizard nav is hidden during setup and a Finish button now exits the installer.

### 2026-02-22 — macOS installer fit-to-frame

- **Frame-safe layout**: the installer now uses a height-aware flex layout with internal step scrolling to prevent overflow.

### 2026-02-22 — macOS installer API key explanation

- **Key clarity**: the setup wizard now explains that API keys are stored locally in the AbstractCore config and used for provider authentication.

### 2026-02-22 — macOS installer install panel wrap

- **Log wrap**: install log output now wraps and stays inside the card while remaining scrollable.

### 2026-02-22 — macOS installer log visibility

- **Log sizing**: the install panel now reserves more space for logs so progress output remains readable without resizing.

### 2026-02-22 — macOS installer env var apply

- **Persistent env vars**: the wizard can now apply Base URL env vars via launchd (GUI apps) and `.zprofile` (terminal shells), with `#FALLBACK` logs on failure.

### 2026-02-22 — macOS installer env defaults

- **Env defaults**: Base URL env persistence is enabled by default, with a warning if the user disables it.

### 2026-02-22 — macOS installer choice alignment

- **Choice layout**: install-mode radio options now align with checkbox rows using a matching grid layout.

### 2026-02-22 — macOS installer log dedup

- **Log noise fix**: removed duplicate UI appends so each installer log entry is shown once.

### 2026-02-21 — AbstractFlow agent approvals + max-iterations default

- **Tool approval waits**: subrun tool approvals emit `reason=user` with `details.mode=approval_required`; UI must surface approvals even when the parent step is “running” and resume with `{"approved": true|false}` (not a free-text response).
- **Approval placement**: approvals live in the run modal footer with a full tool-call detail panel; no step auto-selection is forced, so users can inspect any step during a run.
- **Default tools**: when agent tools are unspecified, default to the full tool set; only explicit allowlists should restrict tools.
- **Input defaults parity**: gateway-hosted runs now pass `input_data` into `create_visual_runner` so runtime defaults align with run-selected provider/model.
- **Max iterations default**: runtime + VisualFlow defaults now use `max_iterations=50`, surfaced as agent pin defaults in the UI.

### 2026-02-22 — Workspace root vs prompt path gotcha

- **Workspace root matters**: if `workspace_root` is not explicitly set, the run uses a per-run default workspace. Agent prompts forbid filesystem ops on absolute paths outside that root, so paths mentioned only in the user prompt (e.g., `/Users/...`) will be refused unless `workspace_root` or `workspace_allowed_paths` includes them.

### 2026-02-22 — Workspace policy prompt removal

- **Prompt removal**: workspace policy guidance was removed from the ReAct prompt to avoid model‑side gating.
- **Runtime authority**: filesystem/path access is enforced in runtime (`rewrite_tool_arguments` → `resolve_user_path`); prompts are no longer used for policy enforcement.

### 2026-02-22 — Workspace policy recheck (post-removal)

- **Restart required**: gateway processes keep the old system prompt in memory; a process restart is required for prompt changes to take effect.
- **Absolute-path success**: with `workspace_access_mode=all_except_ignored`, approved `execute_command` calls can write to absolute paths like `/Users/alboul/flow-rtype/snake-game` without runtime rejection.

### 2026-02-22 — Snake game flow execution

- **Flow execution**: VisualFlow `test` run successfully created files under `/Users/alboul/flow-rtype/snake` after tool approval.
- **Prompt stale**: gateway still injects the workspace policy block until the process restarts, so a `workspace_root` override was used to avoid model refusal.

### 2026-02-22 — Workspace policy enforcement confirmed (post-restart)

- **Prompt cleared**: after gateway restart, the LLM system prompt no longer includes any workspace policy block.
- **Runtime-only gating**: `workspace_access_mode=all_except_ignored` worked without a `workspace_root` override and allowed absolute-path writes to `/Users/alboul/flow-rtype`.

### 2026-02-22 — Run modal follow-up + new run

- **Follow Up**: run modal returns to the start screen while preserving the current session context; follow-up runs seed `context.messages` with the prior prompt + last answer.
- **New Run**: resets the stable session id before starting a fresh run context.

### 2026-02-22 — Run modal session id field

- **Session ID input**: preflight screen exposes a Session ID field (when no `session_id` pin exists) to make context reuse explicit.
- **Follow Up reuse**: follow-up now copies the prior run’s session id into the field and start request.

### 2026-02-22 — Tool approval Approve All

- **Approve All**: approval footer adds an Approve All button that auto-approves future tool waits for the same session.
- **Auto-resume**: when enabled, tool approval waits are resumed immediately without prompting.

### 2026-02-22 — Follow-up context persistence

- **Durable seed**: Follow Up now uses a cached last-run prompt+answer seed so context survives run-state resets.
- **Session fallback**: run submissions always include the derived session id when the field is empty.

### 2026-02-22 — Inline follow-up modal + threaded runs

- **Inline follow-up**: Run modal now opens a dedicated follow-up dialog with a 4-line textarea and drag/drop attachments.
- **Threaded timeline**: follow-up runs are rendered as a continuation of the original execution timeline via a thread run id.
- **Workspace carryover**: follow-up runs reuse prior input settings (workspace + inputs) while overriding prompt/context.
- **Attachment uploads**: follow-up attachments upload through `/api/gateway/attachments/upload` and are passed via `context.attachments`.

### 2026-02-22 — Toolbar duplicate shortcut

- **Duplicate button**: Flow toolbar includes a Duplicate action before New to clone the current flow in one click.

### 2026-02-22 — Ledger JSONL recovery + locking

- **Ledger recovery**: JSONL ledger reads now recover concatenated records and warn with #FALLBACK/#TRUNCATION.
- **Write locking**: ledger appends are serialized with a file lock + fsync to prevent interleaved writes.

### 2026-02-22 — Tool approval wait preserved on subworkflow waits

- **UI wait guard**: subworkflow wait events no longer clear active tool-approval prompts in the run modal.

### 2026-02-22 — Tool approval visible in history view

- **History extraction**: inspected run view now derives tool-approval waits from ledger events so approvals remain visible.
- **Explicit resume**: approval actions can target a specific run_id + wait_key (history-friendly).
- **Approve All scope**: auto-approval can target a root run id so child runs inherit approval.

### 2026-02-22 — Run history root runs + higher limit

- **History coverage**: run history now requests root runs only and increases list limit to 500.

### 2026-02-22 — Run history workflow-id filtering

- **Workflow-scoped history**: run history now queries `/runs` with computed workflow_id candidates to avoid global limits.
- **Suffix fallback**: adds a root-only fallback list filtered by flow id suffix for renamed bundles.

### 2026-02-22 — Tool-calls idempotency + run failure summary

- **Idempotency fix**: tool-calls idempotency includes `call_id` to avoid reusing prior results for distinct tool calls.
- **Failure visibility**: Run modal shows a failure summary panel with node + error and quick jump-to-step.

### 2026-02-22 — AbstractCode wait resolution (cross-client approvals)

- **Stale wait clearing**: subworkflow waits now resolve based on the latest subrun record, clearing approval prompts after resume/completion.
- **Unit coverage**: added wait-resolution tests for stale waits and active waits.

### 2026-02-21 — AbstractAssistant tools dialog grouping + compact UI

- **Tool sections**: tools are grouped by toolset (File system, Internet, System, Comms, SmartNote, Other) using gateway metadata with name-based inference fallback.
- **Compact layout**: buttons, rows, and dialog dimensions are reduced for faster scanning without losing approval controls.
- **Filter headers**: tool group headers hide automatically when filtering removes all tools in a section.

### 2026-02-21 — Tool mode banner + approval default alignment

- **Gateway tool mode exposure**: `/api/gateway/discovery/tools` now returns `tool_mode` for thin-client UI banners.
- **UI mode banner**: AbstractUIC `ToolPolicyEditor` supports a tool-mode banner (approval/passthrough/delegated/local) with warning tones and `#FALLBACK` when missing.
- **Approval defaults**: read-only/search + comms tools auto-approve; only file/system mutation tools default to ask (aligned in AbstractRuntime + AbstractUIC).

### 2026-02-21 — Per-run tool policy enforcement

- **Run-scoped tool policy**: `_runtime.tool_policy` overrides tool approval for a run (safe vs ask) inside the tool-calls effect handler.
- **Thin client wiring**: AbstractAssistant now sends per-session tool approval preferences in gateway run input.
- **Fallback defaults**: tools UI falls back to local policy/heuristics when gateway defaults are missing.
- **Legacy reset**: if a session carries an “all ask” legacy state, approvals reset to safe defaults with `#FALLBACK`.

### 2026-02-21 — Tool approval dialog UX

- **Prompt summary**: tool approval prompt now shows tool name + key parameters in the main message.
- **Structured details**: details view uses readable tool/argument formatting instead of raw JSON.
- **No bubble activation**: approval dialogs no longer open the chat bubble window.

### 2026-02-21 — Tool approval dialog visibility fix

- **Top-level prompt**: approval dialogs use an active window or no parent to avoid hidden-parent suppression.
- **Visibility control**: dialog is application-modal, raised, and marked stay-on-top to ensure the prompt is seen.

### 2026-02-21 — Pending wait rehydrate + approval detection

- **Wait rehydrate**: gateway attach now inspects the history bundle for pending waits and injects them into the event path so prompts appear immediately.
- **Approval detection**: tool approval waits are recognized even when tool call lists are missing, preventing misrouting to free‑text input waits.

### 2026-02-21 — Gateway reattach wait visibility fixes

- **Cache init order**: gateway cache now initializes before tool discovery to avoid `_gateway_cache` attribute errors.
- **Policy fallback**: when runtime tool defaults are unavailable, the UI uses the local policy with a `#FALLBACK` warning.
- **Wait fallback**: pending waits are recovered from run summaries when ledger tail doesn’t include a wait record.

### 2026-02-21 — Follow latest subworkflow wait

- **Replay selection**: gateway reattach now follows the most recent subworkflow wait in ledger replay, preventing stale subrun selection and hidden approvals.
- **Test hang guard**: `test_final_verification` now times out subprocess shutdown to avoid pytest hangs.

### 2026-02-22 — Font alias cleanup + runtime policy mismatch

- **Font alias**: Qt styles now avoid generic `sans-serif`/`Sans Serif` and `-apple-system`, relying on explicit macOS fonts to prevent alias warnings at startup.
- **Runtime mismatch**: tool policy fallback warnings occur when `abstractruntime` resolves to an older site‑packages install lacking `ToolApprovalPolicy`; fix by installing the repo version in editable mode.

### 2026-02-21 — Tray behavior while running

- **Run blocking**: tray clicks refuse to open the bubble while a run is active.
- **Activity summaries**: bubble records a short running summary for the tray (reattach, tool approval, tool execution, ask-user).
- **Tray visibility**: tooltip and notifications surface running status without opening the UI.

### 2026-02-21 — Gateway stream idle watchdog + run activity summary

- **Idle stream guard**: ledger SSE idle timeouts trigger status polling with a `#FALLBACK` warning to prevent stuck “running” state.
- **Run activity detail**: gateway worker emits status + prompt summaries (including waiting reason) and the tray tooltip refreshes immediately.
- **Stale reattach skip**: auto-reattach ignores runs with >10m of no updates and clears `last_run_id` to avoid startup lock.

### 2026-02-21 — Installer strategy documentation

- **Two-tier installer model**: recommended a cross-platform Installer Manager that installs signed per-app packages with a manifest-driven pipeline.
- **Gateway-first defaults**: installer design centers on AbstractGateway as the control plane, with thin clients connecting by default.
- **OS trust requirements**: signing + notarization are mandatory to avoid SmartScreen/Gatekeeper blocks; any fallbacks must emit `#FALLBACK`.

### 2026-02-21 — Flow agent trace persistence + tool allowlist defaults

- **Agent output fallback**: Flow UI derives agent output from sub-run trace ledger records when parent ledger lacks node output, keeping traces visible post-run.
- **On Flow Start inputs**: synthetic start step uses `/input_data` payload to display real user inputs instead of run metadata.
- **Tool allowlist default**: Visual Agent only sets `allowed_tools` when explicitly configured; otherwise it uses the runtime tool registry defaults.

### 2026-02-22 — Capability-driven parameter filtering (AbstractCore v2.13.0)

- **`thinking_support` ≠ parameter restrictions**: `thinking_support` in model_capabilities.json means "this model can produce reasoning traces" (output format). `unsupported_parameters` means "this model's API rejects these parameters" (API constraint). These are orthogonal — a model can think AND accept temperature (GPT-5 family), or think AND reject temperature (o1, o3).
- **`_is_reasoning_model()` semantics**: moved to BaseProvider, now reads `thinking_support` from model_capabilities.json. Answers "can this model think?" — no longer used for parameter filtering.
- **`unsupported_parameters` field**: new field in model_capabilities.json declaring which generation parameters a model's API rejects. Providers use `_is_parameter_supported(param)` to check. Absent field = all parameters supported (backward-compatible default).
- **`token_param_name` field**: new field in model_capabilities.json declaring the API parameter name for output token limit (`max_tokens` or `max_completion_tokens`). Replaces hardcoded `_uses_max_completion_tokens()` heuristics.
- **GPT-5/5-mini/5-nano empirically reject temperature**: live API tests (2026-02-22) confirm that gpt-5, gpt-5-mini, gpt-5-nano reject temperature (only default=1 accepted), top_p, frequency_penalty, and presence_penalty. They accept seed. `unsupported_parameters` now set for these models.
- **GPT-5.1 and GPT-5.2 empirically accept temperature**: live API tests (2026-02-22) confirm that gpt-5.1 and gpt-5.2 accept ALL sampling parameters (temperature, top_p, frequency_penalty, presence_penalty, seed). These models do NOT have `unsupported_parameters` set.
- **o3/o3-mini/o4-mini coverage fix**: these reasoning models were not matched by the old `_is_reasoning_model()` heuristic and would incorrectly receive temperature. Now correctly handled via `unsupported_parameters` (empirically verified).
- **max_tokens rejected by all reasoning models**: all o-series and GPT-5 family models reject `max_tokens` and require `max_completion_tokens`. GPT-4.1 accepts both. token_param_name field controls this.
- **Reasoning token capture**: OpenAI reasoning models report `reasoning_tokens` in `usage.completion_tokens_details`. AbstractCore already captures this in the GenerateResponse usage dict. The actual reasoning text is NOT exposed via Chat Completions API (only via Responses API with reasoning summaries).
- **Warning behavior**: unsupported sampling parameters (temperature, top_p, etc.) are silently dropped — upstream callers always pass them as defaults, so warning on every call is noise. The `unsupported_parameters` list in model_capabilities.json is the authoritative enforcement.

### 2026-02-22 — OpenAI Responses API investigation

- **Responses API is OpenAI's successor to Chat Completions**: recommended for all new projects; covers all Chat Completions capabilities plus reasoning summaries, built-in tools (web search, file search, code interpreter, MCP), server-managed conversation state, and better cache utilization.
- **Empirically verified**: `client.responses.create()` works for text, instructions (system prompt), multi-turn, function calling, structured output, and streaming (tested with openai SDK v1.93.0).
- **Reasoning summaries available**: `reasoning: {"effort": "medium", "summary": "auto"}` returns human-readable reasoning text in `output[type="reasoning"].summary` — this is the actual thinking that Chat Completions hides.
- **AbstractCore already supports reasoning text**: `GenerateResponse.metadata["reasoning"]` is populated by Ollama (`thinking`/`reasoning` fields), OpenAI-compatible provider (`reasoning_content`), and base provider normalization (`<think>` blocks). Only the OpenAI provider is missing because Chat Completions doesn't provide it.
- **`store: false` must be explicit**: Responses API stores responses on OpenAI's side by default; AbstractCore should default to `store: false` to avoid unexpected data retention.
- **Backlog**: planned as #076, OpenAI provider only; other providers unaffected.

### 2026-02-22 — Gateway error triage (post parameter-filtering changes)

- **Temperature warning noise**: the `RuntimeWarning` for dropped parameters fired on every call because upstream callers always pass temperature as a standard default. Fixed by removing the warning — parameters are silently dropped per `unsupported_parameters`. The model_capabilities.json list is the authoritative enforcement, not log noise.
- **JSONDecodeError in ledger**: pre-existing issue — corrupted JSONL ledger line (two JSON objects concatenated). The repo code has `_decode_line` with recovery, but the running gateway process had stale bytecode. Fix: restart the gateway to pick up current code.
- **tool_call_id not found**: pre-existing issue — conversation history management in the runtime agent loop. A tool result message references a `tool_call_id` absent from the previous assistant message's `tool_calls`, likely after context truncation. Unrelated to parameter filtering changes.

### 2026-02-23 — Run Flow modal layout focus

- **3-card layout**: Run Flow form is now Session | File System Access | Workflow Parameters. Session is a simple top card. File System Access is collapsible (collapsed by default) and contains access mode, workspace folder, and ignored folders. Workflow Parameters holds all flow input pins.
- **Naming**: "Execution folder" renamed to "Workspace folder" to match the underlying `workspace_root` concept.

### 2026-02-20 — AbstractAssistant macOS tray ready-click fallback

- **Activation gap on macOS**: `QSystemTrayIcon` can enter context-menu show flow without emitting `activated` on fresh clicks, which can skip the ready-state open action.
- **Fallback strategy**: wire the darwin tray menu `aboutToShow` signal to a fallback that hides the menu and only calls `show_chat_bubble()` when (a) no recent activation event occurred and (b) assistant state is `ready`.
- **Safety guard**: keep running/speaking semantics untouched by restricting the fallback to ready state and duplicate-suppressing with an activation timestamp gate.

### 2026-02-24 — AbstractAssistant macOS tray menu artifact

- **Artifact source**: adding a dummy disabled tray menu action can render a tiny popup rectangle under the macOS tray icon.
- **Fix direction**: keep an empty attached menu with `aboutToShow` fallback handling, but do not add placeholder actions.

### 2026-02-24 — AbstractAssistant full voice tray-first listening controls

- **Tool announcement dedupe**: voice announcements for tool execution now use unique tool names (set semantics) so repeated calls to the same tool are not spoken repeatedly.
- **Listening control surface**: full voice mode exposes tray-level `listening` behavior — single click pauses/resumes listening and double click stops full voice mode.
- **Tray-first voice UX**: full voice mode hides the bubble when activated; interaction is driven from tray states (`listening`/`speaking`/`thinking`) instead of keeping the app window visible.
- **Listening pause plumbing**: gateway and local voice manager adapters expose `pause_listening`, `resume_listening`, and `is_listening_paused` with explicit `#FALLBACK` warnings when unsupported.

### 2026-02-24 — AbstractAssistant ready-click visual show race

- **Observed symptom**: logs can show ready-state click handling and `Qt chat bubble shown` while no bubble is visible.
- **Root cause class**: macOS tray event/focus lifecycle race — show can happen in the same cycle as tray activation/menu transitions.
- **Fix pattern**: defer ready-state show by one Qt tick and reassert bubble visibility/activation from `QtBubbleManager.show()`; clamp bubble window on-screen before/after show.

### 2026-02-24 — Full voice mic-reactive listening + start-button semantics

- **Listening meter source**: full voice listening animation can use live mic energy from the existing `VoiceRecognizer` input loop via a lightweight `audio_level_callback` (no second audio stream).
- **Propagation path**: mic levels flow from `abstractvoice.recognition.VoiceRecognizer` -> assistant voice managers (`GatewayVoiceManager` / local `VoiceManager`) -> bubble `_handle_voice_meter` -> tray icon meter.
- **Listening icon behavior**: tray `listening` pulse now scales by real-time mic level; `listening_paused` remains visually calm.
- **Mic control semantics**: full voice mic control is now a start-only button (not a toggle). Runtime full-voice state is sourced from `_full_voice_running`, not button checked state.
- **Window geometry rule**: voice-mode UI switching no longer changes bubble size (`setFixedSize(..., 120)` removed); voice transitions keep stable window geometry.

### 2026-02-24 — Listening meter gain + modal visibility follow-up

- **Strict mic-reactive listening**: removed synthetic baseline oscillation in listening icon dynamics so tray motion reflects perceived mic level rather than default animation.
- **Volume color cue**: listening pulse now shifts toward blue and brightens as voice volume increases, improving visual confidence that live speech is being captured.
- **Qt warning cleanup**: removed unsupported stylesheet `cursor` property from status pill (cursor remains controlled by `setCursor`).

### 2026-02-24 — Tool approval modal crash hardening

- **Revert**: removed the modal-close visibility workaround after user report; the issue was process crash, not visibility.
- **Approval dialog stability**: replaced native `QMessageBox` tool-approval prompt with a custom top-level `QDialog` (Approve/Deny + allowlist checkbox) to reduce macOS native modal teardown risk.
- **Teardown race mitigation**: tool-execution voice announcement is now deferred one Qt tick after approval (`QTimer.singleShot(0, ...)`) to avoid dialog-close + TTS callback races.

### 2026-02-24 — Tray app quit-on-last-window guard

- **Root cause class**: closing a top-level dialog while the bubble is hidden can trigger app termination when Qt quits on last window closed.
- **Fix pattern**: disable `quitOnLastWindowClosed` for the QApplication and mark approval/input dialogs with `WA_QuitOnClose=False` as defense-in-depth.

### 2026-03-17 — Source build macOS quarantine + editable install bootstrap

- **macOS Rollup quarantine**: downloaded workspaces on macOS can carry `com.apple.quarantine`, which blocks native npm addons such as `@rollup/rollup-darwin-arm64/rollup.darwin-arm64.node`. `scripts/build.sh` now clears quarantine on the UI project dirs and `node_modules` before `npm run build`.
- **Local editable installs**: `scripts/build.sh` now uses `pip install --no-build-isolation -e ...` for local repos and reuses the `.venv` toolchain instead of spawning fresh pip build-isolation envs for every package.
- **Build backend compatibility window**: source builds now ensure a shared backend set compatible with both newer local package builds and `abstractassistant`'s `pkg_resources` dependency: `setuptools>=77,<81`, `hatchling>=1.27`, `editables>=0.5`.
- **Umbrella package pin drift**: the root `abstractframework` package now pins `abstractgateway==0.2.1` to match the actual repo version and avoid resolver-noise during editable reinstalls.
