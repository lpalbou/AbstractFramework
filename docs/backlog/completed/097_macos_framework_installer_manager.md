# 097 — macOS Framework Installer Manager (Rust)

**Status**: Completed  
**Date**: 2026-02-21  
**Priority**: High (distribution + UX)  
**Components**: abstractinstallers

## Summary

Create a macOS‑native installer manager (Rust/Tauri) that installs the full
AbstractFramework with customizable component selection, following the
manifest‑driven installer strategy.

## Reason

The current Python installer prototype is useful for iteration but does not
deliver a production‑grade macOS experience. We need a real macOS installer that
is customizable, UI‑driven, and aligned with the framework’s modular design.

## Scope

### In scope

- A macOS installer manager prototype using Rust/Tauri.
- Manifest‑driven component selection (full vs custom).
- Install via PyPI/pip into an isolated venv (no Git clone).
- Clear dependency checks (Python/Node) with explicit `#FALLBACK` warnings.
- A basic UI flow: select components, choose install dir, run install, view logs.

### Out of scope

- Production signing/notarization.
- Windows/Linux installers.
- Full per‑app packaging of native desktop apps.
- Automatic update/rollback (planned later).

## Dependencies

- Tauri toolchain (Rust + Node)
- AbstractFramework package versions (PyPI)
- Installer manifest schema from `docs/installers/release-and-manifest.md`

## Expected outcomes

- A macOS installer manager prototype in `abstractinstallers/`.
- Manifest‑driven install plan with component selection.
- Clear UX that matches gateway‑first defaults and avoids silent fallbacks.

## Report

### Summary

- Added a macOS installer manager prototype at `abstractinstallers/abstractframework-macos`.
- Implemented a Rust/Tauri backend with manifest‑driven component resolution and pip/npm install steps.
- Built a lightweight UI that supports Full vs Custom installs and streams logs.
- Added a local manifest describing the full framework and component dependencies.
- Updated installer docs to acknowledge the macOS prototype.

### Tests

- `cargo tauri build` (macOS app bundle)

### Notes

- Build instructions live in `abstractinstallers/abstractframework-macos/BUILDING.md`.
- Missing prerequisites emit explicit `#FALLBACK` warnings in the installer log.
- Bundle output: `abstractinstallers/abstractframework-macos/src-tauri/target/release/bundle/macos/AbstractFramework Installer.app`.
