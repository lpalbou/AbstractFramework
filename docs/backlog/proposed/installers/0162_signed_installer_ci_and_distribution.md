# Proposed: Signed Installer CI And Distribution

## Metadata
- Created: 2026-05-31
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: `docs/adr/reorg/2026-02-21_installer_manager_strategy.md`, `docs/adr/reorg/2026-02-21_macos_installer_manager.md`
- ADR impact: May revise existing ADR

## Context
The macOS installer prototype can build locally, but production installers need OS-specific
release pipelines, signing, notarization, checksum publication, rollback/repair logs, and
secret-safe automation.

## Current code reality
- `abstractinstallers/abstractframework-macos/BUILDING.md` describes local Tauri build steps.
- `docs/installers/security-and-os-blocks.md` describes signing and OS trust requirements.
- `docs/installers/release-and-manifest.md` describes a future release and manifest process.
- No production installer CI exists in a dedicated installer repository.

## Problem or opportunity
Unsigned GUI installers create friction and security warnings for exactly the users the installer
is meant to help. A production installer must feel trustworthy, recover cleanly, and avoid
embedding secrets in build artifacts.

## Proposed direction
After the installer repo and manifest contract exist, add signed installer CI:

- macOS signed/notarized `.dmg` or `.pkg`;
- Windows signed `.msi` or `.exe`;
- Linux AppImage first, with `.deb` later if demand justifies it;
- release manifest update with artifact URLs, checksums, signatures, minimum app versions, and
  rollback metadata;
- install logs that users can export for support;
- no hardcoded API keys or provider secrets in installer artifacts.

## Why it might matter
This is the difference between a prototype and a real non-technical install path. OS-native trust,
rollback, and support logs reduce failed installs and support load.

## Promotion criteria
- `AbstractInstallers` exists as a dedicated repo.
- macOS prototype is migrated or rebuilt there.
- Generated manifest contract exists and can reference native installer artifacts.
- Signing identities and GitHub environment secrets are available.

## Validation ideas
- CI builds signed artifacts on release tags.
- macOS notarization gate passes.
- Checksums in the manifest match uploaded artifacts.
- A clean machine can install, run doctor checks, launch Gateway/Flow, and uninstall or repair.
- Secrets scan confirms no provider/API keys are bundled.

## Non-goals
- Do not implement auto-update before basic install/repair is solid.
- Do not ship unsigned artifacts as "production".
- Do not use installer CI to publish Python packages; Python package release remains in package
  repos and the root `abstractframework` profile.

## Guidance for future agents
Treat signing and rollback as release gates, not polish. A non-technical installer that trips OS
security warnings is not production-ready.
