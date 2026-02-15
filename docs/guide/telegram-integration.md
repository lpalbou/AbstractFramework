# Telegram Integration (Gateway Bridge + Workflow)

This guide explains how to run a Telegram "permanent contact" that talks to an agent workflow through the gateway:

- Inbound Telegram messages -> gateway emits durable events into a `session_id`
- Outbound replies/files -> workflow calls tools (`send_telegram_message`, `send_telegram_artifact`)
- Attachments -> stored in the ArtifactStore for durable replay

## Security model choices

Telegram has two integration paths:

1. TDLib + Secret Chats (E2EE in transit; recommended)
2. Bot API (easy, not E2EE)

Even with E2EE, messages are decrypted on the gateway host and persisted to durable stores in plaintext by design. Secure
the gateway host and its storage.

## Minimal gateway configuration

Install Telegram support:

```bash
pip install "abstractgateway[http,telegram]"
pip install "abstractcore[tools]"   # Bot API outbound tools (sendMessage/sendDocument)
```

Set env vars on the gateway host:

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"  # directory containing *.flow bundles

export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_ENABLE_TELEGRAM_TOOLS=1
export ABSTRACT_TELEGRAM_FLOW_ID="telegram-agent@0.0.1:tg-agent-main"

# Bot API (easy, not E2EE)
export ABSTRACT_TELEGRAM_TRANSPORT="bot_api"
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."

# Tool execution + approvals:
# - `passthrough` (default): tools become durable waits; the Telegram bridge auto-runs safe tools and prompts for approval on dangerous tools.
# - `approval`: safe tools run in-process; dangerous tools still require a Telegram reply: `/approve` (anything else cancels)
export ABSTRACTGATEWAY_TOOL_MODE="passthrough"
```

Notes:
- Default LLM routing comes from `abstractcore --config` (global provider/model). Override with `ABSTRACTGATEWAY_PROVIDER` / `ABSTRACTGATEWAY_MODEL`.
- Telegram-only routing override (does not affect other gateway traffic): set `ABSTRACT_TELEGRAM_MODEL="..."` (and optionally `ABSTRACT_TELEGRAM_PROVIDER="..."`).
- Durable history limit: `ABSTRACT_TELEGRAM_MAX_HISTORY_MESSAGES` (default: 30; `0` keeps only system messages).
- STT fallback and vision caption fallback are configured via `abstractcore --config` (audio strategy + vision fallback).
- Telegram typing keepalive is best-effort: tune with `ABSTRACT_TELEGRAM_TYPING_INTERVAL_S` (default: 4s) and `ABSTRACT_TELEGRAM_TYPING_MAX_S` (default: 600s; set to `0` to disable).
- `/reset` behavior is best-effort: the bridge clears the durable session, sends a confirmation message, and optionally deletes recent messages in the background. Controls: `ABSTRACT_TELEGRAM_RESET_DELETE_MESSAGES` (default: true), `ABSTRACT_TELEGRAM_RESET_DELETE_MAX` (default: 200), `ABSTRACT_TELEGRAM_RESET_MESSAGE` (confirmation text). Telegram may still reject deletions depending on chat permissions and age.

Start the gateway normally.

## Local dev test (Bot API + LMStudio)

If you're in the AbstractFramework repo, you can use `./execute.sh` as a convenience env setup:

```bash
source ./execute.sh
```

1. Start LMStudio “Local Server” and load `google/gemma-3n-e4b`.
2. Export LLM routing (override the `abstractcore --config` defaults for this run):

```bash
export ABSTRACTGATEWAY_PROVIDER="lmstudio"
export ABSTRACTGATEWAY_MODEL="google/gemma-3n-e4b"
export LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
```

3. Ensure the gateway can see the shipped bundle (a directory containing `*.flow`):

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"  # e.g. ./abstractgateway/flows/bundles in this repo
```

4. Send a Telegram message to the bot and verify:
   - you receive a reply
   - a follow-up (“What did I just say?”) works (durable memory)
   - media messages (photo/voice/video/document) are handled

