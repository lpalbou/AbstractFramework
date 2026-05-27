# AbstractFramework documentation

AbstractFramework is an open-source ecosystem for building **durable, observable, multimodal AI applications**.

This doc set focuses on two things:

1. **How to pick the right entry point** (AbstractCore SDK vs AbstractGateway control plane)
2. **How the pieces compose** (Core → Runtime → Gateway → Flow → Observer)

Most implementation lives in component repositories. This repo ships the `abstractframework` meta-package (a pinned install profile) and the cross-package docs you're reading now.

---

## Start here

### I want to integrate AI via code (Python SDK)

Start with **AbstractCore**:

- Unified provider/model interface (local + cloud)
- Tool calling, structured output (Pydantic), streaming, async
- Media input (images/audio/video/docs) with explicit policies
- Embeddings, MCP integration, optional OpenAI-compatible `/v1` server

Read **[Getting Started](getting-started.md)** → "Core-first" section.

### I want durable orchestration via API routes (any language)

Start with **AbstractGateway** + **AbstractFlow**:

- Durable runs (pause/resume/cancel), persistence, scheduling
- Bundle discovery: author a workflow once, deploy it, run it from any client
- All over HTTP/SSE — use from any language or framework, not just Python
- Ledger streaming so UIs can attach/detach without losing state

Read **[Getting Started](getting-started.md)** → "Gateway-first" section.

---

## How the pieces fit (one picture)

```
Authoring                                Operations
──────────────────────────────────────────────────────────────

 AbstractFlow (author workflows)      AbstractGateway (control plane)
 + Flow Editor (web UI)               - run control + scheduling
 - exports .flow bundles              - bundle discovery + SSE ledger
               │                                │
               └─────────────┬──────────────────┘
                             ▼
          AbstractAgent (ReAct / CodeAct / MemAct)
                             │
                             ▼
                  AbstractRuntime (durable kernel)
                  - runs, effects, waits
                  - ledger + artifacts
                             │
                             ▼
                  AbstractCore (LLM + tools + media)
                  - provider abstraction + routing defaults
                  - capability plugins: voice / vision / music
```

---

## Doc map

| Page | What it covers |
|---|---|
| **[Getting Started](getting-started.md)** | The two entry points + first end-to-end run |
| **[Architecture](architecture.md)** | Layered model, durable execution primitives, honest comparisons |
| **[Configuration](configuration.md)** | Minimal config, where defaults live, Core vs Gateway |
| **[Glossary](glossary.md)** | Shared terminology (run, ledger, effect, wait, bundle, …) |
| **[FAQ](faq.md)** | Common questions, troubleshooting, comparisons |
| **[API](api.md)** | The `abstractframework` meta-package API (pins + helpers + re-exports) |

---

## Example apps

| App | What it does |
|---|---|
| **AbstractCode** | Terminal agentic dev client (local, durable sessions) |
| **AbstractAssistant** | macOS tray client (gateway-first, workflow picker, voice) |
| **AbstractObserver** | Browser UI to monitor, control, and schedule gateway runs |
| **Code Web UI** | Browser coding assistant (gateway-backed) |

---

## More docs

| Folder | What's inside |
|---|---|
| [docs/guide/](guide/) | Focused "how it works" notes |
| [docs/scenarios/](scenarios/) | End-to-end walkthroughs by use case |
| [docs/installers/](installers/) | Installer strategy and prototypes |
| [docs/comparisons/](comparisons/) | Trade-offs vs other frameworks |
