# 1132 — Final stable AbstractFramework release

> Package: AbstractFramework, AbstractSkill
> Type: task
> Created: 2026-11-06
> Priority: high
> Labels: release

## Summary

Publish pending AbstractSkill changes, then release the root package with the existing published component versions. The operator explicitly confirmed that no other packages should be released again.

## Current code reality

Root 0.12.0 pins an older matrix. AbstractSkill 0.3.10 has been published. Root 0.13.0 will pin existing registry versions, including Camera, Python Avatar and Notes, and record shared npm library and TUI extension versions separately from launchable applications.

## Scope

Only AbstractSkill and the root release. Component release preparations were archived on local branches and their normal main checkouts restored; the extra Avatar PR was closed without merging or publishing. Unreleased component fixes are explicitly outside this release. Website publication and Apple uploads remain separate.

## Acceptance criteria

- [x] Publish Skill 0.3.10 after full local gates, independent review and green GitHub checks.
- [x] Pin existing registry-visible versions and align installers, manifest and docs.
- [x] Verify registry installation, root CI and release, then pull every main checkout.

## Receipts

- Matrix: untracked/final-release-target-matrix.json.
- Skill PR: https://github.com/lpalbou/AbstractSkill/pull/8 ; release: https://github.com/lpalbou/AbstractSkill/actions/runs/42298584658.

- All 35 component versions verified on their registries; fresh Python 3.12 installation resolved all 15 Python pins and passed `uv pip check` (136 packages).
- Independent root review approved the release diff; publication remains gated by local and GitHub CI.
- Local full gate found an existing fixed-PID test assumption (PID 4242 belonged to a real shell); the test now explicitly simulates unavailable inspection. Installer command assertions also allow the newly explicit component requirements. Both are root-only test changes.
- Root PR: https://github.com/lpalbou/AbstractFramework/pull/72 (Test and build, Bootstrap smoke on Ubuntu, macOS and Windows green), merge commit a90c25d; tag v0.13.0.
- Release run: https://github.com/lpalbou/AbstractFramework/actions/runs/42305102886 (test, build and PyPI publish green); PyPI abstractframework 0.13.0 uploaded 2026-11-06T22:36Z; release page https://github.com/lpalbou/AbstractFramework/releases/tag/v0.13.0.
- Registry resolution from PyPI with Python 3.12: the light, Apple (macOS 14+ arm64) and GPU (Linux x86_64) profiles each resolve to exactly the 15 pinned Python versions plus the root.
- Final sweep: scripts/pull.sh and scripts/status.sh report all 23 repositories on main, clean and up to date.
- Known follow-up: README.md's component table still says AbstractNote is "Not part of the `abstractframework` profiles", which contradicts the 0.13.0 pins; fix at the next root release.
