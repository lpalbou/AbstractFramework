# AbstractFramework

**Build durable, observable AI systems — fully open source, works offline.**

AbstractFramework is a modular ecosystem for building AI agents and workflows that survive restarts, scale to production, and give you full visibility into what's happening. Every component is open source, works with local models, and designed to be composed however you need.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Host Applications                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ AbstractCode │  │  Abstract    │  │ AbstractFlow │  │  Your Custom │     │
│  │  (terminal)  │  │  Assistant   │  │   (visual)   │  │     App      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Composition Layer                                    │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │        AbstractAgent         │  │           AbstractMemory             │ │
│  │  ReAct · CodeAct · MemAct    │  │  Temporal triples · Vector search    │ │
│  └──────────────────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Foundation Layer                                   │
│  ┌────────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │        AbstractRuntime         │  │          AbstractCore              │ │
│  │  ───────────────────────────── │  │  ────────────────────────────────  │ │
│  │  Durable execution             │  │  Unified LLM API                   │ │
│  │  Append-only ledger            │  │  Tool calling                      │ │
│  │  Pause → Resume → Replay       │  │  Structured output                 │ │
│  │  Effects & Waits               │  │  Any provider (local/cloud)        │ │
│  └────────────────────────────────┘  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                       │
          ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Optional Modalities                                 │
│       AbstractVoice (TTS/STT)  ·  AbstractVision (Image generation)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Why AbstractFramework?

- **100% Open Source** — MIT licensed, no black boxes, you own everything
- **Local First** — Run entirely offline with Ollama, LM Studio, or any local model
- **Durable** — Workflows survive crashes; resume exactly where you left off
- **Observable** — Every operation is logged; replay any run from history
- **Modular** — Use one package or the full stack; compose what you need

## Quick Start

### Option 1: Terminal Agent (5 minutes)

The fastest way to try AbstractFramework:

```bash
# Start a local model with Ollama
ollama serve && ollama pull qwen3:1.7b

# Run AbstractCode
pip install abstractcode
abstractcode --provider ollama --model qwen3:1.7b
```

You now have a durable coding assistant in your terminal. Type `/help` to explore.

### Option 2: Just the LLM API

Use AbstractCore as a drop-in unified LLM client:

```python
from abstractcore import create_llm

# Works with any provider
llm = create_llm("ollama", model="qwen3:4b-instruct")
# llm = create_llm("openai", model="gpt-4o")
# llm = create_llm("anthropic", model="claude-3-5-sonnet-latest")

response = llm.generate("Explain durable execution in 3 bullets.")
print(response.content)
```

### Option 3: Gateway + Browser UI

Deploy a run gateway and observe workflows in your browser:

```bash
pip install "abstractgateway[http]"

export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

abstractgateway serve --port 8080
npx @abstractframework/observer
```

Open http://localhost:3001, connect to the gateway, and start observing.

---

## Install

### Python Packages (pip)

```bash
# Full ecosystem (meta-package)
pip install "abstractframework[all]"

# Or install only what you need:

# Foundation
pip install abstractcore                # Unified LLM API
pip install abstractruntime             # Durable execution

# Composition
pip install abstractagent               # Agent patterns (ReAct, CodeAct, MemAct)
pip install abstractflow                # Visual workflows

# Memory & Semantics
pip install abstractmemory              # Temporal triple store + vector search
pip install abstractsemantics           # Predicate/entity-type registry

# Applications
pip install abstractcode                # Terminal TUI
pip install abstractassistant           # macOS tray app
pip install "abstractgateway[http]"     # HTTP run gateway

# Modalities (optional)
pip install abstractvoice               # Voice I/O (TTS/STT)
pip install abstractvision              # Image generation
```

### JavaScript/Node Packages (npm)

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
| [**AbstractGateway**](https://github.com/lpalbou/abstractgateway) | HTTP server — remote runs, durable commands, SSE | `pip install "abstractgateway[http]"` |
| [**AbstractObserver**](https://github.com/lpalbou/abstractobserver) | Browser UI — observe, launch, and control runs | `npx @abstractframework/observer` |

### Modalities

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractVoice**](https://github.com/lpalbou/abstractvoice) | Voice I/O — TTS (Piper), STT (Whisper) | `pip install abstractvoice` |
| [**AbstractVision**](https://github.com/lpalbou/abstractvision) | Image generation — text-to-image, image-to-image | `pip install abstractvision` |

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
| [Getting Started](docs/getting-started.md) | Pick a path and run something |
| [Architecture](docs/architecture.md) | How the pieces fit together |
| [Configuration](docs/configuration.md) | Environment variables & providers |
| [FAQ](docs/faq.md) | Common questions |

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
