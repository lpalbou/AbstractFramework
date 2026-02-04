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

No. Install only what you need:

| Your Goal | Install |
|-----------|---------|
| LLM integration only | `pip install abstractcore` |
| Durable workflows | `pip install abstractruntime` |
| Agent patterns (ReAct, etc.) | `pip install abstractagent` |
| Visual workflows | `pip install abstractflow` |
| Knowledge graph | `pip install abstractmemory abstractsemantics` |
| Terminal coding assistant | `pip install abstractcode` |
| macOS tray assistant | `pip install abstractassistant` |
| Remote control plane | `pip install "abstractgateway[http]"` |
| Browser UI | `npx @abstractframework/observer` |
| Voice I/O (TTS/STT) | `pip install abstractvoice` |
| Image generation | `pip install abstractvision` |
| Build custom UIs | `npm install @abstractframework/panel-chat` etc. |
| Visual workflow editor | `npx @abstractframework/flow` |
| Browser coding assistant | `npx @abstractframework/code` |

The `abstractframework` PyPI package is a convenience **meta-package** that bundles common installs via extras — useful if you want several packages at once.

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

Local hosts like AbstractCode and AbstractAssistant run everything in one process without needing a gateway.

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

### Is the ecosystem "stable"?

Different components have different maturity levels:

| Status | Packages |
|--------|----------|
| **Stable foundations** | AbstractCore, AbstractRuntime |
| **Active development** | AbstractAgent, AbstractGateway, AbstractObserver |
| **Pre-alpha/experimental** | AbstractCode, AbstractFlow, AbstractAssistant |
| **Early/WIP** | AbstractMemory, AbstractSemantics |
| **Alpha** | AbstractVoice, AbstractVision |

For the authoritative status, check each project's README and changelog. We follow semantic versioning where possible.

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
