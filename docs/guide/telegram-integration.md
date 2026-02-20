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
- DMs: `ABSTRACT_TELEGRAM_DM_POLICY=pairing` (default) — unknown users get a pairing code (sent once; use `/pair` to re-show); an admin approves it.
- Groups: `ABSTRACT_TELEGRAM_GROUP_POLICY=allowlist` (default) — only explicitly allowlisted chats are processed.
- Unauthorized messages are ignored (no run created, no token spend), except pairing prompts in DMs.

Commands:
- `/whoami` — always works; prints your `user_id` and `chat_id` (useful for allowlists).
- `/pair` — request a pairing code (DM only).
- `/pair list` — list pending requests (admin only).
- `/pair approve <code>` — approve a request (admin only).
- `/pair deny <code>` — deny a request (admin only).

Recommended env vars (bridge host):

```bash
# Pairing approvals (set this to *your* numeric Telegram user_id; use /whoami)
export ABSTRACT_TELEGRAM_ADMIN_USERS="123456789"

# DMs: pairing (default) | allowlist | open | disabled
export ABSTRACT_TELEGRAM_DM_POLICY="pairing"
export ABSTRACT_TELEGRAM_PAIRING_TTL_S="3600"

# DMs: allowlist mode (optional when using pairing)
export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789"

# Groups: allowlist (default) | open | disabled
export ABSTRACT_TELEGRAM_GROUP_POLICY="allowlist"
export ABSTRACT_TELEGRAM_ALLOWED_CHATS="-100123456789"

# Groups: mention requirement (default true)
export ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS=1

# Optional: restrict which senders inside allowed groups can trigger the bridge.
# - unset: fall back to ABSTRACT_TELEGRAM_ALLOWED_USERS (+ paired users)
# - [] (empty JSON array): allow any sender in allowed groups
export ABSTRACT_TELEGRAM_GROUP_ALLOWED_USERS='[]'
```

## Step-by-step: secure pairing (try it now)

This is a practical checklist to verify access control + approvals end-to-end.

1. Configure the bridge (Bot API example):

```bash
export ABSTRACT_TELEGRAM_BRIDGE=1
export ABSTRACT_TELEGRAM_TRANSPORT="bot_api"
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."               # from @BotFather
# Optional: override which workflow to run per message (defaults to shipped `basic-agent`)
# export ABSTRACT_TELEGRAM_FLOW_ID="81795ea9"

# Secure defaults
export ABSTRACT_TELEGRAM_DM_POLICY="pairing"
export ABSTRACT_TELEGRAM_GROUP_POLICY="allowlist"
export ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS=1

# IMPORTANT: set this to your own Telegram numeric user_id (discover via /whoami)
export ABSTRACT_TELEGRAM_ADMIN_USERS="123456789"

# Optional: customize /reset confirmation message
export ABSTRACT_TELEGRAM_RESET_MESSAGE="Hi, what can I do for you today?"
```

2. Start the gateway, then DM the bot and run `/whoami`.
   - Copy your `user_id` and put it in `ABSTRACT_TELEGRAM_ADMIN_USERS` (then restart the gateway if needed).

3. From a *different* Telegram account (not in the allowlist), DM the bot anything.
   - Expected: the bot replies with a pairing prompt and a one-time code (it does not spam on every message; use `/pair` to re-show the code).

4. From the admin account, approve the request:
   - `/pair list`
   - `/pair approve <code>`

5. Verify unauthorized DMs are blocked:
   - Set `ABSTRACT_TELEGRAM_DM_POLICY="allowlist"` and restart.
   - Expected: unknown users get ignored (except `/whoami`).

6. Verify group allowlist + mention gate:
   - Add the bot to a group chat, run `/whoami` in that group to get the negative `chat_id` (e.g. `-100...`).
   - Set `ABSTRACT_TELEGRAM_ALLOWED_CHATS="-100..."` and restart.
   - Expected: the bot only responds in allowlisted groups, and only when mentioned (e.g. `@YourBot do X`).

7. Verify tool approvals:
   - In the chat, ask: `run free -m` (or `uname -a`).
   - Expected: the bot asks you to reply `/approve` before executing `execute_command`.
   - Expected: after `/approve`, you receive the final answer/result in Telegram (read-only tools like `web_search` should not require approval).

## Viewing Telegram sessions in AbstractCode

Telegram runs are durable; you can replay them from any thin client.

1. Open AbstractCode (default): http://localhost:3002
2. Go to **History**, click **Refresh**, then open the Telegram session (e.g. `telegram:<chat_id>:r<rev>`).

Notes:
- Each incoming Telegram message creates a new run under the same `session_id` (durable memory across turns).

## Minimal gateway configuration

Install Telegram support:

```bash
pip install "abstractgateway[http,telegram]"
# Optional (only if your workflows call Telegram tools like `send_telegram_message`):
# pip install "abstractcore[tools]"
```

Set env vars on the gateway host:

```bash
export ABSTRACTGATEWAY_FLOWS_DIR="/path/to/bundles"  # directory containing *.flow bundles

export ABSTRACT_TELEGRAM_BRIDGE=1

# Bot API (easy, not E2EE)
export ABSTRACT_TELEGRAM_TRANSPORT="bot_api"
export ABSTRACT_TELEGRAM_BOT_TOKEN="..."

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
