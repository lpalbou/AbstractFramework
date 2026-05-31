# Planned: Multi-user security release blockers

## Metadata
- Created: 2026-05-30
- Status: Completed
- Completed: 2026-05-30

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: None. This item enforces the current Gateway control-plane and browser-session decisions.

## Context
The multi-user Gateway work introduced user-authenticated browser sessions,
per-principal runtime routing, and hosted app proxy sessions. A review found
three release-blocking gaps: retained runtime data could be reassigned after
user deletion, Code Web and Observer allowed browser-supplied Gateway URL
changes on hosted hosts, and the published Gateway/Flow launcher did not
bootstrap Gateway users for browser login.

## Current code reality
- `abstractgateway/src/abstractgateway/users.py` rejects duplicate runtime ids
  among live users but, before this item, user deletion removed the only
  assignment record while retaining runtime data on disk.
- `abstractflow` rejects browser Gateway URL changes on non-local hosts unless
  explicitly enabled, but `abstractcode/web/bin/cli.js` and
  `abstractobserver/bin/cli.js` did not have the same guard.
- `scripts/gateway-flow-local.sh` enables Gateway user auth, prepares the
  default `admin` user, and prints Flow login credentials. `scripts/gateway-flow.sh`
  still used only the legacy Gateway token and did not create a browser-login user.

## Problem
These gaps can break isolation, allow hosted app proxy misuse, or make the
published startup path unusable for the new browser-session auth model.

## What we want to do
Close the release blockers with targeted changes that preserve the current
architecture: Gateway owns users/runtime assignment, hosted apps proxy through
browser sessions, and scripts print only the user credentials needed by Flow.

## Why
Multi-user Gateway support must fail closed before release. A user or admin
should not accidentally route one person's retained runtime data to another
principal, and hosted apps must not become arbitrary browser-directed proxies.

## Requirements
- Deleting a Gateway user reserves that user's runtime id while runtime data is
  retained, preventing assignment to a different principal in the same tenant.
- Flow, Code Web, and Observer share the same hosted/non-local browser Gateway
  URL mutation rule.
- Published-package `gateway-flow.sh` enables user auth, prepares an `admin`
  user by default, caches the generated user token locally, and prints Gateway
  URL/user/token for Flow sign-in.
- `.DS_Store` files are ignored and must not remain tracked.

## Suggested implementation
- Add runtime reservation/tombstone records to the Gateway user registry.
- Add Code Web and Observer URL guards matching Flow and cover them with
  hosted-server tests.
- Mirror the local launcher's user-bootstrap behavior in the published script.
- Remove tracked `.DS_Store` files and keep ignore files aligned.

## Scope
- AbstractGateway user registry and console copy.
- AbstractCode Web and AbstractObserver packaged Node servers plus tests.
- Root startup scripts and docs.
- Ignore hygiene for `.DS_Store`.

## Non-goals
- Do not add a purge, restore, or runtime-transfer UI in this item.
- Do not extract a shared hosted proxy helper unless implementation pressure is
  proven by tests or another drift incident.
- Do not change Core or Runtime behavior.

