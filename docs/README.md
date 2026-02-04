# AbstractFramework docs

This folder is the **gateway documentation** for the AbstractFramework ecosystem.
If you’re new, start with:

- [Getting started](getting-started.md) — pick a path and run something
- [Architecture](architecture.md) — how the stack fits together
- [Configuration](configuration.md) — common configuration knobs
- [FAQ](faq.md) — common questions and gotchas

## Find what you need

### I want…

- a unified LLM client library → **AbstractCore**: https://github.com/lpalbou/abstractcore
- a durable workflow runtime (pause/resume + ledger) → **AbstractRuntime**: https://github.com/lpalbou/abstractruntime
- ready-made agent patterns → **AbstractAgent**: https://github.com/lpalbou/abstractagent
- visual workflows + bundling → **AbstractFlow**: https://github.com/lpalbou/abstractflow
- a terminal app for agentic coding → **AbstractCode**: https://github.com/lpalbou/abstractcode
- a deployable run gateway (HTTP/SSE) → **AbstractGateway**: https://github.com/lpalbou/AbstractGateway
- a browser UI for the gateway → **AbstractObserver**: https://github.com/lpalbou/AbstractObserver
- voice I/O (TTS/STT) → **AbstractVoice**: https://github.com/lpalbou/abstractvoice
- generative vision outputs (images) → **AbstractVision**: https://github.com/lpalbou/abstractvision
- a semantics registry for KG assertions → **AbstractSemantics**: https://github.com/lpalbou/AbstractSemantics
- a temporal triple store for KG memory → **AbstractMemory**: https://github.com/lpalbou/AbstractMemory
- UI building blocks for thin clients → **AbstractUIC**: https://github.com/lpalbou/AbstractUIC

## Notes on what’s “shipped” where

- This repo (`abstractframework` on PyPI) is a **meta-package + index**. It installs bundles via extras and points you to the real projects.
- Most execution happens in **Python** (runtime/agents/gateway).
- The main browser UI is **AbstractObserver** (npm: `abstractobserver`). Other web apps in the ecosystem are typically run from source.
