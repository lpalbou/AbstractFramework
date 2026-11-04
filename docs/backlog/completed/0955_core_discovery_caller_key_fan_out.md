# 0955 — Discovery routes send a caller's key to every provider they check

> Package: abstractcore (server discovery routes)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: security, credentials, discovery
> Status: Completed
> Completed: 2026-11-03 (merged in AbstractCore #49, ships in abstractcore 2.34.0)

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

- [x] A test with two providers proves the caller key reaches only the named one.

## Validation

Stub two providers and assert the key header only on the named one; RED on the current code.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

## Completion report (2026-11-03)

- AbstractCore PR #49 (merged as `dcde7ccc`), released in 2.34.0 (release PR #50). `server/app.py`
  `_discovery_caller_key_target` and `_server_capability_registry(..., provider)`: a caller's
  `X-AbstractCore-Provider-API-Key` on a discovery route reaches one provider only: the one named with
  `?provider=<id>` (voice: `openai` or an OpenAI-compatible server; music: a backend, and that request's registry uses
  only it), else the configured music backend, or the single vision endpoint. A key sent without one named provider
  is refused with 400 and reaches nobody. Server-held keys keep their own rule (server auth required).
- `tests/server/test_discovery_caller_key_one_provider.py`: two music providers, the key reaches only the named one;
  voice per named engine; refusals reach nobody. 8 of its 9 tests fail on the code before the fix (447530e8).
- Docs: `docs/server.md`, `abstractcore/server/README.md`; CHANGELOG 2.34.0 Security entry.
