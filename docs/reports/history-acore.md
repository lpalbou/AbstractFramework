# AbstractCore — history report (last 10 commits since “Global Release”)

This report is **evidence-grounded**: every statement below is derived from the local git history of the `abstractcore/` repository in this workspace.

## Scope & method

- **Repo inspected:** `abstractcore/` (git sub-repo under this monorepo)
- **Baseline (stable):** `cede6ed` — “Global Release” (2026-02-08)
- **Commits covered:** the next **10** commits after `cede6ed`, up to `681b7be`
- **Primary evidence sources:** `git -C abstractcore log -10`, `git -C abstractcore show <sha>`, file diffs, and tests added/updated in those commits
- **Path convention:** file paths below are **relative to the `abstractcore/` repo root** (in this monorepo they live under `abstractcore/<path>`).

## Commit index (newest → oldest)

- `681b7be` | 2026-02-16 | improving telegram security and agency
- `8fb63f4` | 2026-02-15 | telegram openai
- `820e924` | 2026-02-15 | updated telegram handle
- `11b3562` | 2026-02-13 | ongoing work on audio/music
- `f23a9ff` | 2026-02-12 | updates
- `2139058` | 2026-02-10 | improving endpoint for vision generative capabilities
- `d463a11` | 2026-02-09 | update documentation set
- `3e512bf` | 2026-02-09 | Enhance documentation and clarify AbstractCore’s integration…
- `70564c3` | 2026-02-08 | updated llms
- `062568b` | 2026-02-08 | release 2.11.8

## Commit details

### 681b7be — improving telegram security and agency (2026-02-16)

**Files changed**
- `abstractcore/tools/common_tools.py`
- `tests/tools/test_common_tools_execute_command.py`

**What changed (code)**
- `execute_command(...)` now **coerces tool arguments defensively** before any platform detection or command execution:
  - Adds `_coerce_bool(...)` to parse common string/number representations of booleans (e.g. `"true"`, `"false"`, `"1"`, `"0"`).
  - Adds `_coerce_timeout_seconds(...)` to parse timeouts passed as strings/numbers; non-positive values fall back to the default.
  - Coerces/normalizes:
    - `command = str(command)`
    - `working_directory` empty-string → `None`
    - `timeout` defaulting to `300` seconds when invalid/missing
    - `capture_output`, `require_confirmation`, `allow_dangerous` via `_coerce_bool(...)`

**Stated rationale (explicit in code comments)**
- The added block is introduced by a comment stating:
  - “Some providers / runtimes pass tool arguments as strings… In Python, non-empty strings are truthy, which is dangerous for flags like `allow_dangerous`.”

**Tests**
- Adds `test_execute_command_accepts_string_args()` verifying `timeout="10"` and `capture_output="true"` work.
- Adds `test_execute_command_parses_allow_dangerous_false_string()` asserting that `allow_dangerous="false"` **does not** bypass the security block for a dangerous command (`chmod 777 …`) and returns an error containing `"CRITICAL SECURITY BLOCK"`.

**Implications**
- Passing `"false"`/`"0"` for boolean tool args (notably `allow_dangerous`) no longer gets treated as truthy, preventing unintended security bypass when arguments are string-encoded.
- `timeout` passed as a string is now parsed into a numeric timeout instead of being treated as an invalid type.

---

### 8fb63f4 — telegram openai (2026-02-15)

**Files changed**
- `abstractcore/providers/openai_provider.py`
- `abstractcore/tools/telegram_tools.py`
- `tests/providers/test_openai_provider_tool_transcript_unit.py` (new)
- `tests/tools/test_telegram_tools.py`

**What changed (code)**

1) **OpenAIProvider message shaping now preserves tool transcript fields**
- In `abstractcore/providers/openai_provider.py`, the code building `api_messages` from `messages` was hardened:
  - Skips non-dict messages and invalid/blank roles.
  - For role `"assistant"`, if `msg["tool_calls"]` is a non-empty list, it is copied into the outgoing message as `"tool_calls"`.
  - For role `"tool"`, if `tool_call_id` is present, it is preserved as `"tool_call_id"`.
  - If a tool message is missing `tool_call_id`, the provider **rewrites it to a `"user"` message** with content prefixed by `"[TOOL RESULT unknown]:"` (because OpenAI requires tool messages to reference a preceding assistant tool call).
  - For role `"function"`, preserves `"name"` when present.
