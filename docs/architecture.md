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
│  • Scheduled workflows — cron-style durable jobs                            │
│  • Event bridges — Telegram, email, external services                       │
│  • Framework routing defaults — control-plane access to Core route config   │
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
│  ┌───────────────────┐                                                      │
│  │   AbstractCode    │  ◄── Run runtime directly (local dev)                │
│  │    (terminal)     │                                                      │
│  └─────────┬─────────┘                                                      │
│                           ┌────────────────────┐                            │
│                           │     SmartNote      │  ◄── Thin client to        │
│                           │   (systray notes)  │      AbstractGateway       │
│                           └────────────────────┘                            │
└────────────┼────────────────────────┼───────────────────────────────────────┘
             │                        │
             └────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Shared Foundation (see below)                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insights:**
- **Gateway path is recommended**: It provides unified bundle discovery and execution of specialized agents across all thin clients
- **Local path is an alternative**: AbstractCode can run the runtime in-process for local dev; AbstractAssistant is now gateway-first by default
- **Both paths use the same libraries**: The execution semantics are identical; only the host differs
- **SmartNote data model**: fragments and cards are stored as artifacts, with KG edges for graph navigation

### Shared Foundation

Both deployment paths converge on the same foundation: **AbstractRuntime** and
**AbstractCore** are peers, while **Voice**/**Vision**/**Music** are optional
**AbstractCore capability plugins**.

Default provider/model routing is Core-owned and operation-based:
`input.*`, `output.*`, `embedding.*`, and future `rerank.*` routes. Gateway can
edit those defaults as a control plane, but it does not own a separate model
defaults file. In split deployments, Gateway proxies route-default reads/writes
to the execution Core host so provider `base_url` values are evaluated from the
host that actually calls the provider.

**AbstractSemantics** is a lower-level vocabulary/schema registry used by
Runtime for stable schema refs and by memory workflows for predicate/entity
validation. **AbstractMemory** is a separate optional knowledge store. Runtime
depends on Semantics; Runtime does not hard-depend on Memory. Gateway wires
Memory into workflows when the memory package is installed.

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
│  │   Schema refs + effects      │    │    Structured output + media     │   │
│  │   Scheduler + history export │    │    Embeddings + MCP + server     │   │
│  └──────────────────────────────┘    │  ┌────────┐ ┌────────┐ ┌───────┐ │   │
│                                      │  │ Voice  │ │ Vision │ │ Music │ │   │
│                                      │  │TTS/STT │ │Image   │ │Exp.   │ │   │
│                                      │  └────────┘ └────────┘ └───────┘ │   │
│                                      │ capability plugins (optional)    │   │
│                                      └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Shared Semantics                                    │
│     AbstractSemantics: predicates, entity types, schema refs                │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Memory & Knowledge                               │
│       AbstractMemory: optional temporal KG store using shared semantics      │
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
│  • AbstractAssistant (tray) — workflow picker + reattach                     │
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
- Scheduled workflows (cron-style durable jobs)
- Bundle discovery (expose workflows to all clients)
- Event bridges (Telegram, email, external services)

### Split API / Runner (Production)

For production deployments, the gateway supports **split-process architecture**: the HTTP API and the background runner loop can run as separate processes sharing the same data directory. This lets you restart the API without interrupting durable execution:

```
┌──────────────────────┐     ┌──────────────────────┐
│  Process 1: HTTP API │     │  Process 2: Runner   │
│  (stateless, fast    │     │  (ticks runs, polls   │
│   restart)           │     │   inbox, resumes)     │
└──────────┬───────────┘     └──────────┬───────────┘
           │                            │
           └────────────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │  Shared data dir  │
              │  (SQLite / file)  │
              └───────────────────┘
```

## Scheduled Workflows

The gateway supports durable scheduled workflows — recurring jobs that survive restarts:

```
POST /api/gateway/runs/schedule
{
  "bundle_id": "daily-report",
  "start_at": "now",
  "interval": "24h",
  "repeat_count": 30
}
```

A scheduled workflow is a durable **parent run** that triggers **child runs** at specified intervals. If the gateway process stops, due schedules resume on the next poll cycle when it restarts.

## Event Bridges (Inbound Integrations)

Some deployments use inbound "bridges" that turn external messages into durable runtime activity. Typical patterns:

1. Bridge receives an inbound message (email, webhook, etc.).
2. Bridge chooses a stable `session_id` (for example `email:<thread_id>`).
3. Bridge either:
   - starts a new run per message (thin-client semantics), or
   - emits an event into that session (for event-driven workflows).
4. A workflow runs and produces durable ledger history + artifacts.

This preserves durability and observability: inbound content becomes replayable ledger history + artifacts.

```
┌───────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  External Service │     │    Bridge     │     │  AbstractGateway  │
│  (Telegram, Email,│────▶│  (adapter)   │────▶│  (durable event   │
│   Webhook, etc.)  │     │              │     │   → workflow run) │
└───────────────────┘     └──────────────┘     └──────────────────┘
```

