# 0886 — Docs sites stay current: abstractcore deploys at all, runtime and gateway between releases

> Package: abstractcore, abstractruntime, abstractgateway (.github/workflows)
> Type: task
> Created: 2026-09-25
> Priority: normal
> Labels: docs, ci, publishing

## Summary

The public docs sites lag the docs in the repositories. abstractcore has no docs deploy job at all
(its gh-pages branch was last updated 2026-05-27 and the README links that stale site).
AbstractRuntime and abstractgateway deploy only in the `deploy-docs` job of `release.yml`, on a
release tag, so the docs-only coredoc commits of 2026-09-25 (`696f386`, `3312bfe`) are not on their
sites until the next release.

## Current code reality

- abstractcore `.github/workflows/`: `ci.yml`, `publish-ghcr.yml`, `release.yml`; none runs
  `mkdocs gh-deploy`.
- abstractruntime `release.yml` l.283–307 and abstractgateway `release.yml` l.364–387:
  `deploy-docs` on `v*.*.*` tags / `workflow_dispatch`.

## Scope

- Decide the policy (deploy on `main` pushes touching `docs/**`, or keep tag-only and accept the
  lag) and apply it to all three; add the missing abstractcore deploy job.
- One-off: `mkdocs gh-deploy` for the three repos now (owner action), after 0884.
- Out of scope: site theme or structure.

## Acceptance criteria

- [ ] Each site's footer/commit matches `main` (or the latest tag, per the chosen policy).
- [ ] abstractcore's README links a site that is current.

## Testing

- `gh run list -R lpalbou/AbstractCore --workflow docs.yml -L 1`
- `git -C abstractcore log -1 --format=%ci origin/gh-pages`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` ("docs site" column); related 0884.
