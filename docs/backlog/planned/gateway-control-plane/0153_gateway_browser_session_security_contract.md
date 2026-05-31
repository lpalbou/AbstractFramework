# Planned: Gateway browser session security contract

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: Needs new ADR or ADR revision

## Context
Flow already uses browser-session Gateway auth, and the Gateway Console plus
other hosted apps need the same security model. Gateway user tokens are bearer
credentials assigned to a principal. Browser sessions are app-facing sessions
that should be shorter-lived, revocable, and scoped to the browser/app origin.

## Current code reality
- Gateway exposes `/api/gateway/session/login` and
  `/api/gateway/session/logout` for registry-backed user browser sessions.
- Flow accepts Gateway URL, user id, and user token at connection time, validates
  the token, exchanges it for an opaque Gateway browser session, and stores only
  the session id in an HTTP-only Flow cookie across the Python host, Node static
  host, and Vite dev proxy.
- Flow stores a CSRF token in a separate browser cookie and sends it as
  `X-AbstractFlow-CSRF`; the Flow proxy forwards `X-AbstractGateway-Session`
  and `X-AbstractGateway-CSRF` to Gateway for mutating requests.
- Gateway invalidates browser sessions when the backing user is disabled,
  deleted, or its token hash changes.
- Gateway session cookies are HTTP-only for the session id and readable only for
  the CSRF token. They use `SameSite=Lax`, path `/`, no `Secure` flag on plain
  HTTP, and `Secure` when the request scheme or trusted proxy header is HTTPS.
  Non-remembered sessions omit `Max-Age`; remembered sessions set `Max-Age`.
- Gateway user records store hashed bearer tokens and return generated/rotated
  tokens only once.
- Code Web and Observer now follow the same hosted-session proxy contract in
  their packaged Node servers: Gateway user credentials are exchanged
  server-side, app-scoped session cookies are issued, `/api/*` is proxied with
  `X-AbstractGateway-Session`, writes require app CSRF headers, and saved
  browser settings strip bearer tokens. They now also reject browser-supplied
  Gateway URL changes on non-local hosted UI hostnames unless an explicit
  app-specific override is enabled. Host checks trust the request `Host` header
  by default; forwarded host headers require an explicit trust-proxy env setting.
- Assistant remains a local/desktop app and can keep its CLI/env token
  ergonomics until a hosted browser surface exists.

## Problem
Without a formal contract, apps can blur long-lived Gateway user tokens with
browser sessions, duplicate token handling, store bearer tokens in browser
storage, or implement inconsistent logout/revocation semantics. Admin UI work
would then normalize brittle auth behavior.

## What we want to do
Define and implement a hosted browser-session contract for Gateway-connected
apps. Apps should exchange a Gateway user token for an app/browser session and
then proxy Gateway requests with server-side session credentials. Browser code
must not retain the bearer token after connection.

## Requirements
- Browser apps never store Gateway bearer tokens in `localStorage`,
  `sessionStorage`, IndexedDB, or readable cookies in hosted mode.
- Session cookies are `HttpOnly`, `Secure` when served over HTTPS, use an
  explicit `SameSite` posture, and have deliberate domain/path scoping.
- Mutating routes have a CSRF posture appropriate to the deployment mode.
- Sessions have expiry, logout, and server-side revocation behavior.
- A rotated or disabled Gateway user token invalidates future session creation;
  policy defines whether existing sessions are revoked immediately.
- Error and discovery responses distinguish unauthenticated, expired,
  revoked, and forbidden states without leaking hidden resources.
- Local/offline app modes may keep their existing development ergonomics, but
  hosted mode must use this contract.

## Scope
- Gateway-connected browser session contract.
- Shared app expectations for Flow, Code Web, Observer, Gateway Console, and
  future browser apps.
- Tests for cookie flags, logout, revocation, and token-storage audit.

## Non-goals
- Do not replace Gateway user tokens as the principal credential.
- Do not force terminal/local-only apps to use browser cookies.
- Do not implement a full external IdP/OIDC flow in this item.

## Dependencies and related tasks
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0145_gateway_admin_console_bootstrap.md`
- `../../completed/0149_cross_app_gateway_auth_defaults_convergence.md`
- `docs/backlog/completed/0141_flow_browser_session_gateway_auth.md`

## Expected outcomes
- Hosted browser apps share one clear session/security model.
- Admin console work does not rely on raw bearer-token storage in the browser.
- Cross-app convergence has a concrete auth contract to implement against.

## Validation
- Browser tests prove Gateway bearer tokens are not present in web storage.
- Cookie flag tests cover hosted and local-dev variants.
- Logout and revocation tests prevent continued Gateway proxying.
- CSRF tests cover mutating routes exposed through app sessions.
- Origin tests cover same-origin/localhost and explicitly allowlisted
  cross-origin hosted apps while rejecting untrusted origins.

## Recent validation
- `npm test -- --run src/lib/storage.test.ts` in `abstractcode/web` -> 1 passed.
- `npm test -- --run src/ui/auth_storage.test.ts` in `abstractobserver` -> 1 passed.
- Stub-Gateway hosted-session proxy smoke tests for AbstractCode Web,
  AbstractObserver, and AbstractFlow static server -> passed.
- `npm run build` in `abstractcode/web`, `abstractobserver`, and
  `abstractflow/web/frontend` -> passed.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_security_middleware_unit.py abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py` -> 44 passed.
- `npm run build` in `abstractflow/web/frontend` -> TypeScript and Vite production build passed.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_principal_isolation_matrix.py abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_abstractflow_editor_gateway_contract.py -q` -> 26 passed.
- `python -m py_compile abstractgateway/src/abstractgateway/routes/gateway.py abstractgateway/src/abstractgateway/security/sessions.py abstractgateway/src/abstractgateway/security/gateway_security.py` -> passed.

## Progress checklist
- [x] Define session issuance and cookie semantics for Gateway and Flow.
- [x] Define CSRF and logout/revocation behavior for Gateway and Flow.
- [x] Add shared hosted-mode detection expectations.
- [x] Add Gateway/Flow tests and app migration guidance.
- [x] Migrate Code Web and Observer from raw browser bearer-token storage.
- [x] Add full cookie/origin/session matrix tests across HTTP, HTTPS,
  same-origin, allowlisted cross-origin, untrusted cross-origin, expiry, logout,
  and token-rotation revocation.

## Guidance for the implementing agent
Keep user tokens and browser sessions separate. A token authenticates a
principal to Gateway; a browser session lets a specific app/browser continue
acting for that principal under tighter cookie, expiry, and revocation rules.
