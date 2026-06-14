# Configuration

This page answers two practical questions:

1. **What do I need to configure first to be productive?**
2. **Where do defaults live in a Core-first vs Gateway-first setup?**

Key principle: **Core owns model/provider defaults; Gateway owns durable execution and operations.**

---

## Core-first quick start

### Interactive wizard (recommended)

```bash
abstractcore --config      # guided setup — persists to ~/.abstractcore/config/
abstractcore --status      # show current config
abstractcore --install     # check readiness + download missing assets
```

The wizard walks through: default provider/model, base URLs, API keys, vision fallback, audio/video strategies, embeddings, and logging. Config is stored in `~/.abstractcore/config/abstractcore.json`.

### Manual environment variables

**Ollama** (local, free):

```bash
export OLLAMA_HOST="http://localhost:11434"
```

**OpenAI-compatible server** (LM Studio, vLLM, LocalAI, llama.cpp):

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"
```

**Cloud APIs**:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Gateway-first quick start

### Required

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

When user auth is enabled, `abstractgateway serve` ensures `default/admin`
exists and writes the first browser-login token to
`$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token`. Users sign in with a
Gateway user id and that user's token, then browser apps keep only an opaque
Gateway session. `ABSTRACTGATEWAY_AUTH_TOKEN` is still available for legacy
server/operator bearer-token deployments, but it maps to `local-admin` and is
not a browser sign-in token.

Gateway serves `/console` for account/runtime summary, admin user management,
optional user email metadata, token rotation, retained runtime transfer/purge,
provider connections, and multimodal capability defaults selected from
available providers. Deleted users leave retained runtime reservations;
admins can transfer retained runtime data to an existing same-tenant user or
purge the retained runtime directory before releasing the runtime id for reuse.

### Recommended (bundle-based workflows)

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Optional: set only for a custom bundle registry. When unset, Gateway uses
# the packaged shipped bundle directory containing basic-agent.
# export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
```

### Start

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

---

## Model/provider defaults (capability routes)

AbstractCore organizes defaults as **capability routes** — stable slots scoped by capability, not by application:

| Route | Meaning |
|---|---|
| `input.text` | Canonical LLM text model for understanding and generation |
| `output.text` | Read-only derived view of `input.text` |
| `input.image` | Image-understanding fallback when `input.text` is not vision-capable |
| `input.video` | Video-understanding fallback when native video/frame support is not available or should be overridden |
| `input.voice` | Speech-to-text fallback for audio attachments |
| `input.sound` | Non-speech audio/SFX understanding route, not a speech transcription route |
| `input.music` | Music-audio understanding route, not a speech transcription route |
| `embedding.text` | Default embeddings model |

### Set defaults in Core (single-host)

```bash
abstractcore config set-default input.text \
  --provider ollama \
  --model qwen3:4b-instruct

abstractcore config defaults
```

The older `abstractcore --set-global-default ...` and
`abstractcore --set-capability-default ...` flags remain supported for
compatibility. The `abstractcore config ...` form is the preferred explicit
route-default syntax.

Model discovery for LLM and embedding defaults can filter by Core route keys,
for example `capability_route=input.image,output.text`,
`capability_route=input.sound,output.text`, or
`capability_route=embedding.text`. Generated image/video/voice/sound/music
defaults use capability plugin catalogs instead, so plugin readiness and
download/setup state are not stored in `model_capabilities.json`.

AbstractFlow uses the same Gateway/Core discovery contract for text model
authoring. Text provider/model selectors ask Gateway for `output.text` models,
and the Models Catalog node can store a capability route such as
`input.image,output.text` so workflows can discover the provider's models for a
specific input/output shape at run time. Flow stores only selection intent; Core
and Gateway remain the source of truth for model capability metadata.

### Reasoning and thinking controls

AbstractCore exposes a provider-neutral `thinking` generation option for models
that support explicit reasoning controls. Gateway accepts the same field on
`POST /api/gateway/runs/start` and stores it as `_runtime.thinking` for the
run:

```json
{
  "bundle_id": "basic-agent",
  "input_data": {"prompt": "Plan the migration"},
  "thinking": "high"
}
```

Flow LLM Call and Agent nodes also expose a Reasoning selector and a `thinking`
input pin. A node setting or pin value overrides the run default for that node;
leaving it on Auto inherits the Gateway/runtime default. Core performs the
provider-specific translation or unsupported-parameter handling.

