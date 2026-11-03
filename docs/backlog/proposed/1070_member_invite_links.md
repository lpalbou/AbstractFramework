# 1070 — Member invite links: the onboarding screen in "invite" mode

> Package: abstractgateway (console)
> Type: task
> Created: 2026-10-28
> Priority: normal
> Labels: sign-in, accounts

## Summary

Gateway 0.18.0 lets an admin create a member WITH a password (Accounts > Create user, or the key button on a row).
The operator also proposed "an invite link that lets the member set their own password on first open, same
onboarding screen in invite mode". Not shipped: the admin has to choose the member's password and pass it on.

## Scope

### In scope

- `POST /api/gateway/admin/accounts/{id}/invite` mints a single-use, expiring code (hashed at rest, like claim
  codes); `/console#invite=<code>` opens the "Set up your gateway" card in invite mode ("Choose your password");
  `POST /api/gateway/session/invite` sets the password and signs in. Rate limited like the onboarding; the code is
  stripped from the address bar before use; refused for admins' accounts unless the inviter is an admin.
- Accounts row: "Invite link" next to the key button; copy affordance; shown once.

## Acceptance criteria

- Through Tailscale Funnel, a member opens the link in a fresh browser, sets a password, signs in; the link then
  answers "already used"; an expired link says so.
