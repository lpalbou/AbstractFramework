# Planned: Shared Gateway per-principal runtime router

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: May revise existing ADR

## Context
A shared AbstractGateway front door can be the right hosted architecture when it
acts as an authenticated router/control plane and routes each principal to an
isolated runtime/data plane. This avoids a separate public Gateway URL per user
while preserving the isolation properties of separate runtimes.

An adversarial review compared the strongest pro and con arguments. Both sides
converged on the same boundary: the design is sound if the shared Gateway routes
to isolated per-user or per-tenant `GatewayService`/Runtime contexts. It is not
sound if the Gateway keeps one shared service/stores/runtime and merely adds
`user_id` labels.

## Current code reality
- `abstractgateway/src/abstractgateway/security/gateway_security.py` validates
  global bearer tokens and origin policy. It does not currently resolve a
  trusted `Principal` with `tenant_id`, `user_id`, roles, or scopes.
- `abstractgateway/src/abstractgateway/service.py` exposes a singleton
  `GatewayService` with one config, one store set, one host, one runner, one
  auth policy, one embedding client, and optional bridges.
- `abstractgateway/src/abstractgateway/stores.py` builds one file or SQLite
  store set rooted at the configured Gateway data directory.
- `abstractgateway/src/abstractgateway/routes/gateway.py` has many endpoints
  that operate on caller-supplied ids such as `run_id`, `session_id`,
  `artifact_id`, and `bundle_id`. Those ids are references, not authorization
  proofs.
- Session memory owner ids are derived from caller-controlled session ids in
  several paths; global memory is runtime-instance global, not tenant global.
- VisualFlow/bundle publish, artifact search/listing, workspace/file helpers,
  prompt-cache routes, maintenance/process-manager routes, Telegram/email
  bridges, and background command processing are currently designed around the
  singleton service/data-plane shape.

## Problem
Hosted Flow/Gateway needs a multi-user story that is both ergonomic and safe.
One Gateway per user is conceptually simple but operationally heavy: it creates
endpoint sprawl, certificate/domain management overhead, duplicated routing,
harder upgrades, version skew, and more complicated Flow connection UX.

A single shared Gateway front door can solve those operational issues, but a
partial implementation can be worse than no implementation. Routing only LLM
calls per user while leaving runs, ledgers, artifacts, commands, memory,
workspaces, prompt cache, bundles, provider credentials, or background workers
global would still leak or mix users.

## What we want to do
Introduce a hosted-mode architecture where:

```text
Flow/browser
  -> authenticated shared Gateway front door
    -> trusted principal resolution
      -> server-side principal-to-runtime routing
        -> isolated GatewayService / Runtime context
          -> isolated stores, memory, artifacts, workspace, secrets, queues
```

The first implementation should prefer isolated per-principal data planes over
shared stores with tenant columns. A single process may hold several
per-principal service objects, but each object must own its own data directory,
stores, runner/queue, workspace root, provider defaults, secret scope, memory,
artifact store, and prompt-cache namespace.

## Why
This architecture keeps the hosted product manageable while preserving the main
security benefit of per-user runtimes. It gives Flow one stable API endpoint and
lets login determine identity and runtime selection. It also creates a better
foundation for later org/team features: admin consoles, billing, quotas, scoped
collaboration, audit, and explicit shared memory.

## Requirements
- Add a trusted `Principal` model resolved by Gateway auth middleware or a
  trusted front-door integration. It should include at least `tenant_id`,
  `user_id`, roles/scopes, and token/session fingerprint metadata.
- Gateway owns hosted-mode authentication. Apps such as AbstractFlow,
  AbstractCode, AbstractAssistant, and AbstractObserver must authenticate as the
  current user/session and forward only trusted Gateway credentials or cookies;
  they must not share one app-server Gateway token across all browser users.
- Add admin-level user management routes for Gateway operators to list, create,
  update, disable, delete, and rotate credentials for users. These routes must
  require an admin principal and must never disclose stored token hashes.
- Clients must not send authoritative `user_id`, `tenant_id`, `runtime_id`, or
  workspace root values. If accepted for UX, they must be advisory and checked
  against server-side policy.
- Add a server-side `Principal -> RuntimeContext/GatewayService` router.
- Each per-principal context must own an isolated data plane:
  - data directory;
  - run store and ledger store;
  - command inbox/cursor store and runner;
  - artifact store;
  - memory/KG owner namespace or store;
  - prompt-cache/bloc namespace or disabled hosted-mode prompt cache;
  - workspace root and mount policy;
  - provider defaults, credentials, quotas, and secrets.
- Admin/global endpoints must be separated from user endpoints. Hosted mode
  should disable or admin-gate unscoped global enumeration and mutation paths.
- Bundles/VisualFlows must be either tenant-local or global read-only with
  admin-only publishing.
