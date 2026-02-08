# AbstractFramework

**Build durable, observable AI systems — fully open source, works offline.**

AbstractFramework is a modular ecosystem for building AI agents and workflows that survive restarts, scale to production, and give you full visibility into what's happening. Every component is open source, works with local models, and designed to be composed however you need.

This repository is the **single access point** to the ecosystem:
- install the full framework with one `pip` command
- understand how all packages fit together
- create and deploy new specialized solutions (flows/agents) across clients

```
┌──────────────────────────────────────────┬──────────────────────────────────┐
│   GATEWAY PATH (Recommended)             │   LOCAL PATH (Alternative)       │
├──────────────────────────────────────────┼──────────────────────────────────┤
│                                          │                                  │
│  Browser UIs (Observer, Flow Editor,     │  AbstractCode (terminal)         │
│  Code Web, Your App)                     │  AbstractAssistant (macOS tray)  │
│              │                           │             │                    │
│              ▼                           │             │                    │
│  ┌────────────────────────────────────┐  │             │                    │
│  │        AbstractGateway             │  │             │                    │
│  │  ────────────────────────────────  │  │             │                    │
│  │  Bundle discovery (specialized     │  │             │                    │
│  │  agents across all clients)        │  │             │                    │
│  │  Run control (start/pause/resume)  │  │             │                    │
│  │  Ledger streaming (real-time SSE)  │  │             │                    │
│  └──────────────────┬─────────────────┘  │             │                    │
│                     │                    │             │                    │
└─────────────────────┼────────────────────┴─────────────┼────────────────────┘
                      └──────────────────┬───────────────┘
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Composition: AbstractAgent (ReAct/CodeAct/MemAct) + AbstractFlow (.flow)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────----───────┐
│  Foundation: AbstractRuntime + AbstractCore (+ Voice/Vision capability plugins) │
└──────────────────────────────────────────────────────────────────────────----───┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Memory & Knowledge: AbstractMemory · AbstractSemantics                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why AbstractFramework?

- **100% Open Source** — MIT licensed, no black boxes, you own everything
- **Local First** — Run entirely offline with Ollama, LM Studio, or any local model
- **Durable** — Workflows survive crashes; resume exactly where you left off
- **Observable** — Every operation is logged; replay any run from history
- **Modular** — Use one package or the full stack; compose what you need

## Quick Start

### Option 1: Install the Full Framework (Recommended)

```bash
pip install "abstractframework==0.1.1"
```

`abstractframework==0.1.1` installs the pinned global release:

| Package | Version |
|---------|---------|
| `abstractcore` | `2.11.8` |
| `abstractruntime` | `0.4.2` |
| `abstractagent` | `0.3.1` |
| `abstractflow` | `0.3.7` |
| `abstractcode` | `0.3.6` |
| `abstractgateway` | `0.2.1` |
| `abstractmemory` | `0.0.2` |
| `abstractsemantics` | `0.0.2` |
| `abstractvoice` | `0.6.3` |
| `abstractvision` | `0.2.1` |
| `abstractassistant` | `0.4.2` |

Default behavior in this release:
- `abstractcore` is installed with `openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server`
- `abstractflow` is installed with `editor`

### Option 2: Select a Provider / Model

```bash
# Local (recommended)
ollama serve && ollama pull qwen3:4b

# Or use LM Studio
# Or cloud providers via env vars:
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

### Option 3: Terminal Agent (5 minutes)

```bash
abstractcode --provider ollama --model qwen3:4b
```

You now have a durable coding assistant in your terminal. Type `/help` to explore.

> **Durability**: Your session persists across restarts — close and reopen, your full context is preserved. Start fresh with `/clear`.

### Option 4: Tray Assistant (macOS)

```bash
assistant tray
```

The assistant appears in your menu bar. Click to interact, or use keyboard shortcuts.

> **Durability**: Sessions persist — your conversation history is preserved across app restarts.

### Option 5: Just the LLM API

