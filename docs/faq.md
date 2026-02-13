# FAQ

Answers to common questions about AbstractFramework.

---

## General

### What is AbstractFramework?

AbstractFramework is an ecosystem of packages for building **durable, observable** AI systems. The key pieces:

| Layer | Packages |
|-------|----------|
| **Foundation** | AbstractCore (LLM API), AbstractRuntime (durable execution) |
| **Composition** | AbstractAgent (ReAct/CodeAct/MemAct), AbstractFlow (visual workflows) |
| **Memory** | AbstractMemory (temporal triples), AbstractSemantics (schema registry) |
| **Applications** | AbstractCode (terminal), AbstractAssistant (macOS tray), AbstractGateway (HTTP), AbstractObserver (browser UI) |
| **Modalities** | AbstractVoice (TTS/STT), AbstractVision (image generation) |
| **UI Components** | AbstractUIC (React components for building your own apps) |

Start with [Getting Started](getting-started.md) to find the right entry point for your use case.

### Do I have to install the whole stack?

The recommended path is the full pinned release:

```bash
pip install "abstractframework==0.1.2"
```

You can still install only what you need:

| Your Goal | Install |
|-----------|---------|
| LLM integration only | `pip install abstractcore` |
| Durable workflows | `pip install abstractruntime` |
| Agent patterns (ReAct, etc.) | `pip install abstractagent` |
| Visual workflows | `pip install abstractflow` |
| Knowledge graph | `pip install abstractmemory abstractsemantics` |
| Terminal coding assistant | `pip install abstractcode` |
| macOS tray assistant | `pip install abstractassistant` |
| Remote control plane | `pip install "abstractgateway"` |
| Browser UI | `npx @abstractframework/observer` |
| Voice I/O (TTS/STT) | `pip install abstractvoice` |
| Image generation | `pip install abstractvision` |
| Build custom UIs | `npm install @abstractframework/panel-chat` etc. |
| Visual workflow editor | `npx @abstractframework/flow` |
| Browser coding assistant | `npx @abstractframework/code` |

In `abstractframework==0.1.2`, the meta-package is the main distribution entrypoint and installs all ecosystem Python packages with pinned versions.

### What should I start with?

It depends on what you're building:

- **"I need LLMs/tools in my Python app."** → Start with AbstractCore
- **"I want workflows that survive crashes."** → Start with AbstractRuntime
- **"I want an agent loop (ReAct/CodeAct/MemAct)."** → Start with AbstractAgent
- **"I want a terminal assistant today."** → Start with AbstractCode
- **"I want a macOS menu bar assistant."** → Start with AbstractAssistant
- **"I need remote runs + a browser UI."** → Start with AbstractGateway + AbstractObserver
- **"I need voice input/output."** → Start with AbstractVoice
- **"I need to generate images."** → Start with AbstractVision
- **"I need a knowledge graph."** → Start with AbstractMemory + AbstractSemantics

---

## How Does AbstractFramework Compare?

### What makes AbstractFramework different?

AbstractFramework optimizes for a different axis than most agent frameworks:

| What we optimize for | What most frameworks optimize for |
|----------------------|-----------------------------------|
| **Durability** — runs survive crashes, resume exactly | Quick prototyping, minimal boilerplate |
| **Replayability** — reconstruct any state from history | Stateless request/response patterns |
| **Provenance** — know what happened, when, and why | Black-box convenience |
| **Network-safe thin clients** — UIs attach/detach freely | Tightly-coupled UIs |
| **Visual authoring** on the same durable semantics | Code-first only |

This makes AbstractFramework closer to **Temporal/Step Functions** adapted for LLM/tool loops, rather than "yet another agent SDK."

### Honest comparison with other frameworks

