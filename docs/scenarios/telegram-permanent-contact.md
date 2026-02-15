# Scenario: Telegram "Permanent Contact" (Gateway Bridge + Agent Workflow)

Goal: run a Telegram contact that forwards inbound Telegram messages to a durable workflow (via gateway events) and sends
replies back via tools.

This is a gateway-first scenario: the gateway host owns durability and stores plaintext history for replay/observability.

## High-level architecture

1. Telegram bridge receives a message.
2. Gateway maps it to a stable `session_id` (typically `telegram:<chat_id>`).
3. Gateway emits an event (for example `telegram.message`) into that session.
4. Your workflow handles the event and calls outbound Telegram tools:
   - `send_telegram_message`
   - `send_telegram_artifact` (files)

## Security model choices

Telegram has two integration paths:

1. TDLib + Secret Chats (E2EE in transit; recommended)
2. Bot API (easy, not E2EE)

Even with E2EE, messages are decrypted on the gateway host and persisted to the durable stores in plaintext by design.
Secure the gateway host and its storage.

## Step 1: Install gateway Telegram support

```bash
pip install "abstractgateway[http,telegram]"
pip install "abstractcore[tools]"   # Bot API outbound tools (sendMessage/sendDocument)
```

## Step 2: Configure the gateway (minimum)

You need a normal gateway configuration plus Telegram bridge settings. At minimum:

```bash
# Bundles (*.flow). Include the shipped `telegram-agent` bundle.
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"
export ABSTRACTGATEWAY_AUTH_TOKEN="..."  # required
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Tool execution + approvals:
# - `passthrough` (default): tools become durable waits; the Telegram bridge auto-runs safe tools and prompts for approval on dangerous tools.
# - `approval`: safe tools run in-process; dangerous tools still require a Telegram reply: `/approve` (anything else cancels)
export ABSTRACTGATEWAY_TOOL_MODE="passthrough"

export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_TELEGRAM_TRANSPORT="bot_api"  # or "tdlib" (E2EE)
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."      # Bot API transport only
export ABSTRACT_ENABLE_TELEGRAM_TOOLS=1
export ABSTRACT_TELEGRAM_FLOW_ID="telegram-agent@0.0.1:tg-agent-main"  # handles telegram.message
```

Then start the gateway:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Notes:
- Default LLM routing comes from `abstractcore --config` (global provider/model). Override with `ABSTRACTGATEWAY_PROVIDER` / `ABSTRACTGATEWAY_MODEL`.
- Telegram-only routing override: set `ABSTRACT_TELEGRAM_MODEL="..."` (and optionally `ABSTRACT_TELEGRAM_PROVIDER="..."`) without changing other gateway traffic.
- Durable history limit: `ABSTRACT_TELEGRAM_MAX_HISTORY_MESSAGES` (default: 30).
- STT fallback and vision caption fallback are configured via `abstractcore --config` (audio strategy + vision fallback).
- `/reset` clears the durable session; optional best-effort message deletion is controlled by `ABSTRACT_TELEGRAM_RESET_DELETE_MESSAGES` and `ABSTRACT_TELEGRAM_RESET_DELETE_MAX`. The confirmation text is configurable via `ABSTRACT_TELEGRAM_RESET_MESSAGE`.
- Send `/tools` in chat to view/change tool permissions (allowlist, auto-approve, require approval, blocklist).

## Step 3: Workflow wiring

### Option A (recommended): use the shipped `telegram-agent` bundle

`telegram-agent@0.0.1:tg-agent-main` is event-driven and session-scoped:
- Durable memory (uses `use_context=true` + the runtime’s durable `context.messages`)
- Media-aware LLM calls (attachments are stored as artifacts and passed as `media`)
- Workflow-owned delivery (workflow calls `send_telegram_message`; no LLM tool-calling required)

### Option B: author your own flow (Flow Editor)

Create a workflow that:

1. waits for `telegram.message` (On Event)
2. extracts `payload.telegram.text` and `payload.telegram.chat_id`
3. generates a reply (Agent or LLM Call)
4. calls `send_telegram_message(chat_id=..., text=...)`

Inbound attachments arrive with an `artifact_id`. To send a file back, call `send_telegram_artifact(chat_id=..., artifact_id=...)`.

## Step 4: TDLib (E2EE) bootstrap (recommended path)

TDLib requires a real Telegram user account and the TDLib shared library (`tdjson`) installed on the gateway host. You
then authenticate once to create a persistent TDLib session directory.

Because TDLib setup is platform-specific, follow:
- [Guide: Telegram integration](../guide/telegram-integration.md)

## Step 5: Test

Send a Telegram message to the AI contact. You should see:
- gateway emits the event into the session
- your run progresses and sends a reply via tools
- Observer can replay the ledger for the session/run

## See also

- [Guide: Telegram integration](../guide/telegram-integration.md) — configuration and TDLib details
