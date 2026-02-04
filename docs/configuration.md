# Configuration

AbstractFramework is modular, so configuration is **per component**. This page covers the most common settings you'll need — each section links to the canonical docs for deeper configuration.

## Quick Reference

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                          Configuration Overview                                │
├───────────────────┬───────────────────────────────────────────────────────────┤
│ Component         │ Key Environment Variables                                 │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractCore      │ OLLAMA_HOST, OPENAI_API_KEY, ANTHROPIC_API_KEY           │
│                   │ + centralized config: ~/.abstractcore/config/             │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractRuntime   │ (Configured programmatically via stores)                  │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractGateway   │ ABSTRACTGATEWAY_AUTH_TOKEN, ABSTRACTGATEWAY_DATA_DIR     │
│                   │ ABSTRACTGATEWAY_ALLOWED_ORIGINS, ABSTRACTGATEWAY_*        │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractObserver  │ HOST, PORT, ABSTRACTOBSERVER_MONITOR_GPU                 │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ Flow Editor       │ PORT (UI settings for gateway connection)                │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ Code Web UI       │ (UI settings for gateway connection)                     │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractCode      │ ABSTRACTCODE_WORKSPACE_DIR, ABSTRACTCODE_WORKSPACE_*     │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractAssistant │ --data-dir, --provider, --model                          │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractMemory    │ (Configured programmatically; LanceDB path optional)     │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractSemantics │ ABSTRACTSEMANTICS_REGISTRY_PATH                          │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractVoice     │ ABSTRACTVOICE_*, model paths in ~/.piper/                │
├───────────────────┼───────────────────────────────────────────────────────────┤
│ AbstractVision    │ ABSTRACTVISION_*, backend config                         │
└───────────────────┴───────────────────────────────────────────────────────────┘
```

---

## LLM Providers (AbstractCore)

AbstractCore supports multiple providers (cloud and local). Pick what works for you.

### Ollama (Local, Free)

```bash
export OLLAMA_HOST="http://localhost:11434"
```

```python
from abstractcore import create_llm
llm = create_llm("ollama", model="qwen3:4b-instruct")
```

### OpenAI-Compatible Servers (LM Studio, vLLM, LocalAI, llama.cpp)

Most OpenAI-compatible servers accept:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"  # many local servers ignore this but clients require a value
```

```python
from abstractcore import create_llm
llm = create_llm("lmstudio", model="qwen/qwen3-4b-2507", base_url="http://127.0.0.1:1234/v1")
```

### Cloud APIs

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Centralized Config (Recommended)

AbstractCore can persist defaults and keys to `~/.abstractcore/config/abstractcore.json`:

```bash
abstractcore --configure   # interactive setup
abstractcore --status      # show current config
```

