# Planned: Gateway tenant isolation and shared runtime design

## Metadata
- Created: 2026-05-29
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033
- ADR impact: May revise existing ADR

## Context
AbstractGateway currently uses bearer-token security for the gateway API
surface. In user-auth mode, bearer tokens resolve to a user principal and
Gateway can route each principal to a separate runtime/data plane. AbstractFlow
uses browser-session cookies for user tokens and does not let a server/admin
token become shared browser login state.

The present model is suitable for local single-user deployments and trusted
cohorts. It is not a multi-user isolation model for independent users.

## Current code reality
- `abstractflow/web/backend/main.py`, `abstractflow/web/frontend/bin/cli.js`, and
  `abstractflow/web/frontend/vite.config.ts` proxy `/api/gateway/*` and inject
  the signed-in browser session's Gateway user token.
- `abstractgateway/src/abstractgateway/security/gateway_security.py` validates
  global bearer tokens and origin policy, but does not resolve a tenant/user
  principal.
- Gateway run, ledger, command, artifact, KG, prompt-cache, and VisualFlow
  routes are scoped by ids and request parameters, not by authenticated owner.
- AbstractRuntime state carries `actor_id` and `session_id`; those are
  provenance/correlation fields, not authorization boundaries.
- Memory owner ids include run/session/global concepts; global means the runtime
  instance's global owner, not a tenant-isolated namespace.

## Problem
If several independent users share one Flow/Gateway/runtime/data plane today,
one user can potentially list or access another user's run metadata, ledgers,
history bundles, artifacts, prompt-cache state, workflow mutations, memory, tool
execution surface, workspace effects, provider credentials, and audit scope.
`session_id`, `run_id`, `artifact_id`, and `owner_id` are not safe authorization
proofs.

## What we want to do
Define and implement a tenant-aware Gateway architecture that supports
independent users safely. Until that exists, document and enforce the supported
deployment pattern: an authenticated front door routes each user or tenant to a
separate Gateway/runtime/data plane.

## Why
Gateway is the durable control plane. Shared use without tenant authorization
risks confidentiality leaks, integrity failures, workspace/file access problems,
memory poisoning, credential bleed, and weak auditability.

## Requirements
- Add a `Principal` or `TenantContext` resolved from trusted Gateway auth.
- Persist `tenant_id`, `user_id`, roles/scopes, and token fingerprint on runs and
  audit records without logging bearer tokens.
- Enforce tenant filtering for run list/detail, ledger replay/stream, history,
  commands, artifacts, uploads/import/export, prompt cache, workflow CRUD/publish,
  KG/memory owner access, workspace policy, tool execution, and provider
  credentials.
- Treat `session_id`, `run_id`, `artifact_id`, and `owner_id` as references only;
  never as authorization.
- Make `global` memory tenant-global by default; cross-tenant shared memory must
  be an explicit namespace with provenance, consent, deletion, and poisoning
  controls.
- Keep local single-user ergonomics through an explicit single-tenant default.
- Add two-user isolation tests across the control plane and stores.

## Suggested implementation
1. Near term: deploy an identity-aware front door that routes each authenticated
   user or tenant to a separate Gateway process, data dir, artifact store, memory
   store, workspace root, provider credential set, and quota bucket.
2. Add Gateway token-to-principal mapping for single-process deployments, but keep
   it single-tenant until storage and route enforcement are complete.
3. Introduce tenant/user columns or metadata in run stores, artifact metadata,
   prompt-cache keys, memory owner ids, workflow records, and audit logs.
4. Centralize authorization checks in service/storage layers so route handlers
   cannot accidentally bypass tenant filtering.
5. Admin-gate or disable global enumeration paths (`scope=all`, arbitrary
   `owner_id`, `all_owners`, broad artifact search, workflow mutation, and local
   tools) until tenant-aware policy exists.

## Scope
- AbstractFlow hosted connection model.
- AbstractGateway auth, routes, stores, artifact handling, memory/KG access,
  prompt-cache routes, workflow CRUD/publish, commands, audit, and workspace
  policy.
- AbstractRuntime run state and store schemas where tenant ownership must be
  durable.
- Documentation, ADRs, and release gates for supported deployment topologies.

## Non-goals
- Do not claim current shared Gateway deployments are tenant-isolated.
- Do not use caller-supplied `session_id`, `actor_id`, `owner_id`, or headers as a
  trusted identity source.
- Do not make cross-user learning implicit. Shared/org memory must be explicit
  and auditable.
- Do not treat workspace scoping or `execute_command` as an OS sandbox.

## Dependencies and related tasks
- `docs/backlog/completed/0141_flow_browser_session_gateway_auth.md`
- `abstractgateway/docs/backlog/proposed/2026-05-13_shared_identity_context.md`
- ADR-0018 durable Gateway/control-plane contract.
- ADR-0021 deployment topologies and supported scenarios.
- ADR-0033 install profiles and server boundaries.

## Expected outcomes
- Operators can choose between clearly documented single-tenant, trusted-cohort,
  and future shared-tenant modes.
- Independent users cannot enumerate or access each other's runs, artifacts,
  memory, workflow mutations, workspaces, credentials, prompt-cache state, or
  audit details.
- Shared memory/cross-user learning is opt-in, provenance-rich, revocable, and
  separate from private user/tenant memory.

## Validation
- Two-user integration tests for Flow proxy sessions, Gateway runs/list/history,
  ledger stream/replay, commands, artifact search/content/upload/import/export,
  KG/memory queries, prompt-cache routes, VisualFlow CRUD/publish, workspace
  tools, and local tool execution policy.
- Store-level tests proving tenant filters are enforced below route handlers.
- Security docs and ADR checks confirming shared Gateway is not advertised as
  isolated before the tenant model lands.

## Progress checklist
- [ ] Finalize principal/tenant data model and single-tenant compatibility mode.
- [ ] Implement per-user/per-tenant Flow connection routing or front-door contract.
- [ ] Persist tenant/user ownership on Gateway and Runtime records.
- [ ] Enforce tenant filtering in Gateway service/store layers.
- [ ] Add two-user authorization test matrix.
- [ ] Document shared memory and cross-user learning as explicit opt-in.

## Guidance for the implementing agent
Start from code reality, not desired UX. Add authorization at the lowest shared
storage/service layer available, then wire routes to it. Preserve single-user
local ergonomics, but fail closed for shared hosted deployments.
