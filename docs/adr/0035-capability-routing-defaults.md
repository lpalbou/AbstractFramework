# ADR-0035: Capability Routing Defaults

## Status
Accepted (2026-05-24)

## Dates
- Proposed: 2026-05-24
- Accepted: 2026-05-24
- Revised: 2026-05-24

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
- `scene3d`

The current route matrix is:

| Key | Meaning |
|-----|---------|
| `input.text` | Text understanding / prompt input |
| `input.image` | Image understanding / VLM or image caption route |
| `input.video` | Video understanding / native video or frame route |
| `input.voice` | Speech input / STT route |
| `input.sound` | Non-speech audio understanding route |
| `input.scene3d` | 3D scene understanding route |
| `output.text` | Text generation route |
| `output.image` | Image generation route |
| `output.video` | Video generation route |
| `output.voice` | Speech/TTS generation route |
| `output.sound` | Sound/music generation route |
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
writes explicit `input.text` and `output.text` route defaults while older config fields still
exist.

### 6) Residency is separate from defaults

Model residency routes list provider-reported loaded/resident models. Capability defaults list
configuration. A default row may show `provider not loaded`; that is an honest state, not a load
failure by itself.

Thin clients should render these as separate views:

- Loaded models: provider/runtime residency truth.
- Defaults: route configuration for `input`, `output`, `embedding`, and `rerank`.

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
- Gateway code must not add new persisted provider/model defaults files.
- Gateway embedding code must resolve `embedding.text` through the execution-host capability
  defaults path.
- AbstractFlow must keep provider-loaded residency and routing defaults in separate tabs/views.
- Backlog work that changes these boundaries must cite this ADR.

## Validation

- Core config tests cover explicit route defaults, `input.text`/`output.text` global-default writes,
  and embedding route/base URL synchronization.
- Core server tests cover the `/v1/config/capability-defaults/{kind}/{modality}` contract.
- Gateway tests cover route-default precedence and embedding endpoint use of `embedding.text`
  without `gateway_embeddings.json`.
- Flow frontend contract tests cover the separated loaded/defaults modal and absence of browser
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