- These changes appear in two similar loops (one near the top of the file and one later), both responsible for translating internal message lists to the OpenAI SDK payload.

2) **Telegram tools: message delivery robustness**
- In `abstractcore/tools/telegram_tools.py`, `send_telegram_message(...)` gained:
  - `_TELEGRAM_TEXT_MAX_CHARS = 3800` (margin under Telegram’s ~4096 limit).
  - `_split_telegram_text(...)` to chunk long messages with best-effort boundary selection (paragraph/newline/space; falls back to hard split).
  - Bot API helpers:
    - `_telegram_botapi_error_description(...)`
    - `_telegram_botapi_message_id(...)`
  - Empty-text handling: if `text` is blank/whitespace, it sets `was_empty_input=True` and replaces text with `"Sorry, I couldn't generate a reply."` (Telegram rejects empty strings).
  - Bot API transport now sends **multiple messages** (one per chunk) and returns:
    - `responses` (array), `message_ids`, `parts`, `partial`, and `error` (when partially sent before failure), plus `was_empty_input`.
  - Parse-mode fallback: if a send fails with an entity parsing error (`"can't parse entities"`), it retries that chunk without `parse_mode` and (on success) disables parse mode for subsequent chunks.
  - TDLib transport now also loops over chunks; on `TimeoutError` it marks `queued=True`, best-effort enqueues the request with `client.send(req)`, and stops sending remaining parts.

**Tests**
- New `tests/providers/test_openai_provider_tool_transcript_unit.py`:
  - Fakes the OpenAI SDK client to capture outgoing params.
  - Verifies that an assistant message with `tool_calls` and a tool message with `tool_call_id` are preserved in the OpenAI payload.
- `tests/tools/test_telegram_tools.py` additions:
  - `test_send_telegram_message_bot_api_splits_long_messages()` asserts long text is split into ≤3800-char chunks and posted multiple times.
  - `test_send_telegram_message_bot_api_retries_without_parse_mode_on_entity_error()` asserts retry behavior when Telegram returns “can’t parse entities”.
  - `test_send_telegram_message_bot_api_empty_text_falls_back()` asserts blank text is replaced with a non-empty fallback and marks `was_empty_input=True`.

**Implications**
- OpenAI tool-call transcripts (assistant `tool_calls` + tool `tool_call_id`) are preserved when formatting messages for OpenAI, which is required for OpenAI-compatible tool execution loops.
- Telegram message delivery becomes resilient to:
  - message length caps (chunking),
  - common parse-mode failures (retry without parse mode),
  - empty assistant outputs (non-empty fallback message),
  - TDLib request timeouts (best-effort queue).

---

### 820e924 — updated telegram handle (2026-02-15)

**Files changed**
- `docs/README.md`
- `docs/architecture.md`
- `docs/vision-capabilities.md`

**What changed (docs)**
- `docs/README.md`: adds a docs index bullet pointing to the canonical registries:
  - `abstractcore/assets/model_capabilities.json`
  - `abstractcore/assets/architecture_formats.json`
- `docs/architecture.md`: adds a “Model Metadata Registry (Source of Truth)” section describing those registries and stating they should be updated first when models/architectures change.
- `docs/vision-capabilities.md`: annotates `abstractcore/assets/model_capabilities.json` as the “source of truth”.

**Stated rationale**
- Only the commit message (“updated telegram handle”) is present; the changes themselves are documentation about registry ownership/source-of-truth.

**Implications**
- Documentation now explicitly identifies the model/architecture JSON registries as the canonical update point; no runtime behavior change in this commit.

---

### 11b3562 — ongoing work on audio/music (2026-02-13)

**Files changed**
- `abstractcore/capabilities/types.py`
- `abstractcore/core/interface.py`
- `abstractcore/server/README.md`
- `abstractcore/server/audio_endpoints.py`
- `tests/server/test_server_audio_endpoints.py`
- `tests/server/test_server_music_endpoints.py` (new)
- `tests/test_generate_with_outputs.py`

**What changed (code)**

