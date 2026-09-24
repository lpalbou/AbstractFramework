# AbstractFramework

**Write once. Generate everything.**

A modular, open-source ecosystem for building **durable, observable, multimodal** AI systems. Text, voice, image, video, music — one unified interface, any provider, any model, local or cloud.

AbstractFramework is an ecosystem of composable packages for building AI systems that work in operational reality:

- **Durable by default**: workflows **pause and resume** safely (survive crashes and restarts)
- **Observable**: an append-only **ledger** so any UI can reconstruct state by replaying history
- **Controlled actions**: explicit boundaries for **tool execution**, approvals, and evidence
- **Multimodal**: capability plugins (voice, vision, music) that stay out of your way until you need them

Think of it as an **agentic OS**: durable runs + replay-first observability + multimodal capabilities — write once, run across providers and deployment modes.

> **Prerequisites**: none for the one-line install below (it provisions Python and, optionally, Node.js). For a manual install: Python 3.10–3.13, Node.js 18+ for browser UIs, and an LLM backend (Ollama, LM Studio, vLLM, or a cloud API key).

---

## Quick start

The installer sets up the gateway in your user account (no admin password, no system Python),
asks whether to start it at login, starts it on `127.0.0.1:8080`, and opens its web console in
your browser already signed in. A first-run guide then sets up a local engine (Ollama, LM Studio,
MLX, llama.cpp), downloads a model that fits your machine, and lists the apps.

- **Mac, no Terminal:** download and double-click
  [AbstractFramework-Installer.pkg](https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg).
  A Terminal window shows each step; press Return at its one question.
- **macOS / Linux, one line:**

  ```bash
  curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh -s -- --interactive
  ```

- **Windows 10 22H2+ / 11** (PowerShell):

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
  ```

Every failure says what to do next; running the installer again repairs or upgrades in place. To
remove it: `Uninstall AbstractFramework.command`, or
`curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/uninstall.sh | sh`.
Step by step, the failure table, options (`--with-apps`, `--with-ollama`, `--print`, …):
[Install](docs/install.md).

Already have Python? Either entry point works the same way: start it, then open the link it prints.

```bash
pip install abstractcore && abstractcore serve        # http://127.0.0.1:8000/console#claim=…
pip install abstractgateway && abstractgateway serve  # http://127.0.0.1:8080/console#claim=…
```

Both consoles have **Models** (browse models that fit this machine, download, delete) and
**Engines** (detect and install local engines) tabs; every action also shows its command-line
equivalent (`abstractcore models …`, `abstractcore engines …`, `abstractgateway models …`).

---

## Two entrypoints

Start lightweight with just the LLM library, or go all-in with a production gateway. Both paths lead to the same ecosystem.

### 1) AbstractCore — LLM SDK + OpenAI-compatible `/v1` server

Start here if you need a lightweight LLM library for scripts, notebooks, or existing applications. No infrastructure required — just `pip install` and call. Add multimodal capabilities with plugins as you grow.

- 9+ providers with identical API (local + cloud)
- Universal tool calling, structured output, streaming
- Media handling (images, PDFs, audio, video)
- OpenAI-compatible HTTP server mode (`/v1`)
- Multimodal via capability plugins (Voice, Vision, Music)

```bash
pip install abstractcore
```

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("Explain durable execution in 3 bullets.")
print(resp.content)
```

`abstractcore serve` starts the `/v1` server on `127.0.0.1:8000` and prints a one-time link to its
web console (Overview, Models, Engines, Providers). The same Models and Engines screens are
available from the command line (`abstractcore models catalog|list|download|delete`,
`abstractcore engines status|install`) and in the terminal console
(`cargo install abstractcore-console`).

AbstractCore gives you one interface for provider switching, tools, structured output, and media — as a Python SDK or via `/v1` for any OpenAI-compatible client.

### 2) AbstractGateway — durable run control plane (HTTP/SSE APIs)

Start here if you're building persistent AI applications — agents that run for hours, workflows that survive crashes, scheduled tasks. The gateway is your AI control plane: durable runs with ledger replay/streaming and thin clients that can attach/detach across devices.