Use AbstractCore as a drop-in unified LLM client that works with any provider and model:

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
# llm = create_llm("openai", model="gpt-4o")
# llm = create_llm("anthropic", model="claude-3-5-sonnet-latest")

response = llm.generate("Explain durable execution in 3 bullets.")
print(response.content)
```

### Option 6: Gateway + Browser UI

Deploy a run gateway and observe workflows in your browser:

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="for-my-security-my-token-must-be-at-least-15-chars"
export ABSTRACTGATEWAY_DATA_DIR="my-folder/runtime/gateway"

abstractgateway serve --port 8080
npx @abstractframework/observer        # Gateway observability dashboard
npx @abstractframework/flow            # Visual workflow editor
npx @abstractframework/code            # Browser coding assistant
```

Open http://localhost:3001, connect to the gateway, and start observing.

---

## Install

### Python (single command)

```bash
pip install "abstractframework==0.1.1"
```

### Python (install specific components only)

```bash
pip install abstractcore==2.11.8
pip install "abstractflow[editor]==0.3.7"
pip install abstractgateway==0.2.1
```

### JavaScript/Node (browser UIs)

```bash
# Web UIs (run directly)
npx @abstractframework/observer        # Gateway observability dashboard
npx @abstractframework/flow            # Visual workflow editor
npx @abstractframework/code            # Browser coding assistant

# UI component libraries (for building your own apps)
npm install @abstractframework/ui-kit
npm install @abstractframework/panel-chat
npm install @abstractframework/monitor-flow
npm install @abstractframework/monitor-active-memory
npm install @abstractframework/monitor-gpu
```

---

## The Ecosystem

The tables below describe the ecosystem components. The `abstractframework==0.1.1` install profile pins all Python packages to the versions listed in Quick Start.

