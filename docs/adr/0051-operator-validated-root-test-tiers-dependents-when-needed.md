# ADR 0051: Root Releases Are Operator-Validated; Test Tiers; Dependents Re-Release Only When Needed

Status: Accepted — operator rulings 2026-11-04:
- "a light test strategy (when you do small changes) and a full test strategy. imagine you change an icon, a
  dropdown, add a model etc. you shouldn't need to run the full test";
- "when we release a lower level package, we maybe don't need to rebuild every packages on top";
- "when I personally test a release and validate it, that's when the root framework gets released, never
  before, and it gets released with the specific versions i tested. root should be for people installing
  the framework".

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
2. **Dependents re-release only when needed.** When a lower package is released, a dependent is
   re-released only if it needs the lower package's new API or behaviour, or if its install profile
   would otherwise be inconsistent. A compatible floor (`>=`) is left as is, and raised at the
   dependent's next natural release. The wave plan states the decision for each dependent.
3. **The root is operator-validated.**
   - The wave never publishes the root `abstractframework`. It ends with a **candidate matrix**: the
     exact version of every package, all visible on their registries. That matrix is deployed locally
     in full for the operator.
   - The operator tests it and says GO. Only then is the root released, pinning exactly the tested
     versions.
   - Root pins are `==`, never floors. The one-command installer therefore always installs the last
     published root's matrix, whatever newer lower packages appear. Today root 0.12.0 pins
     `abstractgateway==0.19.0` and `abstractcore==2.32.0` and keeps installing them.

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
- The gate implements `--tier`.
- The root's pin tests (`tests/test_install_profiles.py`, `scripts/tests/test_inventory.sh`) keep root
  pins exact.

## Validation

- A tier-L change shows its tier and checks in the PR body.
- Each wave plan lists, per dependent, "re-released (needs X)" or "floor left (compatible)".
- No root release exists without the operator's recorded GO on the exact candidate matrix.

## Related

- ADR 0050 (CI passes here before any push; amended to point to these tiers).
- ADR 0032 (package dependency boundaries and release order).
- The `abstract-release` and `release` skills (abstractskill 0.3.8).
