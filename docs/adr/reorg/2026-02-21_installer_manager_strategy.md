# ADR: Installer manager + per-app packaging

## Status
Proposed — 2026-02-21

## Context
- AbstractFramework installs via pip + npx and requires environment configuration.
- Non-technical users struggle with CLI installs and env vars.
- The architecture is gateway-first and modular, spanning Python services and web UIs.
- OS security policies require signed, OS-native installer artifacts.

## Decision
- Create a cross-platform Installer Manager (one codebase, OS-specific builds).
- Distribute per-app packages that the manager can install independently.
- Use a signed, manifest-driven release model with checksum verification.
- Default to gateway-first installs with guided configuration (no manual env vars).
- Any fallback behavior must emit `#FALLBACK` warnings; truncation must be tagged
  `#TRUNCATION` when used for UI-only display.

## Consequences
- We must maintain a build pipeline for macOS, Windows, and Linux artifacts.
- Code signing and notarization become mandatory for smooth installs.
- The manager becomes a new, central product that must be maintained over time.
- Components with OS-specific support must be surfaced clearly in the UI.
