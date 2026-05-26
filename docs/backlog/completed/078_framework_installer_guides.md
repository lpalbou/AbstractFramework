# Backlog: Framework installer guides and strategy

## Summary
Create a full set of installer guides for AbstractFramework, describing a cross-platform
manager + per-app packaging strategy, user journeys, OS security requirements, and a
manifest-driven release pipeline.

## Why
- Current installation relies on terminal commands and environment variables that are
  too complex for non-technical users.
- The framework is modular and gateway-first, which benefits from a guided installer
  that can assemble the right components.
- A documented strategy is needed before any packaging or installer implementation.

## Scope
### In scope
- Add `docs/installers/` with detailed strategy, component mapping, user journeys,
  OS security constraints, and release/manifest guidance.
- Capture the proposed installer strategy in an ADR.
- Update core documentation to link to installer guidance.
- Record installer-related insights in `AGENTS.md`.

### Out of scope
- Building or shipping an actual installer.
- Refactoring application code to be installer-ready.
- Producing signed artifacts or release manifests.

## Dependencies
- Packaging tool decisions (e.g., Tauri/Electron/Flutter, PyInstaller/Nuitka).
- Code-signing certificates and notarization accounts for each OS.
- A hosting location for signed artifacts + manifest (GitHub Releases, CDN).

## Expected outcomes
- Clear, user-oriented installer documentation tailored to AbstractFramework.
- A consistent strategy that aligns with gateway-first architecture and modular apps.
- A concrete, phased implementation plan for future work.

## Full Report
- **Summary**: Documented a two-tier installer strategy (manager + per-app packages),
  mapped component packaging, and added step-by-step user journeys aligned with the
  gateway-first architecture.
- **Implementation**:
  - Added installer docs under `docs/installers/` (strategy, components, journeys,
    OS security, release/manifest, operations, implementation plan).
  - Added ADR `docs/adr/2026-02-21_installer_manager_strategy.md` to capture the
    proposed installer decision.
  - Updated core docs (`README.md`, `docs/README.md`, `docs/getting-started.md`,
    `docs/architecture.md`, `docs/api.md`, `docs/faq.md`) to reference installer
    guidance.
  - Logged installer strategy insights in `AGENTS.md`.
- **Tests**: Not run (documentation-only change).
