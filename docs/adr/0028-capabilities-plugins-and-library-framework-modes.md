# ADR-0028: Capabilities Plugins + Library/Framework Modes (Audio/Voice/Vision/Music)

## Status
Accepted (2026-02-04)

## Dates
- Proposed: 2026-01-26
- Accepted: 2026-02-04
- Updated: 2026-05-08 (aligned with ADR-0033)

## Context
We want to add multimodal capabilities (audio/voice/vision/music; later video) to the ecosystem without:
- turning `abstractcore` into a kitchen sink,
- breaking layered architecture (ADR-0001),
- or forcing all users into durable runtime/gateway deployments.

We have two distinct user archetypes:
1) **Library users**: want a clean Python API to call LLMs and optionally do TTS/STT/vision generation without running a durable orchestrator.
2) **Framework users**: want durable runs, thin clients, artifact-backed outputs, and long-running orchestration (ADR-0021 / Topology D).

We also already have a precedent for *input enrichment fallback*:
- **Vision fallback** in `abstractcore` for text-only models with images (two-stage caption → main model).
  - This fallback is configured via AbstractCore config (provider/model, fallback chain, optional local models).

Open questions that must be clarified for maintainability:
- Where do modality implementations live (packages, deps)?
- How do we expose “must work” deterministic APIs vs agent-triggered tools?
- How do we handle unsupported modalities cleanly (errors, discovery)?
- How do we make fallback behavior explicit and transparent?

## Decision

### 1) Define two supported usage modes (conceptual, not “different products”)
**Library mode**
- User calls `abstractcore` directly (providers, tool parsing/normalization, structured output, prompt caching).
- Optional deterministic modality APIs are available when plugins are installed.
- Outputs may be returned as bytes or local asset refs; no durability guarantees.

**Framework mode**
- `abstractruntime` orchestrates durable effects; `abstractgateway` provides the remote control plane (ADR-0018/0021).
- Large media outputs are stored in `ArtifactStore` and referenced via `{"$artifact":"..."}` (ADR-0024).
- Deterministic modality actions are invoked via explicit workflow entrypoints/nodes and/or allowlisted tools (ADR-0006).

### 2) Introduce a plugin-first “capabilities” integration surface in `abstractcore`
`abstractcore` provides:
- capability interfaces (audio/voice/vision),
- a host/session-scoped `CapabilityRegistry`,
- and lazy plugin loading via Python entry points (no hard deps on modality packages).

Modality packages provide plugins:
- `abstractvoice` registers `core.voice` and `core.audio` implementations (STT/TTS + audio I/O backends).
- `abstractvision` registers `core.vision` implementations (T2I/I2I/T2V/I2V backends).
- `abstractmusic` registers `core.music` implementations when explicitly installed. It remains
  experimental and local-heavy until its base install is split or a remote music backend exists.

This keeps:
- `abstractcore` dependency-light by default (ADR-0001),
- modality deps isolated to modality packages,
- and preserves standalone usage of `abstractvoice`/`abstractvision` (they remain useful independently).

Packaging expectation (developer UX):
- `pip install abstractcore` → LLM-only (no voice/vision deps).
- `pip install abstractvoice` → voice APIs available standalone, and (when plugin support is present) `core.voice` becomes available in AbstractCore.
- `pip install abstractvision` → vision APIs available standalone, and `core.vision` becomes available in AbstractCore.
- `pip install abstractmusic` → music APIs available standalone, but not part of remote-light
  Core/Gateway defaults until the Music package has a lightweight base.

#### Note: AbstractCore Server exposes optional OpenAI-compatible image + audio endpoints
This ADR’s primary focus is the **library/framework integration contract** (plugins + artifacts).
However, code reality as of 2026-02-04:
- AbstractCore Server can expose `/v1/images/generations` and `/v1/images/edits` (OpenAI-compatible) by delegating to `abstractvision` (`abstractcore/abstractcore/server/vision_endpoints.py`).
- AbstractCore Server can also expose `/v1/audio/transcriptions` and `/v1/audio/speech` (OpenAI-compatible) by delegating to the capability plugin layer (typically `abstractvoice`) (`abstractcore/abstractcore/server/audio_endpoints.py`).
- This is an **HTTP interoperability surface** (useful for non-Python clients), not the durability contract:
  - image endpoints return `b64_json` payloads,
  - audio speech returns audio bytes (`audio/*`),
  - framework mode still prefers `ArtifactStore` + `{"$artifact":"..."}` refs (ADR-0024).

#### Server and security boundaries
Core and Gateway routes own their own inbound HTTP auth/CORS/origin policy. Capability packages
normally own outbound backend configuration: provider credentials, base URLs, model ids, timeouts,
cache paths, device choices, and backend flags.

Gateway auth must not be treated as a capability-package provider key. Core server auth must not be
treated as Gateway auth. When capability packages include local playground/example servers, those
surfaces need their own local/dev security notes and should not be documented as production
Core/Gateway serving boundaries.

### 3) Separate “LLM input modalities” from “transform/generative capabilities”
We must not conflate these:
- `abstractcore/assets/model_capabilities.json` describes **LLM input modalities** (can this model accept image/audio/video as message input?).
- Modality packages describe **capabilities** (STT/TTS/T2I/I2I/… backends), which may not be LLMs at all.

