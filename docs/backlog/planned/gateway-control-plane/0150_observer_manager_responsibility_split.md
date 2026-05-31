# Planned: Observer and Manager responsibility split

## Metadata
- Created: 2026-05-30
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: May revise existing ADR

## Context
Observer is useful but broad. It has grown toward observability, launch,
backlog, email, process, and operational pages. Gateway now needs account,
admin, config, user/runtime, and workflow-permission UX. Putting all of that
into Observer would make app boundaries unclear.

## Current code reality
- Observer is the existing runtime/run observability app.
- Gateway has control-plane APIs and is gaining identity/routing authority.
- There is no dedicated Manager/Admin app yet.
- Gateway Console v0 is planned as a narrow built-in control-plane UX.

## Problem
Without a responsibility split, Observer can become a catch-all operational app
and Gateway can become a monolithic UI. Users need a clearer product map.

## What we want to do
Define app responsibilities early enough to contain scope before Gateway
Console, Runtime Explorer, and cross-app migrations expand. Proposed ownership:
- Gateway/Gateway Console: identity, account, admin, config, runtime summary,
  workflow registry permissions.
- Observer: run/ledger/artifact observability, runtime health, audit views, and
  operational monitoring.
- Flow: workflow authoring.
- Code: coding-agent UX.
- Assistant: personal assistant UX.
- Future Explorer/Manager: only if Gateway Console or Observer becomes too broad.

## Why
Clear product boundaries improve user onboarding, code ownership, security, and
release planning.

## Requirements
- Audit Observer high-trust surfaces: backlog execution, email, process control,
  env management, scheduling, broad runtime management.
- Immediately classify existing high-trust surfaces as observability,
  admin/config, operator-only, domain-app, or migration candidate.
- Hosted-mode unsafe paths must be marked operator-only behind Gateway
  authorization or hidden/disabled until `0146` enforcement exists.
- Decide which surfaces remain Observer operator views and which move behind
  Gateway Console/Manager APIs.
- Define links between apps instead of duplicating full functionality.
- Keep all sensitive operations authorized by Gateway, not by frontend routing.

## Suggested implementation
Write a short app-boundary decision doc or ADR update, then migrate one surface
at a time. Start by documenting which current Observer pages are observability,
which are admin/config, and which are domain apps.

## Scope
- App responsibility audit.
- Docs/ADR update.
- Containment notes for high-trust Observer/Gateway routes that should not be
  presented as ordinary hosted-user UX.
- Follow-up tickets for migrations.

## Non-goals
- Do not create a new package before the boundary is proven.
- Do not remove useful Observer pages without replacement.
- Do not move Flow authoring into Gateway.

## Dependencies and related tasks
- `0145_gateway_admin_console_bootstrap.md`
- `0146_gateway_rbac_scope_policy_matrix.md`
- `0151_runtime_explorer_contract.md`
- `0152_abstractmanager_package_extraction.md`

## Expected outcomes
- Users can understand which app to open for admin/config vs observability vs
  authoring.
- High-trust Observer surfaces are either clearly operator-only or moved into
  Gateway-managed control plane.
- Future package split decisions are grounded in actual use, not naming alone.

## Validation
- Documentation names each app's responsibility and non-goals.
- UI navigation links users to the right app/surface.
- Authorization tests protect high-trust surfaces.

## Progress checklist
- [ ] Audit Observer surfaces.
- [ ] Draft app responsibility matrix.
- [ ] Classify high-trust surfaces and containment status.
- [ ] Update ADR/docs.
- [ ] Create migration backlog items where needed.

## Guidance for the implementing agent
Do not solve this by naming a new app too early. First make the ownership model
explicit, then extract only when code and UX pressure justify it.
