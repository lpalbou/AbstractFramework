# Planned: Gateway workflow registry ACLs

## Metadata
- Created: 2026-05-30
- Status: In progress
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: Needs new ADR or ADR revision

## Context
Flow authors VisualFlows and publishes bundles through Gateway. Runtime treats
workflow bundles as transport/execution artifacts and intentionally does not
own trust policy. Gateway must decide who can import, publish, run, promote,
deprecate, remove, or grant access to workflows.

## Current code reality
- Gateway has per-principal service routing and per-user flow/bundle storage.
- Gateway VisualFlow CRUD, publish, bundle upload/remove/deprecate endpoints
  exist but need clearer admin/user/catalog permission semantics.
- Flow currently consumes Gateway capability/discovery metadata and can hide or
  show actions, but server-side Gateway must enforce permissions.
- Existing per-principal `/visualflows` and bundle directories are private
  authoring/storage surfaces. A shared tenant/framework catalog should be an
  explicit Gateway-level metadata store, not an accidental reuse of one user's
  bundle directory.

## Problem
Workflow registration and permissions are not yet a clean control-plane model.
A globally visible workflow must not imply shared runtime state or unchecked
write/tool permissions. Users should be able to draft private workflows, while
admins control tenant/framework catalogs.

## What we want to do
Implement a two-tier Gateway workflow registry:
- private/user registry for drafts and user-owned workflows;
- tenant/framework catalog for admin-promoted immutable bundle versions with
  explicit ACLs and run policies.

Registry scopes should be explicit (`private`, `tenant_catalog`,
`framework_catalog`, and later `system`) so a `bundle_id` collision or guessed
id cannot silently switch between private and shared authority.

## Why
This lets Flow remain an authoring tool while Gateway becomes the trusted
workflow registry and permission authority.

## Requirements
- Non-admin users can draft/test private workflows in their own runtime.
- Admins can import/register/promote/deprecate/remove tenant/framework catalog
  bundles.
- Global/catalog workflows execute in the requesting user's runtime unless
  explicitly launched as admin/system workflows.
- ACL metadata lives in Gateway, not inside trusted bundle manifest fields.
- Workspace/tool/write permissions are intersected with user role, workflow ACL,
  tenant policy, and operator workspace policy.
- Effective run policy is materialized at run start and includes `run_as`,
  workflow visibility, allowed tools, workspace grants, secret access, approval
  mode, network/process permissions, and destructive-action permissions.
- Enforcement happens both at run start and at later tool/workspace/secret
  access points; a workflow allowed to start is not automatically allowed to
  perform every side effect it requests.
- Admin/system workflow launch semantics require explicit service-principal
  rules, approval gates, workspace binding, secret-source rules, and audit logs
  before they are enabled.
- Discovery exposes permission-aware action metadata for Flow UX.
- Existing workflows that depend on an older catalog workflow version keep
  running against that immutable version unless the version is explicitly
  blocked for safety. Updating a default workflow pointer must not rewrite
  historical bundle references or private workflows built on top of a previous
  version.

## Suggested implementation
Add catalog metadata records keyed by bundle id, version, sha256, status,
visibility, owner, publisher, promoter, timestamps, and ACL. Include review
status, checksum verification, and the immutable policy snapshot or policy
version used at run start. Keep bundle content immutable by version; updates
create new versions and optional default-pointer changes. Add run-start,
scheduled-run, subworkflow, and per-action checks that resolve catalog ACL and
effective run policy before execution.

Recommended state machine:
`private/draft -> submitted -> approved/published -> deprecated -> removed/tombstoned`.
Deprecation blocks new starts but preserves history/replay. Removal should keep
tombstones so dependent workflows can explain why a referenced version is no
longer startable.

## Scope
- Gateway registry metadata and ACL APIs.
- Run-start authorization for catalog/private workflows.
- Flow discovery contract updates for allowed/denied actions.
- Tests for private vs catalog workflows.
- Migration compatibility for existing private `/visualflows` and user bundle
  storage.

## Non-goals
- Do not make Runtime own ACL policy.
- Do not trust bundle-declared permissions without Gateway grants.
- Do not add a full marketplace UX in this item.
- Do not change `/bundles` from "current runtime bundles" to "global catalog"
  without an explicit scope or a separate catalog endpoint.

