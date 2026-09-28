# 0955 — Discovery routes send a caller's key to every provider they check

> Package: abstractcore (server discovery routes)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: security, credentials, discovery

## Summary

When a caller passes `X-AbstractCore-Provider-API-Key` to a capability discovery route that checks several providers, the key is handed to every provider checked, not only the one it was meant for. A key for one vendor should never reach another vendor's endpoint.

## Why

Ledger: "discovery caller key fans out to all checked providers" (core gate follow-up).

## Current code reality (2026-09-28)

- abstractcore 2.18.0 registry guard (`238b693`) protects server-held keys; the caller-key path fans out.

## Scope

### In scope

- Discovery routes accept the caller key for one named provider only (or per-provider keys) and never send it elsewhere.

### Out of scope

- Server-held key rules (done in 2.18.0).

## Acceptance criteria

- [ ] A test with two providers proves the caller key reaches only the named one.

## Validation

Stub two providers and assert the key header only on the named one; RED on the current code.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
