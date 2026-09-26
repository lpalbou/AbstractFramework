# 0894 — Migrate AbstractFlow's and Code web's gateway proxies onto @abstractframework/app-server

> Package: abstractuic (app-server); abstractflow (bin/cli.js, bin/gateway_forwarding.js, vite.config.ts); abstractcode (web/bin/server.js)
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: proxy, app-server, security, dedup

## Summary

Observer, Entity and Continuum proxy the gateway through `@abstractframework/app-server`
(`createGatewaySessionProxy`). AbstractFlow (`bin/cli.js`, ~1,000 lines, with WebSocket proxying) and
Code web (`bin/server.js`, ~760 lines) still carry their own proxies. The 2026-09-25/26 wave made all
three emit the same wire format (one `X-Forwarded-For` = socket peer, one
`X-AbstractFramework-App-Proxy` marker, client forwarding headers dropped, unknown peer → 400), but
by three copies of `socketPeerAddress` and the strip list. The app-server lacks what Flow and Code
need before they can move: WebSocket proxying, a pre-login token check, and their status response
shape. Separately, AbstractFlow's vite DEV proxy strips `X-Forwarded-*` and sends neither the peer nor
the marker. This item realises the trigger of `proposed/gateway-control-plane/0155_hosted_proxy_shared_helper_extraction.md`
("extract a shared Node helper only if … drift again"), which predates app-server.

## Why

- B report, P-flow: "the vite dev proxy lacks the headers; migrating Flow onto
  @abstractframework/app-server needs WebSocket proxying + pre-login token check + status shape in
  app-server first (~600 lines of proxy code to retire)".
- REVIEW/12: "Three copies of one function … A fourth header added to one list will drift."

## Current code reality (2026-09-26; abstractuic `7a5cd8e`, abstractflow `0df9c65`, abstractcode `2baacf3`)

- `abstractuic/app-server/src/index.js` exports only `createGatewaySessionProxy`,
  `normalizeGatewayUrl`; no WebSocket upgrade path (REVIEW/12 scope note). Version 0.1.10, unreleased.
- `abstractflow/bin/cli.js` (1,044 lines) handles `upgrade` (l.375, l.884–907);
  `bin/gateway_forwarding.js` (63 lines) is Flow's copy of the forwarding rules.
- `abstractflow/vite.config.ts` l.463–480: dev `/api` proxy, `ws: false`, removes `X-Forwarded-For`/
  `-Host`/`-Proto`, sets no peer and no marker.
- `abstractcode/web/bin/server.js` (763 lines): own `socketPeerAddress` l.106, `APP_PROXY_HEADER`
  l.116, peer checks l.418/583.

## Scope

### In scope

- app-server: WebSocket proxying with the same header rules; optional pre-login token check; a
  configurable status shape; export `socketPeerAddress` and the strip list.
- Move Flow and Code web onto it; delete their private copies; keep their existing tests as
  conformance tests (plus the REVIEW/12 probe as a shared fixture).
- Flow vite dev proxy: same headers (or document that dev mode is loopback-only and refuse LAN).

### Out of scope

- Continuum's agora-hub WebSocket relay (not a gateway path).
- Changing the gateway's same-machine rule (0893).

## Dependencies

- app-server release (npm) before consumers can depend on it (0899 relock); 0155 folds into this item
  when promoted.

## Expected outcomes

- One implementation of the gateway-bound proxy rules across all five apps.

## Acceptance criteria

- [ ] `grep -rn "function socketPeerAddress"` finds one definition (app-server).
- [ ] REVIEW/12 probe passes against Flow (HTTP + WS), Code web and one app-server consumer.
- [ ] Flow dev proxy either forwards peer + marker or refuses non-loopback clients, tested.

## Validation

- `npm --prefix abstractuic test`; `npm --prefix abstractflow test -- --exclude 'untracked/**'`;
  `npm --prefix abstractcode/web test` (scratch HOME).
- Deliberate break: make the app-server append instead of overwrite XFF; all three consumers red.

## Evidence

- `untracked/missions-2026-09-25/B/REPORT.md` (P-flow)
- `untracked/missions-2026-09-25/REVIEW/12-proxies.md`
- `untracked/missions-2026-09-25/REVIEW/03-code-web.md` (B2)
- `untracked/missions-2026-09-25/U/REPORT.md` (Addition A-2)

## ADR status

- ADR impact: None unless the proxy contract is promoted to a package-boundary ADR (see 0155).

## Receipts

- None yet.