### Foundation

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractCore**](https://github.com/lpalbou/abstractcore) | Unified LLM API — providers, tools, structured output, media | `pip install abstractcore` |
| [**AbstractRuntime**](https://github.com/lpalbou/abstractruntime) | Durable execution — ledger, effects, pause/resume, replay | `pip install abstractruntime` |

### Composition

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractAgent**](https://github.com/lpalbou/abstractagent) | Agent patterns — ReAct, CodeAct, MemAct loops | `pip install abstractagent` |
| [**AbstractFlow**](https://github.com/lpalbou/abstractflow) | Visual workflows — portable `.flow` bundles + editor | `pip install abstractflow` |

### Memory & Semantics

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractMemory**](https://github.com/lpalbou/abstractmemory) | Temporal triple store — provenance-aware, vector search | `pip install abstractmemory` |
| [**AbstractSemantics**](https://github.com/lpalbou/abstractsemantics) | Schema registry — predicates, entity types for KG | `pip install abstractsemantics` |

### Applications

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractCode**](https://github.com/lpalbou/abstractcode) | Terminal TUI — durable coding assistant | `pip install abstractcode` |
| [**AbstractAssistant**](https://github.com/lpalbou/abstractassistant) | macOS tray app — local agent with optional voice | `pip install abstractassistant` |
| [**AbstractGateway**](https://github.com/lpalbou/abstractgateway) | HTTP server — remote runs, durable commands, SSE | `pip install abstractgateway` |
| [**AbstractObserver**](https://github.com/lpalbou/abstractobserver) | Browser UI — observe, launch, and control runs | `npx @abstractframework/observer` |

### Modalities (AbstractCore Capability Plugins)

These are **optional capability plugins** for AbstractCore. Once installed, they expose additional capabilities on `llm` instances (e.g., `llm.voice.tts()`, `llm.vision.t2i()`), keeping AbstractCore lightweight by default.

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractVoice**](https://github.com/lpalbou/abstractvoice) | Voice I/O — adds `llm.voice` (TTS) and `llm.audio` (STT) | `pip install abstractcore abstractvoice` |
| [**AbstractVision**](https://github.com/lpalbou/abstractvision) | Image generation — adds `llm.vision` (text-to-image, image-to-image) | `pip install abstractcore abstractvision` |

### Web UIs (npm)

| Package | What It Does | Install |
|---------|--------------|---------|
| [**@abstractframework/flow**](https://github.com/lpalbou/abstractflow) | Visual workflow editor (drag-and-drop) | `npx @abstractframework/flow` |
| [**@abstractframework/code**](https://github.com/lpalbou/abstractcode) | Browser-based coding assistant | `npx @abstractframework/code` |

### UI Components (npm)

| Package | What It Does |
|---------|--------------|
| [**@abstractframework/ui-kit**](https://github.com/lpalbou/abstractuic) | Theme tokens + UI primitives |
| [**@abstractframework/panel-chat**](https://github.com/lpalbou/abstractuic) | Chat thread + message cards + composer |
| [**@abstractframework/monitor-flow**](https://github.com/lpalbou/abstractuic) | Agent-cycle trace viewer |
| [**@abstractframework/monitor-active-memory**](https://github.com/lpalbou/abstractuic) | Knowledge graph explorer (ReactFlow) |
| [**@abstractframework/monitor-gpu**](https://github.com/lpalbou/abstractuic) | GPU utilization widget |

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Docs Index](docs/README.md) | Entrypoint docs for the ecosystem |
| [Getting Started](docs/getting-started.md) | Pick a path and run something |
| [Architecture](docs/architecture.md) | How the pieces fit together |
| [API](docs/api.md) | Meta-package API (`create_llm`, install profile helpers) |
| [Configuration](docs/configuration.md) | Environment variables & providers |
| [FAQ](docs/faq.md) | Common questions |
| [Scenarios](docs/scenarios/README.md) | End-to-end paths by use case |
| [Guides](docs/guide/README.md) | Focused "how it works" notes |
| [Glossary](docs/glossary.md) | Shared terminology |

---

## Create More Solutions

AbstractFramework is designed so you can author one specialized workflow and deploy it across clients.

1. Build your specialized logic in the Flow editor (`npx @abstractframework/flow`).
2. Export it as a `.flow` bundle with an interface contract (`abstractcode.agent.v1`).
3. Run it in terminal (`abstractcode --workflow ...`), browser UIs, or through `abstractgateway`.

See `docs/getting-started.md` Path 12 for a complete end-to-end example.

---

## Philosophy

We built AbstractFramework because we wanted:

1. **Full control** — No vendor lock-in, no proprietary dependencies
2. **Local by default** — Privacy and cost control with open-source models
3. **Durability** — AI systems that don't lose work when things crash
4. **Observability** — Complete visibility, not a black box
5. **Composability** — Use what you need, replace what you don't

Cloud APIs are supported when you need them (complex reasoning tasks), but the framework is designed to run entirely on your hardware.

---

## Contributing

Every package is its own repo. Find what interests you:

**Foundation:** [AbstractCore](https://github.com/lpalbou/abstractcore) · [AbstractRuntime](https://github.com/lpalbou/abstractruntime)

**Composition:** [AbstractAgent](https://github.com/lpalbou/abstractagent) · [AbstractFlow](https://github.com/lpalbou/abstractflow)

**Memory:** [AbstractMemory](https://github.com/lpalbou/abstractmemory) · [AbstractSemantics](https://github.com/lpalbou/abstractsemantics)

**Apps:** [AbstractCode](https://github.com/lpalbou/abstractcode) · [AbstractAssistant](https://github.com/lpalbou/abstractassistant) · [AbstractGateway](https://github.com/lpalbou/abstractgateway) · [AbstractObserver](https://github.com/lpalbou/abstractobserver)

**Modalities:** [AbstractVoice](https://github.com/lpalbou/abstractvoice) · [AbstractVision](https://github.com/lpalbou/abstractvision)

**UI Components:** [AbstractUIC](https://github.com/lpalbou/abstractuic)

---

## License

MIT — see [LICENSE](LICENSE).
