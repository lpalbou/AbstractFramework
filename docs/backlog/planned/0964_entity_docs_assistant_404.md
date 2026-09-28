# 0964 — Entity docs assistant answers 404: move it to the Observer pattern

> Package: abstractentity
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: entity, docs-assistant, apps-proxy

## Summary

The Entity app's docs assistant fetches `api/gateway/docs/corpus` and sends the whole corpus in its user turn. It answers 404 in the gate's run. The Observer's assistant uses the gateway's docs-qa workflow (question only, per-conversation session, no tools); Entity should do the same.

## Why

Ledger: "BACKLOG: entity docs assistant 404 (use Observer pattern)" (apps gate).

## Current code reality (2026-09-28)

- `abstractentity/src/entity_assistant.ts:34` fetches `joinBaseUrl(baseUrl, 'api/gateway/docs/corpus')` (entity 0.3.0); the gateway route is `GET /api/gateway/docs/corpus` (`routes/gateway.py:1400`).
- Observer 0.2.0 `src/ui/app_assistant.tsx` uses the shared docs-qa bundle.

## Scope

### In scope

- Entity's assistant runs docs-qa like the Observer (question only, `use_session_history`, New conversation).

### Out of scope

- Other Entity chat surfaces.

## Acceptance criteria

- [ ] The assistant answers through `/apps/entity/` and standalone.

## Validation

App test against a hermetic gateway; RED on the current fetch.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
