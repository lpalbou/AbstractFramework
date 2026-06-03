# AbstractFramework

**Write once. Generate everything.**

A modular, open-source ecosystem for building **durable, observable, multimodal** AI systems. Text, voice, image, video, music — one unified interface, any provider, any model, local or cloud.

AbstractFramework is an ecosystem of composable packages for building AI systems that work in operational reality:

- **Durable by default**: workflows **pause and resume** safely (survive crashes and restarts)
- **Observable**: an append-only **ledger** so any UI can reconstruct state by replaying history
- **Controlled actions**: explicit boundaries for **tool execution**, approvals, and evidence
- **Multimodal**: capability plugins (voice, vision, music) that stay out of your way until you need them

Think of it as an **agentic OS**: durable runs + replay-first observability + multimodal capabilities — write once, run across providers and deployment modes.

> **Prerequisites**: Python 3.10+. Node.js 18+ for browser UIs. An LLM backend (Ollama, LM Studio, vLLM, or a cloud API key).

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

export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

abstractgateway serve --host 127.0.0.1 --port 8080
```

On first local start, Gateway creates `default/admin`, writes the browser-login
token to `runtime/gateway/auth/bootstrap-admin-token`, and prints the token in
the terminal. Use that `admin` user token in `/console`, AbstractFlow,
AbstractCode Web, or AbstractObserver. `ABSTRACTGATEWAY_AUTH_TOKEN` remains a
legacy server/operator bearer token; it is not a browser sign-in token.

Monitor runs from a browser:

```bash
npx @abstractframework/observer   # open http://localhost:3001
```

---

## Author once, run everywhere (AbstractFlow)

AbstractFlow lets you author complex agentic orchestration as portable `.flow` bundles:

1. Open the Flow Editor (`npx @abstractframework/flow`)
2. Build a workflow: LLM steps, tool steps, branching, loops, subflows
3. Export a `.flow` bundle and copy it to `ABSTRACTGATEWAY_FLOWS_DIR`
4. Run it from any gateway-backed client (Observer, AbstractAssistant, Code Web UI, your app)

**AbstractAgent** provides ready-made agent patterns (ReAct, CodeAct, MemAct) that can be used inside flows or standalone.

---

## Monitor and schedule with AbstractObserver

- **Observe**: replay the full ledger of any run, or watch one live over SSE
- **Control**: cancel, resume, or inspect runs from the browser
- **Schedule**: durable schedules (cron-style) owned by the gateway — they survive restarts

---

## Example apps

| App | What it does | Install |
|---|---|---|
| **AbstractCode** | Terminal agentic dev client — durable sessions, tool approvals, `/workflow` support | `pip install abstractcode` |
| **AbstractAssistant** | macOS tray client — gateway-first, workflow picker per session, voice support | `pip install abstractassistant` |
| **AbstractObserver** | Browser UI — monitor, control, and schedule gateway runs | `npx @abstractframework/observer` |
| **Code Web UI** | Browser coding assistant (gateway-backed) | `npx @abstractframework/code` |

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

---

## Developer setup (from source)

Clone all sibling repos and build everything in editable mode:

```bash
./scripts/clone.sh           # clone 14 repos as siblings
source ./scripts/build.sh    # editable installs into .venv (use `source` to stay in the venv)
```

Then configure:

```bash
abstractcore --config
abstractcore --install
```

---

## License

MIT. See [LICENSE](LICENSE).
