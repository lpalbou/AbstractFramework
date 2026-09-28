# 0951 — Apps under `/apps/<id>/` share one browser origin: add defense in depth

> Package: abstractgateway (app proxy), abstractuic (app-server)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: security, apps-proxy, same-origin, defense-in-depth

## Summary

Since gateway 0.7.0 every browser app (Flow, Code, Observer, Continuum, Entity) is served on the gateway's own origin at `/apps/<id>/`, next to `/console` and the API. Cookies are isolated by path, but path is not a security boundary in browsers: script running in one app's page can read another app's DOM through same-origin frames and call the gateway API with that browser's credentials. The apps are trusted first-party code today, so this is one trust domain by design (the AbstractUIC README says so); this item adds defense in depth so a compromised or future third-party app cannot act as another app or as the console.

## Why

The AbstractUIC 0.1.14 tag gate (ledger line "Backlog after wave: /apps/* same-origin trust domain (defense in depth: per-app origins or CSP/sandboxing)").

## Current code reality (2026-09-28)

- abstractgateway `app_proxy` serves every app on the gateway origin with `Path=/apps/<id>/` cookies and refuses other origins (0.7.0, `cbe2ef5`).
- AbstractUIC `app-server` `mount.js` documents one trust domain (README, v0.1.14 `d12775f`).

## Scope

### In scope

- Choose and implement one isolation measure: per-app origins (subdomain or port per app behind the same tunnel), or a strict CSP plus `frame-ancestors`/`sandbox` and API calls scoped to the app's own session.
- Document the resulting trust model in the gateway's `docs/apps.md` and the kit README.

### Out of scope

- Changing the one-port, one-tunnel promise for the default install without an operator ruling.

## Acceptance criteria

- [ ] An app page cannot read another app's page or reuse the console's session (browser test proves it).
- [ ] The trust model is documented where apps are configured.

## Validation

A browser-level test that loads two apps and asserts the cross-app read or credential reuse fails; RED when the measure is removed.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
