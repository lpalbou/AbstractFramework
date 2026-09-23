# Getting started

This guide helps you build a correct mental model quickly, then run something end-to-end.

> **Write once. Generate everything.** Durable, observable, multimodal AI systems — one unified interface, any provider, any model, local or cloud.

AbstractFramework is a **stack**:

| Layer | Package | Role |
|---|---|---|
| SDK | **AbstractCore** | Provider/model abstraction, tools, structured output, media, embeddings |
| Agent patterns | **AbstractAgent** | Ready-made loops: ReAct (tool-first), CodeAct (code execution), MemAct (memory-enhanced) |
| Workflow authoring | **AbstractFlow** | Visual editor, portable `.flow` bundles, subflows |
| Durable kernel | **AbstractRuntime** | Runs, effects, waits, ledger, artifacts |
| Control plane | **AbstractGateway** | Persistence, scheduling, bundle discovery, SSE streaming |
| Operations | **AbstractObserver** | Browser UI to monitor, control, and schedule runs |

**Rule of thumb**: start with **Core** when you want a lightweight LLM library (SDK or `/v1`) for scripts/notebooks/apps; add **Gateway** when you need persistent runs, scheduling, and multi-client continuity.

> **Prerequisites**: Python 3.10–3.13 for the manual installs below. Node.js 18+ (only for browser UIs). An LLM backend — local (Ollama, LM Studio, vLLM, llama.cpp) or cloud (OpenAI, Anthropic, etc.).

## Fastest path: the one-line install

If you want a running gateway and its web console without setting up Python yourself, use the
bootstrap script. It installs uv, Python 3.12 and the pinned gateway in your user account, registers
it to start at login, starts it on `127.0.0.1:8080`, and opens `/console` already signed in:

```bash
curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
```

