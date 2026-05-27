# AbstractFramework documentation

**Write once. Generate everything.**

A modular, open-source ecosystem for building **durable, observable, multimodal** AI systems. Text, voice, image, video, music — one unified interface, any provider, any model, local or cloud.

This doc set focuses on two things:

1. **How to pick the right entry point** (AbstractCore SDK vs AbstractGateway control plane)
2. **How the pieces compose** (Core → Runtime → Gateway → Flow → Observer)

Most implementation lives in component repositories. This repo ships the `abstractframework` meta-package (a pinned install profile) and the cross-package docs you're reading now.

---

## Start here

### Choose your entry point

Start lightweight with just the LLM library, or go all-in with a production gateway. Both paths lead to the same ecosystem.

### AbstractCore (SDK + optional `/v1`)

Start with **AbstractCore**:

- 9+ providers with identical API (local + cloud)
- Universal tool calling, structured output, streaming
- Media handling (images, PDFs, audio, video)
- OpenAI-compatible HTTP server mode (`/v1`)
- Multimodal via capability plugins (Voice, Vision, Music)

Read **[Getting Started](getting-started.md)** → "Core-first" section.

### AbstractGateway (durable control plane)

Start with **AbstractGateway** + **AbstractFlow**:

- Durable execution that survives crashes and restarts
- Append-only ledger (replay-first) for auditability
- Scheduled workflows (cron-style, recurring)
- Multi-client: terminal, browser, tray, Telegram, email
- Start on one device, continue on another

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
