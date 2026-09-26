# FAQ

## What is AbstractFramework?

An open-source ecosystem for building **durable, observable, multimodal AI systems**.

Two things share the name:

- **The ecosystem**: composable packages (Core, Runtime, Agent, Gateway, Flow, Observer, apps, modality plugins).
- **This repo / meta-package**: `abstractframework` is a pinned install profile + cross-package docs.

If you're looking for the main SDK, that's **AbstractCore**. If you need durable orchestration, that's **AbstractGateway**.

---

## Where should I start?

- **AbstractCore** — when you want direct LLM/tool/media integration with a clean, provider-agnostic API (Python SDK **or** OpenAI-compatible `/v1`).
- **AbstractGateway** — when you need durability, orchestration, scheduling, or language-agnostic access via HTTP/SSE routes.

Most teams start with Core (SDK or `/v1`), then introduce Gateway when workflows become long-running, scheduled, or shared across clients. See **[Getting Started](getting-started.md)**.

---

## Do I need to install the whole stack?

No.

| Goal | Install |
|---|---|
| A running gateway + web console, no Python setup | the installer (a Mac package, or one line) in [Install](install.md) |
| Smallest useful (LLM SDK only) | `pip install abstractcore` |
| Gateway-first deployment | `pip install abstractgateway` |
| Everything at compatible versions | `pip install abstractframework` |
| A browser app against an existing gateway | `npx @abstractframework/<flow\|code\|observer\|continuum\|entity>` |
| A terminal client | `cargo install abstractcode`, `cargo install abstractgateway-console` or `cargo install abstractcore-console` |
| A container deployment | `ghcr.io/lpalbou/abstractgateway:0.4.3` |

See [Install AbstractFramework](install.md) for the Light / Apple / GPU chooser. Light is
remote-first, not reduced-functionality: multimodal and embeddings still work through remote or
local endpoint providers.

---

## Can I run everything offline with local models?

Yes. The core execution stack works fully offline with local model servers (Ollama, LM Studio, vLLM, llama.cpp, LocalAI). You need internet only to download models or use cloud APIs.

Multimodal plugins also work offline:

- **AbstractVoice**: Piper TTS (ONNX) + faster-whisper STT — prefetch once, run offline.
- **AbstractVision**: local Diffusers models or GGUF via stable-diffusion.cpp.
- **AbstractMusic**: local ACE-Step inference.

---

## What agent patterns are available?

AbstractAgent ships three patterns, all built on the durable Runtime kernel:

| Pattern | How it works |
|---|---|
| **ReAct** | Tool-first reasoning: observe → think → choose tool → execute → reflect |
| **CodeAct** | Code execution: generate Python, run it, observe output |
| **MemAct** | Memory-enhanced: reads/writes a knowledge graph during the loop |

Agents can run standalone or as nodes inside an AbstractFlow workflow.

---

## How does AbstractFramework compare to other frameworks?

### vs direct provider SDKs (OpenAI, Anthropic)

Direct SDKs are fine when you only use one provider and don't need durable orchestration.

AbstractCore adds value when you need: provider portability (local ↔ cloud), consistent tool/structured-output behavior across backends, media policies, modality plugins, or a configuration layer that doesn't leak into app code.

### vs LangChain / LlamaIndex / PydanticAI

Most agent libraries are **in-process orchestration**. AbstractFramework is a **durable orchestration stack**.

**Where AbstractFramework is stronger**: durability and pause/resume as primitives, replay-first observability, portable `.flow` bundles that run across clients.

**Where others are stronger**: large connector/RAG ecosystems, minimal boilerplate for simple use cases, broader community examples.

### vs Temporal / Step Functions / job schedulers

AbstractGateway is architecturally closer to these, but specialized for LLM/tool loops: tool approval waits, AI-oriented artifacts, and replay-first thin-client UIs over HTTP/SSE.

### Can I use AbstractFramework with LangChain/LlamaIndex?

Yes. Use AbstractFramework for orchestration and durability; integrate other libraries as tools or subflows:

- Use LlamaIndex retrievers as tools within an AbstractAgent
- Wrap LangChain chains as tool executors
- Let AbstractRuntime handle durability while external libraries handle specific capabilities

---

## What is a ".flow bundle" and why does it matter?

A `.flow` file is the portable distribution unit for workflows. It packages:

- A VisualFlow workflow graph
- Metadata (entry points, interfaces)
- Optional subflows and assets

