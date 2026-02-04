# AbstractFramework

Durable agents and workflows — an open-source ecosystem for building long-running, restart-safe AI systems.

AbstractFramework is intentionally **modular**: each component is a standalone project (its own package, docs, and releases).
This repository is the ecosystem **gateway**: it helps you pick the right building blocks and get to a first working setup quickly.

## Start Here

- [Getting started](docs/getting-started.md) — pick a path and run something
- [Architecture](docs/architecture.md) — how the stack fits together (libraries + hosts + deployment)
- [Configuration](docs/configuration.md) — common configuration knobs (providers, gateway, clients)
- [FAQ](docs/faq.md) — common questions and gotchas

## The Two Peers Everything Builds On

- **AbstractRuntime** — durable workflow runtime (**pause → checkpoint → resume**) with an append-only execution ledger.
- **AbstractCore** — unified LLM interface (providers, tool calling, structured output, media handling, optional HTTP server).

On top of those peers you can compose:
- **AbstractAgent** — ReAct / CodeAct / MemAct patterns (ready-made agent workflows)
- **AbstractFlow** — VisualFlow portable workflows + `.flow` bundling + a reference web editor
- **AbstractGateway** — deployable HTTP/SSE run gateway (replay-first ledger + durable command inbox)
- **Host apps** — AbstractCode (terminal), AbstractAssistant (tray), AbstractObserver (web/PWA)

## Install (Python)

`abstractframework` on PyPI is a **meta-package**:

```bash
pip install abstractframework
```

That installs the lightweight `abstractcore` base (provider SDKs and other heavy features are behind extras).

Common bundles (zsh: keep the quotes):

```bash
pip install "abstractframework[all]"      # full Python ecosystem (large)
pip install "abstractframework[backend]"  # core+runtime+agent+flow+gateway+memory+semantics
pip install "abstractframework[code]"     # terminal TUI host (AbstractCode)
pip install "abstractframework[gateway]"  # deployable run gateway (HTTP)
```

For a smaller footprint, install provider-specific AbstractCore extras directly:

```bash
pip install "abstractcore[openai]"        # or: anthropic, tools, media, tokens, server, ...
```

## Quickstarts (Pick One)

### 1) Library: unified LLM API (AbstractCore)

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
print(llm.generate("Give me 3 bullets on durable workflows.").content)
```

### 2) Local agent in the terminal (AbstractCode)

```bash
pip install abstractcode
abstractcode --provider ollama --model qwen3:1.7b-q4_K_M
```

Inside the app run `/help`. Tool execution is approval-gated by default.

### 3) Deploy a run gateway + observe in the browser (AbstractGateway + AbstractObserver)

```bash
pip install "abstractgateway[http]"
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"   # *.flow bundles (or upload later)
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

abstractgateway serve --host 127.0.0.1 --port 8080
npx abstractobserver
```

Open `http://localhost:3001`, set Gateway URL to `http://127.0.0.1:8080`, paste the token, and connect.

## Ecosystem Index

### Core libraries (Python)