Capability catalogs should stay close to implementations:
- AbstractCore should not try to become the global registry of “all possible vision/audio models”.
- Instead, modality packages expose *their* supported backends/models via plugin discovery/introspection.
- AbstractCore integrates them and provides consistent errors and configuration surfaces.

### 4) Treat fallback as explicit *context enrichment*, not silent semantic change
When a user attaches media to an LLM call (`generate(..., media=[...])`) and the target model lacks input support:
- the system may run an **enrichment fallback** (caption/transcribe/frames) *only when configured or requested*,
- inject a **short observation** string into the main request,
- and surface fallback metadata for transparency (see #6).

Audio-specific policy must avoid “everything becomes STT” surprises:
- default should not silently transcribe arbitrary audio (music/signals).
- STT should be an explicit operation unless the caller selects a policy that enables it.

#### 4.1) Fallback must be configured via AbstractCore config (like vision fallback)
Enrichment fallback is part of **input handling**; it therefore belongs to AbstractCore’s media/config layer.

Requirement:
- fallback enablement/strategy is controlled through AbstractCore config (CLI + config file), per modality (image/audio/video).

Configuration must be able to reference backends in two ways:
1) **LLM backend**: `provider + model` (e.g. OpenAI/Anthropic/OpenRouter/HF local) used for caption/understanding.
2) **Capability backend**: a plugin-provided backend id (e.g. `abstractvoice:stt:faster-whisper`) when the enrichment step is not an LLM call.

If a configured backend is not available (missing plugin, missing API key, missing local models), `--status` must show “Not configured/Not ready” and calls must fail with actionable errors.

### 5) Naming/taxonomy
To stay simple and not overengineer:
- Keep `core.vision` as the umbrella for image+video generation (with operations like `t2i/i2i/t2v/i2v`).
- Keep `core.audio` for general audio transforms/analysis.
- Keep `core.voice` as the speech-oriented UX surface (STT/TTS), but treat outputs as `audio/*`.

For artifacts:
- `tags.modality` uses physical media types: `audio|image|video`.
- Use `tags.task` for domain tasks: `tts|stt|audio_caption|t2i|...`.

Pragmatic package naming note:
- `abstractvoice` should remain speech-focused short-term; do not imply “music/signal analysis” just because the modality is audio.
- If/when we expand substantially beyond speech, prefer introducing a new package/plugin (e.g. `abstractaudio` / `abstractmusic`) rather than renaming `abstractvoice` prematurely.

### 6) Capability discovery + clean missing-plugin behavior
Both modes require:
- a discovery API (library: `core.capabilities.status()`; framework: a gateway endpoint that reports installed/enabled capabilities),
- and actionable failures when a capability is missing:
  - include install hints (`pip install ...`), configuration hints, and supported alternatives.

In framework mode, missing capabilities must be representable as:
- a structured tool failure and/or deterministic node failure,
- plus an optional host UX event so thin clients can render a clear message (ADR-0017).

Discovery must distinguish:

- `installed`: package import exists.
- `registered`: plugin/backend registered.
- `configured`: required env/config exists.
- `ready`: cheap non-generating preflight passes, or no preflight is needed.
- `route_available`: HTTP route exists.
- `available`: route exists, backend is ready, and policy permits use.

### 7) Out of scope (v0): generative/output fallback
This ADR does **not** define “output fallback routing” such as:
- “main LLM cannot generate an image → route generation to a different backend automatically”.

That requires additional architectural work (approvals, budgets, provenance, retries, durable job semantics) and must be tracked separately.

## Consequences

### Positive
- Clear “two doors” UX: small apps can use `abstractcore` directly; durable deployments use runtime/gateway.
- `abstractcore` stays clean and dependency-light; modality packages remain modular (ADR-0001).
- Deterministic modality APIs exist without requiring “LLM decides to call tools”.
- Fallback behavior is configurable and transparent rather than magical.

### Negative
- Adds a plugin API surface that must be versioned carefully.
- Requires disciplined lazy imports in plugins (avoid heavy model loads at import time).
- Some “magic convenience” (automatic fallback) must remain opt-in to keep semantics honest.

### Neutral
- Tool exposure remains an adapter view of capabilities (agent-facing), not the only integration mechanism.
- We can later add `core.video` as an alias if video-specific UX/contracts justify it.

## Packages Affected
- AbstractCore (capability registry, media policies, fallback transparency)
- AbstractVoice (plugin + tools + artifact adapter)
- AbstractVision (plugin + facade + artifact adapter)
- AbstractMusic (experimental plugin + artifact adapter)
- AbstractRuntime / AbstractGateway (durable wiring, artifact-first outputs)
- AbstractCode (thin-client UX)

## Related
- ADR-0001: Layered Architecture
- ADR-0006: Durable Tool Execution (ToolExecutor boundary)
- ADR-0016: Tool calling pipeline + boundaries
- ADR-0017: Host UI events and durable prompts
- ADR-0021: Deployment topologies
- ADR-0024: Attachment placeholders + compaction invariants
- ADR-0026: Truncation policy and contract
- ADR-0033: Install profiles, config entrypoints, and server boundaries
- Design note: `docs/backlog/unclear/generative-capabilities/recommendation.md`
