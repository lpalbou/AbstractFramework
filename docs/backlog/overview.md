# AbstractFramework Backlog Overview

This root backlog is the framework-level planning ledger for cross-package work. Some older items
use legacy naming and duplicate numeric prefixes; new items should use four-digit global IDs and
the lifecycle folders described by the backlog process.

## Current Counts

- Planned: many legacy items plus active cross-package work.
- Proposed: legacy proposed items exist.
- Completed: historical completion ledger exists under `completed/`.
- Deprecated: not yet normalized at the root level.
- Recurrent: not yet normalized at the root level.

## Active Planned Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0142 | [Gateway tenant isolation and shared runtime design](planned/0142_gateway_tenant_isolation_and_shared_runtime.md) | Planned | Define and implement tenant-aware Gateway/Runtime isolation; current shared Gateway deployments are single-user or trusted-cohort only. |
| 0143 | [Shared Gateway per-principal runtime router](planned/0143_shared_gateway_per_principal_runtime_router.md) | In progress | Gateway principal auth, admin user CRUD, per-principal GatewayService routing, and Flow browser-session routing landed; broader app auth and route-family isolation remain open. |
| 0145-0153 | [Gateway control plane track](planned/gateway-control-plane/README.md) | Planned | Gateway-owned admin/account/config/workflow-permission control plane; starts with responsibility, RBAC, and browser-session contracts before broad UI/app migration. |

## Gateway Control Plane Planned Track

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0145 | [Gateway admin console bootstrap](planned/gateway-control-plane/0145_gateway_admin_console_bootstrap.md) | In progress | Console v0 now serves `/console` with session sign-in, account/runtime summary, admin user management, optional email, create/delete confirmations, token rotation, and discovered provider/model defaults; richer runtime activity remains optional follow-up. |
| 0146 | [Gateway RBAC scope policy matrix](planned/gateway-control-plane/0146_gateway_rbac_scope_policy_matrix.md) | In progress | Central route-family policy gates operator/server-workspace/model-residency surfaces, runtime ids are tenant-unique, and the Alice/Bob matrix now covers runs, ledgers, artifacts, session artifacts, KG/session memory, private workflows, prompt-cache naming, defaults overlays, workspace helper denials, and discovery leak behavior. |
| 0147 | [Gateway per-principal config, secrets, and defaults](planned/gateway-control-plane/0147_gateway_per_principal_config_secrets_defaults.md) | In progress | Gateway-baseline plus per-user capability-default overlays and console UX landed; raw provider-secret storage/injection remains deliberately deferred pending a Core/Gateway secret boundary. |
| 0148 | [Gateway workflow registry ACLs](planned/gateway-control-plane/0148_gateway_workflow_registry_acl.md) | In progress | Immutable tenant catalog versions, admin default pointers, ACL APIs, explicit catalog scope, signed run-start/schedule policy, host-side catalog guards, ACL-aware catalog inspection, and discovery metadata landed; per-tool/workspace/secret policy intersection and UI remain. |
| 0150 | [Observer and Manager responsibility split](planned/gateway-control-plane/0150_observer_manager_responsibility_split.md) | Planned | Early containment audit to keep Observer focused on observability and admin/config ownership in Gateway/Gateway Console or later Manager surfaces. |
| 0153 | [Gateway browser session security contract](planned/gateway-control-plane/0153_gateway_browser_session_security_contract.md) | In progress | Gateway/Flow opaque browser sessions, CSRF, logout, token-rotation revocation, Code/Observer hosted proxy convergence, and HTTP/HTTPS/origin/expiry/logout/revocation cookie matrix tests landed. |

## Active Proposed Work

| ID | Item | Status | Notes |
|----|------|--------|-------|
| 0144 | [User profile metadata for selective model grounding](proposed/0144_user_profile_context_grounding.md) | Proposed | Discuss first/last name, birth date, inferred country, provenance, and query-time selective context injection before implementation. |
| 0151 | [Runtime Explorer contract](proposed/gateway-control-plane/0151_runtime_explorer_contract.md) | Proposed | Reviewer consensus: start with a read-only Gateway envelope contract and Observer page for typed runtime resources; defer `abstractexplorer`, delete/export, raw workspace browsing, and admin cross-user exploration. |
| 0152 | [AbstractManager package extraction](proposed/gateway-control-plane/0152_abstractmanager_package_extraction.md) | Proposed | Revisit a separate `abstractmanager` package only after console/config/workflow ACL surfaces prove real maintenance or reuse pressure. |
| 0155 | [Hosted proxy shared helper extraction](proposed/gateway-control-plane/0155_hosted_proxy_shared_helper_extraction.md) | Proposed | Keep conformance tests now; extract a shared Node helper only if Code/Observer or future hosted apps drift again. |

## Recent Completed Work

| ID | Item | Completed | Notes |
|----|------|-----------|-------|
| 0157 | [Gateway provider endpoint profiles](completed/0157_gateway_provider_endpoint_profiles.md) | 2026-05-31 | Added Gateway-owned provider endpoint profiles with descriptions, write-only API keys, virtual `endpoint:*` providers in discovery, Runtime resolution, local dynamic provider construction, console UI with model discovery, and tests. |
| 0156 | [Retained runtime admin lifecycle](completed/0156_retained_runtime_admin_lifecycle.md) | 2026-05-30 | Added admin-only retained runtime list/transfer/purge routes, Gateway Console actions, scoped purge deletion, transfer semantics, and regression tests. |
| 0154 | [Multi-user security release blockers](completed/0154_multi_user_security_release_blockers.md) | 2026-05-30 | Added retained-runtime reservations, Code/Observer hosted URL guards, published launcher user bootstrap, and `.DS_Store` cleanup. |
| 0149 | [Cross-app Gateway auth and defaults convergence](completed/0149_cross_app_gateway_auth_defaults_convergence.md) | 2026-05-30 | Per-app hosted/local auth/default matrix completed; Flow, Code Web, and Observer use hosted browser-session proxy auth; shared auth/default component intentionally deferred until duplication creates real pressure. |
| 0141 | [Flow browser-session Gateway auth](completed/0141_flow_browser_session_gateway_auth.md) | 2026-05-30 | Initial Flow browser sign-in removed server/admin ambient browser auth; 0153 now supersedes raw token cookies with opaque Gateway browser sessions. |
| 0140 | [Abstract Release Skill](completed/0140_abstract_release_skill.md) | 2026-05-24 | Added a read-only framework release orchestration skill with package discovery, release-wave planning, dependency-floor review, root profile pin drift checks, PyPI visibility gates, and approval/traceability guidance. |
| 0139 | [Unified Framework Capability Defaults](completed/0139_unified_framework_capability_defaults.md) | 2026-05-24 | Core-owned routing defaults for input/output/embedding/rerank, Gateway control-plane access, atomic provider/model resolution, catalog-backed Flow defaults UI, and qwen3.6 text default. |

## Operating Notes

- Use `docs/adr/` for durable architecture policy.
- Use this backlog for execution traceability, validation evidence, and follow-up state.
- New backlog item filenames should use `NNNN_<slug>.md`; date-prefixed legacy files should not be copied for new work.
