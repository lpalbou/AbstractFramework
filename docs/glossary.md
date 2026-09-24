# Glossary

Shared terminology used across AbstractFramework documentation.

If you're new, read these groups first:

- **Durable execution**: run, ledger, effect, wait, artifact
- **Workflows**: flow, bundle, interface contract
- **Control plane**: gateway, schedule, observer, gateway console
- **Distribution**: install profile, release pins

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

A Runtime-owned durable file payload referenced from JSON state/ledger. Use
artifacts for large payloads (files, media, evidence, big tool results) so run
state stays JSON-safe while the bytes remain reusable, searchable, and
observable across runs.

### Workspace File / Workspace Folder

A server-side file or folder inside the current Gateway-approved workspace
scope. This is the engineering term for server paths used by file helpers,
imports, exports, and run workspaces. A workspace file is not generic arbitrary
server filesystem access.

### Local File / Local Folder

A client-side source chosen from the current device. In hosted/browser mode,
this is an intake source, not a durable runtime path. Local file bytes are
typically uploaded and stored as an Artifact before durable execution.

### Server File / Server Folder

A user-facing source label for a workspace-scoped server file or folder. In
product copy, `Server File` means “a file inside the Gateway-approved workspace
scope,” not “any file the server can see.”

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

### Gateway console

The operator console for one gateway. The web console is built into `abstractgateway` and served at `/console`; the terminal console is the separate `abstractgateway-console` crate (`cargo install abstractgateway-console`). Both include AbstractCore's **Models** and **Engines** screens.

### Core console

The console for AbstractCore on its own. The web console is served at `/console` by `abstractcore serve` (Overview, Models, Engines, Providers); the terminal console is the `abstractcore-console` crate, which is also the library that provides the Models and Engines screens to the gateway's terminal console.

### Claim link

A one-time console sign-in link (`/console#claim=<code>`), single use, valid for 10 minutes and redeemable only from the same machine. `abstractgateway serve` and `abstractcore serve` print one on a first local start; `abstractgateway claim` and `abstractgateway-config claim-url` mint a new one.

### First-run guide

The gateway console's setup flow, opened once per data folder by the claim link and later from the **Setup** button: host summary, local engines, a default model that fits the machine, and the apps.

### Models and Engines

The local model and engine management shared by AbstractCore and the gateway: a model catalog with a fit verdict for this machine (`fits`, `tight`, `too_large`, `partial_offload`, `unknown`), installed models with sizes, download and delete jobs, and detection and installation of local engines (Ollama, LM Studio, MLX, llama.cpp, vLLM, transformers). Available as `abstractcore models|engines`, `abstractgateway models|engines`, and in the consoles.

---

## Distribution

### Install profile

One of the three ways to install the pinned Python stack: **Light** (`pip install abstractframework`, remote/endpoint inference only), **Apple** (`abstractframework[apple]`, adds MLX/Metal engines on macOS 14+) and **GPU** (`abstractframework[gpu]`, adds CUDA/ROCm engines). See [Install](install.md).

### Bootstrap script

The one-line installer (`scripts/install.sh` for macOS and Linux, `scripts/install.ps1` for Windows). It installs uv, Python 3.12 and the pinned gateway as a uv tool, registers and starts it, and opens the console with a claim link. See [Install](install.md#advanced-what-the-installer-does).

### Release pins

The exact (`==`) versions a given `abstractframework` release installs, exposed as `RELEASE_VERSIONS` and checked by `abstractframework doctor`. The npm apps and crates released with it are listed in `NPM_RELEASE_VERSIONS` and `CRATE_RELEASE_VERSIONS`.

---

## Memory

### Active context

The current message view sent to the model (what the LLM "sees"). A derived view that can be compacted without losing underlying history.

### Stored history

The durable record of what happened (ledger + artifacts). The source of truth.

### Knowledge graph (KG) memory

Long-term memory stored as temporal triples (AbstractMemory), validated through the shared semantics registry (AbstractSemantics). Optional — not a hard dependency of the runtime kernel.