| Axis | AbstractFramework | LangChain | LlamaIndex | PydanticAI | Letta |
|------|-------------------|-----------|------------|------------|-------|
| **Durable pause/resume** | Strong | — | — | — | Partial |
| **Replay-first control plane** | Strong | — | — | — | Partial |
| **Append-only ledger** | Strong | — | — | — | Partial |
| **Visual authoring** | Yes | Partial | Partial | — | — |
| **Tool approvals as primitive** | Strong | Partial | Partial | Partial | Partial |
| **RAG/connectors ecosystem** | Early | Strong | Strong | — | Partial |
| **Typed minimal API** | — | Partial | Partial | Strong | — |
| **Long-term memory product** | Early | — | Partial | — | Strong |
| **Ecosystem integrations** | Growing | Strong | Strong | Growing | Growing |

**Where we're ahead:**
- Durable orchestration, replay, and auditability as core primitives
- Tool execution boundaries with first-class approval flows
- Visual workflows that compile to the same durable runtime

**Where others are ahead:**
- **LangChain/LlamaIndex**: Massive ecosystem of connectors, integrations, and community
- **PydanticAI**: Minimal typed API with less boilerplate for simple cases
- **Letta**: More mature long-term memory product today

### When should I use AbstractFramework?

**Good fit:**
- Workflows that must survive restarts (long-running, scheduled)
- Systems requiring audit trails and time-travel debugging
- Human-in-the-loop approvals as a first-class concern
- Multi-device architectures (orchestrator + remote tools)
- Visual workflow authoring for non-developers

**Consider alternatives when:**
- You need a quick prototype with minimal code (→ PydanticAI)
- You need extensive RAG connectors today (→ LlamaIndex)
- You need maximum ecosystem integrations (→ LangChain)

### Can I use AbstractFramework with LangChain/LlamaIndex?

Yes. The recommended approach is to use AbstractFramework for orchestration and durability, while integrating other frameworks as tools or subflows:

- Use LlamaIndex retrievers as tools within an AbstractAgent
- Wrap LangChain chains as tool executors
- Let AbstractRuntime handle durability while external libraries handle specific capabilities

This gives you the best of both worlds: durable orchestration + ecosystem components.

---

## Creating & Running Specialized Agents

### How do I create a specialized agent that runs everywhere?

Use AbstractFlow to author a visual workflow, then declare an **interface contract**:

1. **Create your flow** in the visual editor (`npx @abstractframework/flow`)
2. Add `On Flow Start` and `On Flow End` nodes with the required pins
3. Declare the interface: `interfaces: ["abstractcode.agent.v1"]`
4. Export as a `.flow` bundle

The same flow now runs in:
- **AbstractCode** (terminal): `abstractcode --workflow my-agent.flow`
- **AbstractObserver** (browser): Select from the workflow picker
- **Code Web UI** (browser): Select from the workflow picker
- **Custom apps**: Via Gateway bundle discovery API

### What's the `abstractcode.agent.v1` interface?

It's a standard I/O contract for chat-like agents:

**On Flow Start outputs:**
- `provider`, `model` — LLM configuration
- `prompt` — User input
- `tools` — Available tools (optional)
- `context`, `memory` — Context/memory state (optional)

**On Flow End inputs:**
- `response` — Agent response (required)
- `success` — Boolean success flag (required)
- `meta` — Metadata object (required)

Any flow implementing this interface can be run as an agent in compatible clients.

### Can I run flows from other clients?

Yes. The Gateway provides **bundle discovery**:

```bash
# List available flows from a gateway
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/gateway/bundles
```

Clients can query this endpoint to show available workflows in dropdowns/pickers.

### What's the workflow registry?

AbstractCode maintains a local registry of installed workflow bundles:

```bash
# Install a bundle
abstractcode workflow install /path/to/my-agent.flow

# List installed workflows
abstractcode workflow list

# Run an installed workflow
abstractcode --workflow my-agent
```

Bundles can also be deployed to a Gateway for remote access.

---

## Advanced Capabilities

### How does MCP (Model Context Protocol) work?

AbstractCore includes a built-in MCP client that can discover and integrate tools from external MCP servers — both HTTP and stdio transports.

