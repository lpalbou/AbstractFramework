# Scenario: Offline Coding Assistant (Terminal)

Goal: run a durable coding assistant on one machine, offline-first, with Ollama (or an
OpenAI-compatible local server) as the model backend.

AbstractCode is a client of AbstractGateway: the gateway runs the coding agent on your machine and
the terminal client connects to it over HTTP/SSE. Nothing leaves the machine when the model server
is local too.

## Prereqs

- Python 3.10+ (for the gateway)
- Rust 1.87+ (for `cargo install abstractcode`), or a prebuilt binary from the
  [AbstractCode GitHub release](https://github.com/lpalbou/AbstractCode/releases)
- An LLM backend:
  - Ollama (recommended)
  - LM Studio / vLLM / LocalAI (OpenAI-compatible)

## Step 1: Install

```bash
pip install abstractframework     # pinned stack, includes abstractgateway
cargo install abstractcode        # terminal client
```

`pip install abstractgateway` is enough if you only want the gateway.

## Step 2: Start a local model

### Ollama

```bash
ollama serve
ollama pull qwen3:4b-instruct
export OLLAMA_HOST="http://localhost:11434"
```

Pick it as the default text model:

```bash
abstractcore --config
```

## Step 3: Start the gateway on loopback

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

The gateway ships the `coding-agent:coder` workflow that AbstractCode uses by default.

## Step 4: Run AbstractCode

```bash
abstractcode doctor               # checks the gateway connection and available workflows
abstractcode                      # connects to http://127.0.0.1:8080
```

Prefer a browser? `npx @abstractframework/code` serves the same client on
`http://127.0.0.1:3002`.

## Step 5: Work with files and tools

- Type a task and press Enter; reasoning cycles and tool cards stream in live.
- Tools are approval-gated by default: approve or reject each call, from either client.
- Type `/help` for commands.

## What "durable" means here

- The run lives in the gateway, not in the client. Close the terminal and reattach later; the
  session keeps its full history.
- A run gated on your approval in the terminal can be approved from the browser client, and the
  other way round.

## When to go further

Use the same gateway when you want:
- multiple thin clients observing the same run
- remote execution
- scheduling and a durable command inbox
- bundle discovery for specialized agents

See [Gateway-first local development](gateway-first-local-dev.md).
