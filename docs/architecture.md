# Architecture

AbstractFramework is built around a simple but powerful idea: **durable, observable execution**.

Every operation is logged. Workflows survive crashes. UIs can render by replaying history. Tools execute at explicit boundaries. This document explains how the pieces fit together.

## The Big Picture

AbstractFramework supports two deployment patterns: **Gateway-first (recommended)** and **Local in-process (alternative)**.

### The Gateway Path (recommended)

Unified execution of specialized agents across all thin clients, for both remote and local deployments.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                      Thin Clients (Browser UIs)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Observer   │  │ Flow Editor │  │  Code Web   │  │  Your App   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────┘
          │                │    HTTP/SSE    │                │
          └────────────────┴────────┬───────┴────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AbstractGateway (Control Plane)                      │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Bundle discovery — expose .flow specialized agents to all clients        │
│  • Run control — start/pause/resume/cancel/schedule                         │
│  • Ledger streaming — real-time SSE updates                                 │
│  • Unified execution — same workflow runs identically everywhere            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Shared Foundation (see below)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Local Path (alternative)

In-process execution without a gateway, simpler, but limited to local deployments and without access to the abstractions of the gateway.
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Local Host Applications                                │
│  ┌───────────────────┐    ┌──────────────────-─┐                            │
│  │   AbstractCode    │    │  AbstractAssistant │  ◄── Run runtime directly  │
│  │    (terminal)     │    │   (macOS tray)     │      (may migrate to GW)   │
│  └─────────┬─────────┘    └─────────┬─────────-┘                            │
└────────────┼────────────────────────┼───────────────────────────────────────┘
             │                        │
             └───────────-────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Shared Foundation (see below)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insights:**
- **Gateway path is recommended**: It provides unified bundle discovery and execution of specialized agents across all thin clients
- **Local path is an alternative**: AbstractCode and AbstractAssistant run the runtime in-process — simpler for local dev, but lacks unified workflow discovery
- **Both paths use the same libraries**: The execution semantics are identical; only the host differs

### Shared Foundation