```python
from abstractcore import create_llm

llm = create_llm("openai", model="gpt-4o-mini")

# MCP tools are discovered and presented alongside local tools
response = llm.generate(
    "What's in my database?",
    mcp_servers=[{"url": "http://localhost:3000/mcp"}],
)
```

MCP tools integrate with the full durable execution stack: they participate in approval boundaries, ledger logging, and replay semantics just like any other tool.

See [AbstractCore MCP docs](https://github.com/lpalbou/abstractcore/blob/main/docs/mcp.md).

### How does structured output work?

AbstractCore supports Pydantic-based structured output across all providers:

```python
from pydantic import BaseModel
from abstractcore import create_llm

class Report(BaseModel):
    title: str
    findings: list[str]

llm = create_llm("openai", model="gpt-4o-mini")
report = llm.generate("Analyze HTTP/3 adoption.", response_model=Report)
```

AbstractCore uses **provider-aware strategies**: native JSON mode where available, with automatic retry and schema enforcement for models that need it.

See [AbstractCore Structured Output docs](https://github.com/lpalbou/abstractcore/blob/main/docs/structured-output.md).

### Does AbstractFramework support streaming?

Yes. Full streaming support across all providers:

```python
for chunk in llm.generate("Write a poem.", stream=True):
    print(chunk.content or "", end="", flush=True)
```

Async streaming is also supported (`async for chunk in llm.agenerate(..., stream=True)`).

### Does AbstractFramework support async?

Yes. Every `generate()` call has an `agenerate()` async counterpart:

```python
resp = await llm.agenerate("Summarize this document.")
```

See [AbstractCore Async Guide](https://github.com/lpalbou/abstractcore/blob/main/docs/async-guide.md).

### What is glyph visual-text compression?

A unique feature for processing long documents cheaply: render text/PDFs as images, then process them with a vision-capable model. This can dramatically reduce token usage for large documents.

```python
llm = create_llm("openai", model="gpt-4o", glyph="auto")
resp = llm.generate("Summarize this contract.", media=["contract.pdf"])
```

Requires `pip install "abstractcore[compression]"` (and `pip install "abstractcore[media]"` for PDF support).

See [AbstractCore Glyph docs](https://github.com/lpalbou/abstractcore/blob/main/docs/glyphs.md).

### What are embeddings and how do I use them?

AbstractCore includes an embedding API for building RAG pipelines and semantic search:

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
embeddings = llm.embed(["first document", "second document"])
```

Requires `pip install "abstractcore[embeddings]"`.

See [AbstractCore Embeddings docs](https://github.com/lpalbou/abstractcore/blob/main/docs/embeddings.md).

### Can I serve AbstractCore as an OpenAI-compatible API?

Yes. AbstractCore includes a server mode that exposes a multi-provider OpenAI-compatible `/v1` API:

```bash
pip install "abstractcore[server]"
python -m abstractcore.server.app
```

Use any OpenAI client and route to any provider via `model="provider/model"` (e.g., `model="ollama/qwen3:4b-instruct"`).

The server can also optionally expose `/v1/images/*` and `/v1/audio/*` endpoints when the corresponding plugins are installed (including `/v1/audio/music` when `abstractmusic` is installed).

See [AbstractCore Server docs](https://github.com/lpalbou/abstractcore/blob/main/docs/server.md).

### What are the built-in CLI apps?

AbstractCore ships practical CLI tools out of the box:

| App | What It Does |
|-----|-------------|
| `summarizer` | Summarize documents and text |
| `extractor` | Extract structured data |
| `judge` | LLM-as-a-judge evaluation |
| `intent` | Intent classification |
| `deepsearch` | Deep web search with synthesis |

See [AbstractCore CLI Apps docs](https://github.com/lpalbou/abstractcore/blob/main/docs/apps/).

### How do snapshots and history bundles work?

**Snapshots** are named checkpoints of a run's state. You can create them at any point during execution, then restore to that state later:
- Useful for creating restore points before risky operations
- Bookmarking interesting states for later analysis

**History bundles** let you export a complete, reproducible snapshot of a run — including the ledger, artifacts, and state — for debugging, sharing, or archiving.

See [AbstractRuntime Snapshots docs](https://github.com/lpalbou/abstractruntime/blob/main/docs/snapshots.md).

### What is interaction tracing?

AbstractCore emits structured **interaction traces** (prompts, responses, token usage, timing) via a global event bus. Hosts can subscribe to these events for:
- Observability dashboards
- Cost tracking
- Debugging and performance analysis

See [AbstractCore Interaction Tracing docs](https://github.com/lpalbou/abstractcore/blob/main/docs/interaction-tracing.md).

### Does AbstractVoice support voice cloning?

Yes. AbstractVoice includes experimental voice cloning support:

```bash
pip install "abstractvoice[cloning]"
abstractvoice-prefetch --openf5
```

See [AbstractVoice docs](https://github.com/lpalbou/abstractvoice/blob/main/docs/getting-started.md) for details.

### Can AbstractVision run GGUF models locally?

Yes. AbstractVision supports local GGUF diffusion models via the `stable-diffusion.cpp` backend (`sdcpp`):

```bash
abstractvision repl
/backend sdcpp /path/to/model.gguf /path/to/vae.safetensors /path/to/clip.gguf
/t2i "a watercolor painting" --open
```

The Python bindings for `stable-diffusion.cpp` are included in the default install. See [AbstractVision backends docs](https://github.com/lpalbou/abstractvision/blob/main/docs/reference/backends.md).

---

## Architecture & Concepts

### What's the difference between AbstractRuntime, AbstractAgent, and AbstractFlow?

| Package | Purpose |
|---------|---------|
| **AbstractRuntime** | The durable execution substrate — runs, effects, waits, ledger, stores |
| **AbstractAgent** | Agent patterns implemented as runtime workflows (ReAct, CodeAct, MemAct) |
| **AbstractFlow** | Portable workflows (VisualFlow JSON) + authoring helpers and a reference editor |

Think of AbstractRuntime as the engine, AbstractAgent as pre-built cars, and AbstractFlow as a visual car designer.

### What is a "run"? What is the "ledger"?

- A **run** is a durable workflow instance, identified by a `run_id`
- The **ledger** is an append-only list of step records for that run — the complete history of what happened

The ledger is the **source of truth**. Gateway-first UIs (like AbstractObserver) render by replaying the ledger and streaming new steps via SSE.

### What are "effects" and "waits"?

- An **effect** is a request for something to happen (LLM call, tool call, timer, etc.)
- A **wait** is a pause point where the run's state is checkpointed

When a run needs external input (like tool results), it emits a wait. The host process can shut down, restart, or hand off to another process — when the run resumes, it picks up exactly where it left off.

### What's the difference between AbstractMemory and the runtime ledger?

| Aspect | Runtime Ledger | AbstractMemory |
|--------|----------------|----------------|
| **Purpose** | Execution history | Semantic knowledge |
| **Structure** | Append-only steps | Temporal triples |
| **Query** | Sequential replay | Deterministic + vector search |
| **Use case** | Durability, replay, debugging | Knowledge graphs, facts, relationships |

They complement each other. The ledger tracks *what happened*; AbstractMemory tracks *what was learned*.

---

## Tools & Safety

### Why do tools require approval? Why aren't they executed automatically?

Two reasons: **durability** and **safety**.

- Tool **schemas** are durable (stored in the ledger)
- Tool **callables** are not durable (they live in the host process)

So the runtime emits a durable `TOOL_CALLS` wait, then the host:
1. Prompts for approval (default)
2. Executes tools (locally or via remote worker)
3. Resumes the run with JSON tool results

This makes tool execution auditable, restart-safe, and controllable.

---

## Gateway & Deployment

### Do I need AbstractGateway?

Not for local-only usage.

Use a gateway when you want:
- **Remote execution** — server owns durability
- **Multiple clients** — several UIs attached to the same runs
- **Durable inbox** — pause/resume/cancel/schedule commands over HTTP
- **Replay-first observability** — HTTP/SSE access to run history
- **Scheduled workflows** — cron-style execution of automated agents
- **Bundle discovery** — expose workflows to thin clients via API
- **History bundles** — export reproducible run snapshots

Local hosts like AbstractCode and AbstractAssistant run everything in one process without needing a gateway.

### What can the Gateway do?

Key capabilities:

| Capability | Endpoint | Description |
|------------|----------|-------------|
| **Bundle discovery** | `GET /bundles` | List available workflow bundles |
| **Start runs** | `POST /runs/start` | Launch a workflow |
| **Schedule runs** | `POST /runs/schedule` | Cron-style scheduled execution |
| **Ledger replay** | `GET /runs/{id}/ledger` | Replay execution history |
| **Ledger streaming** | `GET /runs/{id}/ledger/stream` | Real-time SSE updates |
| **History bundles** | `GET /runs/{id}/history_bundle` | Export reproducible snapshots |
| **Provider discovery** | `GET /discovery/providers` | List available LLM providers |
| **Tool discovery** | `GET /discovery/tools` | List available tools |
| **Capabilities** | `GET /discovery/capabilities` | Voice/vision plugin status |
| **KG query** | `POST /kg/query` | Query the knowledge graph |

See the [Gateway API docs](https://github.com/lpalbou/abstractgateway/blob/main/docs/api.md) for the full API surface.

### How do scheduled workflows work?

The gateway supports durable scheduled workflows — recurring jobs that survive restarts. A scheduled workflow is a durable parent run that triggers child runs at specified intervals.

```bash
curl -X POST "http://localhost:8080/api/gateway/runs/schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"bundle_id":"daily-report","start_at":"now","interval":"24h"}'
```

If the gateway stops, due schedules resume on restart. Pause or cancel the parent run to control the schedule.

See [Guide: Scheduled Workflows](guide/scheduled-workflows.md).

### How do event bridges (Telegram, email) work?

Event bridges turn external messages into durable runtime events:
1. Bridge receives an inbound message (Telegram, email, etc.)
2. Bridge assigns a stable `session_id`
3. Gateway emits a durable event into that session
4. A workflow consumes the event and replies

This preserves full durability and observability — inbound content becomes replayable ledger history.

See [Guide: Telegram Integration](guide/telegram-integration.md) and [Guide: Email Integration](guide/email-integration.md).

### Can I split the gateway API and runner?

Yes. For production, the HTTP API and runner loop can run as separate processes sharing the same data directory. This lets you restart the API without interrupting durable execution:

```bash
# Process 1: Runner worker
abstractgateway runner

# Process 2: HTTP API only
abstractgateway serve --no-runner --host 127.0.0.1 --port 8080
```

### Can I use SQLite instead of file-based storage?

Yes. The gateway supports SQLite as a storage backend (recommended for production):

```bash
export ABSTRACTGATEWAY_STORE_BACKEND=sqlite
export ABSTRACTGATEWAY_DB_PATH="$PWD/runtime/gateway/gateway.sqlite3"
```

Migration from file-based storage is supported via `abstractgateway migrate`.

### Where is data stored?

Depends on the component:

| Component | Default Location |
|-----------|------------------|
| AbstractGateway | `ABSTRACTGATEWAY_DATA_DIR` (file or SQLite + artifacts) |
| AbstractCode | `~/.abstractcode/` |
| AbstractAssistant | `~/.abstractassistant/` |
| AbstractMemory | In-memory by default, or LanceDB path |
| AbstractVoice | `~/.piper/models` (Piper TTS models) |

See each project's docs for exact directory layouts and backup strategies.

---

## Local & Offline

### Can I run everything with local models (offline)?

Yes. The **core execution stack** works fully offline with local model servers:
- Ollama
- LM Studio
- vLLM
- llama.cpp
- LocalAI

You'll need internet only if you choose to download models or use cloud APIs. See [Configuration](configuration.md) for local setup details.

### Does AbstractVoice work offline?

Yes. AbstractVoice uses:
- **Piper** for TTS (local ONNX models)
- **faster-whisper** for STT (local Whisper models)

Prefetch models once, then run fully offline:

```bash
abstractvoice-prefetch --stt small --piper en
```

### Does AbstractVision work offline?

Yes, with local backends:
- **Diffusers** (local Hugging Face models)
- **stable-diffusion.cpp** (GGUF models)

Or connect to a local OpenAI-compatible image server.

---

## UIs

### Which browser UI should I use?

| UI | Purpose | Install |
|----|---------|---------|
| **AbstractObserver** | Observe, launch, and control gateway runs | `npx @abstractframework/observer` |
| **Flow Editor** | Visual workflow authoring (drag-and-drop) | `npx @abstractframework/flow` |
| **Code Web UI** | Browser-based coding assistant | `npx @abstractframework/code` |

All three connect to an AbstractGateway. See [Getting Started](getting-started.md) for setup.

### Can I build my own UI?

Yes. AbstractUIC provides React components:

| Package | What It Does |
|---------|--------------|
| `@abstractframework/ui-kit` | Theme tokens + primitives |
| `@abstractframework/panel-chat` | Chat thread + message cards |
| `@abstractframework/monitor-flow` | Agent-cycle trace viewer |
| `@abstractframework/monitor-active-memory` | Knowledge graph explorer |
| `@abstractframework/monitor-gpu` | GPU utilization widget |

Install what you need and compose them in your app.

---

## Stability & Maturity

### What's the maturity of each package?

Different components are at different stages:

| Status | Packages |
|--------|----------|
| **Beta** | AbstractCore |
| **Active development** | AbstractRuntime, AbstractAgent, AbstractGateway, AbstractObserver |
| **Pre-alpha** | AbstractCode, AbstractFlow, AbstractAssistant |
| **Early/WIP** | AbstractMemory, AbstractSemantics |
| **Alpha** | AbstractVoice, AbstractVision |

For the authoritative status, check each project's README and pyproject.toml classifiers. We follow semantic versioning where possible.

---

## Troubleshooting

### My LLM calls aren't working

1. Check your provider configuration (see [Configuration](configuration.md))
2. For Ollama: ensure `ollama serve` is running
3. For cloud APIs: verify your API key is set and valid
4. Run `abstractcore --status` to see current LLM config

### The gateway won't start

1. Ensure `ABSTRACTGATEWAY_AUTH_TOKEN` is set
2. Ensure `ABSTRACTGATEWAY_DATA_DIR` exists and is writable
3. Check port availability (default: 8080)

### The observer can't connect

1. Verify the gateway URL is correct (typically `http://127.0.0.1:8080`)
2. Ensure your auth token matches `ABSTRACTGATEWAY_AUTH_TOKEN`
3. Check `ABSTRACTGATEWAY_ALLOWED_ORIGINS` includes your observer URL

### AbstractVoice: "No model found"

Prefetch models explicitly (offline-first design):

```bash
abstractvoice-prefetch --stt small
abstractvoice-prefetch --piper en
```

### AbstractVision: No images generated

1. Ensure your backend is running (local server or configured API)
2. Check `base_url` in your backend config
3. Some models require specific extras: `pip install "abstractvision[huggingface-dev]"`

---

Still stuck? Check the individual project docs or open an issue on GitHub.

---

## Related Documentation

- **[Getting Started](getting-started.md)** — Pick a path and run something
- **[Architecture](architecture.md)** — How the pieces fit together
- **[Configuration](configuration.md)** — Environment variables and settings