1) **Music format default changed to WAV**
- `abstractcore/capabilities/types.py`: `MusicCapability.t2m(..., format: str = "wav")` default changed from `"mp3"` to `"wav"`.
- `abstractcore/core/interface.py`: `generate_with_outputs(... outputs={"t2m": ...})` defaults to `"wav"` when `format` is not provided (`t2m_cfg.get("format") or "wav"`).

2) **Per-instance “music_backend” alias mapping**
- `abstractcore/core/interface.py`: `_merge_backend_preferences(...)` now reads `self.config["music_backend"]` (when present) and maps:
  - `"diffusers"` → `"abstractmusic:diffusers"`
  - `"acestep"`, `"ace-step"`, `"acestep_v15"`, `"acestep-v15"` → `"abstractmusic:acestep-v15"`
  - otherwise uses the provided string as a backend id

3) **Server audio endpoints expanded**
- `abstractcore/server/audio_endpoints.py`:
  - Adds `POST /v1/audio/translations` that **always returns HTTP 501** with an actionable message (the capability contract does not expose a translation operation).
  - Adds `POST /v1/audio/music` (extension; no OpenAI equivalent):
    - Accepts JSON body with `prompt` (or `input`/`text`) and optional `lyrics`.
    - Validates/forces `format="wav"`; any other format returns HTTP 422.
    - Delegates to `core.music.t2m(...)` and returns raw bytes with `Content-Type: audio/wav`.
    - Returns HTTP 501 when music capability plugin is unavailable (`CapabilityUnavailableError`).

**What changed (docs)**
- `abstractcore/server/README.md`: adds entries for:
  - `/v1/audio/translations` (not supported)
  - `/v1/audio/music` (text-to-music)

**Tests**
- `tests/server/test_server_audio_endpoints.py`: adds an assertion that `/v1/audio/translations` returns 501 and an error mentioning `audio/translations`.
- New `tests/server/test_server_music_endpoints.py`:
  - Verifies `/v1/audio/music` returns 501 with an error message containing “pip install abstractmusic” when no plugin is registered.
  - Verifies a stub music plugin yields 200 with `audio/wav` and expected bytes.
- `tests/test_generate_with_outputs.py`: updates the t2m test to use `"wav"` and adjusts stub plugin output bytes accordingly.

**Implications**
- Any code relying on the previous default `format="mp3"` for music generation now defaults to WAV unless explicitly overridden.
- AbstractCore server now exposes `/v1/audio/music` and a non-supported `/v1/audio/translations` endpoint that fails explicitly (501) rather than attempting a silent fallback.

---

### f23a9ff — updates (2026-02-12)

**Files changed**
- `CHANGELOG.md`
- `abstractcore/capabilities/__init__.py`
- `abstractcore/capabilities/registry.py`
- `abstractcore/capabilities/types.py`
- `abstractcore/config/main.py`
- `abstractcore/config/manager.py`
- `abstractcore/core/interface.py`
- `abstractcore/embeddings/manager.py`
- `abstractcore/providers/openai_provider.py`
- `abstractcore/utils/version.py`
- `docs/centralized-config.md`
- `docs/embeddings.md`
- `tests/test_capabilities_registry.py`
- `tests/test_generate_with_outputs.py`

**What changed (code)**

1) **Music capability plumbing**
- `abstractcore/capabilities/types.py`: introduces `MusicCapability` protocol (t2m) with return type `BytesOrArtifactRef`.
- `abstractcore/capabilities/registry.py`:
  - Adds `register_music_backend(...)`, `_default_install_hint()` returns `pip install abstractmusic` for music.
  - Adds `get_music()` and a `_MusicFacade` with `t2m(...)`.
  - Extends `CapabilityRegistry.status()` to include `"music"`.
- `abstractcore/capabilities/__init__.py`: exports `MusicCapability` and updates module docstring to include music.
- `abstractcore/core/interface.py`:
  - Adds `.music` property mapping to `self.capabilities.music`.
  - Extends `generate_with_outputs(..., outputs={"t2m": ...})` to call `self.music.t2m(...)` and include `t2m` in returned `outputs`.

