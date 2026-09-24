# 0882 — abstractcore `llms-full.txt` covers every user doc page

> Package: abstractcore (scripts/update_llms.py, llms-full.txt)
> Type: bug
> Created: 2026-09-25
> Priority: low
> Labels: docs, llms

## Summary

`scripts/update_llms.py` inlined a hand-maintained `SOURCES` tuple (30 entries) that omitted 20 top-level user topic
pages under `docs/` (for example `capabilities.md`, `prompt-caching.md`, `reasoning-control.md`,
`request-output.md`, `web-tools.md` at `v2.15.1`), so `llms-full.txt` — the AI-readable handbook —
silently lacked them, and `--check` passed.

## Current code reality (checked 2026-09-25 ~01:20 CEST)

- Released `v2.15.1`: hand list, 30 entries.
- Local `main` commit `4407015` "docs(tooling): llms sources derive from the docs index":
  `indexed_sources()` reads `docs/README.md`, skips `adr/archive/backlog/known_bugs/reports/
  research`, requires every top-level `docs/*.md` to be linked; new `tests/test_llms_sources.py`.
  **Not pushed, not released** at the time of this trace.

## Scope

- Push and release; confirm `--check` fails when a page is added without an index link.

## Acceptance criteria

- [ ] Fix on `origin/main` and in a released version; `llms-full.txt` regenerated in the same commit.
- [ ] Test red when a top-level docs page is missing from the index.

## Testing

- `python abstractcore/scripts/update_llms.py --check`
- `python -m pytest abstractcore/tests/test_llms_sources.py -q`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractcore row); abstractcore commit `4407015`.
