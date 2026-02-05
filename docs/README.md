# AbstractFramework Docs

This folder is the **gateway documentation** for the AbstractFramework ecosystem.

If you're new, start with:

- [Getting Started](getting-started.md) — pick a path and run something
- [Architecture](architecture.md) — how the stack fits together
- [Configuration](configuration.md) — common configuration knobs
- [FAQ](faq.md) — common questions and gotchas

---

## Find What You Need

### Python Packages (pip)

| I want... | Package |
|-----------|---------|
| A unified LLM client library | [AbstractCore](https://github.com/lpalbou/abstractcore) |
| A durable workflow runtime (pause/resume + ledger) | [AbstractRuntime](https://github.com/lpalbou/abstractruntime) |
| Ready-made agent patterns (ReAct, CodeAct, MemAct) | [AbstractAgent](https://github.com/lpalbou/abstractagent) |
| Visual workflows + bundling | [AbstractFlow](https://github.com/lpalbou/abstractflow) |
| A terminal app for agentic coding | [AbstractCode](https://github.com/lpalbou/abstractcode) |
| A macOS menu bar assistant | [AbstractAssistant](https://github.com/lpalbou/abstractassistant) |
| A deployable run gateway (HTTP/SSE) | [AbstractGateway](https://github.com/lpalbou/abstractgateway) |
| Voice I/O (TTS/STT) — capability plugin for AbstractCore | [AbstractVoice](https://github.com/lpalbou/abstractvoice) |
| Image generation — capability plugin for AbstractCore | [AbstractVision](https://github.com/lpalbou/abstractvision) |
| A temporal triple store for knowledge graphs | [AbstractMemory](https://github.com/lpalbou/abstractmemory) |
| A semantics registry for KG assertions | [AbstractSemantics](https://github.com/lpalbou/abstractsemantics) |

### npm Packages

| I want... | Package |
|-----------|---------|
| A browser UI to observe gateway runs | `npx @abstractframework/observer` |
| A visual workflow editor | `npx @abstractframework/flow` |
| A browser-based coding assistant | `npx @abstractframework/code` |
| UI building blocks for my own app | [@abstractframework/ui-kit](https://github.com/lpalbou/abstractuic), etc. |

---

## Architecture at a Glance

```
 RECOMMENDED: Gateway-first          │  ALTERNATIVE: Local in-process
─────────────────────────────────────┼───────────────────────────────────
 Browser UIs (Observer, Flow         │  AbstractCode (terminal)
 Editor, Code Web, Your App)         │  AbstractAssistant (macOS tray)
              │                      │             │
              ▼                      │             │
       AbstractGateway               │             │
  (bundle discovery, run control)    │             │
              │                      │             │
              └──────────────────────┴─────────────┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│  Composition: AbstractAgent (ReAct/CodeAct/MemAct) + AbstractFlow │
└───────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────--─────┐
│  Foundation: AbstractRuntime + AbstractCore (+ Voice/Vision plugins)│
└────────────────────────────────────────────────────────────────--───┘
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│  Memory & Knowledge: AbstractMemory · AbstractSemantics           │
└───────────────────────────────────────────────────────────────────┘
```

See [Architecture](architecture.md) for details on both paths.

---

## What's in This Repo

This repo (`abstractframework` on PyPI) is a **meta-package + documentation index**:

- Install common bundles via extras: `pip install "abstractframework[all]"`
- Points you to the real projects (each package has its own repo)
- Most execution happens in **Python** (runtime, agents, gateway)
- Browser UIs are distributed via **npm** (`@abstractframework/observer`, etc.)

---

## Quick Links

- [Main README](../README.md) — full ecosystem overview
- [Getting Started](getting-started.md) — pick your path
- [Architecture](architecture.md) — how it all fits together
- [Configuration](configuration.md) — environment variables and settings
- [FAQ](faq.md) — common questions and troubleshooting
