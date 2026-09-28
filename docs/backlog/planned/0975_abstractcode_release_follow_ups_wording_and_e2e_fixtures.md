# 0975 — AbstractCode follow-ups: legacy env wording in getting-started, e2e fixture reads sibling repos

> Package: abstractcode (docs, web/e2e)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: docs, tests, hermetic

## Summary

Two small findings from the abstractcode 0.7.0 gate: the getting-started page still presents the gateway environment variable before the `--gateway-url` flag (it is a legacy alias), and a web e2e fixture reads files from sibling repositories, so the suite depends on the monorepo layout.

## Why

Ledger: "getting-started env legacy wording; e2e fixture reads sibling repos" (code release follow-ups).

## Current code reality (2026-09-28)

- abstractcode `227e000` (crate 0.7.0, web 0.6.0).

## Scope

### In scope

- Docs lead with `--gateway-url`, env named as the legacy alias.
- The e2e fixture vendors what it needs.

### Out of scope

- Other docs.

## Acceptance criteria

- [ ] The e2e suite passes from a lone checkout; docs order fixed.

## Validation

Run the e2e suite from an archive of the repo alone.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
