# ADR-0035: Capability Routing Defaults

## Status
Accepted (2026-05-24)

## Dates
- Proposed: 2026-05-24
- Accepted: 2026-05-24
- Revised: 2026-05-24
- Revised: 2026-06-03

## Context

AbstractFramework previously had several overlapping default concepts:

- AbstractCore global provider/model defaults for text LLM calls.
- AbstractCore media fallback settings for image/audio/video input enrichment.
- Gateway-owned text environment defaults for durable text runs.
- Gateway-owned embedding provider/model settings.
- Capability-package configuration for voice, vision, music, and future modality packages.
- AbstractFlow UI rows that mixed provider-loaded residency state with configured defaults.

This made the user model unclear. A configured default is not proof that a provider has the model
loaded, input capabilities are not the same thing as generative capabilities, and embeddings/rerank
are not input/output directions.

The framework is moving toward an AbstractCore entrypoint shaped like
`generate(request, provider, model, output)`, and later `generate(request, output)` once route
defaults are complete. That requires one small routing-default abstraction shared by Core,
Runtime, Gateway, CLI tooling, installers, and thin clients.

## Decision

### 1) Route defaults are keyed by kind and modality

The shared default key is:

```text
<kind>.<modality>
```

Route kinds:

- `input`: understanding/enrichment routes for user-provided media or context.
- `output`: generative routes for content the framework produces.
- `embedding`: vectorization routes for retrieval and indexing.
- `rerank`: ranking routes for a future reranker manager.

Core modality names are:

- `text`
- `image`
- `video`
- `voice`
- `sound`
- `music`
- `scene3d`

The current route matrix is:

| Key | Meaning |
|-----|---------|
| `input.text` | Canonical LLM text route for understanding and generation |
| `input.image` | Image understanding fallback when `input.text` is not vision-capable |
| `input.video` | Video understanding / native video or frame route |
| `input.voice` | Speech input / STT route |
| `input.sound` | Non-speech audio understanding route |
| `input.music` | Music-audio understanding route |
| `input.scene3d` | 3D scene understanding route |
| `output.text` | Read-only derived view of `input.text` |
| `output.image` | Image generation route |
| `output.video` | Video generation route |
| `output.voice` | Speech/TTS generation route |
| `output.sound` | Sound effects / text-to-audio generation route |
| `output.music` | Music generation route |
| `output.scene3d` | 3D scene generation route |
| `embedding.text` | Text embedding route |
| `embedding.image` | Image or multimodal embedding route |
| `rerank.text` | Text reranking route; reserved until the reranker manager exists |

### 2) Default route payloads are intentionally small

Each route may define:

```json
{
  "provider": "lmstudio",
  "model": "qwen/qwen3.6-35b-a3b",
  "base_url": "http://127.0.0.1:1234/v1",
  "options": {
    "voice": "M1"
  }
}
```

`provider`, `model`, and `base_url` are shared fields. `options` is an opaque JSON object owned by
the selected provider/capability plugin. Examples include `voice`, `profile`, `language`, device,
quality preset, or provider-specific backend flags.

Secrets are not part of this route payload. API keys remain provider credentials managed by
AbstractCore, Gateway deployment secrets, or capability-package configuration.

`base_url` is interpreted from the execution host that performs the capability call. In split
deployments, a provider URL reachable from the Runtime/Core host may not be reachable from Gateway
or the browser, and the control plane must not pretend otherwise.

Effective control-plane rows may add derived metadata such as `source`, `status`, `configured`,
`covered_by`, `read_only`, `overrideable`, `available_actions`, or validation/readiness hints.
Those fields are not persisted route-default payload fields. They are computed from configured
Core routes, model capability coverage, provider catalogs, plugin readiness, and host write policy.

### 2.1) Model capability metadata is route-normalized but not a defaults store

`abstractcore/assets/model_capabilities.json` may expose route-keyed native model support metadata
that uses the same `input.*`, `output.*`, `embedding.*`, and `rerank.*` vocabulary as capability
defaults. This metadata answers questions such as "can this model natively satisfy `input.image`,
`input.sound`, or `embedding.text`?"

It does not replace capability defaults, provider catalogs, plugin catalogs, or readiness checks.
Static model metadata must not claim that a configured provider is reachable, a local model is
downloaded or loaded, a plugin is installed, or a route is allowed by policy. Generative and
transform backend inventories remain owned by the capability packages that implement them, per
ADR-0028.

### 3) Core owns the schema and persistence

AbstractCore owns the shared schema and parser in `abstractcore.config.capability_defaults`.

AbstractCore persists route defaults in `~/.abstractcore/config/abstractcore.json` under
`capability_defaults`. These defaults apply to direct Core usage and to Runtime hosts that load
AbstractCore in-process.

Capability-default APIs list explicit route records only. Older global text defaults and older
embedding fields are not silently displayed as configured route rows. Compatibility setters may
write explicit route records while older lower-level code is retired, but the route record is the
new source of truth.

### 4) Gateway is the control plane, not a second defaults owner

AbstractGateway does not create separate persisted provider/model/defaults files.

Gateway controls the execution host's Core/Runtime defaults:

- In embedded or co-located deployments, Gateway reads and writes the local AbstractCore config.
- In split deployments, Gateway proxies reads and writes to the configured AbstractCore server for
  the Runtime/Core host. If that server does not expose writable config routes, Gateway reports the
  defaults as unavailable or read-only instead of persisting divergent local defaults.
- Gateway may still own deployment internals such as Gateway bind host/port, auth token, store
  backend, and the Core server URL/token it uses to reach the execution host.

Embedding generation follows the same boundary. Gateway resolves `embedding.text` from the
execution host. In embedded mode it may instantiate the local Core embedding manager. In split mode
it delegates embedding generation to the remote AbstractCore `/v1/embeddings` endpoint so provider
`base_url` is evaluated from the Core host, not from the Gateway host.

