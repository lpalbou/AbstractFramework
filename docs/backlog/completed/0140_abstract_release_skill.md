# Completed: Abstract Release Skill

## Metadata
- Created: 2026-05-24
- Completed: 2026-05-24
- Status: Completed

## ADR status
- Governing ADRs: ADR-0034, ADR-0032
- ADR impact: None. This implements release-process tooling around the accepted release-order ADR.

## Context

Framework releases span many package repositories and package directories. ADR-0034 requires
topological release order by published dependency floors, PyPI visibility, branch CI gates, and
Gateway/root package discipline. Releasing package by package manually is slow and easy to get
wrong when lower package versions move.

## Work Completed

- Created a new Codex skill at `~/.codex/skills/abstract-release`.
- Added a read-only release planner script:
  - discovers Python and npm package manifests;
  - resolves dynamic Python package versions;
  - detects package-local dirty state across nested git roots;
  - computes dependency-aware release order;
  - identifies dirty packages plus downstream packages needing dependency-floor review;
  - flags root `abstractframework` profile pin drift against local package versions and
    `abstractframework.RELEASE_VERSIONS`.
- Added a PyPI visibility gate script for released Python versions.
- Added skill references for the framework release process, approval packet, stop rules, backlog
  trace policy, and package discovery behavior.
- Validated the skill with `quick_validate.py`.

## Decisions

- Keep `abstract-release` as a read-only planner/orchestrator by default, not an end-to-end
  publisher.
- Continue using the package-local `$release` skill for version, changelog, validation, CI/CD,
  tagging, publishing, and post-publish checks.
- Require `$coredoc` for release-visible docs and `$backlog` for traceability/follow-ups.
- Stop before irreversible actions unless the user approves the exact package, version, ref,
  workflow/registry, dirty-state classification, and dependency-floor changes.

## Validation

- `python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py ~/.codex/skills/abstract-release`
- `python ~/.codex/skills/abstract-release/scripts/abstract_release_plan.py /Users/albou/tmp/abstractframework --json -o /tmp/abstract-release-plan.json`
- `python ~/.codex/skills/abstract-release/scripts/abstract_release_plan.py /Users/albou/tmp/abstractframework`

## Follow-up

- Consider adding CI-status probing and clean registry-install smoke helpers after the package
  release workflows are normalized enough for safe automation.