2) **Embeddings: additional providers supported**
- `abstractcore/embeddings/manager.py`:
  - Expands supported embeddings providers from `huggingface|ollama|lmstudio` to:
    - `huggingface`, `ollama`, `lmstudio`, `openai`, `openrouter`, `portkey`, `openai-compatible`
  - Adds provider-specific instantiation branches:
    - `OpenAIProvider`, `OpenRouterProvider`, `PortkeyProvider`, `OpenAICompatibleProvider`

3) **OpenAIProvider: embeddings API support**
- `abstractcore/providers/openai_provider.py`:
  - Adds `embed(...)` method that calls `self.client.embeddings.create(...)` and normalizes the response into a JSON-safe dict compatible with other embedding providers.

4) **Config system: new `--install` readiness check**
- `abstractcore/config/main.py`:
  - Adds CLI flags:
    - `--install` (preflight check and optional installs/downloads)
    - `--yes` / `-y` (auto-accept downloads during `--install`)
  - Extends interactive configuration (`interactive_configure()`):
    - Detects provider from model string and prompts for base URLs for local providers (`OLLAMA_BASE_URL`, `LMSTUDIO_BASE_URL`, `VLLM_BASE_URL`, `OPENAI_COMPATIBLE_BASE_URL`).
    - Adds audio strategy prompts (`auto|speech_to_text|native_only`) and guidance for `abstractvoice`.
    - Adds video strategy prompts (`auto|frames_caption|native_only`) and guidance for ffmpeg.
    - Adds embeddings provider/model setup prompt with examples and provider validation.
    - Renumbers subsequent steps (console logging becomes step 7).
  - Adds `install_check(auto_accept=...)` which prints a sectioned readiness report and may:
    - probe local provider HTTP endpoints (via `httpx`) for reachability,
    - validate embeddings provider selection and optionally install `abstractcore[embeddings]` and/or download a sentence-transformers model,
    - validate vision fallback config and optionally download a local caption model via `download_vision_model(...)`,
    - check for `abstractvoice` and best-effort prefetch STT/TTS assets (invoking `python -m abstractvoice download ...`),
    - check `ffmpeg`/`ffprobe` presence,
    - check `abstractvision` presence,
    - summarize configured API keys.
- `abstractcore/config/manager.py`:
  - Changes `AudioConfig.strategy` default to `"auto"`.
  - Adds `_apply_api_keys_to_env()` invoked at `ConfigurationManager` init:
    - Injects config-persisted API keys into `os.environ` **only if** the env var is absent (env vars take precedence).
    - Mapping includes: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `PORTKEY_API_KEY`, `GOOGLE_API_KEY`.

5) **Version bump**
- `abstractcore/utils/version.py`: `__version__` from `2.11.9` → `2.12.0`.

**What changed (docs)**
- `docs/centralized-config.md`:
  - Adds a “Quick Setup” section (`abstractcore --config`, `--install`, `--install --yes`, `--status`).
  - Documents config-persisted API keys being injected into env vars and that env vars take precedence.
  - Updates Audio section to reflect default `audio_policy="auto"` and `abstractvoice` guidance.
- `docs/embeddings.md`:
  - Updates provider count to 7 and adds sections for OpenAI, OpenRouter, Portkey, OpenAI-compatible embeddings, plus table updates.

**Tests**
- `tests/test_capabilities_registry.py`: adds music capability missing-plugin error coverage and includes a music backend in the fake plugin.
- `tests/test_generate_with_outputs.py`: adds a `t2m` output test and registers a fake music backend in the plugin.

**Implications**
- Music capability becomes a first-class capability surface (registry + interface + outputs).
- Embeddings can be routed through OpenAI/OpenRouter/Portkey/OpenAI-compatible providers via `EmbeddingManager`.
- Config manager now bridges persisted API keys into env vars at runtime (without overwriting existing env vars).
- Default audio policy becomes `auto` at the configuration layer (behavior depends on whether `abstractvoice` is installed; see `AudioConfig` comment and runtime logic).
- Adds an opinionated preflight/installer CLI (`abstractcore --install`) capable of mutating the current environment (pip installs, model downloads) when the user accepts.

---

### 2139058 — improving endpoint for vision generative capabilities (2026-02-10)

