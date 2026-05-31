# Completed: Cross-app Gateway auth and defaults convergence

## Metadata
- Created: 2026-05-30
- Status: Completed
- Completed: 2026-05-30

## ADR status
- Governing ADRs: ADR-0018, ADR-0033, ADR-0035
- ADR impact: No ADR change in this pass; the convergence behavior is covered
  by the existing Gateway/control-plane/defaults ADRs and the browser-session
  contract tracked in `0153`.

## Context
AbstractFlow now uses browser-session Gateway user auth. Other apps still have
older or duplicated auth/default patterns. Code, Observer, Assistant, and any
browser UI should converge on the same Gateway session and default-resolution
model.

## Current code reality
- Flow uses Gateway URL + user + token only during sign-in; it exchanges the
  user token for a Gateway browser session and stores only the opaque session id
  in an HTTP-only browser cookie.
- Flow mutating Gateway proxy calls carry a CSRF token, and Gateway validates it
  for session-authenticated writes.
- Code Web now supports the same hosted Gateway URL + user + token sign-in
  shape. Its static server creates an app-scoped browser session by exchanging
  the user token with Gateway server-side, stores no bearer token in
  localStorage, proxies `/api/*` with `X-AbstractGateway-Session`, and requires
  an app CSRF header for mutating calls.
- Observer now has the same hosted browser-session path and no longer persists
  Gateway bearer tokens in localStorage. Its direct bearer mode remains a local
  development escape hatch.
- Flow static/Vite-hosted session login now consumes Gateway's cookie-based
  login response correctly; it no longer assumes the Gateway session id and
  CSRF token are returned in JSON.
- Code Web start flow no longer blocks when provider/model are blank; hosted
  runs can rely on Gateway/Core defaults unless the user sets an explicit
  override.
- Observer and Code Web still have app-specific UI copy and settings layouts;
  a shared auth/default component remains optional if duplication grows.

## Problem
Users must learn different auth/default models for each app. Duplicated
provider/model/default UI causes drift and can defeat per-user isolation.

## What we want to do
Move every hosted app to Gateway user-session auth and Gateway/Core defaults.
Apps should expose provider/model only as explicit per-run, per-workflow, or
advanced overrides.

## Why
This improves security, reduces duplicated UI, and makes Gateway the consistent
deployment control plane.

## Requirements
- Flow, Code, Observer, Assistant, and future browser apps use Gateway
  user-session auth in hosted mode.
- No hosted browser app stores bearer tokens in localStorage.
- Hosted mode detection and session semantics come from
  `0153_gateway_browser_session_security_contract.md`; local/offline app modes
  remain allowed to keep local development ergonomics.
- Apps use Gateway catalogs/defaults by default.
- Provider/model pins remain available where they are natural task-specific
  overrides.
- Disconnect/sign-out clears only the browser session for that app/domain.

## Per-app hosted/local behavior matrix

This matrix is the concrete meaning of "cross-app convergence": each app keeps
its natural local ergonomics, but hosted browser surfaces share the Gateway
session/default model.

| App/surface | Hosted auth behavior | Local/development behavior | Default provider/model behavior | Notes |
|---|---|---|---|---|
| AbstractFlow web | User enters Gateway URL, user id, and user token once. The host exchanges the token for a Gateway browser session and proxies Gateway calls with session + CSRF. | Local script can print a dev user/token and start Flow/Gateway together. No ambient admin login should appear in the browser. | Nodes default to Gateway/Core capability defaults unless the flow pins provider/model. | Reference browser UX for Gateway sign-in. |
| AbstractCode Web | Hosted server exchanges Gateway user credentials server-side, stores only app-scoped session cookies, strips bearer tokens from saved browser settings, and proxies `/api/*`. | CLI/env bearer token remains acceptable for trusted local runs. | Blank provider/model means "use Gateway defaults"; explicit per-run overrides remain allowed. | No localStorage bearer token in hosted mode. |
| AbstractObserver web | Hosted server follows the same app-scoped session proxy and token-storage stripping as Code Web. | Direct bearer-token mode remains a local/operator escape hatch. | Observer should read Gateway catalogs/defaults for display and filters, not own global model defaults. | Observer remains observability UX, not the admin setup surface. |
| Gateway Console | Native Gateway browser-session app. Users sign in with user id + token; admins manage users and Gateway baselines; normal users manage their own overlays. | Same URL works locally; dev scripts print the admin/user credential to enter. | Admin/default runtime owns Gateway baseline; user runtime owns per-user overlay. Provider/model selectors must be discovery-driven. | Console is account/admin/config, not deep runtime exploration. |
| AbstractAssistant desktop | Not a hosted browser app today. It can keep CLI/env token or stored local config for trusted desktop use. | Same as hosted until a browser Assistant exists. | Gateway mode should prefer Gateway/Core defaults and only send explicit overrides when the user chooses them. | Do not force browser-cookie auth onto terminal/desktop-only surfaces. |
| Scripts/automation | Use bearer tokens or admin/user tokens directly as server-to-server credentials. | Same. | Prefer Gateway defaults unless a reproducible run needs explicit provider/model. | Automation is not browser storage; protect tokens with OS/process controls. |

