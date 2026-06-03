# Glossary

Shared terminology used across AbstractFramework documentation.

If you're new, read these groups first:

- **Durable execution**: run, ledger, effect, wait, artifact
- **Workflows**: flow, bundle, interface contract
- **Control plane**: gateway, schedule, observer

---

## Core (LLM SDK)

### Provider

An LLM backend integration (Ollama, OpenAI, Anthropic, any OpenAI-compatible server, etc.).

### Model

A provider-specific model identifier (`qwen3:4b-instruct`, `gpt-4o-mini`, `claude-3-5-sonnet-latest`, etc.).

### Capability route

A stable "slot" for a default model/provider choice, scoped by capability rather than by application. Examples: `input.text` (canonical LLM text route), `input.image` (fallback image-understanding route when the text model is not vision-capable), and `embedding.text` (default embeddings). `output.text` is a read-only derived view of `input.text`.

### Capability plugin

An optional package that extends AbstractCore with a modality API without bloating the base install. Install a plugin and the API appears on `llm` instances:

- `abstractvoice` → `llm.voice` (TTS) / `llm.audio` (STT)
- `abstractvision` → `llm.vision` (image generation)
- `abstractmusic` → `llm.music` (text-to-music)

---

## Tools

### Tool spec (schema)

A JSON-serializable description of a tool: name, description, and input schema. Tool specs are durable — they can be stored in the ledger and replayed.

### Tool executor (callable)

The host-side implementation that actually runs a tool. Executors are **not** durable; they live in the process that owns tool execution.

### Approval boundary

By default, tool execution is gated behind an explicit approval/resume step. This makes tool side-effects auditable, controllable, and restart-safe. Approval policy is configurable per tool (auto-approve safe tools, require manual approval for mutations).

---

## Durable execution (Runtime)

### Run

A durable workflow instance, identified by a `run_id`. A run has persisted state and a full append-only history.

### Session ID

A stable identifier used to group multiple runs into a long-lived "session" across time and clients (a chat thread, a device session, etc.).

### Ledger

The append-only history of what happened in a run (steps, effects, results, waits, errors). Replay-first clients render by replaying the ledger and then streaming new events.

### Step

One recorded unit in the ledger (node transitions, effect requests, results, errors).

### Effect

A typed request for a side-effect (LLM call, tool calls, ask user, wait-until, …). Effects are recorded so a run can resume correctly after restarts.

### Wait

A durable pause point: the run is checkpointed and stops progressing until it is resumed with external input (tool results, user input, time, or an event).

### Artifact

A file- or store-backed blob referenced from JSON state/ledger. Used for large payloads (files, media, big tool results) to keep state JSON-safe while preserving evidence.

---

## Agent patterns

### Agent

A runtime workflow that implements a reasoning loop: observe → think → act → repeat. AbstractAgent ships three patterns:

- **ReAct**: tool-first reasoning (observe environment, choose tool, execute, reflect)
- **CodeAct**: code execution (generate Python, execute, observe output)
- **MemAct**: memory-enhanced (read/write a knowledge graph during the loop)

Agents can run standalone or as nodes inside a Flow.

---

## Workflows (Flow)

### Flow

A workflow graph: nodes + edges + state transitions. Flows encode orchestration logic: LLM steps, tool steps, branching, loops, subflows, and agent nodes.

### VisualFlow

The JSON workflow graph format used by AbstractFlow and executed by AbstractRuntime.

### Workflow bundle (`.flow`)

A portable distribution unit that packages a VisualFlow graph plus metadata (and optionally subflows/assets). Gateways discover `.flow` bundles and expose them to clients.

### Interface contract

A versioned input/output contract a flow can implement so multiple clients can run it consistently (for example `abstractcode.agent.v1` for chat-like agent flows).

---

## Control plane (Gateway) + operations (Observer)

### Gateway

The control plane for durable runs: start/resume/cancel, persistence, scheduling, bundle discovery, and ledger serving/streaming over HTTP/SSE.

### Schedule

A durable recurring trigger owned by the gateway ("run this workflow every 24h"). Schedules survive restarts.

### Observer

A thin-client browser UI for operations: monitor runs, inspect ledger history, watch live execution, control runs, and (when enabled) create schedules.

---

## Memory

### Active context

The current message view sent to the model (what the LLM "sees"). A derived view that can be compacted without losing underlying history.

### Stored history

The durable record of what happened (ledger + artifacts). The source of truth.

### Knowledge graph (KG) memory

Long-term memory stored as temporal triples (AbstractMemory), validated through the shared semantics registry (AbstractSemantics). Optional — not a hard dependency of the runtime kernel.
