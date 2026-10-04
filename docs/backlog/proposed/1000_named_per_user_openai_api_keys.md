# 1000 — Named per-user API keys for the OpenAI API

> Package: abstractgateway
> Type: feature (proposed, not built)
> Created: 2026-10-04
> Priority: normal
> Labels: openai-api, security, accounts

## Summary

Named, endpoint-only API keys per account for the gateway's OpenAI API at `/v1`, instead of using the
account's gateway token as the key. Written at the operator's request (2026-10-04, R5.1: "write,
don't build"); building it is decision 3 of the gate
[1001](../planned/1001_operator_decisions_after_the_round_4_to_7_rework.md).

## Current code reality (2026-10-04)

On abstractgateway `round4/2026-10-03`: `/v1/*` authenticates with the caller's gateway token and runs
as that account; each account has an **OpenAI API** switch (403 `openai_api_off` when off); tokens are
stored hashed with fingerprints; the console's OpenAI API page shows the key from the token the browser
kept at sign-in and **New key** rotates the gateway token itself. No named keys exist.

## What

Each account can create several **named API keys** for the OpenAI API at `/v1`, separate from
its gateway token:

- Create: a label ("laptop Cursor", "home assistant"), shown once at creation (like New key today).
- List: label, created, last used (time + client address), fingerprint (SHA-256, 12 hex), never the key.
- Revoke: one key at a time; immediate (the next request answers 401 `invalid_api_key`).
- Endpoint-only: a named key works at `/v1/*` only. It never signs in to the console, never calls
  `/api/gateway/*`, never acts on runs, files, email or workflows.
- Requests run as the owning account and obey its **OpenAI API** switch (off = every key of the account
  answers 403 `openai_api_off`); admins see every account's keys and can revoke any.
- Storage: hashed like gateway tokens (PBKDF2 + fingerprint) in the user registry, additive field;
  the audit line names the key's label so the request log shows which app called.

## Why

- Today the API key IS the person's gateway token (decision of 2026-10-04, DESIGN R5.1): one secret that also signs in
  to the console and drives every gateway API. Pasting it into third-party apps (editors, chat UIs,
  phones) spreads a full-power credential; one leaky app means rotating the token everywhere,
  including the person's own clients.
- Per-app keys give least privilege (endpoint-only), per-app revocation without touching sign-in,
  and attribution in the request log ("which app made this call").
- It removes the reason the console keeps the typed token in browser storage to show the key
  (the exception documented in the gateway's docs/configuration.md): the page would list named keys instead and show a new
  key once, so the gateway token could return to never being kept in the browser.

## Acceptance criteria

- Create/list/revoke for the signed-in account (`/api/gateway/me/openai-keys`) and for admins
  (`/api/gateway/admin/accounts/{id}/openai-keys`); key shown only in the create answer.
- A named key: 200 at `/v1/models`, 401 at `/api/gateway/*` and `/api/gateway/session/login`.
- Revoked key: 401 at once; the account switch off: 403 `openai_api_off` for all its keys.
- The page's Connect card lists keys (label, last used, Revoke) with "New key" asking for a label.
- Tests red on removal; no route returns a stored key (extend `test_no_route_answers_a_stored_token_in_clear`).

## Receipts

`untracked/round4/BACKLOG-R5.md` (adversary G8 PASS), `untracked/round4/DESIGN.md` R5.1.
