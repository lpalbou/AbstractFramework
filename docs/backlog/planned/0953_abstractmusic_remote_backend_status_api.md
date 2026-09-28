# 0953 — AbstractMusic says which backends are remote, replacing AbstractCore's key-name guard

> Package: abstractmusic, abstractcore (server music routes)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: security, music, credentials, api

## Summary

AbstractCore 2.18.0 guards `/v1/audio/music` with an interim rule: while the server holds any key AbstractMusic reads (`ACEMUSIC_API_KEY`, `ELEVENLABS_API_KEY`), an unauthenticated request gets 401 whatever backend it names, even a local one. AbstractVoice solved the same problem with `abstractvoice.engine_runtime` (it says which engines are remote). AbstractMusic needs the equivalent so Core can apply the guard to remote backends only.

## Why

Ledger: "BACKLOG: AbstractMusic remote-backend API (like engine_runtime) to replace the key-name interim" (core gate, 2026-09-28).

## Current code reality (2026-09-28)

- abstractcore 2.18.0 CHANGELOG: "This is an interim rule until AbstractMusic can say which of its backends are remote."
- abstractmusic 0.1.15 has no backend runtime-status API.

## Scope

### In scope

- An `abstractmusic` API that reports per backend whether it is remote and which credential it spends.
- AbstractCore's music guard reads it and fails closed for backends it does not know.

### Out of scope

- New music backends.

## Acceptance criteria

- [ ] Local music on a server holding a remote-backend key works unauthenticated; remote backends still need authentication.

## Validation

Core server tests for both cases, RED when the API is bypassed.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
