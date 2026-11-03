# ADR-0042: Every Checkout Stays in Step With Its Remote

- Status: Accepted
- Date: 2026-10-28
- Scope: every repository of the framework workspace, every agent and person working in it

## Context

On 2026-10-27 several local `main` checkouts were found dozens of commits behind their GitHub
remotes (abstractuic 86, the root 10, others a handful). Pull requests had been merged on GitHub
by agents and merge watchers while nobody fast-forwarded the local checkout, and new branches and
worktrees were then cut from the stale local `main`. The result: duplicated work, release branches
missing merged fixes, merge conflicts on every later pull, and a root `main` that had to be merged
by hand with releases made elsewhere. The permission policy that denies `git reset`, `git checkout`,
`git clean` and `git stash` is NOT the cause (`git pull --ff-only` is allowed); the missing habit is.

## Decision

1. Before cutting a branch or a worktree, the actor fetches and fast-forwards the repository's
   `main` checkout: `git -C <repo> fetch origin && git -C <repo> pull --ff-only origin main`. A dirty
   checkout is left alone and reported; nobody stashes or resets another seat's work.
2. Worktrees and branches are cut from `origin/main`, never from the local `main` ref.
3. Whoever merges a pull request on GitHub (a person, an agent, a watcher) pulls the local `main`
   checkout right after the merge.
4. Before any release wave, a sweep runs over every repository: `git rev-list --count main..origin/main`
   must be 0 for every clean checkout on `main` (the root `scripts/status.sh` prints ahead/behind per
   repository).
5. A diverged `main` holding the operator's local commits is merged, never rebased: local commits keep
   their hashes; in conflicts the remote release's pins and version win, local docs and backlog
   additions are kept, duplicated release sections are dropped.

## Consequences

Agents spend a fetch per task; merge watchers carry a pull step; the abstract-release skill carries
this rule ("Keep every checkout in step with GitHub") so it survives sessions.

## Enforcement

- Agent briefs and the abstract-release skill state rules 1–3 verbatim.
- The merge watchers used in release waves pull the local `main` after every GitHub merge.
- Code review of a release PR checks that its branch was cut from `origin/main`.

## Validation

- `scripts/status.sh` at the root shows 0 behind for every clean `main` checkout before a release.
- The audit of 2026-10-27 is the baseline: abstractuic 86 behind, root 10 behind, both reconciled.

## Related

- abstract-release skill, section "Keep every checkout in step with GitHub (repo sync rule)".
- Root backlog 1055 (release wave 2026-10-27) and recurrent 1060 (gateway standing duty).
