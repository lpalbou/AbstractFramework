# 0954 — The every-route key-spend test builds bodies from the route schemas and walks every POST

> Package: abstractcore (tests)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: security, tests, credentials

## Summary

AbstractCore 2.18.0 added a test that calls routes unauthenticated and checks no server-held key is spent. It uses hand-written bodies and a subset of POST routes, so a new route or a changed body can slip past it.

## Why

Ledger: "BACKLOG: every-route test should build bodies from schemas + walk all POSTs" (core gate).

## Current code reality (2026-09-28)

- The every-route test landed in `238b693` (abstractcore v2.18.0) with fixed bodies.

## Scope

### In scope

- Generate a minimal valid body per route from the FastAPI/OpenAPI schema.
- Walk every POST (and every GET that can spend a key) registered on the app.

### Out of scope

- Changing the guard itself.

## Acceptance criteria

- [ ] Adding a route without a guard makes the test fail.

## Validation

Add an unguarded dummy route in a test and watch the test go RED.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
