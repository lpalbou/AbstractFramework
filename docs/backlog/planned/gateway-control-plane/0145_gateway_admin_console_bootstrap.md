# Planned: Gateway admin console bootstrap

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: May revise existing ADR

## Context
Gateway now has concrete principals, user-registry auth, admin-only user CRUD,
and per-principal runtime routing. The first usable hosted experience still
requires operators to use raw routes or scripts to see who they are, create
users, rotate tokens, and understand what runtime a user owns.

## Current code reality
- `abstractgateway/src/abstractgateway/security/principal.py` defines
  `GatewayPrincipal.is_admin()` as the `admin` role check.
- `abstractgateway/src/abstractgateway/routes/gateway.py` exposes
  `/api/gateway/me` and admin-only `/api/gateway/admin/users`.
- `abstractgateway/src/abstractgateway/users.py` stores user records with
  hashed bearer tokens, roles, scopes, enabled state, and `runtime_id`.
- `scripts/gateway-flow-local.sh` now prepares `default/admin` by default and
  gives it roles `admin,user`.
- Gateway now serves a dependency-free console at `/console`, with `/`
  redirecting there. The console uses Gateway browser sessions, reads `/me`,
  lets admins manage `/admin/users`, and lets users edit per-principal
  capability defaults.
- The console now lists retained runtime reservations and lets admins explicitly
  transfer or purge them after confirmation.
- Console user creation now collects optional email contact metadata, asks for
  confirmation before creating/deleting users, and uses Gateway discovery
  endpoints for provider/model selection instead of free-text provider/model
  fields.

## Problem
Installing or hosting Gateway is opaque. Admins need a browser-visible control
plane for first-run account state, user creation, runtime assignment, token
rotation, and runtime summary. Normal users need an account/runtime page that
does not require raw API calls.

## What we want to do
Add a narrow Gateway-served console v0 at canonical `/console`, while keeping
OpenAPI docs at `/docs`. `/` may redirect to `/console` when the console is
enabled. The first version should focus on sign-in/session state, `/me`,
account/runtime summary, and admin user management only for routes already
covered by the RBAC policy matrix. Normal users should see their own
account/runtime state and token-management options that policy permits.

## Why
Gateway is the trust boundary. A clean built-in control-plane UX reduces setup
mistakes, avoids duplicating admin configuration in Flow/Observer/Code, and
makes the `1 user = 1 runtime` model visible.

## Requirements
- Admin mutation pages are blocked on `0146` enforcement for every route they
  call; frontend hiding is not authorization.
- First-run credential disclosure is local-dev/loopback only, never a hosted
  production pattern. Hosted deployments must use explicit operator bootstrap
  and rotation paths.
- Local-dev token display must avoid server logs, respect file permissions,
  explain the token cache/recovery path, and encourage rotation.
- Login follows the browser-session contract in `0153`: Gateway user tokens are
  exchanged for app/browser sessions and are not retained in browser storage.
- Admin views: list/create/update/disable/delete users, rotate tokens, assign
  runtime ids, collect optional account email, inspect roles/scopes, transfer or
  purge retained runtime reservations.
- User views: current principal, runtime id, created date, enabled state, token
  rotation if allowed, recent activity summary if available.
- Never display token hashes or existing bearer tokens after issuance.
- Keep `/docs` available for OpenAPI.

## Suggested implementation
Start with a small static app served by Gateway and backed by existing
`/api/gateway/me` and `/api/gateway/admin/users`. Reuse AbstractUIC visual
tokens/theme primitives where practical, but keep the first version small.

## Scope
- Gateway-served console route and static assets.
- Account page and admin user-management page.
- Minimal runtime summary endpoints if current API data is insufficient and
  `0146` authorizes the route family.
- Documentation for local and hosted setup.

## Non-goals
- Do not build workflow authoring into Gateway Console.
- Do not build full run trace visualization; link to Observer.
- Do not add per-user provider secret storage in this item; that is `0147`.

## Dependencies and related tasks
- `0146_gateway_rbac_scope_policy_matrix.md` (hard prerequisite for admin
  mutation UX)
- `0153_gateway_browser_session_security_contract.md`
- `0147_gateway_per_principal_config_secrets_defaults.md`
- `docs/backlog/planned/0143_shared_gateway_per_principal_runtime_router.md`
- `abstractgateway/docs/security.md`

## Expected outcomes
- A fresh local Gateway can be administered from a browser without raw curl.
- The default local prepared user is `admin`.
- Admin-only user CRUD remains enforced server-side.
- Normal users cannot access admin pages or admin APIs.

## Validation
- Unit/API tests for admin and non-admin console API access.
- Browser/manual check: admin can create a user and rotate token; normal user
  cannot.
- Security check: no token hashes or existing tokens are returned in user lists.

## Recent validation
- `python -m pytest abstractgateway/tests/test_gateway_security_middleware_unit.py abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_console.py abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py -q` -> 51 passed, 2 warnings.
- `python -m compileall -q abstractgateway/src/abstractgateway abstractflow/web/backend` -> passed.
- Earlier full-gateway validation: `python -m pytest abstractgateway/tests` -> 261 passed, 2 skipped.

## Progress checklist
- [x] Decide console route and static asset packaging.
- [x] Implement `0153` session semantics for console login.
- [x] Add account/runtime summary page.
- [x] Add admin user-management page after `0146` route checks exist.
- [x] Add minimal per-user defaults UX through `0147` overlay APIs.
- [x] Add retained-runtime reservation transfer/purge UX.
- [ ] Add richer runtime summary/activity API if needed.
- [x] Add tests and docs.

## Implementation note - 2026-05-30

Console v0 is implemented in `abstractgateway/src/abstractgateway/console.py`
and mounted from `abstractgateway/src/abstractgateway/app.py`. It intentionally
stays narrow: session sign-in/logout, account/runtime summary, admin user CRUD,
token rotation, retained runtime reservation lifecycle, and per-principal
capability-default editing. It does not own workflow authoring, deep runtime
exploration, or raw provider secret storage.

Follow-up console polish landed in the same track: provider/model defaults now
come from Gateway discovery selectors, admin create/delete uses confirmation
modals, and user records include optional email metadata for future
notification/invite workflows. User deletion currently removes account/token
access; runtime data retention/deletion must be handled by a separate retention
policy before destructive runtime cleanup is exposed.

2026-05-31 sign-in hardening: the console sign-in form now mirrors the shared
AbstractUIC Gateway browser-session sign-in card shape, omits Gateway URL
because `/console` is same-origin with Gateway, and has a generated JavaScript
syntax regression test so a malformed inline script cannot silently break the
login button again. React thin clients should use
`GatewaySessionSignInCard` from `@abstractframework/ui-kit`; the built-in
Gateway Console remains dependency-free static HTML and mirrors the same visual
contract.

## Guidance for the implementing agent
Keep this console narrow. If it starts becoming a full observability or workflow
authoring product, stop and split the concern into later items.