Shared auth/default UI extraction is intentionally deferred. The current
duplication is understandable and app-specific enough that a shared component
could harden the wrong abstraction too early. Extract a shared component only
after two or more browser apps need the same fields, validation, cookie-status
display, logout behavior, and defaults picker with no app-specific branching.

## Design review tensions

The useful disagreement in this item is not "should apps converge" versus "do
nothing"; it is where convergence should stop.

- Centralized hosted auth/defaults vs app-local ergonomics: hosted browser apps
  should share the Gateway browser-session and Gateway/Core defaults model, but
  desktop, CLI, and trusted local development flows should keep direct token
  ergonomics. Forcing cookie auth onto every client would make automation and
  local development worse without improving hosted browser safety.
- Shared component now vs delayed extraction: a common sign-in/defaults
  component would reduce visual drift, but the apps still have different
  layouts, status affordances, and local modes. Extracting now would likely
  encode the wrong abstraction. The threshold is repeated identical behavior,
  not the existence of similar fields.
- Gateway baseline defaults vs per-user overrides: Gateway should provide the
  tenant/admin baseline so apps stop duplicating global provider/model
  configuration. Per-user overlays remain a separate `0147` concern so one
  user's defaults do not silently change everyone else's behavior.
- Gateway Console vs Observer or a future Manager/Explorer: account, admin,
  auth, and baseline configuration belong in the Gateway Console. Observer
  should stay focused on runs and platform observability. Runtime exploration is
  intentionally separate until `0151` proves the contract and UX pressure.
- Browser security vs operator escape hatches: hosted browser mode must not
  persist bearer tokens in localStorage. Server-to-server scripts and local
  operator tools can still use tokens directly, but docs and startup scripts
  must label that as trusted-local or automation behavior.

## Suggested implementation
Audit each app. Introduce shared session/auth helpers or a small common UI kit
component if duplication becomes high. Migrate app docs and settings screens to
Gateway defaults.

## Scope
- App auth/session flows.
- App provider/model default UX.
- Docs and tests.

## Non-goals
- Do not remove local/offline app modes.
- Do not remove explicit provider/model overrides needed for reproducibility.
- Do not make Observer the admin setup UI.

## Dependencies and related tasks
- `0147_gateway_per_principal_config_secrets_defaults.md`
- `0145_gateway_admin_console_bootstrap.md`
- `0153_gateway_browser_session_security_contract.md`
- `0150_observer_manager_responsibility_split.md`

## Expected outcomes
- A Gateway user can sign in consistently across apps.
- Apps default to Gateway/Core configuration without duplicating global default
  settings.
- Hosted app auth no longer relies on app-local admin/server tokens.

## Validation
- Per-app login/logout tests.
- Token storage audit proving no localStorage bearer token in hosted mode.
- Blank provider/model smoke tests resolving through Gateway defaults.
- Cross-app Alice/Bob isolation smoke tests.

## Progress checklist
- [x] Audit Code Web auth/default storage.
- [x] Audit Observer auth/default storage.
- [x] Audit Assistant Gateway mode auth/defaults.
- [x] Migrate Code Web hosted mode to Gateway browser-session proxy auth.
- [x] Migrate Observer hosted mode to Gateway browser-session proxy auth.
- [x] Fix Flow static/Vite session login to parse Gateway login cookies.
- [x] Define per-app hosted/local auth/default behavior matrix.
- [x] Decide whether to extract shared auth/default UX now. Result: defer; the
  current app-specific duplication is acceptable and a shared component should
  wait until two or more apps need the same fields, validation, status display,
  logout behavior, and defaults picker without app-specific branching.
- [x] Add initial token-storage and hosted proxy smoke tests.
- [x] Update package and framework docs/tests for the current convergence
  behavior.

## Recent audit notes
- Code Web and Observer now store only app-scoped browser-session cookies in
  hosted mode. Their settings persistence explicitly strips `auth_token`, and
  their packaged servers reject browser-supplied Gateway URL changes on
  non-local hosted UI hostnames unless an explicit app override is enabled.
