# 1126 — The install manifest's field reference moves to a user page (docs/api.md)

> Package: root (abstractframework docs)
> Type: task
> Created: 2026-11-04
> Priority: normal
> Labels: docs, install-manifest, llms

## Summary

`docs/installers/release-and-manifest.md` is the only field reference for the install manifest (its "Fields (schema
version 2)" table). Two user pages that are mirrored into `llms-full.txt` link to it as that reference:
`docs/api.md` ("Field reference: release-and-manifest.md") and `docs/install.md` (the manifest paragraph near the end).
Since the llms scope rule, that page is an internal release-steps page and is not mirrored, so a reader of
`llms-full.txt` meets a link to a page it does not carry.

## Why

Operator ruling of 2026-11-04: `llms*.txt` and the external docs are for people and agents who use the framework. A
tool that installs the framework from the manifest needs its fields; the release steps around them are internal.

## Scope

### In scope

- Move the Fields table (and only what a manifest consumer needs) into `docs/api.md`, next to `manifest`.
- Point `docs/api.md` and `docs/install.md` at that section; `release-and-manifest.md` keeps the release steps and
  links the new section.
- Regenerate `llms-full.txt`.

### Out of scope

- Changing the manifest or its schema.

## Acceptance criteria

- [ ] No page mirrored into `llms*.txt` links `docs/installers/release-and-manifest.md`.
- [ ] `llms-full.txt` carries the manifest's field table once, from `docs/api.md`.
- [ ] The CONTRIBUTING note naming this hole is removed in the same change.

## Receipts

- Review of root PR #63 (`untracked/council-2026-11-02/review-root-62-64.md`, root, untracked).
