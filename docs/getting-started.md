# Getting Started

Welcome! This guide gets you from zero to a working AbstractFramework setup in minutes.

AbstractFramework is modular — you can use a single package or compose several together. Let's find the right starting point for you.

## What Do You Want to Build?

| Your Goal | Start Here | What You'll Use |
|-----------|------------|-----------------|
| Call LLMs with a unified API | [Path 1](#path-1-llm-integration) | `abstractcore` |
| Build a local coding assistant | [Path 2](#path-2-terminal-agent) | `abstractcode` |
| Create durable workflows | [Path 3](#path-3-durable-workflows) | `abstractruntime` |
| Deploy a remote run gateway | [Path 4](#path-4-gateway--observer) | `abstractgateway` + `abstractobserver` |
| Use agent patterns (ReAct, etc.) | [Path 5](#path-5-agent-patterns) | `abstractagent` |
| Add voice I/O to your app | [Path 6](#path-6-voice-io) | `abstractvoice` |
| Generate images | [Path 7](#path-7-image-generation) | `abstractvision` |
| Build a knowledge graph | [Path 8](#path-8-knowledge-graph) | `abstractmemory` + `abstractsemantics` |
| macOS menu bar assistant | [Path 9](#path-9-macos-assistant) | `abstractassistant` |
| Visual workflow editor (browser) | [Path 10](#path-10-flow-editor) | `@abstractframework/flow` |
| Browser-based coding assistant | [Path 11](#path-11-code-web-ui) | `@abstractframework/code` |

## Prerequisites

**Python**: 3.10 or newer

**Node.js**: 18+ (only for browser UIs)

**An LLM Backend** (pick one):
- **Local (recommended)**: Ollama, LM Studio, vLLM, llama.cpp, LocalAI
- **Cloud**: OpenAI, Anthropic, Google, Groq, Together AI, Mistral

---

## Path 1: LLM Integration

The simplest path. Use AbstractCore as a unified LLM client.

### Install

```bash
pip install abstractcore
```

### Configure a Provider

**Local with Ollama** (free, no API key):

```bash
ollama serve
ollama pull qwen3:4b-instruct
export OLLAMA_HOST="http://localhost:11434"
```

**Or with LM Studio** (OpenAI-compatible):

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"
```

**Or with Cloud APIs**:

```bash
export OPENAI_API_KEY="sk-..."
# or
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Use It

```python
from abstractcore import create_llm

# Local
llm = create_llm("ollama", model="qwen3:4b-instruct")

# Or cloud
# llm = create_llm("openai", model="gpt-4o")
# llm = create_llm("anthropic", model="claude-3-5-sonnet-latest")

response = llm.generate("What is durable execution?")
print(response.content)
```

**Next**: Add [tool calling](https://github.com/lpalbou/abstractcore/blob/main/docs/tools.md) or [structured output](https://github.com/lpalbou/abstractcore/blob/main/docs/structured-output.md).

---

## Path 2: Terminal Agent

Get a durable coding assistant running in your terminal.

### Install

```bash
pip install abstractcode
```

### Start Ollama

```bash
ollama serve
ollama pull qwen3:1.7b-q4_K_M
export OLLAMA_HOST="http://localhost:11434"
```

### Run

```bash
abstractcode --provider ollama --model qwen3:1.7b-q4_K_M
```

### Inside AbstractCode

- Type `/help` for all commands
- Mention files with `@path/to/file` in your prompts
- Tool execution requires approval by default (toggle with `/auto-accept`)
- Sessions are durable — close and reopen, your context is preserved

**Next**: See [AbstractCode docs](https://github.com/lpalbou/abstractcode/blob/main/docs/getting-started.md).

---

## Path 3: Durable Workflows

Build workflows that survive crashes and can pause/resume.

### Install

```bash
pip install abstractruntime
# Add LLM integration:
pip install "abstractruntime[abstractcore]"
```

### Key Concepts

- **Run**: A durable workflow instance
- **Ledger**: Append-only log of everything that happened
- **Effect**: A request for something to happen (LLM call, tool call, timer)
- **Wait**: An explicit pause point (state is checkpointed)

### Example

```python
from abstractruntime import (
    Effect, EffectType, Runtime, StepPlan, WorkflowSpec,
    InMemoryLedgerStore, InMemoryRunStore
)

# Define workflow nodes
def ask(run, ctx):
    return StepPlan(
        node_id="ask",
        effect=Effect(
            type=EffectType.ASK_USER,
            payload={"prompt": "What would you like to do?"},
            result_key="user_input",
        ),
        next_node="done",
    )

def done(run, ctx):
    return StepPlan(node_id="done", complete_output={"answer": run.vars.get("user_input")})

# Create workflow and runtime
wf = WorkflowSpec(workflow_id="demo", entry_node="ask", nodes={"ask": ask, "done": done})
rt = Runtime(run_store=InMemoryRunStore(), ledger_store=InMemoryLedgerStore())

# Start and tick
run_id = rt.start(workflow=wf)
state = rt.tick(workflow=wf, run_id=run_id)
print(state.status.value)  # "waiting"

# Resume with user input
state = rt.resume(workflow=wf, run_id=run_id, wait_key=state.waiting.wait_key, payload={"text": "Hello!"})
print(state.status.value)  # "completed"
```

**Next**: See [AbstractRuntime docs](https://github.com/lpalbou/abstractruntime/blob/main/docs/getting-started.md).

---

## Path 4: Gateway + Observer

Deploy a remote control plane and observe runs in your browser.

### Install

```bash
pip install "abstractgateway[http]"
# If your workflows use LLM/tools:
pip install "abstractruntime[abstractcore]>=0.4.0"
```

### Configure

```bash
# Required: authentication token
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

# Required: CORS for browser access
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"

# Workflow source
export ABSTRACTGATEWAY_WORKFLOW_SOURCE=bundle
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/your/bundles"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"
```

### Start the Gateway

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Verify it's running:

```bash
curl -sS "http://127.0.0.1:8080/api/health"
```

### Start the Observer

In another terminal:

```bash
npx @abstractframework/observer
```

Open http://localhost:3001 in your browser:
1. Set **Gateway URL** to `http://127.0.0.1:8080`
2. Paste your **Auth Token**
3. Click **Connect**

You're now observing your runs.

**Next**: See [AbstractGateway docs](https://github.com/lpalbou/abstractgateway/blob/main/docs/getting-started.md).

---

## Path 5: Agent Patterns

Use ready-made agent loops (ReAct, CodeAct, MemAct).

### Install

```bash
pip install abstractagent
```

### Example: ReAct Agent

```python
from abstractagent import create_react_agent

agent = create_react_agent(provider="ollama", model="qwen3:4b-instruct")
agent.start("List the files in the current directory")
state = agent.run_to_completion()
print(state.output["answer"])
```

**Next**: See [AbstractAgent docs](https://github.com/lpalbou/abstractagent/blob/main/docs/getting-started.md).

---

## Path 6: Voice I/O

Add speech-to-text and text-to-speech to your app.

### Install

```bash
pip install abstractvoice
```

### Prefetch Models (Recommended)

AbstractVoice is offline-first — prefetch models explicitly:

```bash
abstractvoice-prefetch --stt small
abstractvoice-prefetch --piper en
```

### Use It

```python
from abstractvoice import VoiceManager

vm = VoiceManager()

# Text-to-speech
vm.speak("Hello! This is AbstractVoice.")

# Speech-to-text (from file)
text = vm.transcribe_file("audio.wav")
print(text)
```

### Interactive REPL

```bash
abstractvoice --verbose
```

**Next**: See [AbstractVoice docs](https://github.com/lpalbou/abstractvoice/blob/main/docs/getting-started.md).

---

## Path 7: Image Generation

Generate images with text-to-image or image-to-image.

### Install

```bash
pip install abstractvision
```

### Use It

```python
from abstractvision import VisionManager, LocalAssetStore
from abstractvision.backends import OpenAICompatibleBackendConfig, OpenAICompatibleVisionBackend

# Configure backend (e.g., local server)
backend = OpenAICompatibleVisionBackend(
    config=OpenAICompatibleBackendConfig(
        base_url="http://localhost:1234/v1",
        api_key="local",
    )
)

vm = VisionManager(backend=backend, store=LocalAssetStore())

# Generate image
result = vm.generate_image("a watercolor painting of a lighthouse")
print(result)  # {"$artifact": "...", "content_type": "image/png", ...}
```

### CLI

```bash
abstractvision t2i --base-url http://localhost:1234/v1 "a photo of a red fox"
```

**Next**: See [AbstractVision docs](https://github.com/lpalbou/abstractvision/blob/main/docs/getting-started.md).

---

## Path 8: Knowledge Graph

Build a temporal, provenance-aware knowledge graph.

### Install

```bash
pip install abstractmemory
pip install abstractsemantics  # Schema registry

# Optional: persistent storage + vector search
pip install "abstractmemory[lancedb]"
```

### Use It

```python
from abstractmemory import InMemoryTripleStore, TripleAssertion, TripleQuery

store = InMemoryTripleStore()

# Add knowledge
store.add([
    TripleAssertion(
        subject="Paris",
        predicate="is_capital_of",
        object="France",
        scope="session",
        owner_id="sess-1",
    )
])

# Query
hits = store.query(TripleQuery(subject="paris", scope="session", owner_id="sess-1"))
print(hits[0].object)  # "france"
```

**Next**: See [AbstractMemory docs](https://github.com/lpalbou/abstractmemory/blob/main/docs/getting-started.md).

---

## Path 9: macOS Assistant

Get a menu bar AI assistant with optional voice.

### Install

```bash
pip install abstractassistant
# Or with voice support:
pip install "abstractassistant[full]"
```

### Run

```bash
# Tray mode (menu bar)
assistant tray

# Or single command
assistant run --provider ollama --model qwen3:4b-instruct --prompt "Summarize my changes"
```

**Next**: See [AbstractAssistant docs](https://github.com/lpalbou/abstractassistant/blob/main/docs/getting-started.md).

---

## Path 10: Flow Editor

Build and edit visual workflows in your browser.

### Run

```bash
npx @abstractframework/flow
```

Open http://localhost:3003 in your browser.

### What You Can Do

- Drag-and-drop workflow nodes (LLM, tools, conditionals, loops)
- Connect nodes visually
- Test workflows in real-time
- Export as `.flow` bundles for deployment

**Next**: See [AbstractFlow docs](https://github.com/lpalbou/abstractflow/blob/main/docs/web-editor.md).

---

## Path 11: Code Web UI

Run the browser-based coding assistant.

### Prerequisites

You need a running AbstractGateway (see [Path 4](#path-4-gateway--observer)).

### Run

```bash
npx @abstractframework/code
```

Open http://localhost:3002 in your browser. Configure the gateway URL in the UI settings, then start coding.

**Next**: See [AbstractCode web docs](https://github.com/lpalbou/abstractcode/blob/main/docs/web.md).

---

## What's Next?

Now that you have something running:

- **[Architecture](architecture.md)** — Understand how the pieces fit together
- **[Configuration](configuration.md)** — All the environment variables and settings
- **[FAQ](faq.md)** — Common questions and troubleshooting

Each package also has detailed documentation:
- Every repo has `docs/getting-started.md`, `docs/architecture.md`, and more
- Check the repo README for the quickest overview