- Durable execution that survives crashes and restarts
- Append-only ledger (replay-first) for auditability
- Scheduled workflows (cron-style, recurring)
- Multi-client: terminal, browser, tray, Telegram, email
- Start on one device, continue on another

```bash
pip install abstractgateway
abstractgateway serve
```

With no auth configured, `abstractgateway serve` binds `127.0.0.1:8080`, enables user auth,
creates `default/admin` in the per-user data folder, and prints a one-time sign-in link
(`http://127.0.0.1:8080/console#claim=…`, valid 10 minutes, this machine only). Open it to reach the
web console and its first-run guide. `abstractgateway claim` mints a new link;
`abstractgateway service install` starts the gateway at login.

To choose the data folder, the allowed browser origins or your own workflow bundles, set the
environment explicitly:

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
# export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"   # serve your own bundle registry

abstractgateway serve --host 127.0.0.1 --port 8080
```

Out of the box this serves a ready set of workflows — a verify-gated coding
agent, `deep-research`, and `co-scientist` among them. See
[shipped workflows](abstractgateway/docs/shipped-workflows.md).

The `admin` user token is kept in `<data dir>/auth/bootstrap-admin-token`; use it to sign in to
AbstractFlow, AbstractCode Web or AbstractObserver, or to the console without a claim link.
`ABSTRACTGATEWAY_AUTH_TOKEN` remains a legacy server/operator bearer token; it is not a browser
sign-in token.

Monitor runs from a browser, or from a terminal with the gateway console:

```bash
npx @abstractframework/observer   # open http://localhost:3001

