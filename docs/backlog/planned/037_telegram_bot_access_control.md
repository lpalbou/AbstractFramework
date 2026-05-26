# 037 — Telegram Bot Access Control (User/Chat Allowlist + Pairing)

**Status**: Implemented  
**Date**: 2026-02-15  
**Priority**: Critical (security)  
**Component**: abstractgateway (telegram_bridge.py)

## Summary

Implement bot-level access control for the Telegram bridge so that only authorized Telegram users and
chats can interact with the bot. Currently, any Telegram user who discovers the bot can message it and
trigger full LLM processing — burning API tokens, creating durable runs, and receiving responses.

## Problem Statement

Telegram bots created via `@BotFather` are **public by default**. Anyone on Telegram can find the bot
by its username and send messages. The current `TelegramBridge` implementation (both Bot API and TDLib
paths) processes **every** inbound message without any user or chat filtering:

- `_handle_bot_update()` (Bot API path): only filters `is_bot == True` (prevents self-loops), then
  processes all messages unconditionally.
- `_handle_tdlib_update()` (TDLib path): only filters `is_outgoing == True`, then processes all
  messages unconditionally.
- `TelegramBridgeConfig`: has no `allowed_users`, `allowed_chats`, or DM policy fields.

### Impact

- **Cost exposure**: any random Telegram user can consume LLM API tokens indefinitely.
- **Resource exhaustion**: unlimited durable runs/sessions can be created by strangers.
- **Data exposure**: the agent responds to anyone, potentially leaking system prompt details or
  available tool capabilities.
- **Tool execution risk**: even with tool approval gates (which are good), the agent still runs its
  full reasoning loop and sends back text for every unauthorized message.

### Comparison: OpenClaw has this solved

OpenClaw (a comparable open-source self-hosted AI chat framework) implements multi-layered access
control for Telegram, documented in their `channels.telegram` configuration:

1. **DM Policy** (`dmPolicy`): `disabled` | `open` | `allowlist` | **`pairing`** (default)
   - `disabled`: no DMs allowed.
   - `open`: anyone can message (requires explicit `allowFrom: ["*"]` — opt-in dangerous).
   - `allowlist`: only numeric Telegram user IDs in `allowFrom` are permitted.
   - `pairing` (default): unknown users can request access; they receive a pairing code that the
     operator must approve. Codes expire after 1 hour.

2. **Group Policy** (`groupPolicy`): `disabled` | `allowlist` (default) | `open`
   - Independent from DM policy.
   - `groups` field controls which group chat IDs are permitted (explicit IDs or `"*"`).
   - `groupAllowFrom` controls which senders within allowed groups can trigger the bot; falls back to
     `allowFrom` if not set.

3. **Mention requirement**: in groups, the bot requires `@mention` by default (configurable).

4. **Rejection behavior**: unauthorized messages are silently ignored — no response, no resource
   consumption, no run creation.

## Scope

### What we do

**Phase 1 (MVP — this backlog item):**

- Add `allowed_users` to `TelegramBridgeConfig`: a set of numeric Telegram user IDs. Env:
  `ABSTRACT_TELEGRAM_ALLOWED_USERS` (newline-separated or JSON list of numeric IDs).
- Add `allowed_chats` to `TelegramBridgeConfig`: a set of numeric Telegram chat IDs. Env:
  `ABSTRACT_TELEGRAM_ALLOWED_CHATS` (newline-separated or JSON list).
- Add `dm_policy` to `TelegramBridgeConfig`: `allowlist` (default) | `open`. Env:
  `ABSTRACT_TELEGRAM_DM_POLICY`.
  - `allowlist` (default): only user IDs in `allowed_users` (or chat IDs in `allowed_chats`) can
    interact. If both are empty, only the bridge operator's own user ID is permitted (require
    explicit opt-in for public access).
  - `open`: any user can message (requires explicit configuration — dangerous; log a WARNING on
    startup).
- Add early guard in `_handle_bot_update()` and `_handle_tdlib_update()`:
  - Extract `from_user_id` and `chat_id`.
  - Check against `dm_policy`, `allowed_users`, `allowed_chats`.
  - If unauthorized: silently ignore (no response, no run, no event, no token cost).
  - Log a WARNING: `"Telegram bridge: ignoring message from unauthorized user_id=%s in chat_id=%s"`.
- Add `/whoami` bot command: responds with the sender's numeric Telegram user ID, so operators can
  easily discover IDs to add to the allowlist.
- Update `docs/guide/telegram-integration.md` with the new env vars and security section.
- Update `docs/scenarios/telegram-permanent-contact.md` with a security setup step.
- Update `docs/configuration.md` with the new env vars.

**Phase 2 (future — separate backlog item):**

- `pairing` DM policy: unknown users receive a time-limited pairing code; operator approves via a
  `/pair approve <code>` command or an Observer/API endpoint. Codes expire after 1 hour.
- `group_policy`: independent group access control (`disabled` | `allowlist` | `open`).
- `require_mention`: in groups, require `@botname` mention before processing.
- Rate limiting: per-user message rate cap to mitigate abuse even from authorized users.
- `/ban` and `/unban` runtime commands for the operator.