- Every read/write path must authorize against the resolved principal, including
  run start/list/detail, ledger replay/SSE, history bundle, resume/cancel,
  commands, artifacts, uploads/import/export, memory/KG, prompt cache, workflow
  CRUD/publish, workspace/file tools, provider config, maintenance routes, and
  bridge-triggered runs.
- Background workers must carry tenant context through queued commands, child
  runs, event emission, artifact projection, and resume paths.
- Logs, traces, temporary files, metrics, audit records, and error reports must
  avoid unscoped user content or include principal-safe ownership metadata.

## Suggested implementation
1. Add a principal abstraction and middleware hook, but keep local single-user
   mode as a default principal.
2. Introduce a `GatewayServiceRouter` composition root that returns the current
   principal's service/context instead of the process-wide singleton service.
   In the first code slice, preserve the public `get_gateway_service()` helper
   but make it resolve through a request context variable when hosted user auth
   is enabled. This lets the existing route surface inherit per-principal data
   planes before every endpoint is converted to explicit dependencies.
3. Implement hosted v0 using separate data directories and store sets per
   principal. Avoid a shared DB/schema migration in the first version.
4. Add `/api/gateway/me` and `/api/gateway/admin/users` before app-specific
   login UX so Flow and native apps can test the resolved principal contract.
5. Move route dependencies from `get_gateway_service()` to
   `get_gateway_service_for_principal(...)` or an equivalent request-scoped
   dependency as route families are touched.
6. Make global/admin surfaces explicit and fail closed in hosted mode:
   broad artifact search, `scope=all`, arbitrary owner ids, workflow publishing,
   process manager, backlog execution, local workspace tools, bridge admin
   config, and provider credential mutation.
7. Add app-auth adapters: browser apps should rely on Gateway session cookies or
   request-bound user bearer tokens, while native apps should use user API
   tokens/device login. All apps should call `/api/gateway/me` after connect.
8. Add a two-user test harness that tries guessed ids across every route family.

## Scope
- AbstractGateway security, service composition, routes, stores, runner,
  artifacts, workflow/bundle registry, memory/KG integration, prompt cache,
  workspace policy, provider defaults, maintenance routes, and bridge entry
  points.
- AbstractRuntime ownership context where run state, child runs, memory owner
  ids, prompt-cache bindings, and artifact projection need durable tenant
  provenance.
- AbstractFlow hosted connection UX for identity-aware Gateway discovery and
  no browser-controlled runtime selection.
- Documentation and ADR updates for supported hosted topologies.

## Non-goals
- Do not build a shared `GatewayService`/store set with only `user_id` labels as
  the first version.
- Do not claim that the current Gateway bearer token model provides per-user
  isolation.
- Do not trust caller-supplied `session_id`, `run_id`, `artifact_id`,
  `owner_id`, or `bundle_id` as authorization.
- Do not make cross-user memory or learning implicit. Shared/team memory must be
  a later explicit namespace with consent, ACLs, audit, deletion semantics, and
  poisoning controls.
- Do not turn workspace scoping into a claimed OS sandbox.
- Do not expose per-user runtime URLs or internal routing identifiers to the
  browser as control inputs.

## Dependencies and related tasks
- `docs/backlog/completed/0141_flow_browser_session_gateway_auth.md`
- `docs/backlog/planned/0142_gateway_tenant_isolation_and_shared_runtime.md`
- `abstractgateway/docs/backlog/proposed/2026-05-13_shared_identity_context.md`
- ADR-0018 durable Gateway/control-plane contract.
- ADR-0021 deployment topologies and supported scenarios.
- ADR-0033 install profiles and server boundaries.

## Expected outcomes
- Hosted Flow can connect to one public Gateway endpoint while each
  authenticated user/tenant receives an isolated runtime/data plane.
- Alice cannot enumerate, read, stream, resume, cancel, export, import, mutate,
  or infer Bob's runs, ledgers, artifacts, sessions, memory, prompt cache,
  workspaces, bundles, provider credentials, or command inbox.
- Gateway operators can run local single-user mode, trusted-cohort mode, or
  hosted per-principal runtime-router mode with explicit documentation.
- Shared/team memory and collaboration remain future explicit product features,
  not accidental leakage from shared infrastructure.

## Validation
- Unit tests for principal extraction, token/session fingerprinting, scope
  checks, and service-router selection.
- Two-user integration tests proving guessed `run_id`, `session_id`,
  `artifact_id`, `bundle_id`, and memory owner ids cannot cross principals.
- SSE/ledger/history tests proving streams and batch replay are principal-bound.
- Command/resume/cancel tests proving queued records carry tenant context.
- Artifact upload/list/search/content/export/import tests with Alice/Bob data.
- VisualFlow/bundle tests for tenant-local or admin-only global publishing.
- Workspace/file-tool tests proving hosted mode uses per-principal roots and
  rejects arbitrary absolute roots.
