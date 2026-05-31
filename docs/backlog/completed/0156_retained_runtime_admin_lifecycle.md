# Completed: Retained runtime admin lifecycle

## Metadata
- Created: 2026-05-30
- Status: Completed
- Completed: 2026-05-30

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
Gateway user deletion now removes account/token access while retaining the
runtime data directory and reserving the runtime id for the deleted principal.
That prevents accidental cross-user data exposure, but it leaves admins without
an explicit way to intentionally purge retained runtime data or transfer it to
another user.

## Current code reality
- `abstractgateway/src/abstractgateway/users.py` stores live users and
  `runtime_reservations` in the Gateway user registry.
- `GatewayUserRegistry.create_user()` and `update_user()` reject reuse of a
  retained runtime reservation by another principal.
- `GatewayUserRegistry.delete_user()` creates a retained-runtime reservation.
- `abstractgateway/src/abstractgateway/routes/gateway.py` exposes admin user
  CRUD, but no retained-runtime lifecycle routes.
- `abstractgateway/src/abstractgateway/console.py` tells admins that runtime
  data is retained, but has no reservation table, transfer action, or purge
  action.

## Problem
The retained-runtime safety guard is secure but operationally incomplete.
Admins can see that deletion retained data only through the delete confirmation
copy and registry file internals. They cannot intentionally purge stale data or
transfer retained data to a new owner through supported Gateway APIs.

## What we want to do
Add explicit admin-only lifecycle operations for retained runtime reservations:
list, transfer, and purge. Transfer must be intentional and auditable through
the registry. Purge must remove retained runtime files before releasing the
runtime id for reuse.

## Why
This keeps the secure default while giving admins a deliberate recovery path for
real account lifecycle events: employee departure, account rename, mistaken
delete, or data-retention cleanup.

## Requirements
- Admins can list retained runtime reservations.
- Non-admin users cannot list, purge, or transfer retained runtimes.
- Transfer assigns a retained runtime to an existing same-tenant user and
  reserves that user's previous runtime id.
- Purge requires an exact runtime-id confirmation and deletes the retained
  runtime directory before releasing the reservation.
- Runtime file deletion must stay inside the Gateway per-user runtime root.
- The Gateway Console exposes transfer and purge actions with confirmations.
- Tests prove cross-user reuse remains blocked until explicit purge or transfer.

## Suggested implementation
- Extend `GatewayUserRegistry` with reservation listing, lookup, release, and
  transfer helpers.
- Add admin routes under `/api/gateway/admin/runtime-reservations`.
- Add a Gateway service-cache invalidation helper for affected runtime ids.
- Add a console section for retained runtime reservations.
- Add focused Gateway tests around RBAC, transfer, purge, and data deletion.

## Scope
- AbstractGateway registry, admin API, console, tests, and docs.
- Root/Gateway docs and AI-readable docs updates.

## Non-goals
- No runtime explorer UI.
- No partial artifact-level purge.
- No automatic data migration between different runtime layouts.
- No cross-tenant transfer.

## Dependencies and related tasks
- `0145_gateway_admin_console_bootstrap.md`
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0154_multi_user_security_release_blockers.md`

## Expected outcomes
- Deleted users still protect retained data by default.
- Admins have an explicit, confirmed purge path.
- Admins have an explicit, confirmed transfer path.
- Tests and docs describe the lifecycle clearly.

## Validation
- `python -m pytest tests/test_gateway_principal_auth.py -q`
- `python -m pytest tests/test_gateway_console.py -q`
- `python -m py_compile src/abstractgateway/users.py src/abstractgateway/routes/gateway.py src/abstractgateway/service.py src/abstractgateway/console.py`

## Progress checklist
- [x] Add registry lifecycle helpers.
- [x] Add admin routes and service-cache invalidation.
- [x] Add Gateway Console retained-runtime UI.
- [x] Add tests for RBAC, transfer, purge, and reuse.
- [x] Update docs and backlog completion report.

## Guidance for the implementing agent
Preserve the conservative default. A retained runtime id must never become
reusable just because the account row disappeared; reuse must follow an
explicit purge or transfer operation.

## Completion report

Date: 2026-05-30

Summary:
- Added retained-runtime lifecycle helpers to the Gateway user registry.
- Added admin-only list/transfer/purge routes under
  `/api/gateway/admin/runtime-reservations`.
- Added service-cache invalidation for affected runtime ids after transfer or
  purge.
- Added a `purging` reservation state so concurrent transfer attempts cannot
  claim a retained runtime between purge validation and file deletion.
- Added a Gateway Console retained-runtime table with transfer and purge actions
  behind confirmation modals.
- Added tests proving non-admin denial, purge-before-reuse, transfer to an
  existing same-tenant user, previous-runtime reservation, and continued
  cross-user reuse blocking.

Files or symbols touched:
- `abstractgateway/src/abstractgateway/users.py`
- `abstractgateway/src/abstractgateway/routes/gateway.py`
- `abstractgateway/src/abstractgateway/service.py`
- `abstractgateway/src/abstractgateway/console.py`
- `abstractgateway/tests/test_gateway_principal_auth.py`
- `abstractgateway/tests/test_gateway_console.py`
- `abstractgateway/docs/security.md`
- `abstractgateway/docs/configuration.md`
- `abstractgateway/README.md`
- `abstractgateway/llms.txt`
- `docs/guide/gateway-security.md`
- `docs/configuration.md`
- `docs/api.md`
- `llms.txt`

Validation:
- `python -m pytest tests/test_gateway_principal_auth.py tests/test_gateway_console.py -q`
  in `abstractgateway` -> 18 passed.
- `python -m pytest tests/test_gateway_principal_isolation_matrix.py tests/test_gateway_security_middleware_unit.py tests/test_gateway_workflow_catalog_acl.py -q`
  in `abstractgateway` -> 26 passed.
- `python -m py_compile src/abstractgateway/users.py src/abstractgateway/routes/gateway.py src/abstractgateway/service.py src/abstractgateway/console.py`
  in `abstractgateway` -> passed.

Review notes:
- Code quality: purge atomically marks reservations as `purging` before file
  deletion, keeps deletion scoped under
  `<ABSTRACTGATEWAY_DATA_DIR>/users/<tenant>/<runtime>`, and leaves the
  reservation in place if file deletion fails.
- Architecture: Gateway remains the owner of user/runtime assignment and
  retained-runtime lifecycle. Runtime internals are not asked to understand
  Gateway user ownership.
- Naive user: the console now shows retained runtimes directly instead of
  making admins infer them from failed user creation.
- Expert user: the API exposes explicit lifecycle routes and returns data-path
  diagnostics for admin inspection.
- Operations: transfer does not copy data; it changes routing ownership. Purge
  deletes the retained runtime root and then releases the reservation.

Residual risks:
- There is still no rich runtime explorer or artifact-level delete/export for
  retained runtime data. That remains in the proposed runtime explorer track.
- Transfer is same-tenant and existing-user only by design. Account rename flows
  that need create-and-transfer can create the target first, then transfer.
