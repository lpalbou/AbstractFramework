# AbstractFramework Documentation

Welcome! This is the **documentation hub** for the AbstractFramework ecosystem — a modular, open-source platform for building durable, observable AI systems that work offline.

Whether you're a developer looking to integrate LLMs into your app, an AI engineer building production workflows, or a team that needs reliable AI infrastructure — you'll find a starting point here.

## Quick Install

```bash
pip install "abstractframework==0.1.2"
```

That installs all framework Python packages together, including:
- `abstractcore` configured with core extras (`openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server`)
- `abstractflow` configured with `editor`

---

## Start Here

| If You're... | Read This |
|--------------|-----------|
| **Brand new** to AbstractFramework | [Getting Started](getting-started.md) — pick a path based on what you want to build |
| **Evaluating** the framework | [Architecture](architecture.md) — understand how it all fits together |
| **Setting up** your environment | [Configuration](configuration.md) — providers, API keys, and settings |
| **Looking for answers** to common questions | [FAQ](faq.md) — includes honest comparisons with other frameworks |
| **Following a use case** end-to-end | [Scenarios](scenarios/README.md) — step-by-step walkthroughs |
| **Diving into a specific topic** | [Guides](guide/README.md) — focused "how it works" notes |
| **Checking terminology** | [Glossary](glossary.md) — shared definitions across the ecosystem |
| **Using the meta-package API** | [API](api.md) — `abstractframework` package helpers and release profile |

---

## What's Possible

AbstractFramework is more than a collection of packages — it's a complete AI infrastructure. Here's what you can do across the ecosystem:

### Build & Deploy AI Agents
- **Three agent patterns** out of the box: ReAct (tool-first reasoning), CodeAct (Python execution), MemAct (memory-enhanced)
- **Visual workflow editor** — drag-and-drop agent design, export as portable `.flow` bundles
- **Interface contracts** — author once, deploy to terminal, browser, or any custom client
- **Scheduled workflows** — cron-style durable jobs that survive restarts

### Use Any LLM, Anywhere
- **10+ providers**: OpenAI, Anthropic, Ollama, LM Studio, vLLM, HuggingFace, MLX, OpenRouter, Portkey, and any OpenAI-compatible endpoint
- **Universal tool calling** — works even on models that don't natively support tools (via prompted syntax)
- **Structured output** — extract Pydantic models from any provider
- **Streaming + async** — full support across all providers
- **MCP integration** — discover and use tools from Model Context Protocol servers
- **Token budget management** — unified `max_tokens` / `max_output_tokens` across providers
- **Conversation state** — `BasicSession` for multi-turn conversations with history management

### Go Multimodal
- **Voice I/O** (offline) — Piper TTS + Whisper STT, voice cloning, multilingual
- **Image generation** (local) — Diffusers, GGUF, or OpenAI-compatible backends
- **Media input** — images, audio, video, PDFs, Office docs with policy-driven fallbacks
- **Glyph compression** — render long documents as images for cheaper VLM processing

### Ensure Reliability
- **Durable execution** — workflows survive crashes and resume exactly where they left off
- **Append-only ledger** — tamper-evident, hash-chained history of every operation
- **Tool approval boundaries** — configurable approval gates for safe tool execution
- **Snapshots & bookmarks** — named checkpoints for run state
- **Evidence capture** — artifact-backed provenance for debugging and audit
- **History bundles** — export reproducible run snapshots

### Observe & Debug Everything
- **AbstractObserver** browser UI — replay runs, stream real-time updates, voice chat
- **Interaction tracing** — inspect every prompt, response, and token usage
- **Knowledge graph explorer** — visualize and query what your AI has learned
- **GPU monitoring** — real-time utilization widget

### Connect to the Outside World
- **Telegram bridge** — durable bot with full audit trail
- **Email bridge** — process email threads with workflows
- **Event bridges** — any inbound service becomes a replayable ledger source
- **OpenAI-compatible server** — serve any LLM through one `/v1` API

### Build Your Own UI
- **React components** — chat panels, agent traces, KG explorer, GPU monitor
- **Theme system** — CSS variables + dark mode support
- **Host-driven architecture** — components receive data via props, no hidden dependencies

---

## Find What You Need

### Python Packages (pip)

