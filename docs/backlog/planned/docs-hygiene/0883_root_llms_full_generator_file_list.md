# 0883 — Root `gen_llms_full.py`: complete user pages, no backlog/research, and a `--check`

> Package: abstractframework (scripts/gen_llms_full.py, llms-full.txt)
> Type: bug
> Created: 2026-09-25
> Priority: normal
> Labels: docs, llms

## Summary

The root `llms-full.txt` generator inlines a hand list of 90 files. It lacks the new
`docs/troubleshooting.md`, and 35 entries are backlog, research and `docs/claude/` files (including
`docs/backlog/overview.md` and individual backlog items) — planning material in a user-facing
AI handbook, which also goes stale on every backlog edit (this trace's own overview update makes it
stale). It has no `--check` mode and no CI step, so drift is invisible.

## Current code reality (root `cfb4926`)

- `scripts/gen_llms_full.py` `FILES` l.7–98; `main()` writes unconditionally; missing file →
  `SystemExit`.
- `docs/*.md` pages not in `FILES`: `docs/troubleshooting.md`.

## Scope

- Derive the list from the docs index (`docs/README.md`) the way abstractcore now does (0882);
  exclude `docs/backlog/**`, research and agent-skill material; add `--check`; run it in CI.
- Out of scope: rewriting llms.txt content.

## Acceptance criteria

- [ ] `llms-full.txt` contains every page the docs index links and no `docs/backlog/` path.
- [ ] `python scripts/gen_llms_full.py --check` fails on drift; CI runs it.
- [ ] Backlog files referenced by the generator today are not needed by it any more (moving a
      backlog item can no longer break the generator).

## Testing

- `python scripts/gen_llms_full.py --check`
- `grep -c "^--- docs/backlog/" llms-full.txt` (expect 0)

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (root row); related 0882.
