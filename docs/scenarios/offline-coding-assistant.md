# Scenario: Offline Coding Assistant (Terminal)

Goal: run a durable coding assistant locally, offline-first, with Ollama (or an OpenAI-compatible local server).

## Prereqs

- Python 3.10+
- An LLM backend:
  - Ollama (recommended)
  - LM Studio / vLLM / LocalAI (OpenAI-compatible)

## Step 1: Install

Minimal install:

```bash
pip install abstractcode
```

Full pinned stack (includes AbstractCode):

```bash
pip install "abstractframework==0.1.1"
```

## Step 2: Start a local model

### Ollama

```bash
ollama serve
ollama pull qwen3:4b-instruct
export OLLAMA_HOST="http://localhost:11434"
```

## Step 3: Run AbstractCode

```bash
abstractcode --provider ollama --model qwen3:4b-instruct
```

## Step 4: Work with files and tools

- Mention files in prompts with `@path/to/file`.
- Type `/help` for commands.
- Tools are approval-gated by default:
  - Toggle in-session: `/auto-accept`
  - Start with: `--auto-approve`

## What "durable" means here

- Closing and reopening the app keeps state.
- Default storage:
  - `~/.abstractcode/state.json` (UI snapshot)
  - `~/.abstractcode/state.d/` (durable run state + ledger + artifacts)
- Start fresh: `/clear`
- Disable persistence: `--no-state`

## When to switch to the Gateway path

Use a gateway when you want:
- multiple thin clients observing the same run
- remote execution
- scheduling and a durable command inbox
- bundle discovery for specialized agents

See [Gateway-first local development](gateway-first-local-dev.md).

