# Gateway control plane backlog track

## Status
Planned/in progress, with adjacent proposals for package extraction decisions.
Gateway/Flow now have browser-session auth, central route-family authorization,
the first Gateway Console, Gateway-baseline plus per-user capability-default
overlays, secret-free browser login responses, full Gateway cookie/origin
session matrix tests, an extended Alice/Bob isolation matrix for the current
user-owned data surfaces, retained-runtime reservations after user deletion,
retained-runtime transfer/purge lifecycle, and completed cross-app auth/default
convergence planning. Gateway provider endpoint profiles now cover the first
secret-safe reusable endpoint path. The track remains open for future
route-family growth, workflow ACL UI, runtime exploration contracts, and a
fuller provider-secret vault/bridge policy.

## Purpose
This track groups the Gateway admin/account/config/runtime-control work raised
by the multi-user Gateway review. Gateway is the trust boundary and control
plane; Flow, Code, Observer, and Assistant should become task UIs that consume
Gateway auth, defaults, permissions, and catalogs instead of each owning global
identity or model configuration.

## Items
- `0145_gateway_admin_console_bootstrap.md`: Gateway-served admin/account console v0.
- `0146_gateway_rbac_scope_policy_matrix.md`: route-family role/scope hardening.
- `0147_gateway_per_principal_config_secrets_defaults.md`: per-principal config, provider keys, and defaults through Gateway with Core as schema/persistence authority.
- `0148_gateway_workflow_registry_acl.md`: private workflow registry plus tenant/framework catalog ACLs.
- `0150_observer_manager_responsibility_split.md`: keep Observer focused and move admin/config ownership out.
- `0153_gateway_browser_session_security_contract.md`: define hosted browser session, cookie, CSRF, logout, and revocation semantics.

Adjacent proposals:
- `../../proposed/gateway-control-plane/0151_runtime_explorer_contract.md`
- `../../proposed/gateway-control-plane/0152_abstractmanager_package_extraction.md`

Completed in this track:
- `../../completed/0149_cross_app_gateway_auth_defaults_convergence.md`: converged Flow, Code Web, Observer, Gateway Console, Assistant, and automation behavior expectations for hosted/local auth and defaults; shared component extraction is deferred.
- `../../completed/0154_multi_user_security_release_blockers.md`: closed the retained-runtime reuse, Code/Observer hosted Gateway URL guard, published launcher bootstrap, and `.DS_Store` hygiene release blockers.
- `../../completed/0156_retained_runtime_admin_lifecycle.md`: added explicit admin list/transfer/purge lifecycle for retained runtime reservations.
- `../../completed/0157_gateway_provider_endpoint_profiles.md`: added Gateway-owned endpoint profiles that surface as virtual `endpoint:*` providers with write-only credentials.

## Reading order
Continue by keeping `0146` and `0153` tests current as new route families and
browser apps appear. `0145` now has a narrow console v0 with user email, confirmations,
    and discovered provider/model selectors; keep it narrow. `0147` now has a
Gateway baseline, per-principal defaults, and the initial Gateway provider
endpoint profile injection boundary; encryption, bridge, delegated-tool, and
audit policy remain. Use `0148` after the
authorization/session boundaries are stable, with immutable catalog versions
and explicit default pointers. `0149` is complete; do not extract a shared auth
component until duplication creates a real maintenance problem. Keep `0151`,
`0152`, and `0155` proposed until overlap, package pressure, or repeated hosted
proxy drift is proven.

## Relevant ADRs and docs
- ADR-0018: Durable Run Gateway and Remote Host Control Plane.
- ADR-0021: Deployment topologies and supported scenarios.
- ADR-0033: Install profiles, config entrypoints, and server boundaries.
- ADR-0035: Capability routing defaults.
- `docs/guide/capability-routing-defaults.md`
- `docs/guide/gateway-security.md`
- `docs/backlog/planned/0143_shared_gateway_per_principal_runtime_router.md`

## Non-goals
This track does not make Gateway a workflow authoring UI, coding UI, or rich run
trace viewer. Flow remains the workflow authoring surface. Code remains the
coding-agent UX. Observer remains the run/ledger observability UX unless future
proposals intentionally split runtime exploration into a new app.
