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

### Recommended (bundle-based workflows)

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
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
- **Bearer token** (must match `ABSTRACTGATEWAY_AUTH_TOKEN`)

### AbstractObserver

```bash
npx @abstractframework/observer
```

Set the gateway URL + token in the UI (http://localhost:3001).

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
