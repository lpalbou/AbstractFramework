# FAQ

## What is AbstractFramework?

AbstractFramework is an ecosystem of packages for building **durable, observable** agentic systems:
- **AbstractRuntime** provides durable execution (pause/resume) and an append-only **ledger**
- **AbstractCore** provides provider-agnostic LLM/tool integration (tools, structured output, media, optional server)
- **AbstractAgent** and **AbstractFlow** compose those peers into agent loops and portable workflows
- **AbstractGateway** + **AbstractObserver** provide a deployable control plane + browser UI (replay-first)

Start with [Getting started](getting-started.md).

## Do I have to install the whole stack?

No. Most users should install only what they need:

- LLM integration only → `abstractcore`
- Durable pause/resume workflows → `abstractruntime` (plus `abstractruntime[abstractcore]` if you need LLM/tool effects)
- Agent patterns → `abstractagent`
- VisualFlow workflows → `abstractflow`
- Terminal app → `abstractcode`
- Server control plane → `abstractgateway[http]`
- Browser UI → `abstractobserver` (Node)

The `abstractframework` PyPI package is a convenience **meta-package** that bundles common installs via extras.

## What should I start with?

It depends on your goal:

- “I’m building a Python app and just need LLMs/tools.” → AbstractCore
- “I need workflows that can pause and resume tomorrow.” → AbstractRuntime
- “I want an off-the-shelf agent loop (ReAct/CodeAct/MemAct).” → AbstractAgent
- “I want a usable terminal UI today.” → AbstractCode
- “I want remote runs + a browser UI.” → AbstractGateway + AbstractObserver

## What’s the difference between AbstractRuntime, AbstractAgent, and AbstractFlow?

- **AbstractRuntime**: the durable execution substrate (runs, effects, waits, ledger, stores).
- **AbstractAgent**: agent patterns implemented as runtime workflows (ReAct/CodeAct/MemAct).
- **AbstractFlow**: portable workflows (VisualFlow JSON) + authoring/execution helpers and a reference editor.

## What is a “run”? What is the “ledger”?

- A **run** is a durable workflow instance (`run_id`).
- The **ledger** is an append-only list of step records for a run. It’s the source of truth for replay and UI rendering.

Gateway-first UIs (like AbstractObserver) render by replaying the ledger and optionally streaming new steps via SSE.

## Why do tools require approval / why aren’t tools executed automatically?

Durability and safety:

- tool **schemas/specs** are durable (stored in state/ledger)
- tool **callables** are not durable (they live in the host process)

So the runtime emits a durable `TOOL_CALLS` wait, then the host:
1) prompts for approval (default),
2) executes tools (local or remote worker),
3) resumes the run with JSON tool results.

This makes tool execution auditable and restart-safe.

## Do I need AbstractGateway?

Not for local-only usage.

Use a gateway when you want:
- remote execution (server owns durability)
- multiple clients/UIs attached to the same runs
- a durable command inbox (pause/resume/cancel/schedule)
- replay-first observability over HTTP/SSE

Local hosts like AbstractCode and AbstractAssistant can run everything in one process without a gateway.

## Can I run everything with local models (offline)?

You can run the **core execution** stack locally with local model servers (Ollama, LM Studio, vLLM, etc.).
Some features may still require internet if you choose to download models or use cloud APIs.

For local setups, see [Configuration](configuration.md) (Ollama + OpenAI-compatible servers).

## Which browser UI should I use?

If you’re running a gateway, start with:

- **AbstractObserver** (npm: `abstractobserver`): a gateway-only observability and control UI.

There are additional reference web apps in the ecosystem (Flow editor, Code web host), but they are typically run from source and may have extra workspace assumptions.

## Where is data stored?

It depends on the host:

- **AbstractGateway**: everything is rooted at `ABSTRACTGATEWAY_DATA_DIR` (file or SQLite backend + artifacts).
- **AbstractCode**: defaults to `~/.abstractcode/` (state + durable stores).
- **AbstractAssistant**: defaults to `~/.abstractassistant/` (session snapshot + durable runtime stores).

See each project’s docs for exact layouts.

## Is the ecosystem “stable”?

Different components have different maturity:
- AbstractCore and AbstractRuntime are designed as reusable foundations.
- Some hosts and UIs are explicitly pre-alpha/alpha; expect UX/API iteration.

For the authoritative status, see each project’s README and changelog.
