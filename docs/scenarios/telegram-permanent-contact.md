# Scenario: Telegram "Permanent Contact" (Gateway Bridge + Agent Workflow)

Goal: run a Telegram contact that forwards inbound Telegram messages to a durable workflow (one run per message) and sends
replies back to Telegram.

This is a gateway-first scenario: the gateway host owns durability and stores plaintext history for replay/observability.

## High-level architecture

1. Telegram bridge receives a message.
2. Gateway maps it to a stable `session_id` (typically `telegram:<chat_id>:r<rev>`).
3. Gateway starts a new run for the configured flow (thin-client semantics).
4. The bridge sends the run output back to Telegram.

## Security model choices

Telegram has two integration paths:

1. TDLib + Secret Chats (E2EE in transit; recommended)
2. Bot API (easy, not E2EE)

Even with E2EE, messages are decrypted on the gateway host and persisted to the durable stores in plaintext by design.
Secure the gateway host and its storage.

## Step 1: Install AbstractGateway (Telegram bridge)

```bash
pip install abstractgateway
# Optional (only if your workflows call Telegram tools like `send_telegram_message`):
# pip install "abstractcore[tools]"
```

## Step 2: Configure the gateway (minimum)

You need a normal gateway configuration plus Telegram bridge settings. At minimum:

```bash
# Bundles (*.flow). Include the shipped `basic-agent` bundle (and any custom bundles).
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"
export ABSTRACTGATEWAY_AUTH_TOKEN="..."  # required
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
export ABSTRACTGATEWAY_DATA_DIR="$PWD/runtime/gateway"

# Tool execution + approvals:
# - `approval` (default): safe tools run in-process; dangerous/unknown tools require a Telegram reply: `/approve` or `/deny`.
export ABSTRACTGATEWAY_TOOL_MODE="approval"

export ABSTRACT_TELEGRAM_BRIDGE=1
# Bot API (easy, not E2EE). If ABSTRACT_TELEGRAM_BOT_TOKEN is set, transport defaults to bot_api.
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."      # from @BotFather
# Optional: TDLib (E2EE) instead of Bot API:
# export ABSTRACT_TELEGRAM_TRANSPORT="tdlib"
# Optional: override which workflow to run per message.
# Default (when unset): shipped `basic-agent` bundle entrypoint.
# export ABSTRACT_TELEGRAM_BUNDLE_ID="basic-agent"
# export ABSTRACT_TELEGRAM_FLOW_ID="81795ea9"

# Access control (required by default)
# Use /whoami in Telegram to discover your numeric user_id.
export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789"

# Optional: pairing mode (lets unknown users request access, but requires an admin):
# export ABSTRACT_TELEGRAM_DM_POLICY="pairing"
# export ABSTRACT_TELEGRAM_ADMIN_USERS="123456789"

# Optional: group chat support (disabled by default):
# export ABSTRACT_TELEGRAM_GROUP_POLICY="allowlist"
# export ABSTRACT_TELEGRAM_ALLOWED_CHATS="-100123456789"  # use /whoami inside the group to discover chat_id
# export ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS=1     # default true
```

Then start the gateway:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Notes:
- Default LLM routing comes from the execution-host `input.text` capability
  route. Set it with `abstractcore --set-global-default ...` or
  `abstractgateway-config set-default input.text ...`.
- Telegram-only routing override: set `ABSTRACT_TELEGRAM_MODEL="..."` (and optionally `ABSTRACT_TELEGRAM_PROVIDER="..."`) without changing other gateway traffic.
- Durable history limit: `ABSTRACT_TELEGRAM_MAX_HISTORY_MESSAGES` (default: 30).
- STT fallback and vision caption fallback are configured via `abstractcore --config` (audio strategy + vision fallback).
- `/reset` clears the durable session; optional best-effort message deletion is controlled by `ABSTRACT_TELEGRAM_RESET_DELETE_MESSAGES` and `ABSTRACT_TELEGRAM_RESET_DELETE_MAX`. The confirmation text is configurable via `ABSTRACT_TELEGRAM_RESET_MESSAGE`.
- For tool approvals, the bridge will prompt you in chat; reply with `/approve` to run tools, or `/deny` to cancel.

## Step 3: Workflow wiring

Telegram is a thin client: any workflow that reads `prompt`/`context` (like `abstractcode.agent.v1`) and writes a string
to `run.output.answer` or `run.output.response` will work. Durable memory comes from the Telegram `session_id`.

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
