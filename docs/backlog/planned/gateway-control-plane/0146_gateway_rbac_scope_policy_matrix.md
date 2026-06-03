# Planned: Gateway RBAC scope policy matrix

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: Needs new ADR or ADR revision

## Context
Gateway has an `admin` role and admin-only user CRUD. Broader Gateway route
families are not yet governed by a complete role/scope matrix. The current
per-principal service router is a strong data-plane baseline, but route-family
authorization still needs explicit policy.

## Current code reality
- `GatewayPrincipal.is_admin()` is a string-role check.
- `/api/gateway/admin/users` is admin-gated.
- `/api/gateway/admin/runtime-reservations` list/transfer/purge routes are
  admin-gated.
- Non-admin users get per-principal data directories through Gateway service
  routing.
- Gateway now has a central authorization helper and a first route-family
  policy gate in the security middleware for admin, audit, process, backlog,
  triage, reports, capability-default writes, model load/unload, bloc writes,
  and prompt-cache writes.
- Gateway route-family policy is now centralized in
  `abstractgateway/src/abstractgateway/security/authorization.py`, and
  `GatewaySecurityMiddleware` delegates route-family checks to that table.
- Non-admin users can no longer satisfy admin-only route families via broad
  scopes such as `*`; `admin_required` means the `admin` role is required.
- Server-workspace file helpers, server-workspace artifact import/export, host
  metrics, email bridge routes, model residency listing, and model load/unload
  are admin-only in hosted user-auth mode. Browser file upload remains
  available to ordinary users.
- Capability-default writes are no longer treated as global admin writes in
  hosted user-auth mode; they are stored as per-principal overlays under the
  caller's runtime data plane by `0147`.
- Gateway user records now reject duplicate runtime ids within the same tenant,
  so `1 user = 1 runtime` cannot be accidentally broken by user creation or
  user update. Deleted users also leave a retained-runtime reservation, so a
  runtime whose data is retained cannot be assigned to a different principal in
  the same tenant unless an admin explicitly transfers the retained runtime or
  purges its data. The same runtime id can still exist in a different tenant.
- Per-principal routing is now covered by an initial Alice/Bob matrix for runs,
  run history, run input, ledger reads/streams/batches, artifact metadata,
  artifact content, and artifact search. Cross-user guessed ids return `404` or
  are omitted from batch/search results instead of returning empty records that
  imply existence.
- The Alice/Bob matrix now also covers private workflow bundles, VisualFlow
  drafts, per-principal capability-default overlays, session artifacts,
  prompt-cache key naming, and KG/session memory. Prompt-cache key hashing now
  includes a private principal scope while keeping the returned public identity
  app-level and portable.
- Capability discovery now reports admin-only server-workspace artifact
  import/export and provider prompt-cache control surfaces as unavailable for
  ordinary users, with machine-readable `admin_required` metadata. Admin
  principals still see those operations as available.
- `ABSTRACTGATEWAY_DEV_READ_NO_AUTH=1` now uses a non-admin
  `loopback-readonly` principal, and admin/operator route families still return
  machine-readable `403` denials.
- Powerful surfaces still need audit: workflow publish/remove/deprecate,
  workspace/file helpers, broader prompt-cache variants, provider defaults,
  credentials, broad runtime enumeration, bridge administration, discovery
  visibility, and global/operator endpoints.

## Problem
The words `admin` and `user` exist, but most of Gateway does not yet have a
decision-grade authorization matrix. Without one, future UI work can accidentally
surface privileged operations to ordinary users.

## What we want to do
Define and enforce a route-family RBAC/scope policy matrix for Gateway. The
matrix should state subject, action, resource class, owner/caller relation,
required role, required scope, audit requirement, discovery visibility, and
destructive/side-effect classification for each route family.

## Why
Gateway is now the shared control plane. Authorization must be centralized and
testable before Gateway Console, workflow catalog permissions, per-user
secrets, and runtime exploration can be trusted.

## Requirements
- Formalize at least `admin` and `user` roles plus concrete scope fields for
  narrow grants; do not leave downstream items to invent their own scope model.
- Model route authorization as subject/action/resource/condition checks, not
  scattered `if admin` branches.
- Admin-only: user management, credential/global config writes, global workflow
  catalog promotion/removal, process control, broad tenant/runtime enumeration,
  operator maintenance, and global policy changes.
- User-owned: own runs, ledgers, artifacts, memory, private workflows, and
  allowed runtime state.
- Explicit policy needed for shared/org memory, shared workspaces, workflow
  publishing, cross-runtime search, and destructive actions.
- Dev read bypass must never create a principal that satisfies `is_admin()`.
  Replace `local-admin` semantics with a distinct loopback/read-only principal,
  route allowlist, and tests proving admin/user/secret/catalog data remains
  unreachable.
- Denial responses and discovery metadata must not leak hidden resource ids,
  user existence, workflow existence, secret provider presence, or cross-runtime
  counts.
- Denials should be machine-readable, for example `reason_code`,
  `required_role`, `required_scope`, and `resource_class`, without exposing
  forbidden resource details.
- Admin/global writes and denied high-risk attempts are audit-log events.