See:
- [Scenario: Telegram permanent contact](scenarios/telegram-permanent-contact.md)
- [Scenario: Email inbox agent](scenarios/email-inbox-agent.md)
- [Guide: Telegram integration](guide/telegram-integration.md)

## MCP Integration (Model Context Protocol)

AbstractCore integrates with **MCP (Model Context Protocol)** servers, enabling your agents to discover and use tools from external ecosystems without writing adapter code:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AbstractCore                                  │
│  ┌────────────────┐                                                  │
│  │   MCP Client   │──────▶ MCP Server (HTTP) → external tool set    │
│  │                │──────▶ MCP Server (stdio) → local tool provider  │
│  └────────────────┘                                                  │
│         │                                                            │
│         ▼                                                            │
│  MCP-discovered tools are presented alongside local tools            │
│  to the LLM as part of the tool schema set                           │
└─────────────────────────────────────────────────────────────────────┘
```

MCP tools integrate seamlessly with AbstractRuntime's durable tool execution: they participate in the same approval boundaries, ledger logging, and replay semantics as any other tool.

## Evidence & Provenance Architecture

AbstractFramework provides multiple layers of traceability for production-grade auditability:

### Tamper-Evident Ledger

The ledger is **hash-chained**: each step record includes a hash of the previous step, creating a tamper-evident audit trail. If any step is modified after the fact, the chain breaks.

### Artifacts & Evidence

Large payloads (file contents, screenshots, API responses) are stored as **artifacts** — referenced from JSON state and ledger by handle. This keeps run state JSON-safe while preserving full evidence.

### Snapshots & Bookmarks

Named **snapshots** let you checkpoint a run's state at any point. Useful for:
- Creating restore points before risky operations
- Bookmarking interesting states for later analysis
- Exporting reproducible run states as **history bundles**

### Interaction Tracing

AbstractCore emits structured **interaction traces** (prompts, responses, token usage, timing) via a global event bus. Hosts can subscribe to these events for observability dashboards, cost tracking, or debugging.

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
   - AbstractMemory is optional storage; AbstractSemantics is the shared schema
     authority used by Runtime/Gateway memory integrations

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

AbstractVoice, AbstractVision, and AbstractMusic extend AbstractCore with multimodal capabilities:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AbstractCore                                 │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Unified LLM API                                                 ││
│  │ create_llm("ollama", model="...") → LLM instance                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│              ┌───────────────┼───────────────┬───────────────┐      │
│              ▼               ▼               ▼               ▼      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  │ Capability:     │ │ Capability:     │ │ Capability:     │ │ Capability:     │
│  │ llm.voice       │ │ llm.vision      │ │ llm.audio       │ │ llm.music       │
│  │ (via Abstract   │ │ (via Abstract   │ │ (via Abstract   │ │ (via Abstract   │
│  │  Voice)         │ │  Vision)        │ │  Voice)         │ │  Music)         │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
└─────────────────────────────────────────────────────────────────────┘
```

**Capability plugins** are discovered automatically via Python entry points. Install `abstractvoice`, `abstractvision`, and/or `abstractmusic`, and the corresponding capabilities become available on any `llm` instance. Missing plugins raise actionable errors with install hints.

## Media Input Architecture

AbstractCore handles media input (images, audio, video, documents) with a **policy-driven** approach — no silent semantic changes:

```
┌──────────────────────────────────────────────────────────────────┐
│  Media Input Pipeline                                            │
│                                                                  │
│  generate(..., media=["image.png", "doc.pdf", "audio.wav"])      │
│              │                                                   │
│              ▼                                                   │
│  ┌────────────────────────┐                                      │
│  │ Policy check per type  │                                      │
│  │ • image: native or     │                                      │
│  │   vision fallback      │                                      │
│  │ • audio: native or     │                                      │
│  │   STT transcription    │                                      │
│  │ • video: native or     │                                      │
│  │   frame sampling       │                                      │
│  │ • docs: text extract   │                                      │
│  │   or glyph compress    │                                      │
│  └────────────────────────┘                                      │
│              │                                                   │
│              ▼                                                   │
│  Content routed to LLM with appropriate representation           │
└──────────────────────────────────────────────────────────────────┘
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

### Production (Split API + Runner)

```
Browser ──► Nginx ──► AbstractGateway API ──► Shared storage
                                                    ▲
                      AbstractGateway Runner ────────┘
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

## Distribution & Install Paths

- **End-user installs**: PyPI packages via `pip` (including the GUI installer prototype for AbstractCore).
- **Developer/source installs**: clone repos and run `scripts/clone.sh` + `scripts/build.sh` (editable installs).
- **Installer prototype**: `abstractinstallers/abstractcore` wraps pip installs and a config wizard; it does not clone GitHub.
- **Production installer design**: see `docs/installers/README.md`.

---

## Related Documentation

- **[Getting Started](getting-started.md)** — Pick a path and run something
- **[Installers](installers/README.md)** — Proposed GUI installer design and steps
- **[Configuration](configuration.md)** — Environment variables and settings
- **[FAQ](faq.md)** — Common questions and troubleshooting
