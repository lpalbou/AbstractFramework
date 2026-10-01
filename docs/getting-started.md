# Getting started

This guide helps you build a correct mental model quickly, then run something end-to-end.

> **Write once. Generate everything.** Durable, observable, multimodal AI systems — one unified interface, any provider, any model, local or cloud.

## Install

- **Mac, no Terminal:** download and double-click
  [AbstractFramework-Installer.pkg](https://github.com/lpalbou/AbstractFramework/releases/latest/download/AbstractFramework-Installer.pkg).
  The first time, allow it with **Open Anyway** in **System Settings > Privacy & Security**: the
  package is not signed with an Apple Developer ID (see [Install](install.md#install-on-a-mac)).
- **macOS / Linux, one line** in Terminal:

  ```bash
  curl -LsSf https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.sh | sh
  ```

- **Windows 10 22H2+ / 11** (PowerShell):

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/lpalbou/AbstractFramework/main/scripts/install.ps1 | iex"
  ```

To upgrade later, run the same line again, or, on macOS and Linux, press **Update** in a
console or the menu-bar icon (it runs the same installer); see [Upgrade](install.md#upgrade).

The installer puts uv, Python 3.12 and the pinned gateway with local voice (Supertonic and Whisper) in
your user account (no admin password), asks whether to start it at login (Enter = yes; an
unattended install leaves it off and its summary says how to turn it on), starts it on
`127.0.0.1:8080`, and opens its console in your browser already signed in. The console's first-run
guide sets up a local engine or a cloud key and a default model (the **Models** tab lists the
models that fit your machine and downloads them), and its **Apps** page installs and opens the
browser apps, which the gateway serves at `http://127.0.0.1:8080/apps/<app>/`. The **Setup** button
at the bottom of the sidebar runs the guide again; it keeps your choices unless you replace them. The
console's sidebar groups its pages: **Accounts**; **Work** (Workflows, Runtimes, Apps); **Models**
(Providers, Models, Engines, Multimodal); **System** (Resources, Sandbox, Network). The installer also
builds the terminal console, `abstractgateway-console`, which offers the same guide on a server
without a browser (its **Network** screen, `N`, decides who can reach the gateway); over SSH the
installer offers to open it at the end, and its summary prints the command (see
[Headless or remote machine](install.md#headless-or-remote-machine)).

The commands it puts on PATH (in `~/.local/bin`; open a new terminal), each listed in its summary:

- `abstractgateway`: the gateway itself (`serve`, `service`, `network`, `models`, `engines`).
- `abstractgateway-config`: the gateway's admin and configuration command: `status`, `claim-url`
  (a new one-time console sign-in link), `set-default` (which model each capability uses),
  `get` / `set` (runtime settings), `bootstrap-admin`.
- `abstractgateway-console`: the terminal console; the summary prints it ready to paste, with
  `--gateway-url` and `--token`.
- `abstractcode`: AbstractCode's terminal client. Sign it in once with
  `abstractcode login --token <admin token>` (the summary prints this line with your token), then
  run `abstractcode`; or, on the gateway's computer, `abstractgateway apps tui-command code` opens
  it signed in without a token.
- AbstractCore's commands: `abstractcore` (also `abstractcore-config`: setup wizard, models,
  engines, `serve`), `abstractcore-chat` (a chat in the terminal), `abstractcore-endpoint` (a
  single-model `/v1` server), and its apps `summarizer` (summarize a document), `extractor`
  (entities and relationships as a knowledge graph), `judge` (LLM-as-a-judge scoring), `intent`
  (intent analysis) and `deepsearch` (a research agent that writes a sourced report), each also as
  `abstractcore-<app>`.
- `abstractvoice` (a spoken chat, `tts`, `web`) and `abstractvoice-prefetch` (download voice
  models), `abstractvision` (generate or edit images and video: `t2i`, `i2i`, `t2v`, …) and
  `abstractmusic` (`t2m`: text to music).

A package puts all of the commands it declares on PATH (uv cannot pick a subset). `--no-console`,
`--no-code-cli` and `--no-core-cli` leave them out, and a package whose command name another
program already has is left out with a warning naming that file; see
[Commands you get](install.md#commands-you-get). Then
continue with [Monitor runs](#4-monitor-runs-with-abstractobserver) or
[AbstractFlow](#author-orchestration-with-abstractflow). Step by step, what to do when something
fails, and how to remove it: [Install](install.md); fixes for common problems:
[Troubleshooting](troubleshooting.md). The sections below cover manual installs for library and
developer use.

---

AbstractFramework is a **stack**:

| Layer | Package | Role |
|---|---|---|
| SDK | **AbstractCore** | Provider/model abstraction, tools, structured output, media, embeddings |
| Agent patterns | **AbstractAgent** | Ready-made loops: ReAct (tool-first), CodeAct (code execution), MemAct (memory-enhanced) |
| Workflow authoring | **AbstractFlow** | Visual editor, portable `.flow` bundles, subflows |
| Durable kernel | **AbstractRuntime** | Runs, effects, waits, ledger, artifacts |
| Control plane | **AbstractGateway** | Persistence, scheduling, bundle discovery, SSE streaming |
| Operations | **AbstractObserver** | Browser UI to monitor, control, and schedule runs |

**Rule of thumb**: start with **Core** when you want a lightweight LLM library (SDK or `/v1`) for scripts/notebooks/apps; add **Gateway** when you need persistent runs, scheduling, and multi-client continuity.

> **Prerequisites**: Python 3.10–3.13 for the manual installs below. Node.js 18+ (only for browser UIs). An LLM backend — local (Ollama, LM Studio, vLLM, llama.cpp) or cloud (OpenAI, Anthropic, etc.).

---

## Choose your entry point

| If you are… | Start with | Why |
|---|---|---|
| Calling LLMs/tools/media (SDK or OpenAI-compatible `/v1`) | **AbstractCore** | Lightweight, smallest surface area, fastest feedback loop |
| Building persistent agents/workflows (durable runs) | **AbstractGateway** + **AbstractFlow** | Durability, scheduling, bundle discovery, ledger replay/streaming |

You can also install the entire pinned ecosystem in one command:

```bash
pip install abstractframework
```

For the full Light / Apple / GPU profile chooser, see [Install AbstractFramework](install.md).

---

## Core-first: integrate via AbstractCore (SDK or `/v1`)

### 1. Install

```bash
pip install abstractcore
```

This light install runs every remote provider (OpenAI, Anthropic, OpenRouter, Ollama, LM Studio and
any OpenAI-compatible endpoint). For local engines, install `"abstractcore[apple]"` on an Apple
silicon Mac or `"abstractcore[gpu]"` on an NVIDIA or AMD machine instead. These are AbstractCore's
three install settings.

### 2. Configure a provider

**Local (Ollama)** — free, no API key:

```bash
ollama serve
ollama pull qwen3:4b-instruct
export OLLAMA_HOST="http://localhost:11434"
```

**OpenAI-compatible** (LM Studio, vLLM, LocalAI, llama.cpp):

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234/v1"
export OPENAI_API_KEY="local"
```

**Cloud APIs**:

```bash
abstractcore --set-api-key openai <key>
abstractcore --set-api-key anthropic <key>
```

The keys are saved in AbstractCore's configuration (also from `abstractcore --config`) and win
over `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in the environment.

**Or use a console.** `abstractcore serve` starts the server on `127.0.0.1:8000` and prints a
one-time link to its web console, where the **Engines** tab detects and installs local engines
(Ollama, LM Studio, MLX, llama.cpp) and the **Models** tab downloads a model that fits this machine.
The same actions exist on the command line and in the terminal console:

```bash
abstractcore serve                      # open the printed http://127.0.0.1:8000/console#claim=… link
abstractcore engines status             # which local engines are installed and running
abstractcore models catalog             # models, with a fit verdict for this machine
abstractcore models download ollama qwen3:4b-instruct
cargo install abstractcore-console      # terminal console (Rust 1.87+)
```

The interactive terminal wizard persists config to `~/.abstractcore/config/`:

```bash
abstractcore --config
abstractcore --status
```

### 3. Call the model

```python
from abstractcore import create_llm

llm = create_llm("ollama", model="qwen3:4b-instruct")
resp = llm.generate("Explain durable execution in 3 bullets.")
print(resp.content)
```

### What else you can do with Core

```python
# Tool calling
resp = llm.generate("What's the weather?", tools=[get_weather])

# Structured output (Pydantic)
report = llm.generate("Analyze this.", response_model=Report)

# Media input (images, audio, video, documents)
resp = llm.generate("Describe this image.", media=["photo.jpg"])

# Embeddings
vectors = llm.embed(["first document", "second document"])

# Streaming
for chunk in llm.generate("Write a poem.", stream=True):
    print(chunk.content or "", end="", flush=True)
```

---

## Gateway-first: durable runs + monitoring + scheduling

### 1. Install

```bash
pip install abstractgateway
```

### 2. Configure (optional)

With no configuration, `abstractgateway serve` binds `127.0.0.1:8080`, enables user auth, and keeps
its data in the per-user data folder (macOS `~/Library/Application Support/AbstractGateway`, Linux
`~/.local/share/abstractgateway`, Windows `%LOCALAPPDATA%\AbstractGateway`). Choose another data
folder with `serve --data-dir <folder>`. Browser apps on `http://localhost:*` and
`http://127.0.0.1:*` may always call it; allow another origin with
`abstractgateway network set --allowed-origins https://ui.example.com`.

The gateway serves its shipped workflows (basic-agent, coding-agent, deep-research, co-scientist,
and more). To serve your own bundle registry instead, start it with `ABSTRACTGATEWAY_FLOWS_DIR`
pointing at your bundle folder.

### 3. Start the gateway

```bash
abstractgateway serve
```

On first local start, Gateway creates `default/admin`, keeps its token in
`<data dir>/auth/bootstrap-admin-token` (readable by you only), and prints a one-time link:
`First run: open http://127.0.0.1:8080/console#claim=…`. Open it to sign in to the web console and
its first-run guide (engines, default model, apps); `abstractgateway claim --open` mints a new
link. Use the `admin` token from the file to sign in to AbstractFlow, AbstractCode Web or
AbstractObserver. `ABSTRACTGATEWAY_AUTH_TOKEN` is only the legacy server/operator bearer-token
path; it does not sign in browsers.

To start the gateway at login, turn on **Start at login** in the console (web: the Gateway
section of **Resources**; terminal: `F3`), or run `abstractgateway service install --port 8080`. The login item
listens where the gateway's Network setting says (this computer only until you change it; see
[Network setting](install.md#network-setting-who-can-reach-the-gateway)).

Verify:

```bash
curl -sS "http://127.0.0.1:8080/api/health"
```

### 4. Monitor runs with AbstractObserver

Open the gateway console's **Apps** page and click **Install**, then **Open** next to Observer: it
opens at `http://127.0.0.1:8080/apps/observer/`, already signed in. To run it on its own instead,
in another terminal:

```bash
npx @abstractframework/observer --gateway-url http://127.0.0.1:8080
```

Open the address it prints and sign in with a gateway user and that user's token; Observer
exchanges the token for a browser session and does not persist the token in browser settings.

AbstractObserver is replay-first: it renders runs by replaying the ledger, then streams new steps live via SSE.

The console and every browser app work on phones, tablets and any window size. To open them from
another device, set the gateway's Network setting to `lan` (`abstractgateway network set lan`, then
`abstractgateway network restart --token <admin token>`) and open the same `/console` and
`/apps/<app>/` paths on the gateway's address; see [Phones and tablets](guide/deployment-iphone.md).
With Tailscale, `tailscale serve --bg http://127.0.0.1:<port>` on the gateway's computer gives an
https address (`https://<host>.<tailnet>.ts.net/`) and the Network setting can stay `localhost`;
voice and camera in the browser need https
([Reached through Tailscale](guide/deployment-iphone.md#reached-through-tailscale-https)).

### 5. Automate recurring work

An automation runs a workflow on a fixed interval and keeps every run as a conversation. Create
one from the Observer (**Launch → Automate**), from an Assistant conversation (**Schedule this
conversation…**), or through the gateway API on a gateway that advertises the Automations API.
`<admin token>` is the gateway's admin token: `abstractgateway serve` prints it when it starts
(`Gateway admin token: …`), and the installer's summary shows it in its `--token` lines. Paste the
value in place of `<admin token>`.

```bash
curl -X POST "http://127.0.0.1:8080/api/gateway/automations" \
  -H "Authorization: Bearer <admin token>" \
  -H "Content-Type: application/json" \
  -d '{"request_id":"memory-watch-1","title":"Memory every 2 minutes",
       "target":{"flow_id":"@default","interface":"abstractcode.agent.v1",
                 "input_data":{"prompt":"Report the memory usage of this computer in one line."}},
       "trigger":{"source_id":"schedule","source_version":1,"config":{"every":"2m"}},
       "context":{"mode":"independent"}}'
```

The automation survives restarts, runs each tick once, and stays quiet unless its workflow asks for
attention. See [Automations](automations.md) for the mental model, worked examples, management
and limits.

To run an automation when an email arrives, or to get its results by email, first connect your own
mailbox on your account page in the gateway console (**Accounts**; an administrator uses **Email**
on their own row), or `@` on the Accounts screen of the terminal console. The Assistant, the Observer and AbstractCode's browser client then offer **When an email
arrives**, **Email me the result** and the recipients the automation may email without asking. See
[Email automations](automations.md#email-automations). The same account gives you sign-in by email,
and your agents get the email tools only when you switch **Agent email tools** on
([Email integration](guide/email-integration.md)).

---

## Author orchestration with AbstractFlow

The ecosystem's distribution unit is a **workflow bundle** (`.flow` file): a VisualFlow graph + metadata. Gateways discover bundles and expose them to all clients.

You do not have to start from an empty registry. A packaged Gateway already
serves a set of ready workflows — a verify-gated coding agent, `deep-research`,
and `co-scientist` among them — listed in
[AbstractGateway's shipped workflows](https://github.com/lpalbou/AbstractGateway/blob/main/docs/shipped-workflows.md).
Author your own when you need something they do not cover.

### 1. Open the Flow Editor

With the gateway running, open the console's **Apps** page and **Open** the Flow Editor (it opens
at `http://127.0.0.1:8080/apps/flow/`, signed in), or run it on its own:

```bash
npx @abstractframework/flow --gateway-url http://127.0.0.1:8080
```

Open the address it prints and sign in with a gateway user and that user's token; Flow keeps an
opaque browser session instead of storing the token.

### 2. Build a workflow

- **On Flow Start** → takes input (prompt, provider, model, …)
- LLM steps, tool steps, branching, loops, subflows
- **On Flow End** → returns output (response, success, metadata)

To make it reusable across clients, implement an **interface contract** (for example `abstractcode.agent.v1` — a standard chat-like agent I/O contract).

### 3. Export and deploy

```bash
mkdir -p "$PWD/bundles"
cp my-agent.flow "$PWD/bundles/"
```

Start or restart Gateway with `ABSTRACTGATEWAY_FLOWS_DIR="$PWD/bundles"` when
you want that directory to be the active custom bundle registry. You can also
publish bundles through the Gateway API from AbstractFlow.

### 4. Run from any client

Once deployed, the bundle appears in:

- **AbstractObserver** — workflow picker / run launcher
- **AbstractCode** (terminal and browser) and **AbstractAssistant** — workflow pickers, for
  workflows that implement their agent interface
- **Your own client** — via the gateway bundle discovery API

An admin can also make it the gateway's default agent workflow, which every client that follows
the gateway default then runs at its next turn. See [Agent sessions](agent-sessions.md#the-default-agent-workflow).

---

## Example apps

### AbstractCode (terminal and browser)

A coding client for durable agentic sessions on the gateway you started above. The installer
already built the Rust terminal client, `abstractcode`; sign it in once with
`abstractcode login --token <admin token>` (the installer summary prints the line with your token),
or open it signed in on the gateway's computer with `abstractgateway apps tui-command code` (see
[Commands you get](install.md#commands-you-get)). Otherwise install it from crates.io (or download a prebuilt binary from the
[AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases)), or run the
browser client (the gateway console's **Apps** page opens it at `/apps/code/`, or run it with
`npx`):

```bash
cargo install abstractcode
abstractcode doctor              # check the gateway connection
abstractcode                     # finds the local gateway; --gateway-url <url> for another one

npx @abstractframework/code --gateway-url http://127.0.0.1:8080   # the browser client on its own
```

Sessions are durable: close and reopen, your full context is preserved. Each turn runs the
gateway's default agent workflow unless you pick another (`/workflow`, `--workflow`). `/files`
(the **Files** tab in the browser) shows the run's workspace on the gateway host, `/stream`
chooses live replies, and `/about` shows the versions in use. `/automations` lists and manages the
gateway's automations and `/schedule` creates one (the browser client has an **Automations**
section); see [Automations](automations.md). Type `/help` for commands.

### AbstractAssistant (macOS tray)

A desktop app on the gateway's computer. The simplest start is **Open** on its card in the
gateway console: it starts the Assistant already signed in as you. To install and start it
yourself:

```bash
pip install abstractassistant
assistant                                   # the menu-bar app
assistant run --prompt "Summarize today's news"   # one turn in the terminal
```

Each turn runs the gateway's default workflow for the Assistant, or the workflow you pick in
Settings → Models → **Workflow**. See [Agent sessions](agent-sessions.md#opening-the-assistant-from-the-gateway).

---

## Next steps

- **[Agent sessions](agent-sessions.md)** — default agent workflow, workspace, skills, live replies
- **[Architecture](architecture.md)** — the layered model (Core / Runtime / Agent / Gateway / Flow / Observer)
- **[Configuration](configuration.md)** — where defaults live and how to configure them
- **[Glossary](glossary.md)** — shared terms (run, ledger, effect, wait, bundle, interface contract)
- **[API](api.md)** — the `abstractframework` helpers, `doctor` and `manifest` commands
- **[FAQ](faq.md)** — comparisons, offline operation, limits
- **[Troubleshooting](troubleshooting.md)** — symptoms and fixes
- **[Workspace scripts](workspace-scripts.md)** — work from source: clone, build and sync every package in dependency order
