# Proposed: Runtime Explorer contract

## Metadata
- Created: 2026-05-30
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021
- ADR impact: May revise existing ADR

## Context
Users need to understand their runtime: runs, ledgers, artifacts, memories,
workflows, workspaces, quotas, storage, and recent activity. Gateway can expose
the data, Observer already visualizes runs, and a future `abstractexplorer`
could become a dedicated runtime browser.

## Current code reality
- Gateway has many endpoints for runs, artifacts, workflows, prompt cache,
  workspaces, schedules, and maintenance.
- Observer already handles run/ledger observability and some broad operational
  surfaces.
- Gateway Console v0 is planned for account/admin/runtime summary, not deep
  runtime exploration.
- Hosted user auth now routes normal users to per-principal runtime data
  planes; any explorer contract must derive the browsed owner from the current
  principal unless an admin-only audited route explicitly selects another user.

## Problem or opportunity
Runtime state is opaque. Users want a file-system-like way to list, search,
inspect, export, delete, and understand their own runtime data. It is unclear
whether that belongs in Gateway Console, Observer, or a new app.

## Proposed direction
Define an API-first Runtime Explorer contract before creating a package. The
contract should cover list/search/detail/export/delete for current user's runs,
artifacts, memory, workflows, sessions, workspace files, prompt-cache metadata,
and storage usage. Keep admin cross-user exploration behind explicit RBAC.
Before promotion, classify data by sensitivity: prompts, tool parameters,
artifacts, memory, logs, PII, secrets, deleted data, retention state, and export
redaction needs.

Start with a read-only normalized resource envelope:
`type`, `id`, `scope`, `owner`, `sensitivity`, `created_at`, `updated_at`,
`summary`, `metadata`, `links`, and permission-aware `actions`. Keep
`browse/search/detail` separate from `export/delete`; export and deletion need
separate RBAC, audit logging, retention semantics, and confirmation UX.

The runtime should feel queryable like an operating/file system, but that does
not mean it should expose raw files first. The first API should expose typed
runtime resources (runs, artifacts, memories, workflows, sessions, prompt-cache
entries, workspace files, and storage summaries) with cursor pagination,
date/type filters, and redacted previews.

## Why it might matter
If runtime exploration becomes a large UX, `abstractexplorer` is a clean name
and boundary. If it stays small, it can remain Gateway Console tabs or Observer
pages.

## Promotion criteria
- Gateway Console v0 and Observer both need overlapping runtime browsing.
- Users need cross-cutting runtime search beyond run observability.
- RBAC policy matrix can safely expose explorer routes.
- Data classification, pagination, quota, export redaction, delete/retention,
  and audit requirements are written down.

## Validation ideas
- Alice/Bob cannot explore each other's runtime data.
- User can search own artifacts/runs/memory by metadata.
- Admin cross-user views require admin role and audit logging.
- Non-admin explorer requests cannot pass `owner_id`, `all_owners`, or arbitrary
  runtime paths to escape their principal-derived runtime.
- Export/delete actions require explicit action-level authorization and produce
  audit events.

## Non-goals
- This proposal does not authorize a new package yet.
- Do not build broad runtime exploration before route-family RBAC exists.
- Do not implement delete/export as ordinary browsing actions; treat them as
  high-risk operations with explicit RBAC, audit, and retention semantics.
- Do not turn the initial Gateway Console into a deep explorer before the API
  contract and sensitivity labels exist. It can link to Explorer/Observer once
  the boundary is stable.

## Guidance for future agents
Reserve `abstractexplorer` as a plausible future package name, but start with
contracts and narrow Gateway/Observer integrations.

## Review synthesis - 2026-05-30

Three independent review perspectives converged on the same boundary:

- Product/UX perspective: build Runtime Explorer as a read-only Observer page
  first. A user should be able to inspect their own runs, artifacts,
  session-level memory, workflow references, and storage summaries without
  learning raw Gateway routes. Keep destructive operations and admin
  cross-user views out of v0.
- Security/control-plane perspective: Gateway should own the explorer API
  contract, RBAC, redaction, sensitivity labels, links, and permission-aware
  actions. Normal user routes must derive owner from the authenticated
  principal; do not accept `tenant_id`, `runtime_id`, `owner_id`, raw workspace
  paths, or `all_owners` as ordinary user selectors.
- Architecture perspective: do not create `abstractexplorer` yet. Gateway
  already owns the data access and Observer already owns observability UX. A
  separate package becomes justified only if cross-resource search, saved
  views, export/retention tooling, and runtime "file system" navigation grow
  beyond Observer's natural scope.

If this proposal is promoted, narrow the first planned item to
`runtime_explorer_read_only_v1`: a Gateway envelope contract plus an
Observer-hosted page. The first envelope should cover `run`, `artifact`,
`memory`, `workflow`, and `defaults` resources with bounded previews,
provenance links, sensitivity labels, and action availability. Defer raw
workspace browsing, prompt-cache internals, delete/export, and admin cross-user
runtime browsing until separate RBAC, audit, redaction, and retention semantics
are written.