On Windows: `powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"`.
The console's first-run guide sets up a local engine or a cloud key and a default model (the
**Models** tab lists the models that fit your machine and downloads them). Then continue with
[Monitor runs](#4-monitor-runs-with-abstractobserver) or [AbstractFlow](#author-orchestration-with-abstractflow).
Options and uninstall: [Install](install.md#quick-start). The sections below cover manual installs
for library and developer use.

---

## Choose your entry point

| If you are… | Start with | Why |
|---|---|---|
| Calling LLMs/tools/media (SDK or OpenAI-compatible `/v1`) | **AbstractCore** | Lightweight, smallest surface area, fastest feedback loop |
| Building persistent agents/workflows (durable runs) | **AbstractGateway** + **AbstractFlow** | Durability, scheduling, bundle discovery, ledger replay/streaming |

You can also install the entire pinned ecosystem in one command:

```bash
pip install abstractframework
```

For the full Light / Apple / GPU profile chooser, see [Install AbstractFramework](install.md).

---

## Core-first: integrate via AbstractCore (SDK or `/v1`)

### 1. Install

```bash
pip install abstractcore
```

### 2. Configure a provider

**Local (Ollama)** — free, no API key:

```bash
ollama serve
ollama pull qwen3:4b-instruct
export OLLAMA_HOST="http://localhost:11434"
```

**OpenAI-compatible** (LM Studio, vLLM, LocalAI, llama.cpp):

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"
```

**Cloud APIs**:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Or use a console.** `abstractcore serve` starts the server on `127.0.0.1:8000` and prints a
one-time link to its web console, where the **Engines** tab detects and installs local engines
(Ollama, LM Studio, MLX, llama.cpp) and the **Models** tab downloads a model that fits this machine.
The same actions exist on the command line and in the terminal console:

```bash
abstractcore serve                      # open the printed http://127.0.0.1:8000/console#claim=… link
abstractcore engines status             # which local engines are installed and running
abstractcore models catalog             # models, with a fit verdict for this machine
abstractcore models download ollama qwen3:4b-instruct
cargo install abstractcore-console      # terminal console (Rust 1.87+)
```

The interactive terminal wizard persists config to `~/.abstractcore/config/`:

```bash
abstractcore --config
abstractcore --status
```

### 3. Call the model

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("Explain durable execution in 3 bullets.")
print(resp.content)
```

### What else you can do with Core

```python
# Tool calling
resp = llm.generate("What's the weather?", tools=[get_weather])

# Structured output (Pydantic)
report = llm.generate("Analyze this.", response_model=Report)

# Media input (images, audio, video, documents)
resp = llm.generate("Describe this image.", media=["photo.jpg"])

# Embeddings
vectors = llm.embed(["first document", "second document"])

# Streaming
for chunk in llm.generate("Write a poem.", stream=True):
    print(chunk.content or "", end="", flush=True)
```

---

## Gateway-first: durable runs + monitoring + scheduling

### 1. Install

```bash
pip install abstractgateway
```

### 2. Configure (optional)

With no configuration, `abstractgateway serve` binds `127.0.0.1:8080`, enables user auth, and keeps
its data in the per-user data folder (macOS `~/Library/Application Support/AbstractGateway`, Linux
`~/.local/share/abstractgateway`, Windows `%LOCALAPPDATA%\AbstractGateway`). Set the environment
when you want another data folder, browser origins or bundle registry:

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Optional: set only for a custom bundle registry. When this is unset,
# Gateway serves its shipped workflows (basic-agent, coding-agent,
# deep-research, co-scientist, and more).
# export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
```

### 3. Start the gateway

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

On first local start, Gateway creates `default/admin`, keeps its token in
`<data dir>/auth/bootstrap-admin-token` (readable by you only), and prints a one-time link:
`First run: open http://127.0.0.1:8080/console#claim=…`. Open it to sign in to the web console and
its first-run guide (engines, default model, apps); `abstractgateway claim --open` mints a new
link. Use the `admin` token from the file to sign in to AbstractFlow, AbstractCode Web or
AbstractObserver. `ABSTRACTGATEWAY_AUTH_TOKEN` is only the legacy server/operator bearer-token
path; it does not sign in browsers.

To start the gateway at login, use `abstractgateway service install --host 127.0.0.1 --port 8080`.

Verify:

```bash
curl -sS "http://127.0.0.1:8080/api/health"
```

### 4. Monitor runs with AbstractObserver

In another terminal:

```bash
npx @abstractframework/observer
```

Open http://localhost:3001 and connect. In hosted user-auth mode, enter Gateway
URL, Gateway user, and that user's token; Observer exchanges the token for a
browser session and does not persist the token in browser settings.

AbstractObserver is replay-first: it renders runs by replaying the ledger, then streams new steps live via SSE.

### 5. Schedule recurring work

Schedules are owned by the gateway (they survive restarts):

```bash
curl -X POST "http://127.0.0.1:8080/api/gateway/runs/schedule" \
  -H "Authorization: Bearer $(cat "$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token")" \
  -H "Content-Type: application/json" \
  -d '{"bundle_id":"my-bundle","flow_id":"my-entrypoint","start_at":"now","interval":"24h"}'
```

---

## Author orchestration with AbstractFlow

The ecosystem's distribution unit is a **workflow bundle** (`.flow` file): a VisualFlow graph + metadata. Gateways discover bundles and expose them to all clients.

You do not have to start from an empty registry. A packaged Gateway already
serves a set of ready workflows — a verify-gated coding agent, `deep-research`,
and `co-scientist` among them — listed in
[AbstractGateway's shipped workflows](../abstractgateway/docs/shipped-workflows.md).
Author your own when you need something they do not cover.

### 1. Open the Flow Editor

With the gateway running:

```bash
npx @abstractframework/flow
```

Open http://localhost:3003 and connect to your gateway. In hosted user-auth
mode, use Gateway URL, Gateway user, and that user's token; Flow keeps an
opaque browser session instead of storing the token.

### 2. Build a workflow

- **On Flow Start** → takes input (prompt, provider, model, …)
- LLM steps, tool steps, branching, loops, subflows
- **On Flow End** → returns output (response, success, metadata)

To make it reusable across clients, implement an **interface contract** (for example `abstractcode.agent.v1` — a standard chat-like agent I/O contract).

### 3. Export and deploy

```bash
mkdir -p "$PWD/bundles"
cp my-agent.flow "$PWD/bundles/"
```

Start or restart Gateway with `ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"` when
you want that directory to be the active custom bundle registry. You can also
publish bundles through the Gateway API from AbstractFlow.

### 4. Run from any client

Once deployed, the bundle appears in:

- **AbstractObserver** — workflow picker / run launcher
- **AbstractAssistant** — workflow picker (per session)
- **Code Web UI** — workflow picker
- **Your own client** — via the gateway bundle discovery API

---

## Example apps

### AbstractCode (terminal and browser)

A coding client for durable agentic sessions on the gateway you started above. Install the Rust
terminal client from crates.io (or download a prebuilt binary from the
[AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases)), or run the
browser client with `npx`:

```bash
cargo install abstractcode
abstractcode doctor              # check the gateway connection
abstractcode

npx @abstractframework/code      # browser client on http://127.0.0.1:3002
```

Sessions are durable: close and reopen, your full context is preserved. Type `/help` for commands.

### AbstractAssistant (macOS tray)

Gateway-first by default. Select a workflow per session from the tray UI:

```bash
pip install abstractassistant
assistant tray
```

---

## Next steps

- **[Architecture](architecture.md)** — the layered model (Core / Runtime / Agent / Gateway / Flow / Observer)
- **[Configuration](configuration.md)** — where defaults live and how to configure them
- **[Glossary](glossary.md)** — shared terms (run, ledger, effect, wait, bundle, interface contract)
- **[FAQ](faq.md)** — comparisons, offline operation, troubleshooting
- **[Workspace scripts](workspace-scripts.md)** — work from source: clone, build and sync every package in dependency order
