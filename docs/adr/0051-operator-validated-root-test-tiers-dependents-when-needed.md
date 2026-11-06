# ADR 0051: Root Releases Are Operator-Validated; Test Tiers; Dependents Re-Release Only When Needed

Status: Accepted — operator rulings 2026-11-04:
- "a light test strategy (when you do small changes) and a full test strategy. imagine you change an icon, a
  dropdown, add a model etc. you shouldn't need to run the full test";
- "when we release a lower level package, we maybe don't need to rebuild every packages on top";
- "when I personally test a release and validate it, that's when the root framework gets released, never
  before, and it gets released with the specific versions i tested. root should be for people installing
  the framework";
- "your job is to get us there, to make sure everything below works and redeploy what you think is
  prepared for release locally, so i can fully test it PERSONALLY, and only *I* can declare if this is
  something to release or not. this include the redeployment of the GH pages site LOCALLY, so i can test
  it and a report of the changes for that global release".

## Context

ADR 0050 made every push wait for the repository's own CI jobs to pass locally. Applied uniformly, that
runs the whole PR + main matrix for a one-line copy change. Release waves also re-cut every package above
a changed one, even when a dependent only needs to keep a compatible floor. And the root
`abstractframework` was published as soon as the wave's packages were, before anyone had used that
matrix. The root is what people install: the one-command installer resolves the last published root
and installs exactly its pins.

## Decision

1. **Two test tiers.** The author states the tier and why in the PR body; a reviewer may raise it.
   - **Tier L (light):** documentation, copy, icons, CSS, a single dropdown or control, a catalog or
     model entry, a changelog, or a pin bump together with its pin tests. Run the tests of the
     changed files, lint and type-check, and the build of that package. Not the full matrix.
   - **Tier F (full):** anything in a code path shared across features, concurrency or lifecycle,
     schemas and contracts, and every release branch. Run the whole PR + push-to-main job set
     (ADR 0050).
   - The local gate takes `scripts/ci_local.sh <repo> --tier light|full`, with `full` as the default.
     The root `scripts/ci_local.sh` implements it; backlog 1116 delivers it with the gate.
   - `--tier light` selects the tests mapped from the changed files, plus lint, type-check and the
     build. It fails loudly when a changed source maps to no test. Where a repository has no mapping
     yet, tier L runs the same checks by hand.
2. **Dependents re-release only when needed.** When a lower package is released, a dependent is
   re-released only if it needs the lower package's new API or behaviour, or if its install profile
   would otherwise be inconsistent. A compatible floor (`>=`) is left as is, and raised at the
   dependent's next natural release. The wave lead decides and records it in the wave plan for each
   dependent; the operator may override.
3. **The root is operator-validated.**
   - The wave never publishes the root `abstractframework`. It ends with a **candidate** for the
     operator, in four parts:
     1. every package below the root published and visible on its registry, with its exact version;
     2. the whole stack redeployed on the operator's machine at those versions;
     3. the website rebuilt LOCALLY and served for the operator to test (never pushed);
     4. a written report of every change in that global release.
   - The operator tests it personally, and only the operator declares it a release. After that GO the
     root is released, pinning exactly the tested versions; the operator alone pushes the site.
   - Root pins are `==`, never floors. The one-command installer therefore always installs the last
     published root's matrix, whatever newer lower packages appear. Today root 0.12.0 pins
     `abstractgateway==0.19.0` and `abstractcore==2.32.0` and keeps installing them.
4. **Pull before edits, branches and PRs** (operator, 2026-11-05).
   - Synchronization is work the agent performs automatically as task preparation. A stale-source
     check or an instruction for the operator to pull is not a substitute for doing the pull.
   - Before editing code or release metadata, fetch and pull the affected normal main checkout:
     `git fetch origin` then `git pull --ff-only origin main` while on main. Cross-package work
     starts with `bash scripts/pull.sh`, covering Python, browser apps and Rust source checkouts.
   - Repeat the fetch/pull immediately before creating a branch or worktree, and create it from
     freshly fetched `origin/main`.
   - Before submitting/updating a PR, pull normal main again. Fetch the feature branch's upstream,
     merge any upstream feature commits and `origin/main` it lacks, resolve conflicts, then validate
     the integrated code and push/create/update the PR. Refresh if upstream moves during validation.
   - Existing feature worktrees need the same upstream/main integration before edits. Pulling main
     elsewhere does not update their source. Ordinary merges preserve published commit identities.
   - Immediately after a GitHub merge, pull the corresponding normal main checkout. The coordinator
     owns this step for worker merges too, using the worker's repository and merge SHA.
   - Before final handoff, perform the all-repository pull sweep, then inspect status. If sources
     moved, refresh affected tests/builds/deployment before claiming the candidate is ready.
   - Preserve existing work; never reset, force-push or automatically stash someone else's edits.
     Resolve routine integration within the task and ask only for a real conflict/ownership decision.
     Read-only audits remain read-only unless synchronization was also authorized.
   - Build/start commands do not acquire a freshness gate or mandatory receipt workflow. The optional
     `check_workspace.py`/`status.sh --check` checks provide fresh-remote confirmation; they do not
     replace pulling. Source identity, publication, installed artifacts and operator acceptance
     remain distinct facts. Root/site publication stays held for the operator.

## Consequences

Positive:
- Small changes cost a light check, not the full matrix.
- A wave cuts fewer packages.
- What people install is a matrix the operator has used.

Negative:
- The tier is a judgement: a change filed as light can hide a shared code path. The reviewer's upgrade
  and the full gate on release branches catch most of these.
- A dependent left on an old floor stays installable with the newer lower package, but its next release
  must re-check that floor.
- Fixes reach installer users only after the operator's GO: lower packages on their registries are
  available to `pip install <package>` users first.

## Enforcement

- `abstract-release` and `release` (abstractskill 0.3.8) carry the tiers, the dependent policy, and
  the root order: candidate matrix, then the operator's GO, then the root.
- `scripts/ci_local.sh --tier light|full` implements the tiers (backlog 1116 delivers it with the gate).
  A repository with no test mapping yet falls back to the by-hand list in Decision 1.
- The root's pin tests (`tests/test_install_profiles.py`, `scripts/tests/test_inventory.sh`) keep root
  pins exact.
- Local AGENTS.md and installed/bundled `abstract-release` and `release` skills specify all
  preparation points in Decision 4. `scripts/pull.sh` performs the main-checkout synchronization;
  ordinary Git commands integrate active feature worktrees (backlog 1131).
- `scripts/status.sh --check` exposes optional live-remote confirmation; the default overview
  explicitly labels cached refs. Neither command replaces the actual preparation pull.

## Validation

- A tier-L change shows its tier and checks in the PR body.
- Each wave plan lists, per dependent, "re-released (needs X)" or "floor left (compatible)".
- No root release exists without the operator's recorded GO on the exact candidate (published packages,
  local redeploy, local website, written report).

## Related

- ADR 0050 (CI passes here before any push; amended to point to these tiers).
- ADR 0032 (package dependency boundaries and release order).
- The `abstract-release` and `release` skills (abstractskill 0.3.8).