## Suggested implementation
Add a centralized Gateway authorization helper and route-family policy table.
Refactor high-risk routes to call it. Keep denial reasons machine-readable so
UIs can hide or disable actions cleanly.

## Scope
- Gateway policy definitions and helper APIs.
- Route-family audits and tests.
- Discovery metadata for allowed/denied actions where clients need UX hints.

## Non-goals
- Do not implement the full Gateway Console here.
- Do not rely on frontend hiding as authorization.
- Do not treat caller-supplied ids as authorization proof.

## Dependencies and related tasks
- `0143_shared_gateway_per_principal_runtime_router.md`
- `0145_gateway_admin_console_bootstrap.md`
- `0153_gateway_browser_session_security_contract.md`
- `0148_gateway_workflow_registry_acl.md`
- `0151_runtime_explorer_contract.md`

## Expected outcomes
- A non-admin cannot call admin-only route families.
- A user cannot read or mutate another user's runtime by guessing ids.
- Discovery can report permission-aware action availability.

## Validation
- Alice/Bob route-family isolation tests across users, runs, ledgers,
  artifacts, memory, workflows, prompt cache, workspace files, and admin routes.
- Dev read-bypass tests proving admin user lists and sensitive data remain
  protected.
- Contract tests for permission metadata.

## Recent validation
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_security_middleware_unit.py -q` -> 31 passed.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py::test_gateway_user_runtime_ids_are_unique_per_tenant abstractgateway/tests/test_gateway_principal_isolation_matrix.py -q` -> 2 passed.
- `python -m py_compile abstractgateway/src/abstractgateway/users.py abstractgateway/src/abstractgateway/routes/gateway.py` -> passed.
- `python -m pytest abstractgateway/tests/test_gateway_security_middleware_unit.py abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_console.py abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py -q` -> 51 passed, 2 warnings.
- `python -m compileall -q abstractgateway/src/abstractgateway abstractflow/web/backend` -> passed.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_security_middleware_unit.py abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py` -> 44 passed.
- `python -m pytest abstractgateway/tests` -> 261 passed, 2 skipped.
- `python -m pytest abstractflow/tests/test_gateway_connection_config.py abstractflow/tests/test_web_gateway_proxy_auth.py` -> 20 passed.
- `python -m pytest abstractgateway/tests/test_gateway_install_profiles.py abstractgateway/tests/test_gateway_capability_catalog_proxy.py` -> 29 passed.
- `python -m compileall -q abstractgateway/src/abstractgateway` -> passed.
- `python -m pytest abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_gateway_principal_isolation_matrix.py abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_abstractflow_editor_gateway_contract.py -q` -> 26 passed.
- `python -m py_compile abstractgateway/src/abstractgateway/routes/gateway.py abstractgateway/src/abstractgateway/security/sessions.py abstractgateway/src/abstractgateway/security/gateway_security.py` -> passed.

## Progress checklist
- [ ] Write route-family policy matrix.
- [x] Add central authorization helper.
- [x] Harden dev read bypass for admin/operator route families.
- [x] Add first hosted route-family policy table in Gateway middleware.
- [x] Admin-gate server-workspace and operator route families.
- [x] Add runtime-id uniqueness and retained-runtime reservation guards for
  tenant-local Gateway users.
- [x] Add admin-only retained runtime list/transfer/purge routes.
- [x] Add initial Alice/Bob isolation tests for runs, ledgers, and artifacts.
- [x] Extend Alice/Bob matrix to KG/session memory, private workflows,
  prompt-cache key naming, session artifacts, and runtime-scoped defaults.
- [x] Prove regular users cannot use admin-only workspace helper/import/export
  surfaces.
- [x] Add machine-readable denial tests for first operator route families.
- [x] Add discovery leak tests for admin-only workspace artifact and
  prompt-cache provider-control availability.
- [x] Update docs with current route-family boundaries.

## Guidance for the implementing agent
Add authorization at the lowest shared Gateway layer available. Avoid scattering
ad hoc `if admin` checks without a policy table.

## Implementation note - 2026-05-30

This item is materially advanced but not fully closed. The current code now has
a central policy table and tested denials for operator/server-workspace route
families. The remaining closure criterion is the broader Alice/Bob isolation
matrix and discovery leak tests across every user-owned route family.

The latest security pass adds table-driven denial coverage for admin, audit,
process, backlog, triage, report, email, host, model residency, workspace,
bloc, and prompt-cache route families using a non-admin user with wildcard
scopes. This proves broad scopes cannot bypass `admin_required=True`; it does
not replace the remaining user-owned data-plane isolation matrix.

The latest isolation pass adds runtime-id uniqueness enforcement and extends
the cross-user matrix to run, ledger, artifact, session artifact, KG/session
memory, private workflow bundle, VisualFlow draft, prompt-cache naming, and
capability-default overlay surfaces. It also verifies that ordinary users see
admin-only workspace artifact import/export and provider prompt-cache controls
as unavailable in discovery, and that direct workspace helper/import calls
return machine-readable `403` denials.

This item should remain open only for future route families as they are added
or promoted. The user-requested Alice/Bob matrix extension is complete.
