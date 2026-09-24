# 0871 — The `abstract-release` planner must not discover packages in scratch trees

> Package: abstract-release skill (`~/.claude/skills/abstract-release/scripts/abstract_release_plan.py`); consumed by abstractframework release waves
> Type: bug
> Created: 2026-09-25
> Priority: normal
> Labels: release, tooling

## Summary

The release planner walks the workspace with `os.walk` and prunes only `IGNORE_PARTS`
(`.git`, `.venv`, `venv`, `build`, `dist`, `node_modules`, `site`, `target`, caches) and names
ending in `-backup` / `-gh-pages`. It does not prune `untracked/` (every agent's scratch: package
copies, `git archive` extracts such as `untracked/release-2026-09-24/root-0.3.0/` with its own
`pyproject.toml`, scratch venvs with installed `site-packages`), agent git worktrees, or gateway
runtime workspaces. A scratch copy of a package can be reported as a package with pending changes
or pollute the dependency edges.

## Current code reality (2026-09-25)

- `abstract_release_plan.py` l.24–42 (`IGNORE_PARTS`, `IGNORE_SUFFIXES`), `should_skip` l.134,
  `iter_manifests` l.147, `iter_source_dependency_files` l.304.
- The workspace currently holds `untracked/release-2026-09-24/root-0.3.0/pyproject.toml` (a full
  root tree extracted from the tag) and dozens of mission folders with package copies.

## Scope

### In scope

- Prune `untracked`, any directory whose `.git` is a file pointing into another repo's
  `worktrees/`, and gateway runtime/workspace folders (`workspaces/`, `runtime/`), or better:
  discover packages only from the workspace inventory (`scripts/lib/packages.txt`) and each
  repository's `git ls-files`.
- A regression test with a fake workspace holding a scratch copy under `untracked/`.

### Out of scope

- Changing the release order logic (0860).

## Acceptance criteria

- [ ] With a package copy under `untracked/x/`, the planner lists the real package once and no
      scratch path.
- [ ] Output on today's workspace names no path under `untracked/`.

## Testing

- `python3 ~/.claude/skills/abstract-release/scripts/abstract_release_plan.py --help`
- `python3 ~/.claude/skills/abstract-release/scripts/abstract_release_plan.py /Users/albou/tmp/abstractframework | grep -c untracked/` (expect 0)

## ADR status

- Governing: ADR-0034 (release sequence). ADR impact: None.

## Receipts

- Task brief of the 2026-09-25 backlog trace (operator's release process); code read above.
  Related: 0168 (planner root-pin guard), 0860.