cargo install abstractgateway-console   # Rust 1.87+
ABSTRACTGATEWAY_AUTH_TOKEN=<token> abstractgateway-console --url http://127.0.0.1:8080
```

Container images are published for the gateway and the AbstractCore server:
`ghcr.io/lpalbou/abstractgateway:0.4.1` and `ghcr.io/lpalbou/abstractcore-server:2.15.0`.

For artifact and runtime-resource investigation, see
`docs/guide/runtime-artifacts.md`.

---

## Author once, run everywhere (AbstractFlow)

AbstractFlow lets you author complex agentic orchestration as portable `.flow` bundles:

1. Open the Flow Editor (`npx @abstractframework/flow`)
2. Build a workflow: LLM steps, tool steps, branching, loops, subflows
3. Export a `.flow` bundle into your own bundle directory and point `ABSTRACTGATEWAY_FLOWS_DIR` at it (or publish it through the Gateway API)
4. Run it from any gateway-backed client (Observer, AbstractAssistant, Code Web UI, your app)

**AbstractAgent** provides ready-made agent patterns (ReAct, CodeAct, MemAct) that can be used inside flows or standalone. The workflows Gateway ships with are authored the same way — their editable sources are documented in [shipped workflow sources](abstractflow/docs/shipped-workflow-sources.md).

---

## Monitor and schedule with AbstractObserver

- **Observe**: replay the full ledger of any run, or watch one live over SSE
- **Control**: cancel, resume, or inspect runs from the browser
- **Schedule**: durable schedules (cron-style) owned by the gateway — they survive restarts

---

## Package map

The ecosystem, grouped by layer. Each name links to the package's own README.

### Foundation

| Package | What it is |
|---|---|
| [abstractcore](abstractcore/) | Unified LLM interface: 9+ providers, tools, structured output, media, embeddings, `/v1` server, capability plugins |
| [abstractsemantics](abstractsemantics/) | Central semantics registry (predicates + entity types) with JSON-Schema helpers |
| [abstractmemory](abstractmemory/) | Durable, append-only agent memory: usage-weighted graph + journal — recall, formation, consolidation (the entity mind engine) |

### Durable execution

| Package | What it is |
|---|---|
| [abstractruntime](abstractruntime/) | Durable execution kernel: runs, effects, waits, append-only ledger, artifacts; the VisualFlow compiler (visual graphs → executable workflows); the entity identity lane (homes, chat/life/visit drivers) |
| [abstractagent](abstractagent/) | Agent patterns (ReAct / CodeAct / MemAct) composing Runtime + Core |
| [abstractflow](abstractflow/) | Visual workflow editor + portable `.flow` bundles — author once, run anywhere |

### Control plane

| Package | What it is |
|---|---|
| [abstractgateway](abstractgateway/) | Deployable control plane: durable runs over HTTP/SSE, scheduling + run commands (cancel/steer), workflow catalog, artifact/ledger serving, multi-user auth with per-user runtimes, the summoned-entity lifecycle (create / summon / visit / state / blueprint), and the operator consoles (web + TUI) |

### Multimodal capabilities

| Package | What it is |
|---|---|
| [abstractvoice](abstractvoice/) | Voice I/O (TTS / STT), local and remote backends |
| [abstractvision](abstractvision/) | Model-agnostic generative vision (images, optional video) |
| [abstractmusic](abstractmusic/) | Text-to-music / text-to-audio (Core capability plugin) |
| [abstract3d](abstract3d/) | Local-first 3D generation |
| [abstractcamera](abstractcamera/) | Camera control and capture tools |
| [abstractsound](abstractsound/), [abstractvideo](abstractvideo/), [abstractspatial](abstractspatial/), [abstractgeometry](abstractgeometry/), [abstractcognition](abstractcognition/) | Reserved capability packages (namespaces held; APIs landing incrementally) |

### Apps and clients

| App | What it does | Install |
|---|---|---|
| [AbstractCode](abstractcode/) | Terminal agentic dev client (Rust, on the AbstractTUI engine) — durable sessions, tool approvals, `/workflow` support | `cargo install abstractcode`, or a prebuilt binary from the [GitHub release](https://github.com/lpalbou/AbstractCode/releases) |
| [AbstractAssistant](abstractassistant/) | macOS tray client — gateway-native, workflow picker per session, voice support | `pip install abstractassistant` |
| [AbstractObserver](abstractobserver/) | Browser UI — monitor, control, and schedule gateway runs | `npx @abstractframework/observer` |
| [AbstractEntity](abstractentity/) | Summoned-entity manager — roster, blueprint (cognition map + editing), chat drawer, live replay | `npx @abstractframework/entity` |
| [AbstractContinuum](abstractcontinuum/) | Continuous iterative development and deployment console | `npx @abstractframework/continuum` |
| **Gateway consoles** | Operator consoles for a running gateway: web at `/console` (first-run guide, Models, Engines, providers, users), terminal via `abstractgateway-console` | built into `abstractgateway`; `cargo install abstractgateway-console` |
| **Core consoles** | Consoles for AbstractCore: web at `/console` of `abstractcore serve`, terminal via `abstractcore-console` (config, Models, Engines) | built into `abstractcore`; `cargo install abstractcore-console` |
| **Code Web UI** | Browser client of AbstractCode (gateway-backed) | `npx @abstractframework/code` |
| **Flow Editor** | Visual workflow authoring in the browser | `npx @abstractframework/flow` |

### Shared libraries

| Package | What it is |
|---|---|
| [abstracttui](abstracttui/) | Rust terminal-UI engine built on fine-grained reactive signals |
| [abstractuic](abstractuic/) | Reusable UI kit for framework clients (React components + Web Components) |
| [abstractskill](abstractskill/) | Shared library for Agent Skills (`SKILL.md` folders: load, trust-gate, activate) |

---

## Install the pinned ecosystem profile

### Light / Apple / GPU profiles

Choose how the framework runs based on your hardware and constraints. All profiles keep the same interfaces; they mainly change which **local inference stacks** are available.

**Light (default)** — endpoint-only inference (cloud APIs or local OpenAI-compatible servers), no in-process ML engine stacks:

```bash
pip install abstractframework
```

**Apple** — native Apple Silicon local stacks (MLX/Metal) in addition to endpoint providers:

```bash
pip install "abstractframework[apple]"
```

**GPU** — native GPU local stacks (CUDA/ROCm) in addition to endpoint providers:

```bash
pip install "abstractframework[gpu]"
```

| Profile | Command | Platforms | Python |
|---|---|---|---|
| Light | `pip install abstractframework` | macOS, Linux, Windows | 3.10–3.13 |
| Apple | `pip install "abstractframework[apple]"` | macOS 14+ on Apple Silicon | 3.10–3.13 (F5-TTS voice cloning needs 3.11+) |
| GPU | `pip install "abstractframework[gpu]"` | Linux / Windows with a CUDA or ROCm GPU | 3.10–3.13 (F5-TTS voice cloning needs 3.11+) |

### Release matrix (abstractframework 0.3.0)

`abstractframework` pins every Python package with `==`, so one version of the
meta-package always installs the same stack. The browser apps and Rust tools are
distributed through npm and crates.io; the versions below are the ones released
and tested together.

| Registry | Package | Version |
|---|---|---|
| PyPI | `abstractgateway` | 0.4.1 |
| PyPI | `abstractassistant` | 0.5.0 |
| PyPI | `abstractcore` | 2.15.0 |
| PyPI | `AbstractRuntime` | 0.4.33 |
| PyPI | `abstractagent` | 0.3.13 |
| PyPI | `AbstractMemory` | 0.3.0 |
| PyPI | `abstractsemantics` | 0.0.5 |
| PyPI | `abstractvoice` | 0.11.4 |
| PyPI | `abstractvision` | 0.3.29 |
| PyPI | `abstractmusic` | 0.1.15 |
| npm | `@abstractframework/flow` | 0.3.20 |
| npm | `@abstractframework/code` | 0.4.2 |
| npm | `@abstractframework/observer` | 0.1.12 |
| npm | `@abstractframework/continuum` | 0.3.0 |
| npm | `@abstractframework/entity` | 0.2.0 |
| crates.io | `abstractcode` | 0.5.1 |
| crates.io | `abstractgateway-console` | 0.8.0 |
| crates.io | `abstractcore-console` | 0.2.0 |
| crates.io | `abstracttui` | 0.6.0 |
| GHCR | `ghcr.io/lpalbou/abstractgateway` | 0.4.1 (`gpu-latest` / `<version>-gpu` experimental) |
| GHCR | `ghcr.io/lpalbou/abstractcore-server` | 2.15.0 |

Optional add-ons that are not part of any profile install separately:
`pip install abstract3d` (0.3.1), `pip install abstractcamera` (0.2.0) and
`pip install abstractskill` (0.2.1).

See [docs/install.md](docs/install.md) for the full install chooser, `uv`/venv guidance,
`abstractframework doctor`, and the generated installer manifest contract.

---

## Documentation

| Page | What it covers |
|---|---|
| [docs/README.md](docs/README.md) | Documentation hub — pick your starting point |
| [docs/install.md](docs/install.md) | Light / Apple / GPU install chooser and first checks |
| [docs/getting-started.md](docs/getting-started.md) | Two entry points + first end-to-end run |
| [docs/architecture.md](docs/architecture.md) | Layered model, durable execution primitives, comparisons |
| [docs/configuration.md](docs/configuration.md) | Minimal config, where defaults live, Core vs Gateway |
| [docs/glossary.md](docs/glossary.md) | Shared terminology (run, ledger, effect, wait, bundle, …) |
| [docs/faq.md](docs/faq.md) | Common questions, comparisons, troubleshooting |
| [docs/api.md](docs/api.md) | Meta-package API (pins, helpers, re-exports) |
| [docs/workspace-scripts.md](docs/workspace-scripts.md) | Working from source: package tiers, build, status, pull/commit/push scripts |

---

## Developer setup (from source)

Clone all sibling repos and build everything in editable mode:

```bash
./scripts/clone.sh           # clone every sibling repository next to this one
./scripts/deps.sh            # dependency tiers: what builds and installs first, and why
source ./scripts/build.sh    # Python (editable, into .venv), npm and Rust builds, tier by tier
```

Keep the whole workspace in sync with `./scripts/status.sh` (git overview per tier; `--registry`
compares local versions with PyPI, npm and crates.io), `./scripts/pull.sh`, `./scripts/commit.sh`
and `./scripts/push.sh` (a dry run until you add `--yes`). See
[docs/workspace-scripts.md](docs/workspace-scripts.md) for every script and option.

Then configure providers and models in a console (`abstractcore serve` or
`abstractgateway serve`, then open the printed link), or from the terminal:

```bash
abstractcore --config    # interactive configuration wizard
abstractcore --install   # check every subsystem and download missing models and dependencies
```

---

## License

MIT. See [LICENSE](LICENSE).
