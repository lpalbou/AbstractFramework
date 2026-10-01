# 0995 — Gateway-native TLS for remote browsers

> Package: abstractgateway (network, serve), abstractframework (docs)
> Type: proposal
> Created: 2026-09-30
> Priority: low
> Labels: network, https, tailscale, remote-access

## Summary

Browsers expose the microphone, the camera, the clipboard, service workers and `crypto.randomUUID`
only on https pages (or on the gateway's own computer). The supported path is `tailscale serve` or
a reverse proxy on the gateway's computer, which needs no gateway code from abstractgateway 0.10.0
on (framework 0.8.0: forwarded-origin check, manifest and icons without the app session,
`browser_url` / `browser_gateway_url`, the Tailscale paragraph in the docs). This item keeps the
assessment of a gateway-native https listener (`network set --https-cert/--https-key`, or an
automatic `tailscale cert`) for users who can run neither. Not built: about 600-900 lines and a
second listener, duplicating what `tailscale serve` does with no code.

## Current code reality (2026-10-01)

- The `fix/apps-behind-proxy` work named below is merged into the 0.8.0 wave (gateway 0.10.0);
  "on 0.9.0" statements describe the release before it.
- The gateway serves plain http only; local clients (app servers, tray, CLI, TUI, the pointer
  file) dial `http://127.0.0.1:<port>`.

## Assessment (2026-09-30)

Status: **proposed** (gateway-native TLS). The recommended path, `tailscale serve`, needs no new
gateway code once branch `fix/apps-behind-proxy` ships. Evidence is in
`untracked/day-review/https-proxy/`.

### Why https at all

Browsers expose `crypto.randomUUID`, `crypto.subtle`, `navigator.clipboard`,
`navigator.mediaDevices.getUserMedia` (voice, camera), service workers, PWA install and
`Notification` only in a secure context: https, or `localhost`/`127.0.0.1` on the gateway machine
itself. Remote access over plain `http://100.x:8080` or `http://<lan-ip>:8080` is never a secure
context. This was measured: over `http://gw.test:18412` every one of those APIs is `undefined`
(`evidence/http-vs-https-contrast.txt`). Over https (proxied) `isSecureContext === true`, and
published Code 0.8.0 and Observer 0.4.0 render with no app change (`evidence/*/05-*.png`).

### Options compared

| | `tailscale serve` (recommended) | Reverse proxy (nginx/Caddy) on the gateway machine | Gateway-native TLS (`network set --https-cert/--https-key`) |
|---|---|---|---|
| Certificate | Let's Encrypt for `<host>.<tailnet>.ts.net`, issued and renewed by tailscaled | Caddy: automatic (public DNS name needed); nginx: yours | Self-signed (trust warnings everywhere), or `tailscale cert` (renewal is ours), or your own |
| iPhone / iPad | Works in Safari once the device is on the tailnet (Tailscale app). Voice, camera and Add to Home Screen work (trusted cert) | Works with a publicly trusted cert | Self-signed: needs a configuration profile installed and "full trust" enabled in Settings → General → About → Certificate Trust Settings. Service workers and PWA refuse untrusted certs. Impractical for normal users |
| Gateway code needed | none after `fix/apps-behind-proxy` (Origin rule, manifest). On 0.9.0 today: one `network set --allowed-origins https://<host>.ts.net` | none after the fix (proxy must keep `Host` and set `X-Forwarded-Proto`) | ~600-900 lines (see below) |
| Reach | tailnet only (`tailscale funnel` = internet) | whatever the proxy exposes | whatever the bind exposes |
| Undo | `tailscale serve reset` | stop the proxy | `network set --https-cert ""` + restart |
| Local clients (app servers, tray, CLI, TUI, pointer file) | untouched: they keep `http://127.0.0.1:<port>` | untouched | **all break** if the one port becomes TLS-only (they dial `http://127.0.0.1`; a ts.net cert does not match `127.0.0.1`). A second, https-only listener is needed |

Notes on Tailscale:
- The tailnet needs MagicDNS and "HTTPS Certificates" enabled (admin console → DNS). The first
  `tailscale serve` prompts for it.
- The machine name appears in public Certificate Transparency logs (tailnet names are public).
- serve.go keeps the browser's `Host` and adds `X-Forwarded-Host`, `X-Forwarded-Proto: https`
  and `X-Forwarded-For: <tailnet IP>`. SSE is flushed. WebSocket upgrades pass through. The
  gateway believes these headers from a loopback peer only (cli.py `forwarded_allow_ips`), so the
  audit log and lockouts see the tailnet IP without turning `trust_proxy` on.
- The first-run `#claim=` link stays loopback-only by design, so a remote device signs in with
  user name and token.

### What 0.9.0 does behind `tailscale serve` (measured, Chromium + WebKit, TLS proxy forwarding exactly like serve.go)

- FAIL on 0.9.0: **console sign-in: 403 "Forbidden (origin not allowed)"** (the Origin
  allowlist does not contain `https://<host>.ts.net`). Workaround today:
  `abstractgateway network set --allowed-origins https://<host>.<tailnet>.ts.net` (live, no
  restart). Fixed on `fix/apps-behind-proxy` (https same-origin through a local TLS proxy).
- FAIL on 0.9.0, cosmetic: `manifest.webmanifest` / icons → 401 (fetched without cookies). Fixed
  on the branch (public-asset allowlist).
- PASS with the workaround: Secure console cookies. App handover lands on
  `https://<host>/apps/<id>/` with cookies `Path=/apps/<id>/; Secure; SameSite=Lax`. App API
  calls, SSE and the WebSocket upgrade go through `/apps/<id>/`. Every browser request stays on
  the page origin (no loopback, no mixed content). The page is a secure context and
  `crypto.randomUUID` is present.
- Still shows a loopback or LAN address to the remote visitor (console, A's files): the first-run
  "Console" tile (console.py:12917 `gatewayBaseUrl`) and the top-bar "Gateway address"
  (console_ui.py:2946, `copy_hint`). The seams are in COORD. The gateway now returns
  `browser_url` / `browser_gateway_url` for them.

### Backlog entry: gateway-native TLS (not built; exceeds the ≤400-line containment bar)

**Goal.** `abstractgateway network set --https-cert <pem> --https-key <pem>` (or
`--https tailscale`) makes the gateway ALSO answer https on a second port. Loopback http stays
for local clients.

**Files and steps.**
1. `network_exposure.py`: new setting fields `https: {mode: off|files|tailscale, cert, key, port}`,
   validated (readable PEM, key matches cert via `ssl.SSLContext.load_cert_chain`, port ≠ http
   port). Add them to status (`effective.https`, `addresses[]` rows with `scheme: https`,
   `copy_hint` preferring https) and to the change door (`apply_network_change`, audit line), plus
   `url_for(..., scheme)` for https rows.
2. `cli.py serve`: when https is on, run a SECOND `uvicorn.Server` in the same process and event
   loop (`asyncio.gather(server_http.serve(), server_https.serve())`) with
   `ssl_certfile/ssl_keyfile`, the same app object, the same `proxy_headers`/`forwarded_allow_ips`.
   Shutdown ordering follows the existing bounded graceful shutdown (W5's area: coordinate).
3. `tailscale` mode: `tailscale cert --cert-file <data>/tls/<host>.crt --key-file <data>/tls/<host>.key <host>.<tailnet>.ts.net`
   (host from `tailscale status --json` → `Self.DNSName`). Renewal: a daily task re-runs it and
   calls `load_cert_chain` again on the running server's `SSLContext` (new connections use the new
   cert; no restart). A missing binary or disabled HTTPS certs gives a 409 with the exact
   `tailscale` hint.
4. `routes/network.py` + CLI `network set` flags `--https-cert/--https-key/--https-port/--https tailscale|off`.
5. Surfaces: console Network page and TUI Connection screen (A), tray menu "Open console (https)".
   The pointer file keeps the loopback http URL.
6. Docs: configuration.md (TLS section, iPhone trust steps for self-signed), security.md,
   deployment.md.

**Tests (all hermetic).** A self-signed cert generated in the test (`cryptography`, or `openssl
req -x509` with a SAN for `127.0.0.1`). Uvicorn https on a scratch port with `curl -k` /
`httpx(verify=cert)`: `GET /console` 200, `scope.scheme == "https"`, Secure cookies, Origin
`https://127.0.0.1:<port>` accepted (native TLS path of `_https_same_origin`). The http loopback
listener keeps answering. A fake `tailscale` binary on PATH (writes cert/key, prints status JSON)
drives the tailscale mode, and running renewal twice proves the reload. Validation refusals:
unreadable file, key/cert mismatch, port clash. Status rows carry `scheme: https`.

**Risks.**
- Two listeners: the port allocation, restart story (`network restart`), service unit and tray all
  learn a second port.
- Self-signed certs on iOS/iPadOS are a poor experience (profile install + full trust). Without
  trust, service workers and PWA install fail and each visit shows a warning. For Apple devices,
  recommend Tailscale certificates (or a reverse proxy with a public cert), not self-signed.
- The `tailscale cert` key sits in the data dir and must be `0600`. Renewal failure has to show as
  a warning, not a silent expiry.
- It duplicates what `tailscale serve` already does with zero code. Value: only for users who
  cannot run `tailscale serve` (no admin rights on tailscaled, other VPNs, LAN-only with their own
  CA).

**Recommendation.** Ship `fix/apps-behind-proxy`, document `tailscale serve` (done on the
branch), and let A show the one-line Network-page hint. Keep gateway-native TLS proposed until a
user needs https without Tailscale or a reverse proxy.

## Acceptance criteria (if promoted)

- [ ] A second https listener; the loopback http listener keeps answering local clients.
- [ ] Hermetic tests from the plan above (self-signed cert, fake `tailscale`, renewal reload,
      validation refusals), each red without the change.
- [ ] Console Network page and terminal console Connection screen show the https address.

## Receipts

- `untracked/day-review/https-proxy/` (evidence, `B-self-proof.md`), 0994 items 43–45.
