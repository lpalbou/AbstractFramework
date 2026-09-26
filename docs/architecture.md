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
- OpenAI-compatible HTTP server mode (`/v1`), with a web console at `/console`
- Local model and engine management: browse models that fit this machine, download, delete, install engines
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

## Component view

Every client talks to the gateway over HTTP/SSE. The browser apps are served by a small local
server that also relays their gateway calls (see [App proxies](#app-proxies-and-the-forwarded-address)).
The gateway composes the Python packages below it in one process: agent patterns, the durable
runtime, memory, skills and AbstractCore, which reaches the model providers and local engines.
Arrows point from a component to what it calls or depends on.

```mermaid
flowchart TB
    subgraph CLIENTS["Native clients"]
        CODET["AbstractCode terminal<br/>(Rust)"]
        ASSIST["AbstractAssistant<br/>desktop menu-bar app"]
        GCON["abstractgateway-console<br/>terminal operator console"]
        APP["Your app"]
    end

    subgraph BROWSER["Browser apps, each behind its local app proxy"]
        CODEW["Code Web UI"]
        FLOWED["Flow Editor<br/>author .flow bundles"]
        UIAPPS["Observer · Entity · Continuum<br/>(ui-kit app-server)"]
    end

    subgraph GATEWAY["AbstractGateway (control plane)"]
        API["HTTP/SSE API<br/>runs · schedules · workflow catalog<br/>ledger + artifacts · users · network · /about"]
        SESS["agent sessions<br/>default workflow · workspace guard<br/>skills shelf · live-reply hub"]
        WEB["web /console<br/>first-run guide · Models · Engines · Resources"]
        TRAY["menu-bar icon<br/>status · Network · open apps"]
    end

    AGENT["AbstractAgent<br/>ReAct · CodeAct · MemAct"]
    RT["AbstractRuntime<br/>runs · effects · waits · ledger · artifacts<br/>VisualFlow compiler · model residency"]
    MEM["AbstractMemory<br/>durable agent memory"]
    SEM["AbstractSemantics<br/>predicates + entity types"]
    SKILL["AbstractSkill<br/>curated skill shelf · trust gate"]
    CORE["AbstractCore<br/>providers · tools · media · embeddings<br/>models + engines · eject"]
    PLUG["Capability plugins<br/>abstractvoice · abstractvision · abstractmusic"]
    CSRV["abstractcore serve<br/>/v1 · /acore · web /console"]
    CCON["abstractcore-console<br/>terminal console + shared screens"]
    PROV[("LLM providers and local engines<br/>Ollama · LM Studio · MLX · llama.cpp · vLLM · cloud APIs")]

    CLIENTS -->|HTTP/SSE| API
    BROWSER -->|"HTTP/SSE through the app proxy"| API
    WEB --> API
    TRAY --> API
    TRAY -.->|"Open: starts it signed in"| ASSIST
    API --> SESS
    SESS --> SKILL
    SESS --> RT
    API --> AGENT
    API --> MEM
    AGENT --> RT
    AGENT --> CORE
    RT --> CORE
    RT --> MEM
    RT --> SEM
    CORE -.->|entry-point plugins| PLUG
    CORE --> PROV
    GCON -->|embeds Models/Engines screens| CCON
    CSRV --> CORE
    CCON -->|abstractcore CLI| CORE
```

The layers, from the top:

- **Apps and clients** are thin: they hold no durable state and rebuild their view by replaying
  the ledger, then follow new events over SSE. The Flow Editor publishes `.flow` bundles to the
  gateway; the others start, observe and steer runs. Every app has an About screen with the
  framework identity (see [Framework identity](#framework-identity-and-about-screens)).
- **AbstractGateway** owns the run lifecycle (start, resume, cancel), durable schedules, private
  bundle discovery and the shared workflow catalog, users and auth, the Network setting, and
  ledger/artifact serving. For agent sessions it also resolves the default agent workflow, gives
  every run a guarded workspace, seeds and serves the skill shelf, and relays live replies. Its
  web console and menu-bar icon are part of the same package.
- **AbstractAgent** provides ready-made agent loops; **AbstractRuntime** is the durable kernel that
  executes them, compiles VisualFlow graphs from `.flow` bundles into workflows, and tracks which
  models are resident and who uses them.
- **AbstractSkill** ships the curated skill shelf and the trust gate the gateway applies before a
  skill reaches a run.
- **AbstractCore** is the LLM layer: provider and model abstraction, capability routing defaults,
  tools, structured output, media, embeddings, MCP, streaming, and the local model and engine
  management (catalog with a fit verdict, downloads, engine installs, eject). Voice, image and
  music arrive as capability plugins.
- **AbstractCore on its own** (`abstractcore serve`) is the second entry point: an
  OpenAI-compatible `/v1` server with its own console, without the durable layers.

## How the framework is distributed

Each layer ships through the registry that fits it. The `abstractframework` meta-package pins the
Python side with exact versions; the apps and terminal tools are installed next to it.

```mermaid
flowchart LR
    subgraph PyPI["PyPI (pinned by abstractframework)"]
        GW["abstractgateway<br/>server + /console"]
        AS["abstractassistant"]
        STACK["abstractcore · AbstractRuntime · abstractagent<br/>AbstractMemory · abstractsemantics<br/>abstractvoice · abstractvision · abstractmusic"]
    end
    subgraph npm["npm (npx @abstractframework/...)"]
        APPS["flow · code · observer<br/>continuum · entity"]
    end
    subgraph crates["crates.io (cargo install)"]
        CLI["abstractcode"]
        CON["abstractgateway-console"]
        CCON["abstractcore-console<br/>(app + Models/Engines screens library)"]
    end
    subgraph GHCR["GHCR images"]
        IMG["abstractgateway · abstractcore-server"]
    end
    BOOT["install.sh / install.ps1<br/>(uv tool install abstractgateway)"]
    BOOT -->|installs, starts, opens /console| GW
    AS -->|HTTP/SSE| GW
    APPS -->|HTTP/SSE| GW
    CLI -->|HTTP/SSE| GW
    CON -->|HTTP/SSE| GW
    CON -->|embeds screens| CCON
    CCON -->|abstractcore CLI| STACK
    GW --> STACK
    IMG -.->|same server, containerized| GW
```

The Models and Engines features are implemented once, in AbstractCore, and inherited by the
gateway:

```mermaid
flowchart TB
    CORE["AbstractCore<br/>host profile · catalog + fit · engines · jobs"]
    CORE --> CCLI["abstractcore models / engines (CLI)"]
    CORE --> CAPI["abstractcore serve<br/>/acore/* + web /console"]
    CORE --> CTUI["abstractcore-console<br/>screens 9 Models, 0 Engines"]
    CORE -->|via AbstractRuntime| GAPI["abstractgateway<br/>/api/gateway/models, engines, jobs, host/profile"]
    GAPI --> GWEB["gateway web /console<br/>embeds Core's Models and Engines screens"]
    GAPI --> GTUI["abstractgateway-console<br/>mounts the abstractcore-console screens over HTTP"]
    GAPI --> GCLI["abstractgateway models / engines (CLI)"]
```

Every console action shows its command-line equivalent. Download, delete and engine installs are
admin-only jobs; engine installs from a console are enabled by default only for a server bound to
loopback (`allow_engine_install` on the gateway, `ABSTRACTCORE_ALLOW_ENGINE_INSTALL` on the core
server).

See [Install AbstractFramework](install.md) for the versions released together and the commands
for each registry.

**AbstractFlow** is the authoring/distribution layer: you design a VisualFlow graph, export a `.flow` bundle, and run it anywhere a compatible host exists.

**AbstractAgent** is the composition layer: ready-made agent loops (ReAct, CodeAct, MemAct) built on top of Runtime. These can be used standalone or inside a Flow as agent nodes.

Portable workflow execution does not require every client to be a generic workflow picker. Some
products expose workflow selection, while others intentionally bind to one published workflow or
interface family for a specialized task. The invariant is that execution still happens as a durable
Gateway/Runtime workflow.

---

## Agent sessions: how a turn flows

When you send a message from AbstractCode, the Assistant or your own client, the gateway resolves
everything the turn needs before the runtime runs it. What each step means for users is in
[Agent sessions](agent-sessions.md).

```mermaid
flowchart LR
    START["POST /runs/start<br/>flow_id @default + interface<br/>_runtime.stream · skills"]
    subgraph GW["AbstractGateway"]
        WF["default agent workflow<br/>agents.default_workflow.*"]
        WS["workspace guard<br/>conversation folder + built-in deny list"]
        SK["skill selection<br/>shelf + trust gate"]
        STR["stream switch<br/>run value, else agents.streaming_default"]
    end
    RUN["AbstractRuntime run<br/>(AbstractAgent loop)"]
    START --> WF --> WS --> SK --> STR --> RUN
```

- **Default workflow.** `flow_id: "@default"` with an `interface` is rewritten to the workflow the
  gateway's setting names, at every run start. An unresolvable default refuses the run with the
  setting's name and value; it never falls back silently. The response's `resolved_workflow`
  names what ran.
- **Workspace guard.** One guard runs at every run start, whatever started the run (HTTP routes,
  schedules, bridges, entity summons): it assigns the conversation's folder when none was named,
  refuses a folder inside the gateway's data folder (other than the caller's own conversation
  folder), and adds the built-in deny list for credential folders and the data folder. The file
  tools enforce the list without writing it into the prompt.
- **Skills.** Names in `input_data.skills` pass through the same trust gate as the skill listing;
  validated skills reach the run as a stable index plus a `read_skill` tool, and every decision is
  recorded on the run.
- **Stream switch.** `input_data._runtime.stream` (a boolean) wins; when absent, the gateway's
  `agents.streaming_default` applies to interactive starts only. A workflow step can still turn
  streaming off for its own model call.

### The live-reply lane

Live replies never touch the ledger. The runtime hands each text chunk to a sink the gateway
registers; the gateway's hub forwards it on the run's existing SSE stream, next to the durable
ledger records.

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway SSE stream
    participant H as Live-reply hub
    participant R as AbstractRuntime
    participant P as AbstractCore provider
    C->>G: GET /runs/{id}/ledger/stream
    R->>P: model call with streaming on
    P-->>R: text chunks (answer / reasoning)
    R-->>H: llm.delta (in memory, not a ledger record)
    H-->>C: event llm.delta, no id line
    R->>R: append the llm_call record to the ledger
    G-->>C: ledger record, its id line is the ledger cursor
    R-->>H: llm.delta_end
    H-->>C: event llm.delta_end
    Note over C: the durable record replaces the live text
```

- The hub is keyed by the root run, so a stream also carries the deltas of the sub-runs below it.
- A client that connects or reconnects mid-answer first receives one snapshot per open call.
- When the gateway serves its API and runs its runner in separate processes
  (`serve --no-runner` plus `abstractgateway runner`), the runner writes the deltas to a file under
  `<data dir>/live/` that only the gateway's user can read; the API process tails it, and the file
  is deleted when the run ends.
- A call that cannot stream still ends with `llm.delta_end` and a `reason` of `unavailable` plus
  the cause, so clients can say why.

## App proxies and the forwarded address

Each browser app runs behind a small local server that serves the page and relays its gateway
calls: the AbstractCode web server, the Flow Editor's server, and the ui-kit app-server used by
Observer, Entity and Continuum. The gateway gives a few defaults only to the person at its own
keyboard (opening a folder, installing apps and engines, the Assistant hand-over), so it must
know where a relayed request really comes from. The rule has two halves:

- **Every app proxy** overwrites `X-Forwarded-For` with the real socket address of the browser it
  serves (it never appends to or passes on a value the browser sent), adds its marker header
  `X-AbstractFramework-App-Proxy: <app>`, and drops `Forwarded`, `X-Forwarded-Host`,
  `X-Forwarded-Proto` and `X-Real-IP`.
- **The gateway** believes `X-Forwarded-For` only from a loopback peer. A request counts as "this
  computer" when that derived address is loopback or one of the host's own addresses. A marked
  request without `X-Forwarded-For`, a forwarded header from a non-loopback peer, and any
  proxied request while the gateway trusts a reverse proxy are never "this computer".

So a browser on another machine that reaches an app proxy on the gateway's computer is treated as
remote, and a browser on the gateway's computer is treated as local. See
[Gateway exposure security](guide/gateway-security.md).

## Model residency and eject

AbstractCore loads models in the gateway's process (MLX, llama.cpp GGUF engines, transformers and
embedding models); AbstractRuntime records which clients use each model. Ejecting a model (the
console's **Resources** view, `abstractgateway models unload`) frees it from every holder in the
process, weights and caches included. A model locked by another client is refused unless the eject
is forced. Switching the default model ejects the previous one before the new one loads, unless
something still uses it; the console lists ejects that wait for an in-flight call or failed, with
the reason.

The accelerator meter shows the memory the gateway process holds and names how it was measured
(the Mac's GPU counter for the process, the NVIDIA reserved bytes plus the llama.cpp estimate, or
the sum of MLX and llama.cpp figures). When memory is held with no model listed, the console says
so and names the holder. Reference:
[AbstractGateway console: memory figures](https://github.com/lpalbou/AbstractGateway/blob/main/docs/console.md#memory-figures-on-resources).

## Framework identity and About screens

Every app shows the same identity in its About screen: app name and version, "Part of
AbstractFramework", the website, author, licence and copyright, source, documentation, issue and
feedback links, and a contact address, followed by the versions the connected gateway runs. The
identity has one canonical descriptor in this repository, `identity/abstractframework.json`; each
package that renders it carries a byte-identical copy so installed packages stay self-contained.

```mermaid
flowchart LR
    ID["identity/abstractframework.json<br/>(this repository, canonical)"]
    CHK["scripts/check_identity_sync.py<br/>byte comparison of every copy"]
    subgraph COPIES["Vendored copies"]
        PY["abstractcore<br/>abstractcore.utils.identity"]
        UI["abstractuic ui-kit<br/>AfAboutDialog"]
        CT["abstractcode terminal<br/>/about"]
        GT["abstractgateway-console<br/>About (F1)"]
    end
    ABOUT["GET /api/gateway/about<br/>public, versions only"]
    ROWS["gateway version rows<br/>ui-kit gatewayVersionRows =<br/>abstractcore gateway_version_rows"]
    ID --> PY & UI & CT & GT
    CHK -.->|verifies| COPIES
    ABOUT --> ROWS
    PY --> APY["Assistant · gateway menu-bar icon"]
    UI --> AUI["Code Web · Flow · Observer · Entity<br/>Continuum · gateway web console"]
    ROWS --> APY & AUI & CT & GT
```

`GET /api/gateway/about` needs no sign-in and returns only versions: the framework meta-package
(or null when it is not installed on the gateway's computer), the gateway, and each installed
framework package. Both formatters of the gateway rows are checked against one shared fixture.
Contributors change the identity in one place; see
[CONTRIBUTING](../CONTRIBUTING.md#framework-identity).

---

## Durable execution primitives

These are the "why" behind the design — the properties that make the framework operationally useful.

### Run

A durable workflow instance with persisted state. Identified by a `run_id`.

### Ledger

The append-only history of a run: every step, effect, result, wait, and error is recorded.

This is what makes replay-first UIs possible: a client reconstructs state by replaying history, then follows along by streaming new events over SSE.

For Core-backed multimodal generation, Runtime can also persist bounded `resolved_actions`
summaries in replay exports. Those records capture the normalized request/output summary and the
effective resolved route without turning route internals into the ordinary app-facing vocabulary.

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

For hosted or multi-user gateways, admins can also promote immutable bundle
versions into the Gateway workflow catalog. The catalog owns shared/default
workflow pointers and ACLs; each catalog run executes in the requesting user's
runtime.

### 3) Run from any client

Any gateway-backed client can: list bundles/entrypoints, start a run, attach to ledger replay/streaming, and resume waits (approvals, user input, tool results).

### 4) Observe and schedule with AbstractObserver

- Inspect any run (ledger replay)
- Watch a run live (SSE)
- Control runs (cancel, resume)
- Schedule recurring runs

## File-like sources in hosted clients

Hosted clients such as AbstractFlow need a clear split between file origin and
runtime value:

- `Artifact`: a saved Runtime-owned file payload. Reusable across runs.
- `Local File`: a file chosen from the client device. In hosted/browser mode it
  is uploaded and normalized into an Artifact before durable execution.
- `Server File`: a user-facing label for a file inside Gateway-approved
  workspace scope on the server. Path-based operations still depend on
  workspace policy and current grants; importing it creates an Artifact
  snapshot.

Internally, the durable payload handle is the artifact ref. Server-side path
access stays a Gateway-owned workspace capability rather than a generic server
filesystem abstraction. Some UI surfaces label server files `Workspace`; it
means the same Gateway-approved scope.

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
- **[Agent sessions](agent-sessions.md)** — default workflow, workspace, skills, live replies, Assistant hand-over
- **[Configuration](configuration.md)** — minimal config, where defaults live
- **[Glossary](glossary.md)** — shared definitions (run, ledger, effect, wait, bundle, interface contract)
- **[API](api.md)** — the meta-package helpers and the functional API owner of each concern
- **[Install](install.md)** — how each part reaches a machine, and the Network setting
- **[Installer design](installers/README.md)** — the bootstrap + console install model
- **[ADR index](adr/README.md)** — accepted cross-package decisions, including
  [package dependency boundaries](adr/0032-package-dependency-boundaries-and-gateway-first-apps.md),
  [install profiles](adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md) and
  [the script bootstrap install](adr/0038-script-bootstrap-and-gateway-console-install.md)
- **[Runtime artifacts and retrieval](guide/runtime-artifacts.md)** — who owns artifacts, ledger and retrieval
- Per-project architecture docs live in the component repositories