## Dependencies and related tasks
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0145_gateway_admin_console_bootstrap.md`
- `0153_gateway_browser_session_security_contract.md` for browser-admin
  interactions with registry controls.
- Flow publish/import UI.
- Runtime workflow bundle validation.

## Expected outcomes
- Users cannot run or mutate workflows by guessing bundle ids.
- Admins can promote workflows to a tenant/framework catalog.
- Catalog workflows run in the caller's data plane by default.
- Deprecation blocks new starts while preserving historical replay.

## Validation
- Alice/Bob private workflow isolation tests.
- Non-admin publish-to-catalog denial tests.
- Catalog ACL start/deny tests.
- Immutable bundle version/sha256 tests.
- Default-pointer update tests proving existing version references are not
  rewritten.
- Scheduled-run and subworkflow policy inheritance tests.
- Workspace policy enforcement tests.

## Progress checklist
- [x] Define registry tiers and metadata schema.
- [ ] Define effective run policy and admin/system workflow semantics.
- [x] Add catalog ACL APIs.
- [x] Enforce run-start ACL/policy.
- [x] Enforce scheduled-run and catalog subworkflow status/policy checks.
- [ ] Enforce per-tool/per-workspace policy checks.
- [x] Update Gateway discovery metadata for catalog/private action split.
- [x] Add two-user tests.

## Implementation note - 2026-05-30

Implemented the first catalog-control slice in `abstractgateway`:

- Added a Gateway-owned workflow catalog store under the root Gateway data dir.
  Catalog bundle bytes are immutable by `scope + tenant + bundle_id +
  bundle_version + sha256`; re-uploading the same version with different bytes
  is rejected.
- Added explicit catalog endpoints:
  - user-visible `GET /api/gateway/workflow-catalog`;
  - admin-only upload, promote, default pointer, ACL, deprecate, block, and
    tombstone routes under `/api/gateway/admin/workflow-catalog`.
- Kept private `/api/gateway/visualflows` and `/api/gateway/bundles` as
  per-principal runtime authoring/storage surfaces.
- Loaded tenant catalog bundles into each user's runtime host under internal
  catalog bundle ids so private bundle ids cannot shadow catalog ids.
- Added `registry_scope` to run start and scheduled run requests. Catalog
  starts resolve through ACLs and the admin default pointer, then run in the
  requesting user's runtime.
- Added host-side guards so direct internal catalog starts require a
  Gateway-issued signed workflow-policy snapshot, and catalog subworkflow
  starts are blocked when the signature, runtime binding, ACL, content hash, or
  catalog status no longer validates.
- Made catalog scope explicit: omitted `registry_scope` stays on the private
  runtime bundle surface and does not silently fall through to the shared
  catalog.
- Blocked direct private-bundle inspection of catalog-internal bundle ids and
  added ACL-aware catalog flow/schema inspection routes.
- Reworked catalog install so byte immutability and metadata updates are
  checked in one critical section; same-content inactive re-uploads cannot move
  the default pointer back to an inactive version.
- Rejected `framework_catalog` at the API until cross-tenant host loading and
  policy semantics are implemented.
- Added discovery metadata so clients can distinguish private bundle actions
  from catalog/admin actions.

Validation:

- `python -m py_compile abstractgateway/src/abstractgateway/workflow_catalog.py abstractgateway/src/abstractgateway/config.py abstractgateway/src/abstractgateway/service.py abstractgateway/src/abstractgateway/hosts/bundle_host.py abstractgateway/src/abstractgateway/routes/gateway.py abstractgateway/tests/test_gateway_workflow_catalog_acl.py`
- `python -m pytest abstractgateway/tests/test_gateway_workflow_catalog_acl.py -q` -> `2 passed`
- `python -m pytest abstractgateway/tests/test_gateway_workflow_catalog_acl.py abstractgateway/tests/test_gateway_workflow_deprecation.py abstractgateway/tests/test_gateway_principal_auth.py abstractgateway/tests/test_capabilities_endpoint_contract.py abstractgateway/tests/test_abstractflow_editor_gateway_contract.py -q`
- `python -m pytest abstractgateway/tests -q` -> `265 passed, 2 skipped`

Remaining work:

- Define any future admin/system run mode separately; current catalog runs are
  caller-runtime only.
- Intersect workflow catalog policy with tool, workspace, secret, network, and
  destructive-action policies at effect/action boundaries.
- Build Flow/Gateway Console UX for catalog promotion, default movement, ACLs,
  and version status operations.

## Refinement note - 2026-05-30

Admin install/update/remove of default workflows should be modeled as catalog
version management, not file replacement. Admins can promote a new immutable
bundle version and move a default pointer, but private workflows and historical
runs must retain their exact version reference. A later admin/system workflow
execution mode must be explicit and audited; the default for catalog workflows
is still "run in the requesting user's runtime."

## Guidance for the implementing agent
Keep authoring and authority separate: Flow may request publication, but Gateway
must decide and audit the permission result.