- Assistant remains a local/desktop client and can keep CLI/env bearer-token
  ergonomics until a hosted browser surface exists.
- Flow is the reference implementation for the current browser session contract.

## Recent validation
- `npm test -- --run src/lib/storage.test.ts` in `abstractcode/web` -> 1 passed.
- `npm test -- --run src/ui/auth_storage.test.ts` in `abstractobserver` -> 1 passed.
- `npm run build` in `abstractcode/web` -> passed.
- `npm run build` in `abstractobserver` -> passed.
- `npm run build` in `abstractflow/web/frontend` -> passed.
- `node --check abstractcode/web/bin/cli.js && node --check abstractobserver/bin/cli.js && node --check abstractflow/web/frontend/bin/cli.js` -> passed.
- Stub-Gateway hosted-session proxy smoke tests for AbstractCode Web,
  AbstractObserver, and AbstractFlow static server -> passed. The smoke tests
  verified cookie-based login exchange, no token leakage into app cookies,
  Gateway session/CSRF injection, browser cookie stripping, Authorization
  stripping, and app CSRF enforcement for mutating proxied calls.
- `python -m pytest abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py -q` -> 21 passed, 2 warnings.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_principal_isolation_matrix.py abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_abstractflow_editor_gateway_contract.py -q` -> 26 passed.

## Guidance for the implementing agent
Preserve task-specific app ergonomics. The goal is not to make all apps look the
same, but to make identity, defaults, and secrets consistent.

## Completion report

Date: 2026-05-30

Summary:
- Documented the concrete per-app hosted/local auth/default behavior matrix for
  AbstractFlow Web, AbstractCode Web, AbstractObserver Web, Gateway Console,
  AbstractAssistant desktop, and scripts/automation.
- Confirmed the shared auth/default component should not be extracted yet. The
  right criterion is repeated identical behavior across multiple browser apps,
  not a desire for visual uniformity.
- Verified the current hosted browser apps use Gateway browser-session proxy
  auth and do not persist Gateway bearer tokens in browser settings.
- Repaired one stale AbstractFlow CLI doc sentence so it now says Flow stores
  the opaque Gateway session id, not the user token.

Files or symbols touched:
- `docs/backlog/completed/0149_cross_app_gateway_auth_defaults_convergence.md`
- `docs/backlog/overview.md`
- `docs/backlog/planned/gateway-control-plane/README.md`
- `docs/backlog/planned/gateway-control-plane/0147_gateway_per_principal_config_secrets_defaults.md`
- `docs/backlog/planned/gateway-control-plane/0153_gateway_browser_session_security_contract.md`
- `docs/guide/gateway-security.md`
- `llms.txt`, `llms-full.txt`
- `abstractflow/docs/cli.md`

Validation:
- `rg` audit across AbstractFlow, AbstractCode Web, AbstractObserver, and root
  docs for hosted auth/default/token-storage wording.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_principal_isolation_matrix.py abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_abstractflow_editor_gateway_contract.py -q` -> 26 passed.
- `python -m py_compile abstractgateway/src/abstractgateway/routes/gateway.py abstractgateway/src/abstractgateway/security/sessions.py abstractgateway/src/abstractgateway/security/gateway_security.py` -> passed.
- `python /Users/albou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/albou/.codex/skills/architect` -> passed.
- `python /Users/albou/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/albou/.codex/skills/review` -> passed.

Behavior changes:
- No runtime behavior change is introduced by completing this item. The
  behavior had already landed in Flow, Code Web, Observer, Gateway session
  routing, and Gateway defaults. This completion closes the planning item by
  making the behavior matrix, deferral decision, docs state, and validation
  explicit.

Residual risks:
- Direct bearer-token mode remains available for local/operator development in
  Code Web and Observer. This is intentional, but hosted docs must continue to
  steer users toward browser-session proxy auth.
- AbstractAssistant is still a local/desktop client. If a hosted browser
  Assistant appears, it should implement the same Gateway browser-session
  contract rather than reusing desktop token storage.
- A shared auth/default component should be revisited only when duplicate app
  implementation creates proven drift or maintenance cost.

Follow-ups:
- Keep `0153` open as the durable session/cookie contract while new browser
  apps are added.
- Keep `0147` open for provider-secret storage/injection boundaries; `0149`
  does not solve per-user provider credentials.
- See proposed item `0155` before extracting a shared hosted proxy helper; the
  current posture is package-local code plus conformance tests.