Both deployment paths converge on the same foundation: **AbstractRuntime** and **AbstractCore** are peers, while **Voice**/**Vision** are optional **AbstractCore capability plugins**. Memory and semantics are separate components that can be used by workflows via runtime effects/tooling.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Composition: AbstractAgent (ReAct/CodeAct/MemAct) + AbstractFlow (.flow)   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Foundation (Two Peers)                               │
│                                                                             │
│  ┌──────────────────────────────┐    ┌──────────────────────────────────┐   │
│  │       AbstractRuntime        │    │         AbstractCore             │   │
│  │   Durable kernel + ledger    │    │    LLM API + tool schemas        │   │
│  └──────────────────────────────┘    │  ┌────────────┐ ┌─────────────┐  │   │
│                                      │  │   Voice    │ │   Vision    │  │   │
│                                      │  │  (TTS/STT) │ │ (Image gen) │  │   │
│                                      │  └────────────┘ └─────────────┘  │   │
│                                      │ capability plugins (optional)    │   │
│                                      └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Memory & Knowledge                               │
│         AbstractMemory (temporal triples) + AbstractSemantics (KG)          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### Runs & The Ledger

A **run** is a durable workflow instance. Every run has a **ledger** — an append-only log of everything that happened.

```
Run: agent_task_abc123
┌─────────────────────────────────────────────────────────┐
│ Ledger                                                  │
├──────┬──────────────┬───────────────────────────────────┤
│ Step │ Type         │ Data                              │
├──────┼──────────────┼───────────────────────────────────┤
│ 1    │ LLM_CALL     │ prompt, response, tokens          │
│ 2    │ TOOL_CALLS   │ [{name: "read_file", args: ...}]  │
│ 3    │ TOOL_RESULTS │ [{result: "file contents..."}]    │
│ 4    │ LLM_CALL     │ prompt, response, tokens          │
│ ...  │ ...          │ ...                               │
└──────┴──────────────┴───────────────────────────────────┘
```

This design enables:
- **Replay**: Reconstruct any state from the ledger
- **Observability**: UIs render by reading history
- **Durability**: Resume after crashes
- **Debugging**: Inspect exactly what happened

### Effects & Waits

An **effect** is a typed request for something to happen (LLM call, tool call, user input, timer).

A **wait** is an explicit pause. The run stops and stores its state. Later, something resumes it.

```
Agent: "I need to read a file"
    │
    ▼
┌─────────────────────────────────┐
│ Effect: TOOL_CALLS              │
│ tools: [{read_file, path: ...}] │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│ Wait: WAITING_FOR_TOOL_RESULTS  │
│ State checkpointed to storage   │
└─────────────────────────────────┘
    │
    │  ← Host executes tool, resumes with results
    ▼
┌─────────────────────────────────┐
│ Resume with tool results        │
│ Run continues...                │
└─────────────────────────────────┘
```

This is why AbstractCode and AbstractAssistant can survive restarts — tool execution happens at a durable boundary.

### Flows & Bundles

A **flow** is a specialized agent authored with AbstractFlow. Unlike simple agent loops, flows enable:
- **Deterministic execution** — The same inputs produce the same execution path
- **Recursive composition** — Flows can invoke subflows (nested workflows)
- **Multi-state coordination** — Complex state machines with branching, loops, and parallel paths
- **Multi-agent orchestration** — Multiple agent patterns coordinated within a single workflow

A **bundle** (`.flow` file) is the portable distribution unit:
- VisualFlow JSON (the workflow graph)
- Manifest (metadata, entry points, interface declarations)
- Subflows (dependencies)

The Gateway discovers bundles and exposes them to thin clients. This is how you deploy and share workflows.

### Interface Contracts (Run Anywhere)

Flows can implement **interface contracts** that define standard I/O patterns. This lets the same flow run in any compatible client:

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Interface: abstractcode.agent.v1                                          │
│  ───────────────────────────────────────────────────────────────────────── │
│  On Flow Start (outputs):  provider, model, prompt, tools, context, ...    │
│  On Flow End (inputs):     response, success, meta, scratchpad             │
└────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Runs in:                                                                   │
│  • AbstractCode (terminal) — /workflow command                              │
│  • AbstractObserver (browser) — workflow picker                             │
│  • Code Web UI (browser) — workflow picker                                  │
│  • Custom apps — via Gateway bundle discovery                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why this matters:** You author a specialized agent once in the visual editor (e.g., a "deep researcher" or "code reviewer") and it automatically works in every client that supports the interface. No client-specific code needed.

## Gateway Architecture

For production deployments, AbstractGateway provides the control plane:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Browser / Clients                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  Observer   │  │  Flow Editor│  │  Your App   │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          │         HTTP/SSE                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AbstractGateway                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  REST API   │  │   Runner    │  │   Stores    │                  │
│  │  /api/*     │  │  tick runs  │  │  ledger,    │                  │
│  │             │  │  poll inbox │  │  artifacts  │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Why a gateway?**
- Remote execution (server owns durability)
- Multiple clients can observe the same runs
- Durable command inbox (pause, resume, cancel)
- Replay-first observability over HTTP/SSE

## Event Bridges (Inbound Integrations)

Some deployments use inbound "bridges" that turn external messages into durable runtime events. Typical pattern:

1. Bridge receives an inbound message (Telegram, email, etc.).
2. Bridge chooses a stable `session_id` (for example `telegram:<chat_id>` or an email thread id).
3. Gateway emits an event into that session (for example `telegram.message` or `email.message`).
4. A workflow consumes the event (On Event) and replies by calling tools.

This preserves durability and observability: inbound content becomes replayable ledger history + artifacts.

See:
- [Scenario: Telegram permanent contact](scenarios/telegram-permanent-contact.md)
- [Scenario: Email inbox agent](scenarios/email-inbox-agent.md)

## Memory Architecture

AbstractFramework separates two concerns:

1. **Durable History** (AbstractRuntime)
   - Recoverable from ledger + artifacts
   - Spans archived with summaries
   - Provenance handles for deterministic recall

2. **Semantic Knowledge** (AbstractMemory + AbstractSemantics)
   - Temporal, provenance-aware triples
   - Deterministic query semantics
   - Schema consistency via AbstractSemantics registry

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent Context                                  │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Active Memory (what the LLM sees)                              │ │
│  │ ─────────────────────────────────                              │ │
│  │ Recent messages, compacted history, relevant knowledge         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│              ┌───────────────┴───────────────┐                      │
│              ▼                               ▼                      │
│  ┌─────────────────────┐       ┌─────────────────────┐              │
│  │ Durable History     │       │ Knowledge Graph     │              │
│  │ (Runtime + Ledger)  │       │ (AbstractMemory)    │              │
│  │                     │       │                     │              │
│  │ • Step records      │       │ • Temporal triples  │              │
│  │ • Artifacts         │       │ • Vector search     │              │
│  │ • Provenance        │       │ • Schema validation │              │
│  └─────────────────────┘       └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

## Modality Architecture

AbstractVoice and AbstractVision extend AbstractCore with multimodal capabilities:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AbstractCore                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Unified LLM API                                                 ││
│  │ create_llm("ollama", model="...") → LLM instance                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐        │
│  │ Capability:     │ │ Capability:     │ │ Capability:     │        │
│  │ llm.voice       │ │ llm.vision      │ │ llm.audio       │        │
│  │ (via Abstract   │ │ (via Abstract   │ │ (native or      │        │
│  │  Voice)         │ │  Vision)        │ │  fallback)      │        │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

## Security Model

### Authentication

- Gateway uses Bearer token authentication
- Token set via `ABSTRACTGATEWAY_AUTH_TOKEN`
- All API endpoints require valid token (except `/api/health`)

### Tool Execution Boundary

Tool **schemas** are durable; tool **callables** are not. This is intentional:

```
┌─────────────────────┐     ┌─────────────────────┐
│ DURABLE (stored)    │     │ NOT DURABLE         │
├─────────────────────┤     ├─────────────────────┤
│ Tool schemas/specs  │     │ Tool implementations│
│ Call arguments      │     │ Actual execution    │
│ Results             │     │ Side effects        │
└─────────────────────┘     └─────────────────────┘
```

This means:
- Tool calls become approval points (configurable)
- Execution is auditable
- Runs remain restart-safe

## Deployment Patterns

### Local Development

```
You
 │
 └──► AbstractCode (terminal)
         │
         └──► Runtime + Core (in-process)
```

### Production (Gateway)

```
Browser ──► Nginx ──► AbstractGateway ──► SQLite/Postgres
                           │
                           └──► Runtime + Core
```

### Distributed

```
Browser ──► Load Balancer ──► Gateway (x3) ──► Postgres
                                  │
                                  └──► Worker pool
```

## Going Deeper

Each project has its own architecture docs:

### Foundation
- [AbstractCore Architecture](https://github.com/lpalbou/abstractcore/blob/main/docs/architecture.md)
- [AbstractRuntime Architecture](https://github.com/lpalbou/abstractruntime/blob/main/docs/architecture.md)

### Composition
- [AbstractAgent Architecture](https://github.com/lpalbou/abstractagent/blob/main/docs/architecture.md)
- [AbstractFlow Architecture](https://github.com/lpalbou/abstractflow/blob/main/docs/architecture.md)

### Memory & Semantics
- [AbstractMemory Architecture](https://github.com/lpalbou/abstractmemory/blob/main/docs/architecture.md)
- [AbstractSemantics Architecture](https://github.com/lpalbou/abstractsemantics/blob/main/docs/architecture.md)

### Applications
- [AbstractCode Architecture](https://github.com/lpalbou/abstractcode/blob/main/docs/architecture.md)
- [AbstractAssistant Architecture](https://github.com/lpalbou/abstractassistant/blob/main/docs/architecture.md)
- [AbstractGateway Architecture](https://github.com/lpalbou/abstractgateway/blob/main/docs/architecture.md)
- [AbstractObserver Architecture](https://github.com/lpalbou/abstractobserver/blob/main/docs/architecture.md)

### Modalities
- [AbstractVoice Architecture](https://github.com/lpalbou/abstractvoice/blob/main/docs/architecture.md)
- [AbstractVision Architecture](https://github.com/lpalbou/abstractvision/blob/main/docs/architecture.md)

### UI Components
- [AbstractUIC Architecture](https://github.com/lpalbou/abstractuic/blob/main/docs/architecture.md)

### Web UIs
- [Flow Editor](https://github.com/lpalbou/abstractflow/blob/main/docs/web-editor.md) — Visual workflow authoring (`npx @abstractframework/flow`)
- [Code Web UI](https://github.com/lpalbou/abstractcode/blob/main/docs/web.md) — Browser-based coding assistant (`npx @abstractframework/code`)

---

## Related Documentation

- **[Getting Started](getting-started.md)** — Pick a path and run something
- **[Configuration](configuration.md)** — Environment variables and settings
- **[FAQ](faq.md)** — Common questions and troubleshooting
