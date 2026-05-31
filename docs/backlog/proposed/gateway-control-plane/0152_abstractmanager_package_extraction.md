# Proposed: AbstractManager package extraction

## Metadata
- Created: 2026-05-30
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018, ADR-0021, ADR-0033, ADR-0035
- ADR impact: May revise existing ADR

## Context
Gateway needs an admin/account/config UX. The first version should likely be
Gateway-served to keep first-run setup simple. If the UI grows into a rich
control-plane product, a separate package such as `abstractmanager` may become
cleaner.

## Current code reality
- Gateway owns identity, routing, user CRUD, and control-plane APIs.
- Core owns config/default schema and persistence.
- Flow, Code, Observer, and Assistant are task-specific apps.
- There is no Manager package.

## Problem or opportunity
A built-in Gateway Console can become too large if it tries to own users,
secrets, defaults, workflows, runtime browsing, audit, setup, and operations.
A separate Manager package could improve frontend code quality and release
boundaries, but creating it too early increases package sprawl.

## Proposed direction
Start with Gateway Console v0 inside Gateway. Reassess extraction after admin
console, config/defaults, and workflow ACL pages are real. If extracted,
`abstractmanager` should be a Gateway-hosted or Gateway-connected control-plane
app, not a second authority.
Gateway Console v0 should still be built behind a clean frontend boundary:
typed Gateway API client, no direct Core calls, no app-local auth assumptions,
and asset/package layout that can be extracted later without rewriting
authorization.

## Why it might matter
This keeps initial setup simple while preserving a path to a cleaner product
boundary if the admin/config UX grows.

## Promotion criteria
- Gateway Console frontend becomes too large for Gateway package maintenance.
- Multiple Gateway deployments need the same rich admin UI.
- AbstractUIC components and release flow make a package split cheaper than
  embedding assets in Gateway.
- Console v0, per-principal config/defaults, workflow ACLs, and the
  responsibility split have shipped or been accepted.
- Extraction does not make first-run setup harder.

## Validation ideas
- Compare bundle size, release overhead, install profile complexity, and user
  setup friction before extraction.
- Confirm Manager never bypasses Gateway authorization.

## Non-goals
- Do not create `abstractmanager` before Gateway Console v0 proves the need.
- Do not let Manager own secrets/config independently of Gateway/Core.
- Do not extract merely because the name is attractive; extract only when
  maintenance, reuse, or release pressure proves the package boundary.

## Guidance for future agents
Treat `abstractmanager` as a package-boundary option, not a feature requirement.
The authority remains Gateway plus Core config APIs either way.
