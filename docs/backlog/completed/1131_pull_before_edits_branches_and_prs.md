# 1131 — Pull before edits, branches and PRs

> Package: AbstractFramework, AbstractSkill (release procedure)
> Type: task
> Created: 2026-11-05
> Status: Completed
> Completed: 2026-11-05
> Priority: high
> Labels: release, workspace, regression

## Summary

The operator requires the agent to fetch and pull proactively before editing code, creating
branches/worktrees, and submitting/updating PRs. The clarification on 2026-11-05 explicitly
rejects replacing those actions with blocking stale-source gates.

## Initial audit and correction

Remote release PRs were merged without consistently updating normal main checkouts. The
redeploy list covered Python release tags and separately installed npm apps, omitting app
source synchronization. The initial implementation added checks to build/start entry points.
After the operator's clarification, those entry-point changes were removed in full, including
the incidental missing-toolchain behavior change. Builds/starts keep their previous behavior.

## Delivered workflow (ADR 0051)

1. Before code or metadata edits, the agent fetches/pulls the affected main checkouts. Cross-package
   work begins with `bash scripts/pull.sh` across the full inventory.
2. Before branch/worktree creation, fetch/pull again and base the new branch on fresh `origin/main`.
3. Before PR submission/update, pull main, fetch the active feature branch's upstream, merge
   missing upstream/main commits, resolve conflicts, validate, then push/create/update the PR.
4. After remote merges, immediately pull the corresponding normal main checkout; the coordinator
   owns worker-merge synchronization too.
5. Before handoff, pull the full inventory again and refresh validation/deployment if source moved.

Existing feature worktrees are integrated before edits, not left stale because normal main was
updated elsewhere. Routine preparation is performed without asking the operator. Existing edits
and published hashes are preserved; no automatic reset, force-push or stash. Read-only audits
remain read-only. Actual conflicts/ownership decisions or unavailable remotes are reported.

## Implementation and persistence

- Local workspace AGENTS.md records the rule for all implementation tasks.
- Both `abstract-release` and `release` carry it in the bundled AbstractSkill source and the active
  Codex installations. The installed abstract-release is also shared with Claude by its existing
  symlink. The Codex release installation points directly at the bundled source.
- AbstractSkill bundle revision 2026.11.09 updates the adopted hashes and content pin without
  raising trust levels. No package version or release was published.
- `pull.sh` retains its executable bit, bounded log fix and applied-commit log correction.
- `status.sh --check` and `check_workspace.py` remain optional final-audit tools. No mandatory
  build/start preflight or receipt ceremony remains in code or in the operative procedure.

## Validation and completion

Completed locally 2026-11-05. The agent performed the fetch/pull preparation on root and
AbstractSkill before making this correction. Both were up to date and existing edits were retained.
Repository-script sandbox tests exercise actual fast-forwards and divergence preservation using
local bare remotes. The optional checker/receipt tests, bundled-skill tests and frontmatter
validators passed after the correction: 24 optional-checker tests + 20 bundled-skill tests
(44 passed together), 35 repository-script sandbox checks, both skill frontmatter validators,
shell syntax and diff-whitespace checks. `git diff --exit-code -- scripts/build.sh
scripts/start-local.sh` confirms both entry points match their pre-session versions.

Independent forward-testing of the earlier optional checker found hidden-index false passes;
these remain fixed. The earlier build-completeness finding (missing selected toolchains can be
skipped) is preserved as a known existing build limitation, outside this pull-preparation task.
Neither a source audit nor a successful arbitrary command proves that every component was built.

Original path: `docs/backlog/planned/1131_enforce_workspace_freshness_before_build_and_handoff.md`.
Source changes remain uncommitted/unpublished. No new hooks, daemons, service restarts, root
release or website publication. The primary prevention is proactive preparation at each named
work transition; optional checks are final confirmation.

Earlier completed-record path: `docs/backlog/completed/1131_enforce_workspace_freshness_before_build_and_handoff.md`; renamed after the operator clarified the pull-first objective.
