# 0976 — Gateway returns rooted server URLs that bypass a standalone app's proxy

> Package: abstractgateway (run and workspace payloads), abstractuic (host routing)
> Type: improvement
> Created: 2026-09-28
> Priority: normal
> Labels: contract, apps-proxy, urls

## Summary

The gateway returns rooted URLs (`ledger_url`, `workspace_url`, `artifacts[].url`). Under the gateway's `/apps/<id>/` proxy they resolve against the gateway with the gateway session, which works. A standalone app on its own port proxies the gateway under its own path, so a rooted URL bypasses that proxy. AbstractUIC routes known rooted links through the host; the contract question is whether the gateway should return relative or explicitly gateway-rooted links.

## Why

Ledger: "Open contract question (not blocking): gateway returns rooted server URLs ... Backlog item after the wave."

## Current code reality (2026-09-28)

- Kit host-routed links landed on AbstractUIC (wave 2); gateway payloads unchanged in 0.7.0.

## Scope

### In scope

- Decide the URL contract, document it, and adjust the gateway or the kit accordingly.

### Out of scope

- Changing the proxy.

## Acceptance criteria

- [ ] Every server-supplied link works in both the proxied and the standalone app.

## Validation

App e2e in both modes.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