### 5) Precedence

Effective routing precedence is:

1. explicit request/run values, when host policy permits them;
2. workflow/flow defaults;
3. execution-host AbstractCore capability route defaults;
4. capability package defaults, with explicit fallback/readiness reporting.

Legacy environment defaults are not part of the conceptual model. New setup surfaces, docs, and
scripts should use capability routes instead of Gateway provider/model env defaults.

For text setup convenience, `abstractcore --set-global-default lmstudio:qwen/qwen3.6-35b-a3b`
writes the canonical `input.text` route default while older config fields still
exist. Writes to `output.text` are accepted for compatibility but canonicalize to
`input.text`.

`input.image` is a fallback route, not a second default for every vision-capable
LLM. If the configured `input.text` model is known in AbstractCore's
model-capability registry to accept image input, effective defaults may report
`input.image` as covered by `input.text` and make it read-only in control-plane
UI.

`input.video` is also a fallback route. If the configured `input.text` model is
known to handle visual frames or video, effective defaults may report
`input.video` as covered by `input.text`, but the row remains overrideable so an
operator can route video through a dedicated VLM/video backend.

`input.voice` gates speech-to-text fallback. Installed voice/STT packages do not
create hidden audio fallback behavior by themselves; a text-only model needs an
explicit `input.voice` route or an explicit per-request speech-to-text policy.
`input.sound` is non-speech audio understanding and must not be reused as a
speech transcription route.

`input.sound` and `input.music` may be covered by `input.text` only when the
configured text route points to a model that AbstractCore's model-capability
registry says accepts those native audio/music inputs. They remain overrideable
so operators can choose a dedicated audio-understanding backend.

### 6) Residency is separate from defaults

Model residency routes list provider-reported loaded/resident models. Capability defaults list
configuration. A default row may show `provider not loaded`; that is an honest state, not a load
failure by itself.

Thin clients should render these as separate views:

- Loaded models: provider/runtime residency truth.
- Defaults: route configuration for `input`, `output`, `embedding`, and
  `rerank`, edited from the control plane that owns the runtime configuration.

AbstractFlow now keeps Model Residency loaded-only and leaves default editing to
Gateway Console or Core/Gateway config CLIs. Flow provider selectors expose a
blank `Auto (Gateway default)` option instead of materializing defaults into
saved workflows.

## Consequences

### Positive

- Establishes one user-facing routing model for Core, Gateway, CLI, installers, and Flow.
- Avoids mixing default configuration with loaded-provider truth.
- Supports embeddings and future reranking without bending input/output terminology.
- Aligns with future `generate(request, output)` defaults.
- Keeps split deployments honest about which host evaluates provider URLs.

### Negative

- Existing text-only and Gateway embedding settings need migration or removal from older docs and
  scripts.
- Split deployments need a Core server/control-plane route for writable defaults; otherwise Gateway
  can report defaults but should not invent a local source of truth.
- Some plugin-specific option schemas remain opaque until capability catalogs expose typed
  controls.

### Neutral

- Capability defaults do not install plugins or load models.
- `rerank.text` is a reserved configuration slot; it does not imply a reranker manager exists.

## Enforcement

- New capability-default API fields use `kind`, not `direction`.
- Persisted route defaults stay limited to `provider`, `model`, `base_url`, and `options`; row
  `source`/`status`/`action`/coverage/readiness metadata must be derived by effective-default APIs
  or thin clients.
- Model capability registry changes that add route-keyed support metadata must use the same route
  vocabulary as this ADR and must not introduce nested boolean `input_capabilities` /
  `output_capabilities` as a second public taxonomy.
- `model_capabilities.json` must not become a provider/plugin readiness or acquisition catalog;
  capability package catalogs remain the authority for implemented transform/generative backends.
- Gateway code must not add new persisted provider/model defaults files.
- Gateway embedding code must resolve `embedding.text` through the execution-host capability
  defaults path.
- AbstractFlow must not mix provider-loaded residency with routing-default
  editing. It may show loaded models for operator visibility, but default route
  editing belongs in Gateway Console or Core/Gateway config CLIs.
- Backlog work that changes these boundaries must cite this ADR.

## Validation

- Core config tests cover explicit route defaults, `output.text` canonicalization
  to `input.text`, image fallback coverage by vision-capable text models, and
  embedding route/base URL synchronization.
- Core model-registry tests cover any route-keyed capability metadata, derived broad-boolean
  compatibility views, and rejection of route taxonomy drift or unsupported source/status/action
  fields in raw model records.
- Core media-policy tests cover explicit `input.voice` STT fallback gating and
  explicit `input.video` VLM/frame fallback routing.
- Core server tests cover the `/v1/config/capability-defaults/{kind}/{modality}` contract.
- Gateway tests cover route-default precedence and embedding endpoint use of `embedding.text`
  without `gateway_embeddings.json`.
- Flow frontend validation covers loaded-only Model Residency behavior,
  `Auto (Gateway default)` provider switch-back options, and absence of browser
  native confirmation dialogs.

## Packages Affected

- `abstractcore`
- `abstractgateway`
- `abstractflow`
- capability packages (`abstractvoice`, `abstractvision`, `abstractmusic`, future `abstractsound`,
  `abstractvideo`, `abstract3d`, reranker package)
- installers and setup wizards

## Related

- Backlog 0139: `docs/backlog/completed/0139_unified_framework_capability_defaults.md`
- ADR-0028: `docs/adr/0028-capabilities-plugins-and-library-framework-modes.md`
- ADR-0031: `docs/adr/0031-workflow-llm-routing-overrides-provider-model-and-base-url.md`
- ADR-0033: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
