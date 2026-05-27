# AbstractFramework

**Durable, observable AI workflows — open source, local-first, multimodal.**

AbstractFramework is an ecosystem of composable packages for building AI systems that work in the real world:

- workflows that **pause and resume** safely (survive crashes and restarts)
- an append-only **ledger** so any UI can reconstruct state by replaying history
- explicit boundaries for **tool execution**, approvals, and evidence
- **multimodal** capability plugins (voice, vision, music) that stay out of your way until you need them

> **Prerequisites**: Python 3.10+. Node.js 18+ for browser UIs. An LLM backend (Ollama, LM Studio, vLLM, or a cloud API key).

---

## Two ways to use the framework

### 1) Code — AbstractCore (Python SDK)

Use when you're integrating AI features directly in code:

```bash
pip install abstractcore
```

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("Explain durable execution in 3 bullets.")
print(resp.content)
```

AbstractCore gives you: provider/model abstraction (local + cloud), tool calling, structured output (Pydantic), media input, embeddings, MCP tool discovery, and an optional OpenAI-compatible `/v1` server.

### 2) API routes — AbstractGateway (language-agnostic control plane)

Use when you need **durable orchestration** accessible from any language or client: persistent runs, scheduling, multi-client UIs — all over HTTP/SSE.

```bash
pip install abstractgateway

export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

abstractgateway serve --host 127.0.0.1 --port 8080
```

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

Remote-first (recommended):

```bash
pip install abstractframework
```

Hardware-local profiles (native installs, not Docker):

```bash
pip install "abstractframework[apple]"       # Apple Silicon native stack (MLX/Metal)
pip install "abstractframework[gpu]"         # GPU native stack (CUDA/ROCm)
```

---

## Documentation

| Page | What it covers |
|---|---|
| [docs/README.md](docs/README.md) | Documentation hub — pick your starting point |
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
