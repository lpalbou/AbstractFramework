# Getting started

AbstractFramework is an ecosystem: you can use **one package** (library-style), or compose several into a durable, observable system.
This page is written to get you to something working quickly.

## Pick your starting point

| Goal | Start with | You’ll end up using |
|---|---|---|
| Call LLMs across providers (tools/structured output/media) | **AbstractCore** | `abstractcore` |
| Build restart-safe workflows (pause → resume) | **AbstractRuntime** | `abstractruntime` (+ `abstractcore` integration when you need LLM/tools) |
| Use ready-made agent loops (ReAct/CodeAct/MemAct) | **AbstractAgent** | `abstractagent` (+ runtime/core underneath) |
| Run a local interactive terminal app | **AbstractCode** | `abstractcode` |
| Deploy remote runs + control from a browser | **AbstractGateway + AbstractObserver** | `abstractgateway` (server) + `abstractobserver` (UI) |
| Add voice or image generation | **AbstractVoice / AbstractVision** | `abstractvoice`, `abstractvision` (via AbstractCore capability plugins) |

## Prerequisites

- **Python**: 3.10+ (the `abstractframework` meta-package requires this)
- **Node.js**: 18+ (only if you want the browser UI `abstractobserver`)
- An LLM backend:
  - Local (recommended): **Ollama**, LM Studio, vLLM, llama.cpp, LocalAI…
  - Cloud (optional): OpenAI, Anthropic…

## Install options (Python)

### Option A: meta-package bundles (convenient)

```bash
pip install abstractframework
```

Common bundles (zsh: keep the quotes):

```bash
pip install "abstractframework[all]"      # full Python ecosystem (large)
pip install "abstractframework[backend]"  # core+runtime+agent+flow+gateway+memory+semantics
pip install "abstractframework[code]"     # AbstractCode terminal TUI
pip install "abstractframework[gateway]"  # AbstractGateway HTTP server
```

### Option B: install only what you need (recommended)

- Just the unified LLM client: `pip install abstractcore`
- Durable runtime: `pip install abstractruntime`
- Agent patterns: `pip install abstractagent`
- Visual workflows: `pip install abstractflow`
- Terminal TUI: `pip install abstractcode`
- Gateway server: `pip install "abstractgateway[http]"`

## Quick path 1: local terminal agent (AbstractCode + Ollama)

1) Start Ollama and pull a model:

```bash
ollama serve
ollama pull qwen3:1.7b-q4_K_M
export OLLAMA_HOST="http://localhost:11434"
```

2) Install and run AbstractCode:

```bash
pip install abstractcode
abstractcode --provider ollama --model qwen3:1.7b-q4_K_M
```

Inside the app:
- run `/help` for the authoritative command list
- tool execution is approval-gated by default (toggle with `/auto-accept` or `--auto-approve`)
- attach local files by mentioning `@path/to/file` in your prompt

## Quick path 2: deploy a run gateway + observe (AbstractGateway + AbstractObserver)

This is the recommended “remote control-plane” setup: the gateway owns durability; UIs are thin clients.

### 2.1 Install

```bash
pip install "abstractgateway[http]"
```

If your workflows use LLM calls or tool calls in **bundle mode**, also install:

```bash
pip install "abstractruntime[abstractcore]>=0.4.0"
```

### 2.2 Start the gateway (bundle mode)

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"   # directory of *.flow files (or a single .flow)
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Required by default: the gateway refuses to start without a token.
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"

abstractgateway serve --host 127.0.0.1 --port 8080
```

Smoke checks:

```bash
curl -sS "http://127.0.0.1:8080/api/health"

curl -sS -H "Authorization: Bearer $ABSTRACTGATEWAY_AUTH_TOKEN" \
  "http://127.0.0.1:8080/api/gateway/bundles"
```

If `bundles.items` is empty, you can either:
- put `*.flow` bundles under `ABSTRACTGATEWAY_FLOWS_DIR`, or
- upload a bundle via `POST /api/gateway/bundles/upload` (see AbstractGateway docs).

### 2.3 Run the browser UI (AbstractObserver)

```bash
npx abstractobserver
```

Open `http://localhost:3001` and configure:
- **Gateway URL**: `http://127.0.0.1:8080`
- **Auth token**: your `ABSTRACTGATEWAY_AUTH_TOKEN`

### 2.4 Where do workflows/bundles come from?

Workflows are typically distributed as `.flow` bundles (zip files) that contain VisualFlow JSON.
You can pack them with **AbstractFlow**:

```bash
pip install abstractflow
abstractflow bundle pack /path/to/root.json --out /path/to/bundles/my.flow --flows-dir /path/to/flows
```

If you don’t have a flow yet, start with the example flows in the AbstractFlow repo:
https://github.com/lpalbou/abstractflow/tree/main/web/flows

## Next reading

- [Architecture](architecture.md) — core concepts (runs, ledger, waits, bundles)
- [Configuration](configuration.md) — common env vars and where to configure providers
- [FAQ](faq.md) — troubleshooting and “which package should I use?”
