# Scenario: Phone Thin Client (iPhone via Web/PWA) + Gateway

Goal: run a thin client UI on a phone that attaches to runs and controls them, while the gateway host owns durability and
execution.

This is especially useful for:
- remote coding/agent sessions from a phone
- observing runs while away from your workstation

## Mental model (thin client)

- The phone does not tick the runtime.
- It renders by replaying/streaming the ledger.
- It acts by sending durable commands (resume/pause/cancel/emit_event).

## Quickstart (LAN dev, no HTTPS)

1. Run the gateway bound to all interfaces (still use auth):
   - `abstractgateway serve --host 0.0.0.0 --port 8080`
2. Run the web UI host on all interfaces (dev server):
   - `npx @abstractframework/code`
3. Allow the dev origin in gateway CORS/origin allowlist.
4. Open the web UI URL on your iPhone Safari and connect it to the gateway.

## Production note (recommended)

For installable iOS PWA behavior, host the web UI over HTTPS and run the gateway behind HTTPS termination (reverse proxy
or tunnel). Restrict `ABSTRACTGATEWAY_ALLOWED_ORIGINS` to the exact UI origin.

## Canonical iPhone guide (deeper)

For a step-by-step iPhone/PWA guide, see:
- [Guide: Web deployment](../guide/deployment-web.md)
- [Guide: iPhone notes](../guide/deployment-iphone.md)
