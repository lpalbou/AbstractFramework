# AbstractFramework

**Build durable, observable AI systems — fully open source, works offline.**

AbstractFramework is a modular ecosystem for building AI agents and workflows that **survive restarts**, **scale to production**, and give you **full visibility** into what's happening. Every component is open source, works with local models, and designed to be composed however you need.

This repository is the **single access point** to the ecosystem:
- Install the full framework with one `pip` command
- Understand how all packages fit together
- Create and deploy new specialized solutions (flows/agents) across clients

---

## What Can You Build?

AbstractFramework is not "yet another LLM wrapper." It's a **complete infrastructure** for AI systems that need to be reliable, observable, and production-ready.

| You Want To... | AbstractFramework Gives You... |
|-----------------|--------------------------------|
| **Build a coding assistant** that remembers everything across restarts | AbstractCode (terminal TUI) + durable runtime — your full session history, tool calls, and context survive crashes and reboots |
| **Deploy a visual AI workflow** (drag-and-drop) that runs in terminal, browser, or any custom app | AbstractFlow visual editor → export `.flow` bundle → runs anywhere via interface contracts |
| **Create a voice-enabled assistant** with offline TTS/STT | AbstractVoice (Piper + Whisper) + AbstractAssistant (macOS tray) — fully offline, no cloud required |
| **Generate images locally** from text prompts | AbstractVision + local Diffusers/GGUF models — no API keys needed |
| **Schedule recurring AI jobs** (reports, analysis, monitoring) | AbstractGateway scheduled workflows — durable, cron-style, survives restarts |
| **Build a knowledge graph** that tracks what your AI has learned | AbstractMemory (temporal triples) + AbstractSemantics (schema validation) |
| **Observe and debug** every LLM call, tool execution, and decision | Append-only ledger + AbstractObserver browser UI — replay any run from history |
| **Connect to Telegram, email, or external services** | Event bridges + durable workflows — inbound messages become replayable ledger entries |
| **Use tools from MCP servers** (Model Context Protocol) | Built-in MCP client discovers and integrates external tool servers (HTTP/stdio) |
| **Compress long documents** for cheaper LLM processing | Glyph visual-text compression — render documents as images, process with VLMs |
| **Serve any LLM** through one OpenAI-compatible API | AbstractCore server mode — multi-provider `/v1` gateway with tool + media support |
| **Build your own UI** with pre-built React components | AbstractUIC — chat panels, agent traces, KG explorer, GPU monitor |

---

## Architecture at a Glance

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
│  │  Scheduled workflows (cron-style)  │  │             │                    │
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
┌─────────────────────────────────────────────────────────────────────────────┐
│  Foundation: AbstractRuntime + AbstractCore (+ Voice/Vision plugins + MCP)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Memory & Knowledge: AbstractMemory · AbstractSemantics                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why AbstractFramework?

- **100% Open Source** — MIT licensed, no black boxes, you own everything
- **Local First** — Run entirely offline with Ollama, LM Studio, or any local model
- **Durable** — Workflows survive crashes; resume exactly where you left off
- **Observable** — Every operation is logged in an append-only ledger; replay any run from history
- **Modular** — Use one package or the full stack; compose what you need
- **Visual** — Build workflows with drag-and-drop; export as portable `.flow` bundles
- **Multimodal** — Voice I/O, image generation, video, and document processing — all offline-capable
- **Interoperable** — MCP tool servers, OpenAI-compatible API, structured output, any LLM provider
- **Production-Ready** — SQLite/Postgres backends, split API/runner, scheduled jobs, event bridges

---

## Quick Start

### Option 1: Install the Full Framework (Recommended)

```bash
pip install "abstractframework==0.1.2"
```

`abstractframework==0.1.2` installs the pinned global release:

| Package | Version |
|---------|---------|
| `abstractcore` | `2.12.0` |
| `abstractruntime` | `0.4.2` |
| `abstractagent` | `0.3.1` |
| `abstractflow` | `0.3.7` |
| `abstractcode` | `0.3.6` |
| `abstractgateway` | `0.1.0` |
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
pip install "abstractframework==0.1.2"
```

### Python (install specific components only)

```bash
pip install abstractcore==2.11.9
pip install "abstractflow[editor]==0.3.7"
pip install abstractgateway==0.1.0
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

The tables below describe the ecosystem components. The `abstractframework==0.1.2` install profile pins all Python packages to the versions listed in Quick Start.

