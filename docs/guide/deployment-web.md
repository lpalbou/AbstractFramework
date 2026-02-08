# Web Deployment (Browser UI + Gateway)

This guide covers deploying a browser UI (Observer / Flow Editor / Code Web UI) against an AbstractGateway.

## What "gateway-first" means

- The browser does not tick the runtime.
- It renders by replaying/streaming the ledger.
- It acts by sending durable commands (start/resume/pause/cancel/emit_event).

## Minimum gateway settings (browser access)

Set these on the gateway host:

```bash
export ABSTRACTGATEWAY_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABSTRACTGATEWAY_ALLOWED_ORIGINS="http://localhost:*,http://127.0.0.1:*"
```

Start the gateway:

```bash
abstractgateway serve --host 127.0.0.1 --port 8080
```

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
- Auth token: your `ABSTRACTGATEWAY_AUTH_TOKEN`

## Production notes (high-signal)

- Terminate TLS at a reverse proxy and forward to `127.0.0.1:8080`.
- Restrict `ABSTRACTGATEWAY_ALLOWED_ORIGINS` to exact UI origins (avoid broad wildcards).
- Keep the gateway token secret and rotate it like any control-plane credential.

See [Guide: Gateway exposure security](gateway-security.md).

