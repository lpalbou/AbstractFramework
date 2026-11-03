# 1068 — Password sign-in in every client (kit card, Code web, Assistant, iPhone, watch)

> Package: abstractuic, abstractcode, abstractassistant (desktop, iPhone, watch)
> Type: task
> Created: 2026-10-28
> Priority: high
> Labels: sign-in, first-run, clients

## Summary

AbstractGateway 0.18.0 signs accounts in with an account and a PASSWORD (`POST /api/gateway/session/login`
`{user_id, password, remember}`) as well as a token, and a fresh gateway is set up from the console's
"Set up your gateway" page. Only the gateway's own console uses it. Every other client still asks for a
token, so a member created with a password (the operator's multi-user test from the watch) cannot sign in there.

## Why

Operator, 2026-10-28: "a better handling of a fresh first install, with a fresh user, with a clean and nice
onboarding to create the admin account." The console part shipped in gateway 0.18.0; the clients are the
follow-up ("implement only the console now").

## Scope

### In scope

- **Kit first** (`abstractuic` `GatewaySessionSignInCard`): a password mode (Password first, "Sign in with a token
  instead" link, `autocomplete="current-password"`), the 429 `too_many_attempts` message with `retry_after_s`, and an
  "unclaimed" state that reads `GET /api/gateway/session/onboarding` and sends the person to `<gateway>/console`
  to set the gateway up (the onboarding form stays in the console). Release the kit, then adopt.
- AbstractCode web, AbstractAssistant desktop (its sign-in sheet), iPhone and watch: account + password, token
  behind a link. Native apps store the SESSION (or a token minted for the device), never the password.
- The watch: password entry is awkward; prefer pairing from the iPhone (the phone signs in, hands the watch a
  device token) and document it.

### Out of scope

- The console (done in gateway 0.18.0); invite links (1070).

## Acceptance criteria

- Each client signs in a member created with a password (`bob`) against a real 0.18.0 gateway, through a proxy
  (Tailscale Funnel), with screenshots; a wrong password shows the gateway's sentence; a token still works.
- A client pointed at an unclaimed gateway says "set it up in the console" with the link, and never shows a
  token form as the only way in.
