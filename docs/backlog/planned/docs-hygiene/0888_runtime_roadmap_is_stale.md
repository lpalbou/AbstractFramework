# 0888 — AbstractRuntime `ROADMAP.md` is stale

> Package: abstractruntime (ROADMAP.md)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: docs

## Summary

`abstractruntime/ROADMAP.md` still says "Current status (v0.4.2)" (the package is at 0.4.34) and
points at a backlog link that no longer resolves. The coredoc pass left it out of its file list.

## Current code reality (`main` `696f386`)

- `ROADMAP.md` l.3 "## Current status (v0.4.2)"; "Near-term priorities … tracked in
  `docs/backlog/planned/`".

## Scope

- Rewrite against today's features and the live backlog, or delete it and link the backlog from the
  docs index.

## Acceptance criteria

- [ ] No stale version and no dead link in `ROADMAP.md` (or the file is gone and nothing links it).

## Testing

- `grep -n "v0.4.2" abstractruntime/ROADMAP.md`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractruntime row).
