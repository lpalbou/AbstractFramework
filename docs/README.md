# AbstractFramework Docs

This folder is the **entrypoint documentation** for the AbstractFramework ecosystem.

Install the full pinned release with one command:

```bash
pip install "abstractframework==0.1.1"
```

That installs all core ecosystem Python packages together, with:
- `abstractcore` configured with core extras (`openai,anthropic,huggingface,embeddings,tokens,tools,media,compression,server`)
- `abstractflow` configured with `editor`

If you're new, start with:

- [Getting Started](getting-started.md) — pick a path and run something
- [Architecture](architecture.md) — how the stack fits together
- [API](api.md) — `abstractframework` package helpers and release profile
- [Configuration](configuration.md) — common configuration knobs
- [FAQ](faq.md) — common questions and gotchas
- [Scenarios](scenarios/README.md) — end-to-end paths by use case
- [Guides](guide/README.md) — focused "how it works" notes
- [Glossary](glossary.md) — shared terminology

## LLM Context Files

If you're feeding this repo into an LLM:

- `llms.txt` is the navigation/index file.
- `llms-full.txt` is a single concatenated context file.
- Regenerate: `python scripts/gen_llms_full.py`

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

This repo provides:

- One canonical package entrypoint (`abstractframework`) for full-stack installation
- Ecosystem documentation (architecture, setup, configuration, FAQ)
- Use-case scenarios and focused guides (see below)
- A map of package responsibilities so teams can build and deploy new specialized solutions
- Links to browser UIs distributed via npm (`@abstractframework/observer`, `@abstractframework/flow`, `@abstractframework/code`)

---

## Quick Links

- [Main README](../README.md) — full ecosystem overview
- [Getting Started](getting-started.md) — pick your path
- [Architecture](architecture.md) — how it all fits together
- [API](api.md) — package-level API helpers
- [Configuration](configuration.md) — environment variables and settings
- [FAQ](faq.md) — common questions and troubleshooting
- [Scenarios](scenarios/README.md) — end-to-end paths by use case
- [Guides](guide/README.md) — focused "how it works" notes
- [Glossary](glossary.md) — shared terminology