Deploy a bundle to a gateway and any gateway-backed client can discover and run it.

---

## How do I author complex agentic orchestration?

1. Run a gateway (for durability + discovery).
2. Open the Flow Editor (`npx @abstractframework/flow`) and connect to the gateway.
3. Build a workflow: LLM steps, tool steps, agent nodes, branching, loops, subflows.
4. Export to `.flow`.
5. Copy into `ABSTRACTGATEWAY_FLOWS_DIR` to deploy.

To make it reusable across clients, implement an **interface contract** (for example `abstractcode.agent.v1`).

See **[Getting Started](getting-started.md)** → "Author orchestration with AbstractFlow".

---

## How do I monitor and schedule agentic work?

- **Monitoring**: use **AbstractObserver** — replay ledger, stream live execution, inspect errors, control runs.
- **Scheduling**: durable schedules are owned by the **gateway** (survive restarts). Create them from a client UI or via the gateway scheduling API.

See **[Getting Started](getting-started.md)** → "Gateway-first" section.

---

## Which workflow answers when I chat with an agent?

The gateway's default agent workflow for the client's interface, unless you pick another in the
client. AbstractCode uses the shipped `basic-agent` until an admin chooses another
(`agents.default_workflow.abstractcode.agent.v1`); the Assistant runs its built-in orchestrator
unless the gateway names one. Clients that follow the gateway default pick up a change at the next
turn. See [Agent sessions](agent-sessions.md#the-default-agent-workflow).

## Where does the agent work, and can it read my credentials?

In a folder on the gateway's computer: the conversation's own folder under the gateway's data
folder, or the folder you started the AbstractCode terminal client from. AbstractCode's **Files**
tab and `/files` show its absolute path and preview its files. Credential folders (`~/.ssh`,
`~/.aws`, `~/.gnupg`, `~/.config/gcloud`, `~/.kube`, `~/Library/Keychains`), the framework's own
settings folders and the gateway's data folder are denied to every run's file tools and never
shown by the workspace browser. Shell commands a run may execute are not confined by that list,
so keep shell tools behind approval. See
[Agent sessions](agent-sessions.md#the-conversation-workspace).

## Which replies stream live?

With live replies on (the gateway's `agents.streaming_default`, or **Stream replies** in the
client), the text and reasoning of every model call in the run stream, sub-agents included.
Structured-output calls, a gateway that calls a remote AbstractCore server, providers that cannot
stream or report usage while streaming, and entity chat do not; the client says why in one line,
and the finished answer is the same either way. See
[Agent sessions](agent-sessions.md#live-replies-streaming).

## Does ejecting a model free its memory?

Yes. Ejecting a model (console **Resources**, `abstractgateway models unload`) frees it from every
holder in the gateway process, for MLX, llama.cpp GGUF, transformers and embedding models, caches
included. Switching the default model ejects the previous one before the new one loads when nothing
else uses it. The console's accelerator meter shows the memory the gateway process holds and how
it was measured. See [Architecture](architecture.md#model-residency-and-eject) and
[Troubleshooting](troubleshooting.md#the-gateway-still-holds-memory-after-an-eject).

## Where do the About screens get their information?

Every app renders the same framework identity (name, website, author, licence, links, contact)
from one descriptor kept in this repository, `identity/abstractframework.json`, plus the
versions the connected gateway reports at `GET /api/gateway/about`. See
[Architecture](architecture.md#framework-identity-and-about-screens).

---

## How does multimodality work?

AbstractCore supports modalities via **capability plugins** (installed separately, discovered via entry points):

| Plugin | Capability |
|---|---|
| `abstractvoice` | `llm.voice` (TTS) / `llm.audio` (STT) |
| `abstractvision` | `llm.vision` (image generation) |
| `abstractmusic` | `llm.music` (text-to-music) |

Plugins are configured on the machine that actually executes (local app host or gateway host). Don't install a plugin; Core stays lightweight.

---

## Where is data stored?

- **Gateway**: its data folder is the durability root (runs, ledger, artifacts, schedules, conversation workspaces, the seeded skill shelf, saved settings). By default it is `~/Library/Application Support/AbstractGateway` (macOS), `~/.local/share/abstractgateway` (Linux) or `%LOCALAPPDATA%\AbstractGateway` (Windows); `serve --data-dir` chooses another, and `abstractgateway-config status` prints the one in use.
- **Core config**: `~/.abstractcore/config/` (persisted by `abstractcore --config`).
- **Local apps**: `~/.abstractcode/` (terminal client preferences), `~/.abstractassistant/` (Assistant preferences, sign-in and chat snapshots), etc.

If you care about auditability and long-lived workflows, back up the gateway data directory.

---

## Installing with the one-line script

### Why does macOS ask me to allow the installer?

`AbstractFramework-Installer.pkg` is not signed with an Apple Developer ID, so macOS blocks the
first double-click. Open **System Settings > Privacy & Security** and click **Open Anyway** next to
the installer's name, once per download. The one-line install in Terminal does not show this
step. See [Install on a Mac](install.md#install-on-a-mac).

### Can other devices on my network use the gateway?

Yes, when you choose it. The gateway listens on this computer only until you change its Network
setting (`abstractgateway network set lan`, the console, or the menu-bar icon). See
[Network setting](install.md#network-setting-who-can-reach-the-gateway).

### Why is `abstractgateway` not found after the install?

The commands live in `~/.local/bin` (`%USERPROFILE%\.local\bin` on Windows). The script runs
`uv tool update-shell` once to add that directory to your PATH, which applies to **new**
terminals. Open a new terminal, or call `~/.local/bin/abstractgateway` directly. Pass
`--no-modify-path` if you manage PATH yourself.

### Which port does the gateway use?

`8080` by default. When something else already listens there (for example `llama-server` or
`mlx_lm.server`, which also default to 8080), the script picks the next free port, remembers it
for later runs, and prints the console URL. Choose one with `--port N` (`-Port N`).

### Will it ask for my password or admin rights?

Not for the default install: uv, Python, the gateway and Node (`nodejs-wheel`) install in your
user account. Only optional vendor installers may: Ollama on Linux uses sudo (it installs a system
service), Ollama on macOS may ask to link `/usr/local/bin/ollama`, and LM Studio on Linux may ask
to install `libatomic1`. The script tells you before running them.

### Do I need Xcode or a C compiler?

No. The default install uses prebuilt wheels only. If macOS shows an "install the command line
developer tools" prompt, cancel it and re-run the one-liner. llama.cpp GGUF models come from upstream's prebuilt wheel on Apple
Silicon, Linux and Windows x64 ([llama.cpp GGUF models](install.md#llamacpp-gguf-models)). You
need a compiler only for `--full`, which adds stable-diffusion.cpp and echo cancellation, and
llama.cpp on machines without a prebuilt wheel ([Compiled extras](install.md#compiled-extras)).

### Windows says scripts are disabled on this system

Pasting the one-liner works under the default `Restricted` policy because
`powershell -ExecutionPolicy ByPass -c "irm … | iex"` runs a command, not a script file, and the
bypass applies to that process only. If your organization sets the policy through Group Policy
(`Get-ExecutionPolicy -List` shows `MachinePolicy` or `UserPolicy`), a saved `install.ps1` will not
run; use the one-liner or ask your administrator. The installer reports this during preflight.

### The sign-in link expired or I closed the tab

The one-time link is valid for 10 minutes and works only from the same machine. Mint a new one with
`abstractgateway claim --open` (or `abstractgateway-config claim-url`). The admin token also stays
in `<data dir>/auth/bootstrap-admin-token`; the install summary prints that path.

### How do I stop or restart the gateway?

When the script registered the login service, `abstractgateway service status` shows it,
`abstractgateway service uninstall` stops the gateway and removes the login entry (your data is
kept), and `abstractgateway service install --port 8080` registers and starts it again. With `--no-service`, the install summary prints the stop and start commands; re-running the
installer starts it again.

### How do I download a model or install Ollama later?

Open the console's **Engines** tab (detect, install with the exact command shown first) and
**Models** tab (models that fit this machine, download, delete). From a terminal:
`abstractgateway engines status|install` and `abstractgateway models catalog|download|delete`.
Engine installs from the console run on the gateway host and are enabled by default only when the
gateway listens on loopback.

### How do I see what the script will do before running it?

Add `--print` (Windows: `-Print` or `-WhatIf`). It runs the read-only checks and prints every
command without changing anything.

### How do I remove it?

Re-run the script with `--uninstall` (`-Uninstall`). Add `--purge` (`-Purge`) to delete the gateway
data as well. See [Install](install.md#upgrade-and-uninstall).

---

## Something does not work

Symptoms, checks and fixes (provider calls failing, a browser app that cannot connect, missing
voice models, install errors) are in **[Troubleshooting](troubleshooting.md)**.