**Files changed**
- `abstractcore/server/vision_endpoints.py`
- `abstractcore/utils/version.py`
- `docs/backlog/planned/788-response.md` (new)
- `tests/server/test_server_vision_image_endpoints.py`

**What changed (code)**

1) **Vision image endpoints: model id normalization**
- `abstractcore/server/vision_endpoints.py` introduces:
  - `_KNOWN_MODEL_PREFIXES` (providers + backend families).
  - `_split_known_prefix(model)` and `_normalize_request_model_for_backend(request_model)` to normalize AbstractCore-style `provider/model` ids into backend model ids.
- Behavioral logic in `_normalize_request_model_for_backend(...)`:
  - If model prefix is in `{huggingface, hf, mlx, diffusers, sdcpp}` → strips prefix and returns the remainder for local vision backends.
  - If prefix is a non-vision provider (e.g. `openai/...`) and no upstream vision proxy is configured (`ABSTRACTCORE_VISION_UPSTREAM_BASE_URL` unset) → returns `None` (treated as “no request model”; server defaults apply).
  - If upstream proxy is configured → strips the prefix and forwards the remainder.
- `_infer_backend_kind(...)` and `_resolve_backend(...)` now operate on the normalized model (or lack of one).
- Updates the “not configured” error copy to say “vision-capable `model`” (clarifies expectation).

2) **Version bump**
- `abstractcore/utils/version.py`: `__version__` from `2.11.8` → `2.11.9`.

**What changed (docs)**
- Adds `docs/backlog/planned/788-response.md` documenting the mismatch and the new normalization behavior (including examples of passing `huggingface/...` and `openai/...` model ids to `/v1/images/*`).

**Tests**
- `tests/server/test_server_vision_image_endpoints.py`:
  - Extends “unconfigured” tests to also clear `ABSTRACTCORE_VISION_SDCPP_MODEL` and `ABSTRACTCORE_VISION_SDCPP_DIFFUSION_MODEL`.
  - Adds `test_images_generations_falls_back_when_chat_model_id_is_passed()` asserting that a chat model id like `openai/gpt-4o-mini` yields the standard “not configured” 501 rather than being misrouted as a local Diffusers id.

**Implications**
- `/v1/images/generations` and `/v1/images/edits` accept AbstractCore-style model ids more safely:
  - provider prefixes used for non-vision models no longer get misinterpreted as local model ids when no upstream proxy is configured.
  - `huggingface/…` and `mlx/…` prefixes are stripped for local vision backends.

---

### d463a11 — update documentation set (2026-02-09)

**Files changed**
- `README.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/media-handling-system.md`
- `docs/troubleshooting.md`
- `llms-full.txt`

**What changed**
- `README.md`: adjusts a “First-class support for” bullet to describe the server as optional and calls out both gateway and single-model endpoint.
- `docs/api.md`: adds a “New to AbstractCore? Start with Getting Started” link.
- `docs/architecture.md`: adds a short “new to AbstractCore” pointer and updates the streaming example to include a concrete `create_llm(...)` + `@tool` snippet, clarifying tool calls are executed by the host/runtime.
- `docs/media-handling-system.md`: minor quoting fix in an install command.
- `docs/troubleshooting.md`: rewrites the “Top mistakes” section (wording + adds that API keys can be persisted with `abstractcore --set-api-key ...`).
- `llms-full.txt`: updates the model list file (content changes are in the diff; this is a large text registry).

**Implications**
- Documentation clarity improvements; no runtime code changes in this commit.

---

### 3e512bf — Enhance documentation and clarify AbstractCore’s integration… (2026-02-09)

**Files changed**
- Documentation-only + model lists:
  - Adds `docs/endpoint.md` (new)
  - Updates many docs pages (`docs/server.md`, `docs/architecture.md`, `docs/api*.md`, `docs/faq.md`, etc.)
  - Updates `llms-full.txt` and `llms.txt`
  - No Python module changes in this commit (per `git show --name-status`)

**What changed (high-signal docs deltas)**
- `README.md`:
  - Adds an “AbstractFramework ecosystem” section describing AbstractCore vs AbstractRuntime and explicitly states tools are pass-through by default (`execute_tools=False`), with a mermaid diagram.
  - Adds a pointer to the new single-model endpoint doc.
