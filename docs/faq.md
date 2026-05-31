# FAQ

## What is AbstractFramework?

An open-source ecosystem for building **durable, observable, multimodal AI systems**.

Two things share the name:

- **The ecosystem**: composable packages (Core, Runtime, Agent, Gateway, Flow, Observer, apps, modality plugins).
- **This repo / meta-package**: `abstractframework` is a pinned install profile + cross-package docs.

If you're looking for the main SDK, that's **AbstractCore**. If you need durable orchestration, that's **AbstractGateway**.

---

## Where should I start?

- **AbstractCore** — when you want direct LLM/tool/media integration with a clean, provider-agnostic API (Python SDK **or** OpenAI-compatible `/v1`).
- **AbstractGateway** — when you need durability, orchestration, scheduling, or language-agnostic access via HTTP/SSE routes.

Most teams start with Core (SDK or `/v1`), then introduce Gateway when workflows become long-running, scheduled, or shared across clients. See **[Getting Started](getting-started.md)**.

---

## Do I need to install the whole stack?

No.

| Goal | Install |
|---|---|
| Smallest useful (LLM SDK only) | `pip install abstractcore` |
| Gateway-first deployment | `pip install abstractgateway` |
| Everything at compatible versions | `pip install abstractframework` |

See [Install AbstractFramework](install.md) for the Light / Apple / GPU chooser. Light is
remote-first, not reduced-functionality: multimodal and embeddings still work through remote or
local endpoint providers.

---

## Can I run everything offline with local models?

Yes. The core execution stack works fully offline with local model servers (Ollama, LM Studio, vLLM, llama.cpp, LocalAI). You need internet only to download models or use cloud APIs.

Multimodal plugins also work offline:

- **AbstractVoice**: Piper TTS (ONNX) + faster-whisper STT — prefetch once, run offline.
- **AbstractVision**: local Diffusers models or GGUF via stable-diffusion.cpp.
- **AbstractMusic**: local ACE-Step inference.

---

## What agent patterns are available?

AbstractAgent ships three patterns, all built on the durable Runtime kernel:

| Pattern | How it works |
|---|---|
| **ReAct** | Tool-first reasoning: observe → think → choose tool → execute → reflect |
| **CodeAct** | Code execution: generate Python, run it, observe output |
| **MemAct** | Memory-enhanced: reads/writes a knowledge graph during the loop |

Agents can run standalone or as nodes inside an AbstractFlow workflow.

---

## How does AbstractFramework compare to other frameworks?

### vs direct provider SDKs (OpenAI, Anthropic)

Direct SDKs are fine when you only use one provider and don't need durable orchestration.

AbstractCore adds value when you need: provider portability (local ↔ cloud), consistent tool/structured-output behavior across backends, media policies, modality plugins, or a configuration layer that doesn't leak into app code.

### vs LangChain / LlamaIndex / PydanticAI

Most agent libraries are **in-process orchestration**. AbstractFramework is a **durable orchestration stack**.

**Where AbstractFramework is stronger**: durability and pause/resume as primitives, replay-first observability, portable `.flow` bundles that run across clients.

**Where others are stronger**: large connector/RAG ecosystems, minimal boilerplate for simple use cases, broader community examples.

### vs Temporal / Step Functions / job schedulers

AbstractGateway is architecturally closer to these, but specialized for LLM/tool loops: tool approval waits, AI-oriented artifacts, and replay-first thin-client UIs over HTTP/SSE.

### Can I use AbstractFramework with LangChain/LlamaIndex?

Yes. Use AbstractFramework for orchestration and durability; integrate other libraries as tools or subflows:

- Use LlamaIndex retrievers as tools within an AbstractAgent
- Wrap LangChain chains as tool executors
- Let AbstractRuntime handle durability while external libraries handle specific capabilities

---

## What is a ".flow bundle" and why does it matter?

A `.flow` file is the portable distribution unit for workflows. It packages:

- A VisualFlow workflow graph
- Metadata (entry points, interfaces)
- Optional subflows and assets

Deploy a bundle to a gateway and any gateway-backed client can discover and run it.

---

## How do I author complex agentic orchestration?

1. Run a gateway (for durability + discovery).
2. Open the Flow Editor (`npx @abstractframework/flow`) and connect to the gateway.
3. Build a workflow: LLM steps, tool steps, agent nodes, branching, loops, subflows.
4. Export to `.flow`.
5. Copy into `ABSTRACTGATEWAY_FLOWS_DIR` to deploy.

To make it reusable across clients, implement an **interface contract** (for example `abstractcode.agent.v1`).

See **[Getting Started](getting-started.md)** → "Author orchestration with AbstractFlow".

---

## How do I monitor and schedule agentic work?

- **Monitoring**: use **AbstractObserver** — replay ledger, stream live execution, inspect errors, control runs.
- **Scheduling**: durable schedules are owned by the **gateway** (survive restarts). Create them from a client UI or via the gateway scheduling API.

See **[Getting Started](getting-started.md)** → "Gateway-first" section.

---

## How does multimodality work?

AbstractCore supports modalities via **capability plugins** (installed separately, discovered via entry points):

| Plugin | Capability |
|---|---|
| `abstractvoice` | `llm.voice` (TTS) / `llm.audio` (STT) |
| `abstractvision` | `llm.vision` (image generation) |
| `abstractmusic` | `llm.music` (text-to-music) |

Plugins are configured on the machine that actually executes (local app host or gateway host). Don't install a plugin; Core stays lightweight.

---

## Where is data stored?

- **Gateway**: `ABSTRACTGATEWAY_DATA_DIR` is the durability root (runs, ledger, artifacts, schedules).
- **Core config**: `~/.abstractcore/config/` (persisted by `abstractcore --config`).
- **Local apps**: typically `~/.abstractcode/`, `~/.abstractassistant/`, etc.

If you care about auditability and long-lived workflows, back up the gateway data directory.

---

## Troubleshooting

### Provider calls fail

- Verify provider environment variables (see **[Configuration](configuration.md)**).
- For local backends, make sure the server is running.
- Run `abstractcore --status` to check persisted config.

### Observer can't connect to the gateway

- Verify the gateway URL and auth token match.
- Ensure `ABSTRACTGATEWAY_ALLOWED_ORIGINS` includes the Observer origin (for local dev: `http://localhost:*`).
- Confirm the gateway is reachable: `curl http://127.0.0.1:8080/api/health`.

### Voice models not found

Prefetch explicitly (offline-first design):

```bash
abstractvoice-prefetch --stt small --piper en
```
