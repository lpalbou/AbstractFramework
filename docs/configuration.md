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
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

For hosted or multi-user browser access, also enable Gateway user auth:

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
```

The bootstrap token remains an admin/operator credential. Users sign in with a
Gateway user id and that user's token, then browser apps keep only an opaque
Gateway session. Gateway serves `/console` for account/runtime summary, admin
user management, optional user email metadata, token rotation, and capability
defaults selected from Gateway-discovered provider/model catalogs. Deleted users
leave retained runtime reservations; admins can transfer retained runtime data to
an existing same-tenant user or purge the retained runtime directory before
releasing the runtime id for reuse.

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
| `output.text` | Default text generation model |
| `input.text` | Default text understanding model |
| `embedding.text` | Default embeddings model |

### Set defaults in Core (single-host)

```bash
abstractcore --set-global-default ollama:qwen3:4b-instruct
```

### Set defaults through the Gateway (control plane)

In gateway-first deployments, set defaults via gateway tooling so the execution host stays consistent:

```bash
abstractgateway-config set-default output.text \
  --provider ollama \
  --model qwen3:4b-instruct
```

The gateway can update route defaults, but the default schema is Core-owned.
When Gateway user auth is enabled, the admin/default runtime overlay acts as the
Gateway baseline. Per-user writes through
`/api/gateway/config/capability-defaults/{kind}/{modality}` are stored under the
current user's runtime data plane and override the Gateway baseline only for
that user, so one user's provider/model defaults do not mutate another user's
defaults.

### Gateway provider endpoint profiles

Gateway Console also lets signed-in users create reusable provider endpoint
profiles. A profile stores a display name, description, provider family such as
`openai-compatible`, optional base URL, optional API key, capabilities, and an
optional model allowlist. The raw API key is write-only through the API/UI and is
not returned in discovery responses.

For OpenAI-compatible and other discoverable endpoints, use the console's model
discovery action to call the configured endpoint and populate the model picker.
Leaving all models unselected keeps live discovery active; selecting models
stores a fixed allowlist for that profile.

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

`~/.abstractcore/config/` stores persisted provider keys, base URLs, and defaults (written by `abstractcore --config`).

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