- `docs/endpoint.md` (new):
  - Documents `abstractcore-endpoint` as a **single-model** OpenAI-compatible `/v1` server, contrasting it with the multi-provider gateway server.
  - Includes install/run instructions and prompt-cache control plane endpoints under `/acore/prompt_cache/*`.
- `docs/server.md`:
  - Adds cross-link to Endpoint for single-model use.
  - Adds Portkey env vars (`PORTKEY_API_KEY`, `PORTKEY_CONFIG`) in the server env example.
  - Introduces request field `agent_format` (AbstractCore extension) and rewrites the “agentic CLI integration” guidance to focus on OpenAI-compat client configuration + tool-call interoperability.
  - Updates docker snippet to remove default provider/model env vars (server routing is request-driven).
- `docs/api.md` / `docs/api-reference.md` / `docs/architecture.md` / `docs/media-handling-system.md` / `docs/troubleshooting.md`:
  - Multiple example and wording adjustments for consistency (details are present per-file in the git diff).
- `llms-full.txt` / `llms.txt`:
  - Updates the shipped model lists.

**Implications**
- Documentation now formalizes two server modes: multi-provider gateway vs single-model endpoint.
- Documentation introduces `agent_format` as a server request knob (the implementation lives in the codebase already; this commit documents it).

---

### 70564c3 — updated llms (2026-02-08)

**Files changed**
- `docs/prerequisites.md`
- `llms-full.txt`
- `llms.txt`

**What changed**
- `docs/prerequisites.md`:
  - Adds “Gateway Provider Setup (OpenRouter, Portkey)” section with env var + usage examples.
  - Adds “OpenAI-Compatible Setup” section for generic `/v1` endpoints.
  - Renames/reshapes vLLM setup section title (drops “(NVIDIA CUDA Only)” from the heading while still stating NVIDIA-only in text).
- `llms-full.txt` and `llms.txt`: large refresh/expansion of model lists.

**Implications**
- Documentation expands supported provider setup guidance (notably Portkey and OpenAI-compatible).
- Model list artifacts significantly change; no runtime code changes in this commit.

---

### 062568b — release 2.11.8 (2026-02-08)

**Files changed (code + docs + tests)**

Provider + routing
- `abstractcore/providers/portkey_provider.py` (new)
- `abstractcore/providers/registry.py`
- `abstractcore/providers/__init__.py`
- `abstractcore/architectures/detection.py`

Server / endpoint
- `abstractcore/server/__init__.py`
- `abstractcore/server/app.py`
- `abstractcore/endpoint/app.py`

Config / CLI
- `abstractcore/config/main.py`
- `abstractcore/config/manager.py`
- `abstractcore/config/vision_config.py`
- `abstractcore/utils/cli.py`
- `abstractcore/utils/version.py`

Docs + tests (selected)
- `docs/*` (multiple)
- `tests/config/test_interactive_config.py` (new)
- `tests/providers/test_portkey_provider_unit.py` (new)
- `tests/providers/test_registry_core.py`

**What changed (code)**

1) **New Portkey provider (OpenAI-compatible gateway with header routing)**
- Adds `abstractcore/providers/portkey_provider.py` implementing `PortkeyProvider` as a subclass of `OpenAICompatibleProvider`.
- Implements three mutually exclusive routing modes (precedence order is encoded in `_routing_mode()` and tested):
  - **Config mode:** `x-portkey-config`
  - **Virtual-key mode:** `x-portkey-virtual-key`
  - **Provider-direct mode:** `x-portkey-provider` + `Authorization` overridden to upstream provider API key
- Header behavior in `_get_headers()`:
  - Always includes `Content-Type: application/json`
  - When Portkey gateway API key is set:
    - `x-portkey-api-key: <key>`
    - `Authorization: Bearer <key>` (unless overwritten by provider-direct mode)
  - Adds routing headers depending on mode.
  - Merges optional user-provided `portkey_headers` as an escape hatch.
- Payload behavior in `_mutate_payload()`:
  - Tracks “explicitly set” generation parameters and strips unsolicited defaults for parameters like `temperature`, `top_p`, and `max_tokens`.
  - For reasoning model families (heuristics include `o1` and `gpt-5`), drops unsupported parameters and can rename token limit fields (`max_tokens` → `max_completion_tokens`) under explicit conditions.

