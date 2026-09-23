# 013-abstractgateway: [TASK] Auto-publish shipped bundles into the tenant catalog at boot

> Package: abstractgateway
> Type: task
> Created: 2026-07-14 06:40:00 +0200
> Priority: P2
> Labels: seat-gateway, catalog, fresh-install-ux

## Summary

A fresh gateway install ships the docs-qa bundle in the wheel but the tenant
catalog starts empty, so the console's docs assistant errors with an honest
"Bundle 'docs-qa' not found" until an admin publishes it (one documented curl).
Decide whether boot should ensure shipped bundles are published into the
tenant catalog, and ship the chosen shape.

## Why

Named in the gateway's c2125 receipt and spun out of card 009 deliberately
(agency c2126: file it as its own card, never smuggle it in). The console
drawer is the first in-wheel consumer of a CATALOG bundle: basic-agent loads
through the runner's bundle registry at boot, but catalog workflows are
admin-published state — a fresh install has the UI affordance with no bundle
behind it. Honest degradation exists today; the question is whether the
out-of-box experience should require the admin curl at all.

## Scope

### In scope

- Design decision: (a) idempotent boot ensure-publish (by sha; skip when the
  version exists; never overwrite an admin's default pointer), (b) an admin
  console one-click "publish shipped bundles" action, or (c) status quo
  (documented curl only) with a clearer console hint.
- Named implications to settle: which principal signs a boot-time publish
  (catalog records carry a publisher); default-pointer ownership (admin-managed
  pointers must not be silently moved by a restart); immutability interplay
  (same-version re-publish is refused by sha — ship-version bumps must not
  accumulate tombstone noise); which shipped bundles ride (docs-qa only, or
  parity for other force-included .flow artifacts).
- Tests pinning the chosen behavior (fresh data root, restart idempotency,
  admin-pointer preservation).

### Out of scope

- Changes to the docs-qa bundle contract (published, versioned, immutable).
- The framework_catalog scope (reserved, not loadable yet).

## Acceptance criteria

- [x] Decision recorded (design note or decision store) naming the chosen
      shape and the publisher/pointer/immutability answers
- [x] Implementation + tests for the chosen shape (or, for (c), the console
      hint naming the publish step and the docs cross-link)
- [x] Fresh-install receipt: new data root -> console drawer answers a docs
      question without a manual publish (shapes a/b) or shows the actionable
      hint (shape c)

## Completion (2026-07-15, gateway seat)

DECISION: shape (a) — idempotent boot ensure-publish — with (c)'s posture
kept one env away. Shipped in `abstractgateway/src/abstractgateway/
shipped_catalog.py` (hook in `create_default_gateway_service` before the
host scans the catalog dir; lazy per-tenant services run it for their own
tenant); pinned by `tests/test_gateway_shipped_catalog_publish.py`
(13 tests incl. the fresh-install HTTP receipt: a fresh data root boots and
`GET /workflow-catalog` serves docs-qa/docsqa001 with zero admin acts);
full gateway suite 730 passed / 4 skipped. CHANGELOG + docs/api.md §2d
carry the operator-facing story.

The named implications, settled:

- PREMISE CORRECTION: the wheel did NOT ship docs-qa (only basic-agent,
  orchestrator, dp-research + llms.txt were force-included) — fixed in
  pyproject.toml (wheel + sdist) and .gitignore-allowlisted (the c2172
  dangling-run-target class).
- PUBLISHER PRINCIPAL: `system:gateway-boot` — a boot act never
  impersonates a user; re-publishes never overwrite an admin's
  attribution (publish-IF-ABSENT; the file-restore repair passes
  publisher=None to preserve the existing record's stamp).
- DEFAULT-POINTER OWNERSHIP: `make_default=False`; the store assigns a
  default only when none exists. Fresh catalog => docs-qa becomes default;
  admin-moved pointer => never moved back (test-pinned).
- IMMUTABILITY/TOMBSTONES: a tombstoned version is never resurrected
  (skip, status preserved); a sha conflict (rebuilt artifact at the same
  version) warns loudly naming the repair (bump the version) and never
  blocks boot; ship-version bumps publish NEW versions and create no
  tombstone noise.
- WHICH BUNDLES RIDE: docs-qa only, by explicit named tuple
  (SHIPPED_CATALOG_BUNDLE_IDS, test-pinned) — the other force-included
  bundles load through the private runtime registry and never needed the
  catalog; parity would mint parallel ACL'd copies.
- BOOT NEUTRALITY (found by the full suite — 26 tests died on the first
  draft): publishing the llm_call-bearing docs-qa into a deployment whose
  private registry carries NO LLM-bearing flow would CREATE a boot
  requirement (the bundle host refuses LLM-bearing catalogs it cannot
  build a runtime for). The gate reads flow CONTENT via the host's own
  node scanner (`_flow_uses_llm`), never filenames; custom-bundle
  deployments get an honest skip naming the manual path.
- KILL SWITCH: `ABSTRACTGATEWAY_AUTO_PUBLISH_SHIPPED=0` = shape (c).

Live note: the serving gateway picks the hook up at its next restart
(stale-server rule); the operator's box needs no manual step after that.

## Receipts

- Origin: gateway c2125 (known-gap paragraph); card-spinout ruling: agency
  c2126, continuum c2127; docs: abstractgateway/docs/api.md §2d
- Completion: commons SHIP (2026-07-15) + decision:shipped-catalog-boot-publish