- Prompt-cache tests proving hosted mode scopes or disables shared cache state.
- Audit/log checks proving bearer tokens are never logged and user content is
  scoped/redacted.

## Progress checklist
- [x] Run adversarial two-subagent review for the shared Gateway router design.
- [x] Define `Principal` and hosted-mode auth contract.
- [x] Add admin user registry and admin-only CRUD routes.
- [x] Design `GatewayServiceRouter` and local single-user compatibility mode.
- [x] Implement per-principal data directories and service contexts.
- [x] Convert existing route dependencies to request-scoped service lookup via
      the `get_gateway_service()` composition root.
- [ ] Admin-gate or disable global surfaces in hosted mode.
- [ ] Carry principal context through runner/command/background paths.
- [x] Add `/api/gateway/me` and app policy display.
- [x] Change AbstractFlow hosted auth to current-user Gateway credentials rather
      than one app-server token.
- [ ] Change AbstractCode/Assistant/Observer hosted auth to current-user Gateway
      credentials rather than one app-server token.
- [ ] Add the two-user isolation test matrix.
- [ ] Update ADRs and hosted deployment docs.

## Review notes: 2026-05-30
Two independent subagent reviews agreed that a shared Gateway can scale as a
control-plane/router only if the per-user data planes are separate. The first
implementation should therefore add identity resolution, admin user CRUD, and
request-scoped service routing before attempting route-by-route tenant columns.

The reviews also called out a hard boundary for hosted apps: AbstractFlow and
other frontends cannot safely use one server-held Gateway token for all users.
They need a current-user auth/session path that lets Gateway resolve the
principal and route to that user's runtime. Until that app-auth migration is
finished, hosted multi-user deployments must be treated as an incremental beta
surface rather than a complete isolation guarantee across every app workflow.

## Implementation report: 2026-05-30
- Added `GatewayPrincipal`, request context propagation, and legacy-token
  compatibility where `ABSTRACTGATEWAY_AUTH_TOKEN` resolves to `local-admin`.
- Added a file-backed `GatewayUserRegistry` at
  `<ABSTRACTGATEWAY_DATA_DIR>/auth/users.json` by default. User tokens are
  PBKDF2-SHA256 hashed; generated/rotated tokens are returned once.
- Added `GET /api/gateway/me` and admin-only
  `/api/gateway/admin/users` list/create/read/update/delete routes.
- Added request-scoped service routing: when user auth is enabled,
  `get_gateway_service()` resolves the current principal and returns a
  per-principal `GatewayService` with separate runtime/flows directories under
  `<DATA_DIR>/users/<tenant_id>/<runtime_id>/`.
- Kept local/single-user Gateway behavior compatible: without user auth, the
  process-wide singleton service and legacy token model remain.
- Changed AbstractFlow hosted connection handling so remote browser sessions
  sign in with Gateway URL, Gateway user id, and user token. Flow validates that
  Gateway `/me` resolves to that expected user before accepting the connection.
  Gateway owns the user's tenant/runtime mapping and returns it as read-only
  principal metadata. This was later hardened by 0153: Flow now exchanges the
  user token for an opaque Gateway browser session, keeps only the session id in
  an HTTP-only browser cookie, and forwards the session plus CSRF token for
  mutating Gateway proxy calls. Different browsers must connect as their own
  Gateway users.
- Simplified the AbstractFlow modal to the three intended fields
  (`Gateway URL`, `User`, `Gateway token`), removed the tenant/runtime input,
  renamed the primary action to sign in, and made the resolved runtime a
  read-only status detail returned by Gateway.
- Hardened the Flow Gateway proxy so browser-supplied `Authorization`, `Cookie`,
  `X-Forwarded-*`, and other unapproved headers are stripped before proxying;
  Flow injects only the resolved Gateway browser session.
- Hardened Gateway admin routes so they fail closed if the router is mounted
  without `GatewaySecurityMiddleware` while Gateway security is enabled.
- Updated Gateway and Flow docs plus `llms.txt`/`llms-full.txt` files to
  describe the new auth/routing contract and remaining hosted-mode limits.

Remaining work is intentionally still open: admin-gating every global/operator
route family, carrying principal context through every background/bridge path,
changing Code/Assistant/Observer hosted auth, and expanding the Alice/Bob
guessed-id isolation matrix across run, artifact, memory, workspace,
prompt-cache, process, and maintenance endpoints.

## Guidance for the implementing agent
Start by preserving the strong isolation boundary: separate per-principal data
planes. Resist the shortcut of adding owner labels to the existing singleton
service. Add authorization at the lowest shared layer available, not only in
route handlers. Re-run the adversarial review before promoting shared stores,
shared prompt cache, shared memory, or collaborative features.
