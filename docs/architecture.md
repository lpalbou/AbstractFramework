# Architecture

AbstractFramework is built around a simple but powerful idea: **durable, observable execution**.

Every operation is logged. Workflows survive crashes. UIs can render by replaying history. Tools execute at explicit boundaries. This document explains how the pieces fit together.

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Host Applications                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │AbstractCode│  │ Abstract   │  │ Abstract   │  │  Your App  │            │
│  │ (terminal) │  │ Assistant  │  │  Observer  │  │            │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼───────────────┼───────────────┼───────────────┼───────────────────┘
         │               │               │               │
         ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Composition Layer                                   │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                 │
│  │      AbstractAgent       │  │      AbstractFlow        │                 │
│  │  ReAct · CodeAct · MemAct│  │  Visual workflows (.flow)│                 │
│  └────────────┬─────────────┘  └────────────┬─────────────┘                 │
└───────────────┼─────────────────────────────┼───────────────────────────────┘
                │                             │
                ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Foundation (Two Peers)                               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                 │
│  │     AbstractRuntime      │  │      AbstractCore        │                 │
│  │  ──────────────────────  │  │  ──────────────────────  │                 │
│  │  • Durable execution     │  │  • Unified LLM API       │                 │
│  │  • Append-only ledger    │  │  • Tool calling          │                 │
│  │  • Effects & waits       │  │  • Structured output     │                 │
│  │  • Checkpoint & replay   │  │  • Multi-provider        │                 │
│  └──────────────────────────┘  └──────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
                │                             │
                ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Memory & Modalities                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ AbstractMemory │  │AbstractSemantic│  │ Abstract   │  │ Abstract   │    │
│  │ Temporal KG    │  │ Schema registry│  │   Voice    │  │   Vision   │    │
│  └────────────────┘  └────────────────┘  └────────────┘  └────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key insight:** Runtime and Core are peers, not layers. You can use Runtime without Core (pure workflows), or Core without Runtime (simple LLM apps). When combined, Runtime mediates LLM/tool effects through Core.

## Package Dependency Graph

```
                    ┌──────────────────┐
                    │   Applications   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ AbstractCode │    │ Abstract     │    │ Abstract     │
│              │    │ Assistant    │    │ Gateway      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────┬───────┴───────────────────┘
                   │
                   ▼
           ┌──────────────┐
           │ AbstractAgent│ ◄── abstractagent
           └──────┬───────┘
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│AbstractRuntime│      │ AbstractCore │
└──────────────┘      └──────────────┘
       │                     │
       │              ┌──────┴──────┐
       │              │             │
       ▼              ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│AbstractMemory│ │ Abstract │ │ Abstract │
│              │ │  Voice   │ │  Vision  │
└──────────────┘ └──────────┘ └──────────┘
       │
       ▼
┌──────────────┐
│Abstract      │
│ Semantics    │
└──────────────┘
```

## Core Concepts

### Runs & The Ledger

A **run** is a durable workflow instance. Every run has a **ledger** — an append-only log of everything that happened.

```
Run: agent_task_abc123
┌─────────────────────────────────────────────────────────┐
│ Ledger                                                   │
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

### Bundles

A **bundle** (`.flow` file) is a portable workflow package containing:
- VisualFlow JSON (the workflow graph)
- Manifest (metadata, entry points)
- Dependencies (subflows)

Bundles are how you distribute and deploy workflows.

## Gateway Architecture

For production deployments, AbstractGateway provides the control plane:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Browser / Clients                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  Observer   │  │  Flow Editor│  │  Your UI    │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          │         HTTP/SSE               │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AbstractGateway                                 │
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
│                      Agent Context                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Active Memory (what the LLM sees)                              │ │
│  │ ─────────────────────────────────                              │ │
│  │ Recent messages, compacted history, relevant knowledge         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│              ┌───────────────┴───────────────┐                      │
│              ▼                               ▼                       │
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
│                        AbstractCore                                  │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Unified LLM API                                                 ││
│  │ create_llm("ollama", model="...") → LLM instance                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              ▼               ▼               ▼                       │
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