## Workflow wiring (VisualFlow)

### Shipped `telegram-agent` bundle (recommended)

AbstractGateway ships a `telegram-agent` bundle that is designed for the bridge:
- event-driven + session-scoped (durable memory across messages)
- media-aware (`attachments` become `media` for the LLM call)
- workflow-owned delivery (workflow calls `send_telegram_message`; no LLM tool-calling required)
- tracks sent Telegram `message_id` values so `/reset` can best-effort delete prior bot messages

To use it, point `ABSTRACT_TELEGRAM_FLOW_ID` at `telegram-agent@0.0.1:tg-agent-main` and ensure the gateway loads the bundle (see `ABSTRACTGATEWAY_FLOWS_DIR`).

### Custom workflow

If you author your own flow, the minimal shape is:
1. wait for `telegram.message` (On Event; scope `session`)
2. extract `payload.telegram.text` and `payload.telegram.chat_id`
3. generate a reply (Agent/LLM Call)
4. call `send_telegram_message(chat_id=..., text=...)`

Inbound attachments arrive with an `artifact_id`. Send them back with `send_telegram_artifact(chat_id=..., artifact_id=...)`.

Notes:
- Telegram `sendMessage` has a ~4096 character limit. `send_telegram_message` automatically splits long text into multiple messages and returns `message_ids` (best-effort) in the tool result.
- Empty/whitespace `text` is rejected by Telegram; `send_telegram_message` falls back to a short error message so workflows still deliver something.

Tip: if you want `/reset` to delete prior bot messages, store sent `message_id` values in `run.vars._runtime.telegram.sent_message_ids` (the bridge scans this on reset).

## TDLib notes (E2EE path)

TDLib requires:
- a real Telegram user account for the AI identity
- the TDLib shared library (`tdjson`) installed on the gateway host
- a persistent TDLib session directory (so you authenticate once)

Because TDLib is platform-specific, keep your setup steps close to your deployment scripts. The gateway integration code
and configuration surface live in:
- https://github.com/lpalbou/abstractgateway

## Testing checklist

1. Confirm the gateway loaded the `telegram-agent` bundle (API: `GET /api/gateway/bundles`).
2. Send a message to the bot; verify you get a reply and that Observer can replay the run.
3. Send a follow-up (“What did I just say?”) to confirm durable memory works.
4. Send media:
   - photo (with and without caption)
   - voice note (STT fallback depends on your `abstractcore --config` audio strategy + installed plugins)
   - video and document
5. Send `/reset` to clear the binding/runs, then confirm the next message starts fresh.

## Tool approvals (Telegram)

When the agent requests a tool call that requires explicit permission (for example `write_file` or `execute_command`),
the bridge sends an approval prompt into the chat. Reply with:
- `/approve` (or `approve`) to execute the tool calls and continue
- anything else to cancel the tool calls and let the workflow continue with failure results

### Tool permissions (Telegram)

You can control which tools are available and which require approval.

In chat:
- Send `/tools` to view the current tool policy.
- Examples:
  - `/tools safe` (default) — safe tools auto-run; dangerous tools require `/approve`
  - `/tools open` — approve everything by default (dangerous)
  - `/tools strict` — allow only the safe tool set
  - `/tools allow read_file web_search` — custom allowlist
  - `/tools block execute_command write_file` — block specific tools

Operator defaults (env; applied per chat unless overridden via `/tools ...`):
- `ABSTRACT_TELEGRAM_APPROVE_ALL_TOOLS=1`
- `ABSTRACT_TELEGRAM_ALLOWED_TOOLS` (newline-separated or JSON list)
- `ABSTRACT_TELEGRAM_AUTO_APPROVE_TOOLS` (newline-separated or JSON list)
- `ABSTRACT_TELEGRAM_REQUIRE_APPROVAL_TOOLS` (newline-separated or JSON list)
- `ABSTRACT_TELEGRAM_BLOCKED_TOOLS` (newline-separated or JSON list)
