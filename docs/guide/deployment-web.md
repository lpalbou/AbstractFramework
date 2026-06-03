# Web Deployment (Browser UI + Gateway)

This guide covers deploying a browser UI (Observer / Flow Editor / Code Web UI) against an AbstractGateway.

## What "gateway-first" means

- The browser does not tick the runtime.
- It renders by replaying/streaming the ledger.
- It acts by sending durable commands (start/resume/pause/cancel/emit_event).

## Minimum gateway settings (browser access)

Set these on the gateway host:

```bash
export ABSTRACTGATEWAY_USER_AUTH=1
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

Start the gateway:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

Gateway creates `default/admin` if needed and writes the first browser-login
token to `$ABSTRACTGATEWAY_DATA_DIR/auth/bootstrap-admin-token`. Use that token
for `/console` and browser apps, then create named users or rotate tokens from
the console.

## Run the UIs

```bash
npx @abstractframework/observer
npx @abstractframework/flow
npx @abstractframework/code
```

Default ports:
- Observer: http://localhost:3001
- Code Web UI: http://localhost:3002
- Flow Editor: http://localhost:3003

In each UI, set:
- Gateway URL: `http://127.0.0.1:8080`
- User: the Gateway user id assigned by the Gateway admin
- Gateway token: that user's token, used only to create the browser session

For hosted deployments on a non-local UI hostname, configure the Gateway URL on
the UI server. Browser-supplied Gateway URL changes are rejected by Flow, Code
Web, and Observer unless the app-specific
`*_ALLOW_REMOTE_BROWSER_GATEWAY_CONFIG=1` override is enabled behind your own
access control. If the UI is behind a reverse proxy that rewrites `Host`, enable
`*_TRUST_PROXY_HEADERS=1` only after the proxy strips client-supplied forwarded
headers.

## Production notes (high-signal)

- Terminate TLS at a reverse proxy and forward to `127.0.0.1:8080`.
- Restrict `ABSTRACTGATEWAY_ALLOWED_ORIGINS` to exact UI origins (avoid broad wildcards).
- Keep the Gateway admin token secret and rotate it like any control-plane
  credential.
- Hosted browser apps should keep only their app-scoped Gateway session cookie;
  do not persist user bearer tokens in browser storage.
- Do not use one shared user token for independent users. Use Gateway
  per-principal routing so each user token maps to that user's runtime.

See [Guide: Gateway exposure security](gateway-security.md).
