# Configuration

AbstractFramework is modular, so configuration is **per component**.
This page lists the knobs people most commonly need on day 1 and points you to the canonical docs for each project.

## LLM providers (AbstractCore)

AbstractCore supports multiple providers (cloud and local). Two common local setups:

### Ollama (local)

```bash
export OLLAMA_HOST="http://localhost:11434"
```

Use with:

```python
from abstractcore import create_llm
llm = create_llm("ollama", model="qwen3:4b-instruct")
```

### OpenAI-compatible servers (LM Studio / vLLM / LocalAI / llama.cpp)

Most OpenAI-compatible servers accept:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"  # many local servers ignore this but clients require a value
```

Then:

```python
from abstractcore import create_llm
llm = create_llm("lmstudio", model="qwen/qwen3-4b-2507", base_url="http://127.0.0.1:1234/v1")
```

### Cloud keys

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Centralized config (recommended)

AbstractCore can persist defaults and keys to:
`~/.abstractcore/config/abstractcore.json`.

```bash
abstractcore --configure
abstractcore --status
```

Canonical docs:
- https://github.com/lpalbou/abstractcore/blob/main/docs/centralized-config.md
- https://github.com/lpalbou/abstractcore/blob/main/docs/prerequisites.md

## AbstractGateway (server configuration)

AbstractGateway is the remote “run control plane”. The minimum you usually need:

### Required by default

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

### Workflow source + durability root

Bundle mode (recommended):

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"   # *.flow bundles (or a single .flow file)
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
```

SQLite backend (optional; artifacts remain file-backed):

```bash
export ABSTRACTGATEWAY_STORE_BACKEND=sqlite
export ABSTRACTGATEWAY_DB_PATH="$PWD/runtime/gateway/gateway.sqlite3"  # optional
```

### Defaults for LLM workflows (only if your bundles use LLM/tool nodes)

```bash
export ABSTRACTGATEWAY_PROVIDER="ollama"   # or: lmstudio/openai/anthropic/...
export ABSTRACTGATEWAY_MODEL="qwen3:4b-instruct"
```

### Tool execution mode (security boundary)

Most deployments should stay in passthrough/approval mode (tools become durable waits).
Local in-process tool execution is a dev-only setting.

Canonical docs:
- Getting started: https://github.com/lpalbou/AbstractGateway/blob/main/docs/getting-started.md
- Configuration: https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md
- Security model: https://github.com/lpalbou/AbstractGateway/blob/main/docs/security.md

## AbstractObserver (browser UI server)

AbstractObserver is a Node CLI that serves a static SPA and talks to the gateway from the browser.

Common CLI env vars:

```bash
export HOST="0.0.0.0"  # default
export PORT="3001"     # default
export ABSTRACTOBSERVER_MONITOR_GPU="on"  # optional header widget
```

Canonical docs:
- https://github.com/lpalbou/AbstractObserver/blob/main/docs/getting-started.md
- https://github.com/lpalbou/AbstractObserver/blob/main/docs/configuration.md

## AbstractCode (terminal UI)

AbstractCode is a local host (by default). Useful env vars:

```bash
export ABSTRACTCODE_WORKSPACE_DIR="$PWD"                # workspace root for @file mentions
export ABSTRACTCODE_WORKSPACE_MOUNTS="repo=/abs/path"   # optional; newline-separated mounts also supported
```

Canonical docs:
- https://github.com/lpalbou/abstractcode/blob/main/docs/getting-started.md
- https://github.com/lpalbou/abstractcode/blob/main/docs/cli.md

## AbstractSemantics (registry path)

To override the default semantics registry YAML:

```bash
export ABSTRACTSEMANTICS_REGISTRY_PATH="/abs/path/to/semantics.yaml"
```

Canonical docs:
- https://github.com/lpalbou/AbstractSemantics/blob/main/docs/getting-started.md

## Voice and vision (optional)

Voice and vision packages have their own configuration surfaces:

- AbstractVoice: https://github.com/lpalbou/abstractvoice/blob/main/docs/getting-started.md
- AbstractVision: https://github.com/lpalbou/abstractvision/blob/main/docs/getting-started.md

If you use the AbstractCore capability plugins, configuration usually comes from:
- AbstractCore centralized config (`~/.abstractcore/config/abstractcore.json`)
- `ABSTRACTVISION_*` / AbstractVoice env vars (see their docs)

## Example: gateway + observer (local dev)

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
export ABSTRACTGATEWAY_AUTH_TOKEN="dev-token"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"

abstractgateway serve --host 127.0.0.1 --port 8080
npx abstractobserver
```