### Core provider endpoint profiles

For reusable OpenAI-compatible endpoints, configure a named Core provider
profile once and point route defaults at its virtual provider id:

```bash
export OVH_AI_API_KEY="..."

abstractcore config set-provider ovh-provider \
  --family openai-compatible \
  --base-url https://oai.endpoints.kepler.ai.cloud.ovh.net/v1 \
  --api-key $OVH_AI_API_KEY \
  --name "OVH Provider" \
  --description "OVH hosted OpenAI-compatible endpoint"

abstractcore config models ovh-provider

abstractcore config set-default input.text \
  --provider endpoint:ovh-provider \
  --model Qwen3.5-9B
```

`endpoint:ovh-provider` is the reusable public id. The URL and key stay in the
Core config file, not in exported workflows. Use
`abstractcore config providers --json` to list profiles; raw keys are not
printed.

If you want the config to store an environment reference instead of the expanded
secret value, pass the variable literally, for example `--api-key
'$OVH_AI_API_KEY'`.

### Set defaults through the Gateway (control plane)

In gateway-first deployments, set defaults via gateway tooling so the execution host stays consistent:

```bash
abstractgateway-config set-default input.text \
  --provider ollama \
  --model qwen3:4b-instruct

abstractgateway-config defaults
```

The gateway can update route defaults, but the default schema and file format
are Core-owned. When Gateway user auth is enabled, the Gateway baseline is
stored as a Core config file:

```text
$ABSTRACTGATEWAY_DATA_DIR/config/abstractcore.json
```

Per-user writes through
`/api/gateway/config/capability-defaults/{kind}/{modality}` or
`/api/gateway/config/capability-defaults/{kind}/{modality}/{task}` are stored
as a runtime-scoped Core config file:

```text
$ABSTRACTGATEWAY_DATA_DIR/users/<tenant>/<runtime>/runtime/config/abstractcore.json
```

User runtime defaults override the Gateway baseline only for that runtime, so
one user's provider/model defaults do not mutate another user's defaults.
Gateway no longer reads or writes `config/capability_defaults.json`; existing
overlay files are ignored. Recreate those defaults with
`abstractgateway-config set-default ...`.

### Gateway provider connections

Gateway Console also lets signed-in users create reusable provider connections
through a guided setup flow for OpenAI, Anthropic, OpenRouter, Portkey, LM
Studio, Ollama, and custom OpenAI-compatible endpoints. A connection stores a
display name, description, provider family, optional base URL, optional API key,
and optional advanced model allowlist. The raw API key is write-only through the
API/UI and is not returned in discovery responses. AbstractCore owns model
capability metadata, so normal setup does not ask users to classify models
manually.

The **Providers** tab is where endpoint base URLs and API keys are configured.
Its **Test** action calls the selected provider or endpoint and previews model
discovery before saving. Leaving all advanced model restrictions unselected
keeps live discovery active; selecting models stores a fixed allowlist for that
profile. The **Multimodal Capabilities** tab intentionally does not ask for a
base URL or API key: it maps each capability route to one available provider
and one discovered/allowed model. Available providers include saved Gateway
provider connections plus direct providers such as `openai` or `anthropic`
when their required key is already present in scoped Core config or process
environment. LM Studio and Ollama also appear automatically when Gateway can
reach their configured or default local endpoints and discover models from
them.

The **Sandbox** tab uses the same provider/default contract. Choose a configured
capability route, then send a short prompt. Text chat uses the selected text
default, and generated media routes such as `output.image.text_to_image`,
`output.video.text_to_video`, `output.voice`, `output.sound`, or
`output.music` run through that route's configured provider/model and return
the generated artifact link. Image edit, image upscale, and image-to-video use
separate defaults: `output.image.image_to_image`,
`output.image.image_upscale`, and `output.video.image_to_video`. Gateway
Console presents these concrete generated-media routes instead of the broad
`output.image` and `output.video` compatibility defaults.

`input.voice`, `input.video`, `input.sound`, and `input.music` are fallback gates, not hidden
package probes. If a route is unconfigured and the primary text model cannot
handle that input natively, the request fails with a configuration error rather
than silently using an installed speech, vision, audio, or music package.
`input.video`, `input.sound`, and `input.music` can be reported as covered by
`input.text` when the text model supports those inputs; operators can still
override them with dedicated routes.