### Foundation

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractCore**](https://github.com/lpalbou/abstractcore) | Unified LLM API — providers, tools, structured output, media, MCP, embeddings, OpenAI-compatible server | `pip install abstractcore` |
| [**AbstractRuntime**](https://github.com/lpalbou/abstractruntime) | Durable execution — ledger, effects, pause/resume, replay, snapshots, provenance | `pip install abstractruntime` |

### Composition

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractAgent**](https://github.com/lpalbou/abstractagent) | Agent patterns — ReAct, CodeAct, MemAct loops with durable runs | `pip install abstractagent` |
| [**AbstractFlow**](https://github.com/lpalbou/abstractflow) | Visual workflows — portable `.flow` bundles, recursive subflows, visual editor | `pip install abstractflow` |

### Memory & Semantics

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractMemory**](https://github.com/lpalbou/abstractmemory) | Temporal triple store — provenance-aware, vector search, LanceDB backend | `pip install abstractmemory` |
| [**AbstractSemantics**](https://github.com/lpalbou/abstractsemantics) | Schema registry — predicates, entity types, JSON Schema for KG assertions | `pip install abstractsemantics` |

### Applications

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractCode**](https://github.com/lpalbou/abstractcode) | Terminal TUI — durable coding assistant with plan/review modes, workflows, MCP | `pip install abstractcode` |
| [**AbstractAssistant**](https://github.com/lpalbou/abstractassistant) | macOS tray app — local agent with optional voice, multi-session, durable | `pip install abstractassistant` |
| [**AbstractGateway**](https://github.com/lpalbou/abstractgateway) | HTTP server — remote runs, durable commands, SSE, scheduling, bundle discovery, SQLite/file | `pip install abstractgateway` |
| [**AbstractObserver**](https://github.com/lpalbou/abstractobserver) | Browser UI — observe, launch, schedule, and control runs, voice chat, mindmap | `npx @abstractframework/observer` |

### Modalities (AbstractCore Capability Plugins)

These are **optional capability plugins** for AbstractCore. Once installed, they expose additional capabilities on `llm` instances (e.g., `llm.voice.tts()`, `llm.vision.t2i()`), keeping AbstractCore lightweight by default.

| Package | What It Does | Install |
|---------|--------------|---------|
| [**AbstractVoice**](https://github.com/lpalbou/abstractvoice) | Voice I/O — TTS (Piper), STT (Whisper), voice cloning, multilingual, offline-first | `pip install abstractcore abstractvoice` |
| [**AbstractVision**](https://github.com/lpalbou/abstractvision) | Image generation — text-to-image, image-to-image, Diffusers + GGUF + OpenAI-compatible | `pip install abstractcore abstractvision` |
| **AbstractMusic** | Music generation — local text-to-music/audio (ACE-Step v1.5 default; Diffusers optional) | `pip install abstractcore abstractmusic` |

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

## Key Capabilities in Depth

Beyond the basics, AbstractFramework offers powerful capabilities that set it apart from other AI frameworks. Here's what's possible.

### 🔧 Universal Tool Calling + MCP

AbstractCore provides **universal tool calling** across all LLM providers — even models that don't natively support tools (via prompted tool syntax). Define tools once, use them everywhere:

```python
from abstractcore import create_llm, tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"{city}: 22°C and sunny"

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("What's the weather in Paris?", tools=[get_weather])
print(resp.tool_calls)  # Structured tool calls, ready for execution
```

**MCP (Model Context Protocol):** AbstractCore can discover and integrate tools from any MCP-compatible server — HTTP or stdio. This means you can connect to external tool ecosystems without writing adapter code.

### 📊 Structured Output

Extract structured data from any LLM using Pydantic models — provider-aware strategies handle the differences:

```python
from pydantic import BaseModel
from abstractcore import create_llm

class Report(BaseModel):
    title: str
    findings: list[str]
    confidence: float

llm = create_llm("openai", model="gpt-4o-mini")
report = llm.generate("Analyze HTTP/3 adoption trends.", response_model=Report)
print(report.findings)
```

### 🔄 Streaming + Async

Full support for streaming responses and async patterns across all providers:

```python
# Streaming
for chunk in llm.generate("Write a poem.", stream=True):
    print(chunk.content or "", end="", flush=True)

# Async
resp = await llm.agenerate("Summarize this document.")
```

### 🎙️ Voice I/O (Offline)

AbstractVoice provides production-ready TTS and STT with no cloud dependency:

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")

# Text-to-speech (Piper, offline)
wav_bytes = llm.voice.tts("Hello from AbstractFramework!", format="wav")

# Speech-to-text (Whisper, offline)
text = llm.audio.transcribe("meeting.wav", language="en")

# Audio in LLM requests (auto-transcribed)
response = llm.generate("Summarize this call.", media=["meeting.wav"])
```

Voice cloning, multilingual support, and interactive REPL are also available.

### 🎨 Image Generation (Local)

Generate images locally with Diffusers, GGUF models, or OpenAI-compatible servers:

```python
from abstractvision import VisionManager, LocalAssetStore
from abstractvision.backends import HuggingFaceBackend, HuggingFaceBackendConfig

backend = HuggingFaceBackend(config=HuggingFaceBackendConfig(
    model_id="stabilityai/stable-diffusion-xl-base-1.0",
))
vm = VisionManager(backend=backend, store=LocalAssetStore())
result = vm.generate_image("a watercolor painting of a lighthouse")
```

### 📦 Glyph Visual-Text Compression

A unique feature: render long documents as images, then process them with vision models. This dramatically reduces token usage for large documents:

```python
llm = create_llm("openai", model="gpt-4o", glyph="auto")
resp = llm.generate("Summarize this contract.", media=["contract.pdf"])
```

### 🔗 Embeddings & Semantic Search

Built-in embedding support for RAG and semantic search:

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
embeddings = llm.embed(["first document", "second document"])
```

### 🌐 OpenAI-Compatible Server

Turn AbstractCore into a multi-provider OpenAI-compatible API server:

```bash
pip install "abstractcore[server]"
python -m abstractcore.server.app
```

Route to any provider/model through one API: `model="ollama/qwen3:4b-instruct"`, `model="anthropic/claude-3-5-sonnet"`, etc.

### 📅 Scheduled Workflows

Create durable, recurring AI jobs through the Gateway:

```bash
curl -X POST "http://localhost:8080/api/gateway/runs/schedule" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"bundle_id":"daily-report","start_at":"now","interval":"24h"}'
```

### 🔌 Event Bridges (Telegram, Email, ...)

Connect external services as durable event sources. Inbound messages become replayable ledger entries:

- **Telegram**: `ABSTRACT_TELEGRAM_BRIDGE=1` — a Telegram bot becomes a permanent, durable contact
- **Email**: `ABSTRACT_EMAIL_BRIDGE=1` — email threads are processed by workflows with full audit trails

### 📋 Built-in CLI Apps

AbstractCore ships practical CLI tools out of the box:
- `summarizer` — Summarize documents and text
- `extractor` — Extract structured data
- `judge` — LLM-as-a-judge evaluation
- `intent` — Intent classification
- `deepsearch` — Deep web search with synthesis

### 🔍 Evidence & Provenance

Every operation is captured with full provenance:
- **Tamper-evident ledger** — hash-chained step records
- **Artifact-backed evidence** — large payloads stored by reference
- **Snapshots/bookmarks** — named checkpoints for run state
- **History bundles** — export reproducible run snapshots

---

## Create More Solutions

AbstractFramework is designed so you can **author one specialized workflow and deploy it across every client**.

### Step 1: Design in the Visual Editor

```bash
npx @abstractframework/flow
```

Open http://localhost:3003 and build your workflow with drag-and-drop:
- LLM nodes, tool nodes, conditionals, loops, subflows
- Multi-agent orchestration, parallel paths, state machines
- Memory integration (knowledge graph read/write)

### Step 2: Export as a Portable Bundle

Set `interfaces: ["abstractcode.agent.v1"]` and export as a `.flow` bundle.

### Step 3: Run Anywhere

```bash
# Terminal
abstractcode --workflow my-agent.flow

# Install for easy access
abstractcode workflow install my-agent.flow
abstractcode --workflow my-agent

# Deploy to gateway (appears in all browser UIs automatically)
cp my-agent.flow $ABSTRACTGATEWAY_FLOWS_DIR/
```

### Use Cases

The same workflow can power:
- **Code reviewers** — analyze PRs with configurable rules
- **Deep researchers** — multi-step research with web search and synthesis
- **Data analysts** — scheduled reports with chart generation
- **Content moderators** — classify and flag content with audit trails
- **Customer support agents** — answer questions from knowledge bases
- **DevOps monitors** — scheduled health checks with escalation workflows

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

## Philosophy

We built AbstractFramework because we believe AI systems deserve the same engineering rigor as any other production software:

1. **Full control** — No vendor lock-in, no proprietary dependencies. You can inspect, modify, and extend every line of code.
2. **Local by default** — Privacy and cost control with open-source models. Cloud APIs are supported when you need them, but the framework runs entirely on your hardware.
3. **Durability** — AI systems that don't lose work when things crash. Every workflow survives restarts and can resume exactly where it left off.
4. **Observability** — Complete visibility, not a black box. Every LLM call, tool execution, and decision is logged in a tamper-evident ledger you can replay anytime.
5. **Composability** — Use what you need, replace what you don't. Every package is independently installable and designed to work with or without the others.
6. **Visual authoring** — Complex workflows shouldn't require complex code. Build, test, and deploy AI workflows with a drag-and-drop editor — on the same durable runtime.

---

## Developer Setup (From Source)

To work on the framework itself (all repos, editable installs):

```bash
# 1) Clone all 14 repos into a single directory
./scripts/clone.sh

# 2) Build everything from local source (editable mode) — stay in the .venv
source ./scripts/build.sh

# Use --clean to start with a fresh .venv (avoids cross-project pollution)
source ./scripts/build.sh --clean

# 3) Configure + verify readiness
abstractcore --config
abstractcore --install
```

See [Developer Setup](docs/getting-started.md#developer-setup-from-source) for details on `clone.sh`, `build.sh`, and `install.sh`.

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
