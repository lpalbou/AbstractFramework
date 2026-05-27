# Architecture

AbstractFramework is open-source AI infrastructure built around one idea: **durable, observable execution** for AI workflows.

Most LLM frameworks optimize for prototyping speed. AbstractFramework optimizes for **operational reality**: workflows that pause/resume safely, runs that survive restarts, UIs that reconstruct state from history, and clear boundaries around tool execution and approvals.

---

## Choose your entry point

Start lightweight with just the LLM library, or go all-in with a production gateway. Both paths lead to the same ecosystem.

### AbstractCore (SDK + optional `/v1`)

Start here if you need a lightweight LLM library for scripts, notebooks, or existing applications. No infrastructure required — just install and call. Add multimodal capabilities with plugins as you grow.

- 9+ providers with identical API (local + cloud)
- Universal tool calling, structured output, streaming
- Media handling (images, PDFs, audio, video)
- OpenAI-compatible HTTP server mode (`/v1`)
- Multimodal via capability plugins (Voice, Vision, Music)

The right first step when you mainly care about calling models/tools/media (in-process via Python or via `/v1`) and want the smallest surface area.

### AbstractGateway (durable control plane)

Start here if you're building persistent AI applications — agents that run for hours, workflows that survive crashes, scheduled tasks. The gateway is your AI control plane: durable runs with ledger replay/streaming and thin clients that can attach/detach across devices.

- Durable execution that survives crashes and restarts
- Append-only ledger (replay-first) for auditability
- Scheduled workflows (cron-style, recurring)
- Multi-client: terminal, browser, tray, Telegram, email
- Start on one device, continue on another

The composition root when you need a control plane (local or remote).

---

## Layered view

```
Apps / UIs (thin clients)
──────────────────────────────────────────────────────
 AbstractObserver (monitor / control / schedule)
 Flow Editor (author workflows)
 Code Web UI, AbstractAssistant, your custom app
                       │  HTTP/SSE
                       ▼
AbstractGateway (control plane)
──────────────────────────────────────────────────────
 run lifecycle (start / resume / cancel)
 scheduling (durable, survives restarts)
 bundle discovery (.flow bundles)
 artifact + ledger serving / streaming
                       │
                       ▼
Composition layer
──────────────────────────────────────────────────────
 AbstractAgent: ReAct, CodeAct, MemAct patterns
 AbstractFlow: visual workflows → portable .flow bundles
                       │
                       ▼
Durable execution kernel
──────────────────────────────────────────────────────
 AbstractRuntime
 runs, effects, waits
 ledger (append-only history) + artifacts (large payloads)
                       │
                       ▼
LLM + tools + multimodality
──────────────────────────────────────────────────────
 AbstractCore
 provider/model abstraction + routing defaults
 tools, structured output, media input, embeddings, MCP
 capability plugins: voice / vision / music
```

**AbstractFlow** is the authoring/distribution layer: you design a VisualFlow graph, export a `.flow` bundle, and run it anywhere a compatible host exists.

**AbstractAgent** is the composition layer: ready-made agent loops (ReAct, CodeAct, MemAct) built on top of Runtime. These can be used standalone or inside a Flow as agent nodes.

---

## Durable execution primitives

These are the "why" behind the design — the properties that make the framework operationally useful.

### Run

A durable workflow instance with persisted state. Identified by a `run_id`.

### Ledger

The append-only history of a run: every step, effect, result, wait, and error is recorded.

This is what makes replay-first UIs possible: a client reconstructs state by replaying history, then follows along by streaming new events over SSE.

### Effects and waits

Work happens at explicit boundaries:

- An **effect** is a request for a side-effect (LLM call, tool call, ask user, wait-until, …).
- A **wait** is a checkpointed pause until external input arrives (tool results, user answer, a timer).

The key property: if a process dies while waiting, **the run is still correct**. Another process (or a restart) can resume it from the recorded wait.

### Artifacts

Large payloads (files, media, big tool results) are stored as **artifacts** and referenced by handle from JSON state and the ledger. This keeps state JSON-safe without losing evidence.

### Tool execution boundary

Tool **schemas** are durable (stored in the ledger). Tool **callables** are not (they live in the host process). This is intentional:

- Tool calls become explicit approval points (configurable per tool)
- Execution is auditable (arguments + results in the ledger)
- Runs remain restart-safe (the tool call is a wait, not an in-process function call)

---

## Workflow lifecycle: author → deploy → run → observe

### 1) Author with AbstractFlow

Build a workflow graph in the Flow Editor and export it as a `.flow` bundle.

### 2) Deploy the bundle

Copy bundles to `ABSTRACTGATEWAY_FLOWS_DIR`. The gateway discovers them automatically.

### 3) Run from any client

Any gateway-backed client can: list bundles/entrypoints, start a run, attach to ledger replay/streaming, and resume waits (approvals, user input, tool results).

### 4) Observe and schedule with AbstractObserver

- Inspect any run (ledger replay)
- Watch a run live (SSE)
- Control runs (cancel, resume)
- Schedule recurring runs

---

## Multimodality

AbstractCore stays lightweight by treating modalities as **capability plugins** (discovered internally via Python entry points, then exposed via the AbstractCore SDK and its optional `/v1` endpoints; gateway-first deployments can also surface them through Gateway):

| Plugin | Capability | API surface |
|---|---|---|
| `abstractvoice` | TTS + STT | `llm.voice.tts(...)`, `llm.audio.transcribe(...)` |
| `abstractvision` | Image generation | `llm.vision.t2i(...)` |
| `abstractmusic` | Music generation | `llm.music.t2m(...)` |

Install a plugin; the API appears on your `llm` instance. Don't install it; Core stays small.

---

## How it compares (honest positioning)

### vs direct provider SDKs (OpenAI, Anthropic)

Direct SDKs are the right choice when you only use one provider and don't need durable orchestration.

AbstractCore adds value when you need: provider portability, consistent tool/structured-output behavior across backends, media policies, modality plugins, or a stable configuration layer that doesn't leak into app code.

### vs LangChain / LlamaIndex / PydanticAI

Those are primarily **in-process orchestration libraries**. AbstractFramework occupies a different niche: an **agentic OS-style** stack for durable, observable execution (runtime + append-only ledger + control plane), where the same workflows can run across providers, devices, and deployment modes.

**Where AbstractFramework is stronger**: durability and pause/resume as primitives, replay-first observability, portable `.flow` bundles that run across clients.

**Where others are stronger**: large connector/RAG ecosystems, minimal boilerplate for simple use cases, broader community examples.

### vs Temporal / Step Functions / job schedulers

AbstractGateway is architecturally closer to these systems, but specialized for LLM/tool loops: tool approval waits, AI-oriented artifacts, and replay-first thin-client UIs over HTTP/SSE.

---

## Where to go deeper

- **[Getting Started](getting-started.md)** — run Core-first or Gateway-first
- **[Configuration](configuration.md)** — minimal config, where defaults live
- **[Glossary](glossary.md)** — shared definitions (run, ledger, effect, wait, bundle, interface contract)
- Per-project architecture docs live in the component repositories
