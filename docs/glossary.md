# Glossary

This glossary defines the terms used across AbstractFramework docs.

If you're new, skim **Core Execution** and **Flows and Bundles** first.

## Core Execution

### Run

A durable workflow instance, identified by a `run_id`. A run has persisted state and an append-only history.

### Ledger

An append-only log of step records for a run. In gateway-first mode, UIs render by replaying the ledger and then
streaming new steps (SSE).

### Step

One recorded unit in the ledger (for example: node start, effect requested, effect result, error).

### Effect

A typed request for side effects (LLM call, tool calls, ask user, wait until, etc.). Effects are durable: the request is
recorded so the run can resume after restart.

### Wait

A pause point where the run stops progressing until it is resumed with external input (human answer, tool results, an
event, or time).

### Artifact

A file- or store-backed blob referenced from JSON state/ledger (used for large payloads). Artifacts keep run state
JSON-safe.

## Flows and Bundles

### WorkflowSpec

A Python in-memory workflow graph (nodes are callables). Durable runs execute a `WorkflowSpec`, but it is not portable as
an artifact because callables cannot be serialized safely.

### VisualFlow

A JSON workflow graph format used by AbstractFlow (and compiled by AbstractRuntime). This is the portable authoring
format.

### WorkflowBundle (`.flow`)

A portable distribution unit that packages a VisualFlow plus any referenced subflows and assets. Gateways discover
`.flow` bundles and expose them to clients.

### Interface contract

A versioned input/output contract a flow can implement so multiple clients can run it the same way (for example
`abstractcode.agent.v1` for chat-like "agent" flows).

## Tools

### Tool spec (schema)

A JSON-serializable description of a tool: name, description, and input schema. Tool specs are durable and can be stored
in the ledger.

### Tool executor (callable)

The host-side implementation that actually runs tools. Executors are not durable; they live in the process that owns
tool execution (terminal host, gateway runner, worker).

### Approval boundary

By default, tool execution is gated behind an explicit approval/resume step. This makes tool side effects auditable and
restart-safe.

## Memory

### Active context

The current message view sent to the model (what the LLM "sees"). It is a derived view and can be compacted without
losing underlying history.

### Stored history

The durable record of what happened (ledger + artifacts). Stored history is the source of truth.

### Span

A durable handle (often an artifact reference) that points to a piece of stored history, typically produced by
compaction or evidence capture.

### Scope

Where memory is read/written:

- `run`: only this run
- `session`: shared across runs that share a `session_id`
- `global`: shared across all runs in the same runtime/gateway instance
- `all`: query fan-out across `run + session + global`

### Knowledge graph (KG) memory

Long-term memory stored as temporal triples (AbstractMemory), optionally validated/normalized by a semantics registry
(AbstractSemantics).

## Modalities

### Capability plugin

An optional add-on that extends AbstractCore with deterministic modality APIs:

- `llm.voice` / `llm.audio` via AbstractVoice
- `llm.vision` via AbstractVision

This keeps AbstractCore lightweight while letting hosts enable modalities where they run durable execution.

