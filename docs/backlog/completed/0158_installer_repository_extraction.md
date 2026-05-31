# Proposed: Installer Repository Extraction

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: `docs/adr/reorg/2026-02-21_installer_manager_strategy.md`, `docs/adr/reorg/2026-02-21_macos_installer_manager.md`
- ADR impact: May revise existing ADR

## Context
The root `AbstractFramework` repository currently contains `abstractinstallers/` as a sandbox for
installer experiments. The root PyPI package does not include these files in the wheel or sdist,
but the source tree now mixes Python release-profile concerns with Rust/Tauri installer product
code.

## Current code reality
- `AbstractInstallers` now exists at `https://github.com/lpalbou/AbstractInstallers`.
- The root `AbstractFramework` repo no longer tracks `abstractinstallers/`.
- `pyproject.toml` still only packages `abstractframework*`.
- `docs/installers/` already documents an installer-manager strategy.

## Problem or opportunity
Installer applications have a different lifecycle from the Python meta-package: native app
toolchains, OS signing, notarization, updater artifacts, platform CI, and support logs. Keeping
that source in the root repo risks confusing release ownership and encouraging hand-maintained
manifest drift.

## Proposed direction
Create a separate GitHub repository named `AbstractInstallers` and move production installer app
source there once the manifest contract is ready. Keep root `AbstractFramework` as the versioned
Python install profile, docs hub, and manifest source of truth.

Use `AbstractInstallers` rather than `AbstractInstaller`, `AbstractInstall`, or `AbstractSetup`:

- `AbstractInstallers` matches the existing directory name and supports multiple artifacts
  (`macOS`, `Windows`, `Linux`, future helper apps).
- Plural naming is clearer for a repo that will hold more than one installer target and shared
  installer infrastructure.
- `AbstractInstaller` sounds like a single application rather than a repo owning several packages.
- `AbstractInstall` reads like a command or package action, not a product/repo.
- `AbstractSetup` is friendlier but less precise; it could mean first-run configuration rather
  than installation, updates, repair, signing, and distribution.

## Why it might matter
Separating the installer repo keeps the framework package clean and makes native release
engineering visible. It also lets installer CI evolve without blocking Python package releases.

## Promotion criteria
- The generated install manifest contract exists or has an accepted schema.
- The macOS prototype needs production signing/distribution work.
- Installer code changes start dominating root framework diffs or release planning.

## Validation ideas
- Verify root `abstractframework` wheel/sdist still exclude installer source.
- Verify `AbstractInstallers` can consume a released manifest from `AbstractFramework`.
- Build the macOS prototype from the new repo without path assumptions back into the root repo.

## Non-goals
- This proposal does not authorize deleting installer docs from `AbstractFramework`.
- This proposal does not require moving historical backlog or ADR records.
- This proposal does not decide the final UI toolkit beyond preserving the current Tauri prototype
  as the first migration candidate.

## Guidance for future agents
Treat `AbstractFramework` as the release-profile authority and `AbstractInstallers` as a consumer.
If a future design requires installers to mutate framework release pins directly, re-check the
architecture before implementing it.

## Completion report
- Moved the tracked installer prototype source into the standalone `AbstractInstallers` repository.
- Added repository-level `.gitignore`, `LICENSE`, and README updates there.
- Pushed `AbstractInstallers` commit `3618978` to `https://github.com/lpalbou/AbstractInstallers`.
- Removed tracked `abstractinstallers/` files and leftover local build artifacts from the root
  `AbstractFramework` checkout.
- Updated root docs to point users and future installer work at the standalone repository.
