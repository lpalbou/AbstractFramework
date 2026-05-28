# Telegram Integration (Gateway Bridge + Workflow)

This guide explains how to run a Telegram "permanent contact" that talks to an agent workflow through the gateway.

Telegram is implemented as a **thin client**:
- Inbound Telegram messages -> gateway starts a new run per message (stable `session_id` for durable memory)
- Outbound replies -> the bridge sends the run output back to Telegram
- Attachments -> stored in the ArtifactStore and passed as `context.attachments` / `context.media`

## Security model choices

Telegram has two integration paths:

1. TDLib + Secret Chats (E2EE in transit; recommended)
2. Bot API (easy, not E2EE)

Even with E2EE, messages are decrypted on the gateway host and persisted to durable stores in plaintext by design. Secure
the gateway host and its storage.

## Access control (critical)

Telegram bots and user accounts are discoverable. Without access control, anyone who finds the handle can message it and
trigger durable runs + LLM calls.

The bridge is **fail-closed by default**:
- DMs: `ABSTRACT_TELEGRAM_DM_POLICY=allowlist` (default) — only allowlisted Telegram `user_id`s are processed.
- Groups: `ABSTRACT_TELEGRAM_GROUP_POLICY=disabled` (default) — all group/supergroup/channel messages are ignored.
- Unauthorized messages are ignored (no run created, no token spend). `/whoami` always works.

Commands:
- `/whoami` — always works; prints your `user_id` and `chat_id` (useful for allowlists).
- `/pair ...` — pairing workflow (DM only; only when `ABSTRACT_TELEGRAM_DM_POLICY=pairing`).

Minimal env vars (Bot API + DM allowlist):

```bash
export ABSTRACT_TELEGRAM_BRIDGE=1

# Bot API (easy, not E2EE). If ABSTRACT_TELEGRAM_BOT_TOKEN is set, transport defaults to bot_api.
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."  # from @BotFather

# Allowlisted DM users (numeric Telegram user_id). Use /whoami to discover yours.
# Accepts comma/newline-separated ints or JSON list.
export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789"
```

## Quickstart (DM-only allowlist)

This is a practical checklist to verify access control + approvals end-to-end.

1. Configure the bridge (Bot API):

```bash
# Gateway (required for `abstractgateway serve`).
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"  # directory containing *.flow bundles (incl. shipped `basic-agent`)
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"

export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."               # from @BotFather
```

2. Start the gateway.
   - You may see a warning about an empty DM allowlist; this is expected until you set `ABSTRACT_TELEGRAM_ALLOWED_USERS`.
   - Then DM the bot and run `/whoami`.
   - Copy your `user_id` (the bot also prints an `export ABSTRACT_TELEGRAM_ALLOWED_USERS="..."` hint).

3. Set your allowlist and restart the gateway:

   - `export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789"`

4. Verify:
   - From an allowlisted account, send “hi” → expected: you receive a reply.
   - From a non-allowlisted account, send “hi” → expected: ignored (except `/whoami`).

5. Verify tool approvals:
   - In the chat, ask: `run free -m` (or `uname -a`).
   - Expected: the bot asks you to reply `/approve` before executing `execute_command`.
   - Expected: after `/approve`, you receive the final answer/result in Telegram (read-only tools like `web_search` should not require approval).

## Optional: pairing mode (DMs)

Pairing lets unknown users request access without editing `ABSTRACT_TELEGRAM_ALLOWED_USERS`, but it requires an admin.

```bash
export ABSTRACT_TELEGRAM_DM_POLICY="pairing"
export ABSTRACT_TELEGRAM_ADMIN_USERS="123456789"   # your operator user_id (use /whoami)
export ABSTRACT_TELEGRAM_PAIRING_TTL_S="3600"      # optional
```

## Optional: group chat support

Group chats are disabled by default. To enable allowlisted groups:

```bash
export ABSTRACT_TELEGRAM_GROUP_POLICY="allowlist"
export ABSTRACT_TELEGRAM_ALLOWED_CHATS="-100123456789"  # use /whoami inside the group to discover chat_id
# Optional (default true): require @mention in groups
export ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS=1
```

## Viewing Telegram sessions in AbstractCode

Telegram runs are durable; you can replay them from any thin client.

1. Open AbstractCode (default): http://localhost:3002
2. Go to **History**, click **Refresh**, then open the Telegram session (e.g. `telegram:<chat_id>:r<rev>`).

Notes:
- Each incoming Telegram message creates a new run under the same `session_id` (durable memory across turns).

## Minimal gateway configuration

Install Telegram support:

```bash
pip install abstractgateway
# Optional (only if your workflows call Telegram tools like `send_telegram_message`):
# pip install "abstractcore[tools]"
```

Set env vars on the gateway host:

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"  # directory containing *.flow bundles
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"  # required

export ABSTRACT_TELEGRAM_BRIDGE=1

# Bot API (easy, not E2EE). If ABSTRACT_TELEGRAM_BOT_TOKEN is set, transport defaults to bot_api.
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."
export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789"  # use /whoami

# Tool execution + approvals:
# - `approval` (default): safe tools run in-process; dangerous/unknown tools still require a Telegram reply: `/approve` or `/deny`.
# - `passthrough`: delegated execution (advanced; not recommended for thin clients).
export ABSTRACTGATEWAY_TOOL_MODE="approval"

# Optional: override which workflow to run per message.
# Default (when unset): shipped `basic-agent` bundle entrypoint.
# export ABSTRACT_TELEGRAM_BUNDLE_ID="basic-agent"
# export ABSTRACT_TELEGRAM_FLOW_ID="81795ea9"
```

Notes:
- Default LLM routing comes from the execution-host `output.text` capability route. Set it with
  `abstractcore --set-global-default ...` or `abstractgateway-config set-default output.text ...`.
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
2. Set the text output route for this run:

```bash
abstractgateway-config set-default output.text \
  --provider lmstudio \
  --model google/gemma-3n-e4b \
  --base-url http://127.0.0.1:1234/v1
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

### Default workflow (recommended)

By default, the bridge runs the shipped `basic-agent` bundle entrypoint once per incoming message and sends the run output back to Telegram.
Durable memory comes from the stable Telegram `session_id` (no special workflow shape required).

### Custom workflow

Any flow that reads `prompt`/`context` (like `abstractcode.agent.v1`) and writes a string to `run.output.answer` or `run.output.response` will work.
The bridge provides Telegram metadata in `input_data.telegram` if you want to branch on it.

## TDLib notes (E2EE path)

TDLib requires:
- a real Telegram user account for the AI identity
- the TDLib shared library (`tdjson`) installed on the gateway host
- a persistent TDLib session directory (so you authenticate once)

Because TDLib is platform-specific, keep your setup steps close to your deployment scripts. The gateway integration code
and configuration surface live in:
- https://github.com/lpalbou/abstractgateway

## Testing checklist

1. Confirm the gateway loaded your bundles (API: `GET /api/gateway/bundles`) and that the configured Telegram flow exists.
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
 
Note: `/tools` is intentionally disabled in thin-client mode; use `/approve` and `/deny`.
