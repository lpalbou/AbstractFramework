# 0884 — The abstractgateway docs site must not publish `docs/backlog/**`

> Package: abstractgateway (mkdocs.yml)
> Type: bug
> Created: 2026-09-25
> Priority: normal
> Labels: docs, publishing

## Summary

MkDocs builds every Markdown file under `docs/` unless excluded. `abstractgateway/mkdocs.yml` has no
`exclude_docs`, so `docs/backlog/` (overview, completed and deprecated items: internal planning,
incident notes, hub message ids) is published on the public site at
`https://www.lpalbou.info/AbstractGateway/` on every tagged release.

## Current code reality (`v0.4.2`, `main` `3312bfe`)

- `mkdocs.yml`: `site_url` set; no `exclude_docs`; `docs/backlog/{overview.md,completed,deprecated}`
  present.

## Scope

- Add `exclude_docs: backlog/` (and any other internal folders), rebuild with `--strict`, redeploy.
- Check abstractcore and abstractruntime `mkdocs.yml` for the same gap in the same pass.

## Acceptance criteria

- [ ] `mkdocs build --strict` output has no `backlog/` directory.
- [ ] The deployed site returns 404 for `/AbstractGateway/backlog/overview/`.

## Testing

- `mkdocs build --strict -f abstractgateway/mkdocs.yml -d /tmp/gw-site && test ! -d /tmp/gw-site/backlog`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractgateway row).
