# Completed: Flow browser-session Gateway auth

## Metadata
- Created: 2026-05-29
- Status: Completed
- Completed: 2026-05-30

## ADR status
- Governing ADRs: ADR-0018, ADR-0033
- ADR impact: May revise existing ADR

## Context
AbstractFlow's browser editor uses a Flow server/proxy to inject Gateway auth
into `/api/gateway/*` requests. Browser login is now scoped to the browser
session and does not treat server/admin tokens as browser login state. This
item describes the initial Flow-side boundary; planned item 0153 supersedes the
raw token cookie implementation with opaque Gateway browser sessions and CSRF.

## Current code reality
- `abstractflow/web/backend/services/gateway_connection.py` persists only the
  Gateway URL and resolves browser auth only from session cookies.
- `abstractflow/web/backend/routes/connection.py` validates submitted user tokens
  through Gateway `/me`, rejects admin/server principals, and sets only
  HTTP-only browser cookies.
- `abstractflow/web/frontend/bin/cli.js` and
  `abstractflow/web/frontend/vite.config.ts` use the same browser-cookie
  session model for status and proxy auth.
- `abstractflow/web/frontend/src/components/GatewayConnectionModal.tsx` presents
  Gateway URL, user, and Gateway token; tenant/runtime are returned by Gateway
  as read-only principal metadata.

## Problem
The original problem was that server-configured Gateway tokens could become
ambient browser auth. The current implementation removes that fallback for
browser requests.

## What we want to do
Keep browser-session authentication as the default AbstractFlow hosted behavior
so each browser/user must authenticate and only receives access to its own
Gateway connection state.

## Why
Hosted Flow deployments need a clear security boundary. Gateway tokens are control-plane credentials and must not become ambient shared credentials for every browser that can load the Flow UI.

## Requirements
- Store Gateway connection state per browser session, not as a single global
  process token.
- Ensure `/api/gateway/*` proxy injection resolves the token from the browser
  session.
- Preserve local loopback ergonomics while still requiring browser sign-in.
- Keep Gateway bearer tokens out of browser `localStorage`/`sessionStorage`.
- Make remote Gateway URL changes explicit through
  `ABSTRACTFLOW_ALLOW_REMOTE_BROWSER_GATEWAY_CONFIG`.

## Suggested implementation
- Use HTTP-only browser cookies for Gateway URL/token session state.
- Remove `CONNECTION.gatewayToken`/`ABSTRACTGATEWAY_AUTH_TOKEN` fallback use from
  browser status and proxy paths.
- Teach the Python FastAPI host, Node static server, and Vite dev proxy the
  same session resolution semantics.

## Scope
- AbstractFlow web backend connection routes.
- AbstractFlow Node static server connection/proxy path.
- Vite dev connection/proxy path.
- Documentation and security guidance for hosted Flow deployments.

## Non-goals
- Do not change AbstractGateway's own bearer-token model in this item.
- Do not store Gateway tokens in browser storage.
- Do not make public multi-user hosting depend on a single shared Gateway token unless explicitly configured by the operator.

## Dependencies and related tasks
- ADR-0018 durable gateway/control-plane model.
- ADR-0033 install profiles and server boundaries.
- `abstractflow/docs/web-editor.md`
- `abstractflow/docs/architecture.md`
- `abstractflow/web/backend/routes/connection.py`
- `abstractflow/web/frontend/bin/cli.js`

## Expected outcomes
- A distinct browser session connecting to the same hosted Flow server cannot use another session's Gateway token.
- Hosted Flow can require each browser/user to authenticate or provide its own token.
- Local single-user development remains easy and documented.

## Validation
- Unit/integration test with two browser clients and separate cookies proves isolation.
- Regression test proves loopback local configuration still works.
- Proxy auth tests prove `/api/gateway/*` injects the session token, not a stale process-global token.
- Documentation explains local, single-user hosted, and multi-user hosted security modes.

## Progress checklist
- [x] Choose session/auth store design and hosted-mode defaults.
- [x] Implement Python backend session-scoped connection storage.
- [x] Implement Node static server session-scoped connection storage.
- [x] Align Vite dev proxy behavior for local development.
- [x] Add browser-session proxy isolation tests.
- [x] Update Flow security docs and generated docs indexes.

## Follow-up guidance
Keep browser-session auth as the default Flow behavior. Future work should add
CSRF/session-hardening tests and extend the same current-user auth model to
Code, Assistant, Observer, and bridge-hosted app flows.
