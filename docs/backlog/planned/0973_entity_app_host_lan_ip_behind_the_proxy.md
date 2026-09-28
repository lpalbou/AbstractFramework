# 0973 — Entity: `/app/host` reports the app server's LAN address

> Package: abstractentity (bin/server.js)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: entity, privacy, apps-proxy

## Summary

The Entity server answers `/app/host` with its first non-internal IPv4 so the UI can display an entity handle like `ephemeral@192.168.1.146`. Served through the gateway at `/apps/entity/` and possibly reached through a tunnel, this exposes the machine's LAN address to any signed-in viewer, and names the app server's host rather than the gateway's. Decide where the handle's host comes from (the gateway, which knows its public address) and who may see it.

## Why

Ledger: "entity /app/host LAN IP" (apps gate).

## Current code reality (2026-09-28)

- `abstractentity/bin/server.js:119` (`/app/host`, `os.networkInterfaces()`), read by `src/entity_view.tsx:196` (entity 0.3.0).

## Scope

### In scope

- Take the handle's host from the gateway, or limit the LAN address to viewers on this machine.

### Out of scope

- Entity handle format.

## Acceptance criteria

- [ ] A remote viewer does not receive the LAN address unless the operator chose so.

## Validation

Server test for a remote viewer.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.