2) **Provider registry + lazy provider exports updated**
- `abstractcore/providers/registry.py`:
  - Registers `portkey` provider metadata.
  - Adds import logic for `PortkeyProvider`.
  - Includes `portkey` in the provider list_models path that instantiates a minimal client for model listing.
- `abstractcore/providers/__init__.py`: adds `PortkeyProvider` to the lazy import map.
- `abstractcore/architectures/detection.py`: adds `"portkey"` to `_KNOWN_PROVIDER_PREFIXES`.

3) **Config system expanded to include Portkey API key + provider-agnostic vision fallback inputs**
- `abstractcore/config/manager.py`:
  - Adds `ApiKeysConfig.portkey` field.
  - Extends status reporting and `set_api_key(...)` handling to include `"portkey"`.
- `abstractcore/config/main.py`:
  - Adds usage examples mentioning `--set-api-key portkey ...`.
  - Updates `--set-api-key` help string to include Portkey.
  - Interactive configure updates:
    - Vision fallback now accepts arbitrary provider/model pairs (supports `provider/model` single-input form).
    - API key configuration list includes `portkey`.
    - Console log default changed from `info` to `error`.
- `abstractcore/config/vision_config.py`:
  - Removes hardcoded provider/model lists and replaces them with provider-agnostic examples.
  - Adds `_prompt_provider_and_model()` helper supporting `provider/model` shorthand input.
  - Refactors interactive “configure vision” paths so “local” and “cloud” wrappers delegate to a unified provider/model configuration flow.

4) **Server UX + schema tweaks**
- `abstractcore/server/__init__.py`:
  - Switches to lazy-loading `app`/`run_server` via `__getattr__` (documented in the file as avoiding “double-import warnings when run as a module”).
- `abstractcore/server/app.py`:
  - Routes Python warnings through structured logging by replacing `warnings.showwarning`.
  - Updates schema descriptions to mention Portkey and `PORTKEY_API_KEY`.
  - Changes OpenAPI schema `examples` structures for `ChatCompletionRequest` and `ResponsesAPIRequest` from dict maps to lists of values.
  - Adds `_resolve_external_host()` (UDP connect heuristic) and prints “Internal URL” + “External URL” at startup.
- `abstractcore/endpoint/app.py`: adds `"portkey"` to the provider prefixes stripped from `model=` in single-model endpoint mode.
- `abstractcore/utils/cli.py`: adds `portkey` to CLI provider choices and usage examples.

5) **Version bump**
- `abstractcore/utils/version.py`: `__version__` from `2.11.7` → `2.11.8`.

**Tests**
- `tests/providers/test_portkey_provider_unit.py` (new): validates routing precedence, header construction, env var resolution, payload mutation behavior, and API-key fallback behavior without network calls.
- `tests/config/test_interactive_config.py` (new): validates interactive config accepts arbitrary vision provider/model inputs and defaults console log level to `ERROR`.
- `tests/providers/test_registry_core.py`: expects `portkey` to be registered.

**Implications**
- AbstractCore gains a first-class Portkey provider with explicit header-routing modes and payload adaptation rules aimed at compatibility with strict backends.
- Config CLI and status output now include Portkey API keys; vision fallback configuration becomes provider-agnostic at the CLI layer.
- Server startup and schema generation behaviors change (warnings logging, example formatting, printed URLs, lazy import).

---

## Net diff summary vs baseline (`cede6ed` “Global Release”)

Evidence: `git -C abstractcore diff --stat cede6ed..HEAD` reports (high-level):

- Code additions/changes include:
  - New provider: `abstractcore/providers/portkey_provider.py`
  - Telegram tool robustness: `abstractcore/tools/telegram_tools.py`
  - Tool safety coercion: `abstractcore/tools/common_tools.py`
  - Music capability plumbing + `/v1/audio/music` endpoint
  - Vision endpoint model normalization for `/v1/images/*`
  - Config preflight installer: `abstractcore/config/main.py` (`--install`, `--yes`, `install_check(...)`)
- Large documentation/model-list churn:
  - `llms-full.txt` and many `docs/*.md` updates dominate line-count deltas.