## Dependencies and related tasks
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0153_gateway_browser_session_security_contract.md`
- `../../completed/0149_cross_app_gateway_auth_defaults_convergence.md`

## Expected outcomes
- A deleted user's retained runtime cannot be assigned to another user.
- Hosted Code/Observer reject remote-host Gateway URL changes just like Flow.
- `./scripts/gateway-flow.sh` produces usable `admin` browser-login credentials.
- Release hygiene no longer includes tracked `.DS_Store` files.

## Validation
- Gateway user-registry tests cover delete-plus-cross-user-runtime-reuse.
- Code/Observer hosted server tests cover remote-host URL mutation rejection.
- `bash -n scripts/gateway-flow.sh scripts/gateway-flow-local.sh`.
- Targeted Gateway, Flow, Code, and Observer test suites pass.

## Progress checklist
- [x] Add Gateway runtime reservations.
- [x] Add Code Web and Observer hosted URL guards.
- [x] Align published launcher user bootstrap.
- [x] Clean `.DS_Store` tracking/ignore state.
- [x] Update docs and completion report.

## Guidance for the implementing agent
Keep the fixes narrow. The security model belongs in Gateway and in hosted app
proxy boundaries; do not move user/routing ownership into Flow, Code, Observer,
Core, or Runtime.

## Architecture decision summary

Decision question: how should the release blockers be closed without blurring
Gateway/app responsibilities?

Alternatives considered:
- Disable instead of delete users. This would preserve runtime ownership, but
  would change the user-management API and make the console's delete action
  misleading.
- Add retained-runtime reservations on delete. This preserves existing delete
  UX while preventing cross-principal runtime reassignment.
- Add a full purge/transfer workflow now. This would be most explicit, but it
  adds admin UX and irreversible-data semantics beyond the release blocker.

Chosen design: delete removes the user credential and creates a retained-runtime
reservation. A different same-tenant principal cannot reuse the runtime id while
data is retained. Recreating the same logical principal may reclaim its own
reservation. Explicit purge/transfer remains a future admin workflow, not a
silent side effect.

For hosted app proxy duplication, the chosen near-term design is conformance
tests plus matching URL guards in Code Web and Observer. A shared helper is
proposed in `0155`, but not extracted in this item because the immediate
security risk is closed by tests and the package boundary is not yet proven.

## Completion report

Date: 2026-05-30

Summary:
- Added `runtime_reservations` to the Gateway user registry. Deleting a user now
  reserves the retained runtime id for that principal and blocks assigning it
  to another user in the same tenant.
- Updated Gateway Console delete copy so admins see that runtime data is
  retained and the runtime id remains reserved.
- Added hosted non-local Gateway URL guards to AbstractCode Web and
  AbstractObserver packaged Node servers, matching Flow's behavior.
- Tightened Flow/Code/Observer host checks so forwarded host headers are used
  only when explicit trust-proxy env vars are set.
- Added Code/Observer hosted-server tests proving remote-host browser Gateway
  URL changes are rejected, including forged `X-Forwarded-Host` loopback
  headers.
- Updated `scripts/gateway-flow.sh` to enable Gateway user auth, prepare the
  default `admin` browser user, cache the generated user token, and print the
  Gateway URL/user/token for Flow sign-in.
- Removed tracked `.DS_Store` files from AbstractObserver and added the missing
  ignore rule.
- Updated user-facing docs, backlog, and LLM context files.

Files or symbols touched:
- `abstractgateway/src/abstractgateway/users.py`
- `abstractgateway/src/abstractgateway/console.py`
- `abstractgateway/tests/test_gateway_principal_auth.py`
- `abstractcode/web/bin/cli.js`
- `abstractcode/web/src/lib/hosted_gateway_url_guard.test.ts`
- `abstractobserver/bin/cli.js`
- `abstractobserver/src/ui/hosted_gateway_url_guard.test.ts`
- `abstractobserver/.gitignore`
- `abstractflow/web/backend/services/gateway_connection.py`
- `abstractflow/web/backend/routes/connection.py`
- `abstractflow/web/frontend/bin/cli.js`
- `abstractflow/web/frontend/vite.config.ts`
- `abstractflow/tests/test_gateway_connection_config.py`
- `scripts/gateway-flow.sh`
- Root, Code, Observer, and Gateway docs/LLM context files.

Validation:
- `python -m pytest tests/test_gateway_principal_auth.py tests/test_gateway_principal_isolation_matrix.py tests/test_gateway_security_middleware_unit.py tests/test_gateway_workflow_catalog_acl.py tests/test_gateway_console.py tests/test_gateway_install_profiles.py tests/test_gateway_embeddings_endpoint.py -q` in `abstractgateway` -> 54 passed.
- `python -m pytest tests/test_gateway_connection_config.py tests/test_web_gateway_proxy_auth.py -q` in `abstractflow` -> 21 passed, 2 FastAPI deprecation warnings.
- `node --check bin/cli.js && npm test -- --run src/lib/storage.test.ts src/lib/hosted_gateway_url_guard.test.ts` in `abstractcode/web` -> 2 passed.
- `node --check bin/cli.js && npm test -- --run src/ui/auth_storage.test.ts src/ui/hosted_gateway_url_guard.test.ts` in `abstractobserver` -> 2 passed.
- `node --check web/frontend/bin/cli.js && npm --prefix web/frontend run build` in `abstractflow` -> passed.
- `python -m py_compile web/backend/services/gateway_connection.py web/backend/routes/connection.py` in `abstractflow` -> passed.
- `bash -n scripts/gateway-flow.sh scripts/gateway-flow-local.sh` -> passed.
- Root, Gateway, Flow, Code, and Observer `llms-full` generation -> passed.

Residual risks:
- The explicit retained-runtime purge/transfer workflow was intentionally left
  out of this release-blocker item and is handled by follow-up item `0156`.
- Code Web and Observer still duplicate hosted proxy code. Proposed item `0155`
  records the extraction threshold; current protection is conformance tests.