**Canonical docs**:
- [Centralized config](https://github.com/lpalbou/abstractcore/blob/main/docs/centralized-config.md)
- [Prerequisites](https://github.com/lpalbou/abstractcore/blob/main/docs/prerequisites.md)

---

## AbstractGateway (Server Configuration)

AbstractGateway is the remote control plane. Two variables are **required**:

### Required

```bash
# Generate a secure auth token
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Allow browser connections (CORS)
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

### Workflow Source + Durability Root

Bundle mode (recommended):

```bash
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"   # *.flow bundles
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
```

SQLite backend (optional; artifacts remain file-backed):

```bash
export ABSTRACTGATEWAY_STORE_BACKEND=sqlite
export ABSTRACTGATEWAY_DB_PATH="$PWD/runtime/gateway/gateway.sqlite3"
```

### LLM Defaults (If Your Bundles Use LLM/Tool Nodes)

```bash
export ABSTRACTGATEWAY_PROVIDER="ollama"
export ABSTRACTGATEWAY_MODEL="qwen3:4b-instruct"
```

### Tool Execution Mode

Most deployments should stay in **passthrough/approval mode** (tools become durable waits). Local in-process tool execution is a dev-only setting.

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/AbstractGateway/blob/main/docs/getting-started.md)
- [Configuration](https://github.com/lpalbou/AbstractGateway/blob/main/docs/configuration.md)
- [Security model](https://github.com/lpalbou/AbstractGateway/blob/main/docs/security.md)

---

## AbstractObserver (Browser UI)

Gateway observability dashboard.

```bash
npx @abstractframework/observer
```

```bash
export HOST="0.0.0.0"     # default; bind address
export PORT="3001"        # default; server port
export ABSTRACTOBSERVER_MONITOR_GPU="on"  # optional GPU widget in header
```

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/AbstractObserver/blob/main/docs/getting-started.md)
- [Configuration](https://github.com/lpalbou/AbstractObserver/blob/main/docs/configuration.md)

---

## Flow Editor (Browser UI)

Visual workflow editor for authoring `.flow` bundles.

```bash
npx @abstractframework/flow
```

```bash
export PORT="3003"        # default; server port
```

Configure the gateway connection in the UI settings.

**Canonical docs**:
- [Web editor guide](https://github.com/lpalbou/abstractflow/blob/main/docs/web-editor.md)

---

## Code Web UI (Browser UI)

Browser-based coding assistant (connects to a gateway).

```bash
npx @abstractframework/code
```

Configure the gateway URL and auth token in the UI settings.

**Canonical docs**:
- [Web docs](https://github.com/lpalbou/abstractcode/blob/main/docs/web.md)
- [Deployment](https://github.com/lpalbou/abstractcode/blob/main/docs/deployment-web.md)

---

## AbstractCode (Terminal UI)

AbstractCode is a local host (no gateway needed). Key settings:

```bash
export ABSTRACTCODE_WORKSPACE_DIR="$PWD"                # workspace root for @file mentions
export ABSTRACTCODE_WORKSPACE_MOUNTS="repo=/abs/path"   # optional; newline-separated mounts also supported
```

Data is stored in `~/.abstractcode/` by default.

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/abstractcode/blob/main/docs/getting-started.md)
- [CLI reference](https://github.com/lpalbou/abstractcode/blob/main/docs/cli.md)

---

## AbstractAssistant (macOS Tray App)

AbstractAssistant is configured via CLI flags:

```bash
assistant tray --provider ollama --model qwen3:4b-instruct
assistant tray --data-dir /custom/path
assistant tray --debug
```

Data is stored in `~/.abstractassistant/` by default:
- `session.json`: UI snapshot
- `runtime/`: run store + ledger + artifacts

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/abstractassistant/blob/main/docs/getting-started.md)
- [Architecture](https://github.com/lpalbou/abstractassistant/blob/main/docs/architecture.md)

---

## AbstractMemory (Knowledge Graph)

AbstractMemory is configured programmatically. For persistent storage:

```python
from abstractmemory import LanceDBTripleStore

# Persistent storage with vector search
store = LanceDBTripleStore("/path/to/lancedb")
```

For in-memory (default):

```python
from abstractmemory import InMemoryTripleStore
store = InMemoryTripleStore()
```

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/abstractmemory/blob/main/docs/getting-started.md)
- [Stores](https://github.com/lpalbou/abstractmemory/blob/main/docs/stores.md)

---

## AbstractSemantics (Registry Path)

To override the default semantics registry YAML:

```bash
export ABSTRACTSEMANTICS_REGISTRY_PATH="/abs/path/to/semantics.yaml"
```

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/AbstractSemantics/blob/main/docs/getting-started.md)
- [Registry format](https://github.com/lpalbou/AbstractSemantics/blob/main/docs/registry.md)

---

## AbstractVoice (Voice I/O)

### Model Paths

TTS models (Piper) are stored in `~/.piper/models/`. Prefetch them:

```bash
abstractvoice-prefetch --piper en
abstractvoice-prefetch --stt small
```

### Environment Variables

```bash
# Optional overrides
export ABSTRACTVOICE_TTS_MODEL="en_US-amy-medium"
export ABSTRACTVOICE_STT_MODEL="small"
```

### REPL Configuration

```bash
abstractvoice --verbose              # Enable debug logging
abstractvoice --voice-mode stop      # Enable voice input on startup
```

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/abstractvoice/blob/main/docs/getting-started.md)
- [Installation](https://github.com/lpalbou/abstractvoice/blob/main/docs/installation.md)
- [Model management](https://github.com/lpalbou/abstractvoice/blob/main/docs/model-management.md)

---

## AbstractVision (Image Generation)

### Backend Configuration

Configured programmatically per backend:

```python
from abstractvision.backends import OpenAICompatibleBackendConfig, OpenAICompatibleVisionBackend

backend = OpenAICompatibleVisionBackend(
    config=OpenAICompatibleBackendConfig(
        base_url="http://localhost:1234/v1",
        api_key="local",
        model_id="your-model",
    )
)
```

### Environment Variables (CLI)

```bash
export ABSTRACTVISION_BASE_URL="http://localhost:1234/v1"
export ABSTRACTVISION_API_KEY="local"
```

### CLI Usage

```bash
abstractvision t2i --base-url http://localhost:1234/v1 "a photo of a mountain"
abstractvision repl  # Interactive mode
```

**Canonical docs**:
- [Getting started](https://github.com/lpalbou/abstractvision/blob/main/docs/getting-started.md)
- [Configuration](https://github.com/lpalbou/abstractvision/blob/main/docs/reference/configuration.md)
- [Backends](https://github.com/lpalbou/abstractvision/blob/main/docs/reference/backends.md)

---

## Example: Gateway + Observer (Local Dev)

A complete local development setup:

```bash
# Gateway config
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
export ABSTRACTGATEWAY_AUTH_TOKEN="dev-token"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"

# Start gateway
abstractgateway serve --host 127.0.0.1 --port 8080

# In another terminal: start observer
npx @abstractframework/observer
```

Open http://localhost:3001, paste your token, and connect.

---

## Example: Full Local Stack

Running everything locally with Ollama:

```bash
# 1. Start Ollama
ollama serve
ollama pull qwen3:4b-instruct

# 2. Configure LLM
export OLLAMA_HOST="http://localhost:11434"

# 3. Prefetch voice models (optional)
abstractvoice-prefetch --piper en --stt small

# 4. Run AbstractCode
abstractcode --provider ollama --model qwen3:4b-instruct
```