### What we don't do

- We do not change the gateway HTTP API auth model (`ABSTRACTGATEWAY_AUTH_TOKEN`) — that is
  orthogonal and already works.
- We do not implement a full "pairing store" in Phase 1 — static allowlists are sufficient for MVP
  and cover the critical security gap.
- We do not implement group-specific policies in Phase 1 — the `allowed_chats` field covers the
  basic case.

## Design

### Default behavior change (important)

Today: `dm_policy` is effectively `open` (no filter).  
After this change: `dm_policy` defaults to `allowlist`.

If `ABSTRACT_TELEGRAM_ALLOWED_USERS` is not set and `dm_policy` is `allowlist`, the bridge should
**refuse to start** and log an error:

```
Telegram bridge: dm_policy is 'allowlist' but ABSTRACT_TELEGRAM_ALLOWED_USERS is empty.
Set ABSTRACT_TELEGRAM_ALLOWED_USERS to your Telegram user ID(s),
or set ABSTRACT_TELEGRAM_DM_POLICY=open to allow anyone (dangerous).
Use /whoami in Telegram to discover your numeric user ID.
```

This ensures operators explicitly decide on access policy. No silent open access.

### Config fields

```python
@dataclass(frozen=True)
class TelegramBridgeConfig:
    # ... existing fields ...

    # Access control
    dm_policy: str = "allowlist"  # "allowlist" | "open"
    allowed_users: Optional[frozenset[int]] = None  # numeric Telegram user IDs
    allowed_chats: Optional[frozenset[int]] = None   # numeric Telegram chat IDs
```

### Guard placement

Both `_handle_bot_update()` and `_handle_tdlib_update()` must check authorization **before**:
- Creating bindings (`_ensure_binding`)
- Emitting events (`runner.emit_event`)
- Starting typing indicators
- Any tool-related logic

The only commands exempt from the guard should be `/whoami` (returns the user's ID, so they can give
it to the operator).

### Env var parsing

```bash
# Newline-separated or JSON list of numeric IDs
export ABSTRACT_TELEGRAM_ALLOWED_USERS="123456789
987654321"

# Or JSON format
export ABSTRACT_TELEGRAM_ALLOWED_USERS='[123456789, 987654321]'

# DM policy (default: allowlist)
export ABSTRACT_TELEGRAM_DM_POLICY="allowlist"

# Chat allowlist (optional, for group chats)
export ABSTRACT_TELEGRAM_ALLOWED_CHATS='["-100123456789"]'
```

## Dependencies

- None (pure addition to existing bridge code).

## Expected Outcomes

1. **Default secure**: fresh installs require explicit user allowlist — no accidental public exposure.
2. **Cost protection**: unauthorized users cannot consume LLM tokens.
3. **Silent rejection**: unauthorized messages produce no response, no run, no artifact.
4. **Operator convenience**: `/whoami` command makes it easy to discover Telegram user IDs.
5. **Logged warnings**: every rejected message is logged (operator can audit).
6. **Explicit opt-in for open access**: `ABSTRACT_TELEGRAM_DM_POLICY=open` + WARNING on startup.
7. **Parity with OpenClaw**: achieves functional equivalence with OpenClaw's `allowlist` DM policy for
   Phase 1, with a clear path to `pairing` in Phase 2.

## References

- OpenClaw Telegram security docs: https://docs.openclaw.ai/channels/telegram
- Current bridge code: `abstractgateway/src/abstractgateway/integrations/telegram_bridge.py`
- Current guide: `docs/guide/telegram-integration.md`

---

## Report

Implemented in `abstractgateway/src/abstractgateway/integrations/telegram_bridge.py`:

- Bridge-level access control enforced **before** bindings/events (both Bot API + TDLib paths).
- Default secure posture aligned with OpenClaw:
  - DMs: `dm_policy=allowlist` (default) — only allowlisted users are processed (`ABSTRACT_TELEGRAM_ALLOWED_USERS`).
  - Groups: `group_policy=disabled` (default) — group chats are opt-in.
  - Groups: mention gate enabled by default when groups are enabled (`ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS=1`).
- Commands:
  - `/whoami` always available (prints `user_id` + `chat_id` for configuration).
  - `/pair` request + `/pair list|approve|deny` for admin operations (only when `dm_policy=pairing`).
- Configuration (env):
  - `ABSTRACT_TELEGRAM_DM_POLICY`, `ABSTRACT_TELEGRAM_GROUP_POLICY`
  - `ABSTRACT_TELEGRAM_ADMIN_USERS`
  - `ABSTRACT_TELEGRAM_ALLOWED_USERS`, `ABSTRACT_TELEGRAM_ALLOWED_CHATS`
  - `ABSTRACT_TELEGRAM_GROUP_ALLOWED_USERS`
  - `ABSTRACT_TELEGRAM_REQUIRE_MENTION_IN_GROUPS`
  - `ABSTRACT_TELEGRAM_PAIRING_TTL_S`
- Deviation from initial proposal: the bridge does **not** refuse to start on an empty allowlist; it logs warnings and stays fail-closed to avoid a bootstrap deadlock (operators can use `/whoami` to discover IDs).