After creation, the profile appears in provider discovery as a virtual provider
id such as `endpoint:office-vllm`. Use that provider id in AbstractFlow nodes or
Gateway capability defaults, then select a discovered/allowed model normally.
At run time Gateway resolves the virtual provider into the real provider family,
base URL, and key for the current runtime call; workflow JSON and exported
bundles should not contain raw secrets.

---

## Storage and persistence

### Gateway data directory

`ABSTRACTGATEWAY_DATA_DIR` is the durability root:

- Run state
- Ledger history
- Artifacts (files, media, big payloads)
- Schedules

**Back up this directory** if you care about long-lived runs and audit trails.

### Optional SQLite backend

For production deployments, you can use SQLite for run metadata (artifacts stay file-backed):

```bash
export ABSTRACTGATEWAY_STORE_BACKEND=sqlite
export ABSTRACTGATEWAY_DB_PATH="$ABSTRACTGATEWAY_DATA_DIR/gateway.sqlite3"
```

### Core config directory

`~/.abstractcore/config/` stores persisted provider keys, base URLs, and
defaults for direct Core usage (written by `abstractcore --config` or
`abstractcore config ...`). You can target another config explicitly with
`ABSTRACTCORE_CONFIG_FILE`, `ABSTRACTCORE_CONFIG_DIR`, or
`abstractcore config --config-file /path/to/abstractcore.json ...`.

---

## Client configuration (Observer / Flow Editor / Code Web UI)

All gateway-backed browser UIs need two things:

- **Gateway base URL** (example: `http://127.0.0.1:8080`)
- **Gateway user + user token** in hosted user-auth mode

Local single-user tools can still use `ABSTRACTGATEWAY_AUTH_TOKEN` as an
operator token. Hosted browser apps should exchange user tokens for Gateway
browser sessions and should not store bearer tokens in browser storage.
AbstractFlow, AbstractCode Web, and AbstractObserver use this hosted
browser-session path when you provide a Gateway user id.

When these browser UIs are served from a non-loopback hostname, the Gateway URL
comes from the UI server configuration. Browser-supplied Gateway URL changes
are rejected unless the app-specific remote override is enabled behind your own
access control.

### AbstractObserver

```bash
npx @abstractframework/observer
```

Set Gateway URL, Gateway user, and that user's token in the UI
(http://localhost:3001). Observer exchanges the token for an app-scoped browser
session and does not persist the token in browser settings.

### Flow Editor

```bash
npx @abstractframework/flow
```

Optional convenience variable:

```bash
export ABSTRACTFLOW_GATEWAY_URL="http://127.0.0.1:8080"
```

### Code Web UI

```bash
npx @abstractframework/code
```

Set the gateway URL in the UI settings (http://localhost:3002).

---

## Multimodal capability plugins

Modalities are optional and become available when installed:

| Plugin | Capability | API surface |
|---|---|---|
| `abstractvoice` | Voice | `llm.voice` / `llm.audio` |
| `abstractvision` | Images | `llm.vision` |
| `abstractmusic` | Music | `llm.music` |

**Plugins are configured on the host that actually executes** (local app or gateway host), because that's where model downloads and hardware constraints apply.

---

## Per-project configuration references

This repo covers the overview. Each component repo owns its detailed configuration surface:

- **AbstractCore**: [centralized config](https://github.com/lpalbou/abstractcore/blob/main/docs/centralized-config.md), [prerequisites](https://github.com/lpalbou/abstractcore/blob/main/docs/prerequisites.md)
- **AbstractGateway**: [configuration](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md), [security](https://github.com/lpalbou/AbstractGateway/blob/main/docs/security.md)
- **AbstractVoice**: [installation](https://github.com/lpalbou/abstractvoice/blob/main/docs/installation.md), [model management](https://github.com/lpalbou/abstractvoice/blob/main/docs/model-management.md)
- **AbstractVision**: [configuration](https://github.com/lpalbou/abstractvision/blob/main/docs/reference/configuration.md), [backends](https://github.com/lpalbou/abstractvision/blob/main/docs/reference/backends.md)

---

## Related docs

- **[Getting Started](getting-started.md)** — first run Core-first or Gateway-first
- **[Architecture](architecture.md)** — what lives where and why
- **[Glossary](glossary.md)** — capability routes, durable execution terms