| Project | Purpose | Start here |
|---|---|---|
| [AbstractCore](https://github.com/lpalbou/abstractcore) | Unified LLM API: providers + tools + structured output + media + optional HTTP server | [docs/getting-started.md](https://github.com/lpalbou/abstractcore/blob/main/docs/getting-started.md) |
| [AbstractRuntime](https://github.com/lpalbou/abstractruntime) | Durable runtime: effects + waits + ledger + stores + bundles | [docs/getting-started.md](https://github.com/lpalbou/abstractruntime/blob/main/docs/getting-started.md) |

### Composition libraries (Python)

| Project | Purpose | Start here |
|---|---|---|
| [AbstractAgent](https://github.com/lpalbou/abstractagent) | ReAct / CodeAct / MemAct patterns on Runtime + Core | [docs/getting-started.md](https://github.com/lpalbou/abstractagent/blob/main/docs/getting-started.md) |
| [AbstractFlow](https://github.com/lpalbou/abstractflow) | VisualFlow portable workflows + `.flow` bundling + reference editor | [docs/getting-started.md](https://github.com/lpalbou/abstractflow/blob/main/docs/getting-started.md) |

### Hosts (Python)

| Project | Purpose | Start here |
|---|---|---|
| [AbstractCode](https://github.com/lpalbou/abstractcode) | Durable terminal TUI for agentic coding (local runs + gateway client) | [docs/getting-started.md](https://github.com/lpalbou/abstractcode/blob/main/docs/getting-started.md) |
| [AbstractGateway](https://github.com/lpalbou/AbstractGateway) | Deployable HTTP/SSE run gateway (replay-first ledger + durable commands) | [docs/getting-started.md](https://github.com/lpalbou/AbstractGateway/blob/main/docs/getting-started.md) |
| [AbstractAssistant](https://github.com/lpalbou/AbstractAssistant) | Tray UI + CLI local agent host (optional voice) | [docs/getting-started.md](https://github.com/lpalbou/AbstractAssistant/blob/main/docs/getting-started.md) |

### Observability + UI (JavaScript)

| Package | Purpose | Start here |
|---|---|---|
| [AbstractObserver (npm: `abstractobserver`)](https://github.com/lpalbou/AbstractObserver) | Gateway-only observability UI (Web/PWA) | [README](https://github.com/lpalbou/AbstractObserver#readme) |
| [AbstractUIC](https://github.com/lpalbou/AbstractUIC) | UI building blocks (`@abstractframework/*`) used by thin clients | [docs/getting-started.md](https://github.com/lpalbou/AbstractUIC/blob/main/docs/getting-started.md) |

### Data, memory, semantics (Python)

| Project | Purpose | Start here |
|---|---|---|
| [AbstractMemory](https://github.com/lpalbou/AbstractMemory) | Temporal, provenance-aware triple assertions + deterministic queries | [docs/getting-started.md](https://github.com/lpalbou/AbstractMemory/blob/main/docs/getting-started.md) |
| [AbstractSemantics](https://github.com/lpalbou/AbstractSemantics) | Semantics registry (predicates/entity types) + JSON Schema helpers | [docs/getting-started.md](https://github.com/lpalbou/AbstractSemantics/blob/main/docs/getting-started.md) |

### Modalities (Python)

| Project | Purpose | Start here |
|---|---|---|
| [AbstractVoice](https://github.com/lpalbou/abstractvoice) | Voice I/O (TTS/STT) + AbstractCore capability plugin | [docs/getting-started.md](https://github.com/lpalbou/abstractvoice/blob/main/docs/getting-started.md) |
| [AbstractVision](https://github.com/lpalbou/abstractvision) | Generative vision outputs (images; optional video) + AbstractCore integration | [docs/getting-started.md](https://github.com/lpalbou/abstractvision/blob/main/docs/getting-started.md) |

### Planned / placeholders

These repos exist but are not primary entry points today:

- [AbstractAI](https://github.com/lpalbou/abstractai) — intelligent model selection/routing (planned)
- [AbstractReasoner](https://github.com/lpalbou/AbstractReasoner) — semantic reasoning on top of AbstractMemory (placeholder)
- [abstractagi](https://github.com/lpalbou/abstractagi), [abstractaudio](https://github.com/lpalbou/abstractaudio), [abstractbrain](https://github.com/lpalbou/abstractbrain), [abstractendpoint](https://github.com/lpalbou/abstractendpoint), [abstractintelligence](https://github.com/lpalbou/abstractintelligence), [abstractmind](https://github.com/lpalbou/abstractmind), [abstractmusic](https://github.com/lpalbou/abstractmusic), [abstractserve](https://github.com/lpalbou/abstractserve), [abstractservice](https://github.com/lpalbou/abstractservice), [abstractsignal](https://github.com/lpalbou/abstractsignal), [abstractskills](https://github.com/lpalbou/abstractskills)

## License

MIT (see `LICENSE`).
