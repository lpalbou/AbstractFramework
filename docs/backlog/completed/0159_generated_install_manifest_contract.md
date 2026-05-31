# Proposed: Generated Install Manifest Contract

## Metadata
- Created: 2026-05-31
- Status: Completed
- Completed: 2026-05-31

## ADR status
- Governing ADRs: `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`, `docs/adr/0034-framework-release-sequence-and-gates.md`
- ADR impact: May revise existing ADR

## Context
Installers need a machine-readable description of AbstractFramework release profiles, components,
versions, package extras, prerequisites, and launch commands. Today the macOS prototype uses a
local `manifest.local.json`, and release work had to patch that file manually.

## Current code reality
- Root `pyproject.toml` pins the release profile. The Light profile is the base install;
  `apple` and `gpu` are the hardware-local extras.
- `abstractframework.RELEASE_VERSIONS` duplicates the release matrix for runtime inspection.
- `abstractframework.install_manifest.build_install_manifest()` generates the installer-facing
  manifest from root constants.
- `docs/installers/install-manifest.json` is checked in and tested against the generator.
- `docs/installers/install-manifest.schema.json` defines the current schema shape.
- `abstractframework manifest --check docs/installers/install-manifest.json` validates drift.

## Problem or opportunity
Hand-maintained installer manifests drift. Drift is risky because installers are aimed at users
least able to diagnose version/profile mistakes.

## Proposed direction
Create a generated, versioned install manifest contract owned by `AbstractFramework`. The manifest
should be produced from root pins and profile definitions, then consumed by installer apps.

The contract should include:

- framework version and manifest schema version;
- package pins and package registry type;
- install profiles: Light, Apple, GPU;
- per-profile pip requirements and npm app requirements where applicable;
- Python/Node/platform prerequisites;
- post-install commands such as doctor/config/launch;
- checksum/signature fields for native installer artifacts when applicable;
- compatibility metadata for minimum installer-manager version.

The first implementation can generate a checked-in JSON file under `docs/installers/` or
`abstractframework/assets/`, then later publish it as a GitHub release asset.

## Why it might matter
A generated contract makes the installer trustworthy and reduces duplicated release logic. It also
lets a GUI installer, CLI doctor, docs, and future updater reason about the same release profile.

## Promotion criteria
- Installer app source moves to a separate repository.
- Any release requires editing both root pins and installer manifests.
- Install profile tests need to cover more than the current local macOS prototype.

## Validation ideas
- Generate the manifest from `pyproject.toml` and `abstractframework.RELEASE_VERSIONS`.
- Validate it against a JSON schema.
- Assert generated manifest package pins match root pins in tests.
- Run a dry-run installer plan from the generated manifest for Light, Apple, and GPU profiles.

## Non-goals
- Do not make installers infer package versions from PyPI "latest".
- Do not make the manifest execute arbitrary scripts.
- Do not embed API keys, user secrets, or machine-local paths.

## Guidance for future agents
The manifest should be boring and explicit. Prefer a small schema that covers real installer needs
over a flexible plugin system that can become a hidden package manager.

## Completion report
- Added `abstractframework/install_manifest.py`.
- Added `docs/installers/install-manifest.json` and
  `docs/installers/install-manifest.schema.json`.
- Added `abstractframework manifest`, including `--write` and `--check`.
- Updated install-profile tests so the checked-in manifest must match the generator and root pins.
- Left signed native artifact metadata as explicit future work in item 0162.