| I want... | Package |
|-----------|---------|
| A unified LLM client library (tools, structured output, media, MCP) | [AbstractCore](https://github.com/lpalbou/abstractcore) |
| A durable workflow runtime (pause/resume + ledger + snapshots) | [AbstractRuntime](https://github.com/lpalbou/abstractruntime) |
| Ready-made agent patterns (ReAct, CodeAct, MemAct) | [AbstractAgent](https://github.com/lpalbou/abstractagent) |
| Visual workflows + bundling + recursive subflows | [AbstractFlow](https://github.com/lpalbou/abstractflow) |
| A terminal app for agentic coding (plan/review modes, MCP, workflows) | [AbstractCode](https://github.com/lpalbou/abstractcode) |
| A macOS menu bar assistant (multi-session, voice) | [AbstractAssistant](https://github.com/lpalbou/abstractassistant) |
| A deployable run gateway (HTTP/SSE, scheduling, SQLite) | [AbstractGateway](https://github.com/lpalbou/abstractgateway) |
| Voice I/O (TTS/STT, cloning, multilingual) — capability plugin for AbstractCore | [AbstractVoice](https://github.com/lpalbou/abstractvoice) |
| Image generation (Diffusers, GGUF, OpenAI-compatible) — capability plugin for AbstractCore | [AbstractVision](https://github.com/lpalbou/abstractvision) |
| Music generation (text-to-music) — capability plugin for AbstractCore | `abstractmusic` |
| A temporal triple store for knowledge graphs | [AbstractMemory](https://github.com/lpalbou/abstractmemory) |
| A semantics registry for KG assertions | [AbstractSemantics](https://github.com/lpalbou/abstractsemantics) |
| An OpenAI-compatible multi-provider API server | [AbstractCore Server](https://github.com/lpalbou/abstractcore) (`pip install "abstractcore[server]"`) |
| Built-in CLI tools (summarizer, extractor, judge, deepsearch) | [AbstractCore Apps](https://github.com/lpalbou/abstractcore) |

### npm Packages

| I want... | Package |
|-----------|---------|
| A browser UI to observe, launch, and schedule gateway runs | `npx @abstractframework/observer` |
| A visual workflow editor (drag-and-drop) | `npx @abstractframework/flow` |
| A browser-based coding assistant | `npx @abstractframework/code` |
| UI building blocks for my own app | [@abstractframework/ui-kit](https://github.com/lpalbou/abstractuic), etc. |

---

## Architecture at a Glance

```
 RECOMMENDED: Gateway-first          │  ALTERNATIVE: Local in-process
─────────────────────────────────────┼───────────────────────────────────
 Browser UIs (Observer, Flow         │  AbstractCode (terminal)
 Editor, Code Web, Your App)         │  AbstractAssistant (macOS tray)
              │                      │             │
              ▼                      │             │
       AbstractGateway               │             │
  (bundle discovery, run control,    │             │
   scheduling, event bridges)        │             │
              │                      │             │
              └──────────────────────┴─────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│  Composition: AbstractAgent (ReAct/CodeAct/MemAct) + AbstractFlow │
└───────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────┐
│  Foundation: AbstractRuntime + AbstractCore (+ Voice/Vision + MCP)    │
└───────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│  Memory & Knowledge: AbstractMemory · AbstractSemantics           │
└───────────────────────────────────────────────────────────────────┘
```

See [Architecture](architecture.md) for details on both paths.

---

## What's in This Repo

This repo provides:

- One canonical package entrypoint (`abstractframework`) for full-stack installation
- Ecosystem documentation (architecture, setup, configuration, FAQ)
- Use-case scenarios and focused guides (see below)
- A map of package responsibilities so teams can build and deploy new specialized solutions
- Links to browser UIs distributed via npm (`@abstractframework/observer`, `@abstractframework/flow`, `@abstractframework/code`)

---

## LLM Context Files

If you're feeding this repo into an LLM:

- `llms.txt` is the navigation/index file.
- `llms-full.txt` is a single concatenated context file.
- Regenerate: `python scripts/gen_llms_full.py`

---

## Quick Links

- [Main README](../README.md) — full ecosystem overview
- [Getting Started](getting-started.md) — pick your path
- [Architecture](architecture.md) — how it all fits together
- [API](api.md) — package-level API helpers
- [Configuration](configuration.md) — environment variables and settings
- [FAQ](faq.md) — common questions and troubleshooting
- [Scenarios](scenarios/README.md) — end-to-end paths by use case
- [Guides](guide/README.md) — focused "how it works" notes
- [Glossary](glossary.md) — shared terminology
