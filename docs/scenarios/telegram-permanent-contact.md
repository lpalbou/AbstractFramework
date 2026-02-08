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
pip install "abstractgateway[telegram]"
```

## Step 2: Configure the gateway (minimum)

You need a normal gateway configuration plus Telegram bridge settings. At minimum:

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="..."  # required
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"

export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_ENABLE_TELEGRAM_TOOLS=1
export ABSTRACT_TELEGRAM_FLOW_ID="<bundle_id>:<flow_id>"  # workflow that handles telegram.message
```

Then start the gateway:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

## Step 3: Wire the workflow (Flow Editor)

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
